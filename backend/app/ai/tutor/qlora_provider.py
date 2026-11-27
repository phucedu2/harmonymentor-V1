"""Nhà cung cấp LLM ngoại tuyến dùng mô hình Qwen3-4B-Instruct 4-bit + QLoRA Adapter (Mốc 7).

Hỗ trợ hai phương thức thực thi minh bạch dưới cùng giao diện LLMProvider:
  1. In-process GPU (khi backend chạy trực tiếp trên Linux / WSL2 có CUDA + Unsloth).
  2. Persistent WSL2 GPU Worker qua stdin/stdout cô lập mạng (`unshare -rn`, `HF_HUB_OFFLINE=1`)
     khi backend FastAPI chạy trên Windows host mà GPU đặt trong WSL2.

Mọi lỗi sinh văn bản / hết ngân sách token đều chuyển thành LLMUnavailable để ai_tutor_service
tự động rơi về câu trả lời dự phòng an toàn theo luật (không trả HTTP 500)."""

from __future__ import annotations

import atexit
import hashlib
import json
import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

from .llm import LLMResult, LLMUnavailable
from .local_qlora import BLOCK, CITE

log = logging.getLogger("harmonymentor.qlora_provider")

DEFAULT_BASE_MODEL = "unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit"
DEFAULT_MODEL_REVISION = "7744afa8566e264af1a92a806d8d9aae00cc7c78"
DEFAULT_MAX_SEQ = 1792

SHORT_SYSTEM = (
    "Bạn là trợ giảng nhạc lý của HarmonyMentor. "
    "Trả lời bằng JSON TutorAnswer, trích dẫn chỉ từ LESSON_CHUNKS, không tự suy đoán các nốt."
)
SHORT_SYSTEM_GENERAL = (
    "Bạn là trợ giảng âm nhạc của HarmonyMentor. "
    "Câu hỏi này chưa có đoạn bài học khớp (LESSON_CHUNKS rỗng). "
    "Trả lời ngắn gọn bằng JSON TutorAnswer, không tự suy đoán các nốt ngoài ENGINE_FACTS."
)


def normalize_qlora_user_prompt(user: str) -> tuple[str, str]:
    """Chuẩn hóa khối dữ liệu từ ai_tutor_service.py cho khớp tuyệt đối với phân phối huấn luyện QLoRA."""
    is_general = user.lstrip().startswith("MODE: general_music")
    sys_msg = SHORT_SYSTEM_GENERAL if is_general else SHORT_SYSTEM

    def _clean_match(match: Any) -> str:
        kind, body = match.group(1), match.group(2)
        if kind == "LESSON_CHUNKS":
            try:
                rows = json.loads(body)
                if isinstance(rows, list):
                    trimmed = [
                        {k: r[k] for k in (*CITE, "text") if k in r}
                        for r in rows
                        if isinstance(r, dict)
                    ]
                    return f'<<<HM_DATA kind="LESSON_CHUNKS">>>\n{json.dumps(trimmed, ensure_ascii=False)}\n<<<HM_END>>>'
            except Exception:  # noqa: BLE001
                pass
        return match.group(0)

    normalized_user = BLOCK.sub(_clean_match, user)
    return sys_msg, normalized_user


def win_to_wsl_path(raw_path: str) -> str:
    """Đổi đường dẫn Windows (ví dụ F:\\HarmonyMentor\\...) sang /mnt/f/HarmonyMentor/... cho WSL2."""
    p = raw_path.strip()
    if p.startswith("/"):
        return p
    if len(p) >= 2 and p[1] == ":":
        drive = p[0].lower()
        rest = p[2:].replace("\\", "/").lstrip("/")
        return f"/mnt/{drive}/{rest}"
    return p.replace("\\", "/")


def _verify_snapshot_dir(snapshot_root: Path, repo: str, revision: str) -> Path:
    cache = (snapshot_root / "cache").resolve(strict=True)
    snap = (cache / f"models--{repo.replace('/', '--')}" / "snapshots" / revision).resolve(strict=True)
    report = json.loads((snapshot_root / "verification-report.json").read_text(encoding="utf-8"))
    manifest = json.loads((snapshot_root / "manifest.json").read_text(encoding="utf-8"))
    entries = {x["path"]: x for x in manifest}
    if (report.get("repository") != repo or report.get("revision") != revision
            or Path(report.get("snapshot", "")) != snap
            or not {"model.safetensors", "config.json", "tokenizer_config.json"} <= set(entries)):
        raise RuntimeError("Snapshot identity mismatch")
    for name in ("config.json", "tokenizer_config.json"):
        cfg_path = (snap / name).resolve(strict=True)
        if json.loads(cfg_path.read_text(encoding="utf-8")).get("auto_map"):
            raise RuntimeError("Custom loader auto_map rejected")
    # Kiểm nhanh metadata kích thước của model.safetensors để tải nhanh lúc phục vụ mà vẫn đảm bảo đúng bản.
    ms_info = entries["model.safetensors"]
    ms_path = (snap / "model.safetensors").resolve(strict=True)
    if ms_path.stat().st_size != ms_info["size"] or ms_info["lastCommit"]["id"] != revision:
        raise RuntimeError("Snapshot model.safetensors size/revision mismatch")
    for name, item in entries.items():
        if name == "model.safetensors":
            continue
        fp = (snap / name).resolve(strict=True)
        if fp.stat().st_size != item["size"]:
            raise RuntimeError(f"Snapshot {name} size mismatch")
        lfs = item.get("lfs")
        digest = hashlib.sha256() if lfs else hashlib.sha1(f'blob {item["size"]}\0'.encode())
        digest.update(fp.read_bytes())
        if digest.hexdigest() != (lfs["oid"] if lfs else item["oid"]):
            raise RuntimeError(f"Snapshot {name} checksum mismatch")
    return snap


class _InProcessBackend:
    def __init__(self, adapter_dir: Path, snapshot_root: Path, model_name: str, revision: str, max_seq: int):
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_DATASETS_OFFLINE"] = "1"
        import torch
        from unsloth import FastLanguageModel
        from peft import PeftModel
        from . import local_qlora as lq

        if not torch.cuda.is_available():
            raise LLMUnavailable("unavailable")
        snap = _verify_snapshot_dir(snapshot_root, model_name, revision)
        if not (adapter_dir / "adapter_config.json").exists():
            raise LLMUnavailable("unavailable")
        lq.MAX_SEQ = max_seq
        base, tok = FastLanguageModel.from_pretrained(
            model_name=str(snap),
            max_seq_length=max_seq,
            dtype=None,
            load_in_4bit=True,
            local_files_only=True,
            trust_remote_code=False,
            token=False,
            use_exact_model_name=True,
            use_safetensors=True,
        )
        peft_model = PeftModel.from_pretrained(base, str(adapter_dir), is_trainable=False, local_files_only=True)
        FastLanguageModel.for_inference(peft_model)
        peft_model.eval()
        self._model = peft_model
        self._tok = tok
        self._lq = lq
        self._lock = threading.Lock()

    def infer(self, sys_msg: str, user_msg: str, constrained: bool) -> dict[str, Any]:
        with self._lock:
            messages = [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}]
            _, prefix = self._lq.chat_prefix(self._tok, messages)
            tokens_in = len(self._tok(prefix, add_special_tokens=False)["input_ids"])
            res = self._lq.generate(self._model, self._tok, messages, constrained=constrained)
            return {"raw": res.raw, "issues": list(res.issues), "tokens_in": tokens_in, "tokens_out": res.tokens}

    def close(self) -> None:
        pass


class _WSLWorkerBackend:
    """Giữ một tiến trình WSL2 cô lập mạng (`unshare -rn`) nạp sẵn QLoRA trong VRAM để Windows FastAPI gọi nhanh."""

    def __init__(self, wsl_python: str, repo_root: Path, adapter_dir: str, snapshot_root: str,
                 model_name: str, revision: str, max_seq: int, timeout_s: float):
        self._wsl_python = wsl_python
        self._repo_wsl = win_to_wsl_path(str(repo_root))
        self._adapter_wsl = win_to_wsl_path(adapter_dir)
        self._snap_wsl = win_to_wsl_path(snapshot_root)
        self._model_name = model_name
        self._revision = revision
        self._max_seq = max_seq
        self._timeout_s = max(timeout_s, 60.0)
        self._proc: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()
        atexit.register(self.close)

    def _ensure_started(self) -> subprocess.Popen[str]:
        if self._proc is not None and self._proc.poll() is None:
            return self._proc
        # Chạy dưới dạng module (-m) để import tương đối `from .llm import ...` hoạt động; chạy theo đường dẫn tệp
        # .py thì Python báo "attempted relative import with no known parent package" trước khi nạp model.
        backend_dir = f"{self._repo_wsl}/backend"
        bash_cmd = (
            "export HOME=/tmp/hm_qlora_srv_home TMPDIR=/tmp/hm_qlora_srv_tmp "
            "HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 TOKENIZERS_PARALLELISM=false "
            f"PYTHONPATH='{backend_dir}'; "
            "mkdir -p /tmp/hm_qlora_srv_home /tmp/hm_qlora_srv_tmp; "
            f"cd '{backend_dir}'; "
            f"exec unshare -rn '{self._wsl_python}' -B -u -m app.ai.tutor.qlora_provider --worker "
            f"--adapter-dir '{self._adapter_wsl}' --snapshot-root '{self._snap_wsl}' "
            f"--base-model '{self._model_name}' --revision '{self._revision}' --max-seq {self._max_seq}"
        )
        self._proc = subprocess.Popen(
            ["wsl.exe", "-e", "bash", "-c", bash_cmd],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        assert self._proc.stdout is not None
        ready_line = self._proc.stdout.readline().strip()
        if not ready_line:
            err = self._proc.stderr.read() if self._proc.stderr else ""
            self.close()
            log.warning("qlora_wsl_boot_failed err_len=%d", len(err))
            raise LLMUnavailable("unavailable")
        info = json.loads(ready_line)
        if info.get("status") != "ready":
            self.close()
            raise LLMUnavailable("unavailable")
        return self._proc

    def infer(self, sys_msg: str, user_msg: str, constrained: bool) -> dict[str, Any]:
        with self._lock:
            proc = self._ensure_started()
            assert proc.stdin is not None and proc.stdout is not None
            req = json.dumps({"system": sys_msg, "user": user_msg, "constrained": constrained}, ensure_ascii=False)
            try:
                proc.stdin.write(req + "\n")
                proc.stdin.flush()
                line = proc.stdout.readline()
                if not line:
                    self.close()
                    raise LLMUnavailable("unavailable")
                resp = json.loads(line)
                if "error" in resp:
                    raise LLMUnavailable("unavailable")
                return resp
            except LLMUnavailable:
                raise
            except Exception as exc:  # noqa: BLE001
                log.warning("qlora_wsl_infer_error type=%s", type(exc).__name__)
                self.close()
                raise LLMUnavailable("unavailable") from exc

    def close(self) -> None:
        if self._proc is not None:
            try:
                if self._proc.stdin:
                    self._proc.stdin.close()
                self._proc.terminate()
                self._proc.wait(timeout=3)
            except Exception:  # noqa: BLE001
                try:
                    self._proc.kill()
                except Exception:  # noqa: BLE001
                    pass
            self._proc = None


class LocalQLoRAProvider:
    """LLMProvider chạy cục bộ hoàn toàn ngoại tuyến bằng Qwen3-4B + QLoRA Adapter."""

    def __init__(
        self,
        *,
        adapter_dir: str,
        snapshot_root: str,
        base_model: str = DEFAULT_BASE_MODEL,
        revision: str = DEFAULT_MODEL_REVISION,
        wsl_python: str = "/home/thang/hm-qlora-resolve-guj5dVKF/venv/bin/python",
        max_seq: int = DEFAULT_MAX_SEQ,
        constrained: bool = False,
        timeout_s: float = 60.0,
    ):
        self.model = f"qlora:{Path(adapter_dir).parent.name or 'local'}"
        self.constrained = constrained
        self._adapter_dir = adapter_dir
        self._snapshot_root = snapshot_root
        self._base_model = base_model
        self._revision = revision
        self._wsl_python = wsl_python
        self._max_seq = max_seq
        self._timeout_s = timeout_s
        self._backend: _InProcessBackend | _WSLWorkerBackend | None = None
        self._init_lock = threading.Lock()

    def _get_backend(self) -> _InProcessBackend | _WSLWorkerBackend:
        if self._backend is None:
            with self._init_lock:
                if self._backend is None:
                    repo_root = Path(__file__).resolve().parents[4]
                    if os.name == "nt":
                        self._backend = _WSLWorkerBackend(
                            wsl_python=self._wsl_python,
                            repo_root=repo_root,
                            adapter_dir=self._adapter_dir,
                            snapshot_root=self._snapshot_root,
                            model_name=self._base_model,
                            revision=self._revision,
                            max_seq=self._max_seq,
                            timeout_s=self._timeout_s,
                        )
                    else:
                        self._backend = _InProcessBackend(
                            adapter_dir=Path(self._adapter_dir),
                            snapshot_root=Path(self._snapshot_root),
                            model_name=self._base_model,
                            revision=self._revision,
                            max_seq=self._max_seq,
                        )
        return self._backend

    def generate(self, system: str, user: str, schema: dict[str, Any], max_output_tokens: int | None = None) -> LLMResult:
        start = time.perf_counter()
        sys_msg, norm_user = normalize_qlora_user_prompt(user)
        backend = self._get_backend()
        out = backend.infer(sys_msg, norm_user, self.constrained)
        raw = out.get("raw") or ""
        issues = out.get("issues") or []
        if not raw or "context_budget" in issues or "output_budget" in issues:
            raise LLMUnavailable("unavailable")
        # Nếu giải mã tự do gặp lỗi cú pháp JSON hiếm gặp, tự thử lại ngay 1 lần với grammar constrained=True
        if ("json" in issues or "schema" in issues) and not self.constrained:
            out = backend.infer(sys_msg, norm_user, True)
            raw = out.get("raw") or ""
            if not raw:
                raise LLMUnavailable("unavailable")
        latency_ms = int((time.perf_counter() - start) * 1000)
        return LLMResult(
            text=raw,
            model=self.model,
            tokens_in=out.get("tokens_in"),
            tokens_out=out.get("tokens_out"),
            latency_ms=latency_ms,
            attempts=1,
        )

    def close(self) -> None:
        if self._backend is not None:
            self._backend.close()
            self._backend = None


def _worker_main() -> None:
    """Điểm vào của tiến trình con chạy trong WSL2 (`unshare -rn`). Giao thức JSON-lines qua stdin/stdout."""
    import argparse

    real_stdout = sys.stdout
    sys.stdout = sys.stderr  # Chuyển mọi cảnh báo của thư viện sang stderr để giữ sạch kênh JSON trên stdout

    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", action="store_true")
    ap.add_argument("--adapter-dir", required=True)
    ap.add_argument("--snapshot-root", required=True)
    ap.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    ap.add_argument("--revision", default=DEFAULT_MODEL_REVISION)
    ap.add_argument("--max-seq", type=int, default=DEFAULT_MAX_SEQ)
    args = ap.parse_args()

    backend = _InProcessBackend(
        adapter_dir=Path(args.adapter_dir),
        snapshot_root=Path(args.snapshot_root),
        model_name=args.base_model,
        revision=args.revision,
        max_seq=args.max_seq,
    )
    real_stdout.write(json.dumps({"status": "ready"}) + "\n")
    real_stdout.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            res = backend.infer(req["system"], req["user"], bool(req.get("constrained", False)))
            real_stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
            real_stdout.flush()
        except Exception as exc:  # noqa: BLE001
            real_stdout.write(json.dumps({"error": type(exc).__name__}) + "\n")
            real_stdout.flush()


if __name__ == "__main__":
    _worker_main()
