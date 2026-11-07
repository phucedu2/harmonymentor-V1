"""Mô hình nhúng chạy cục bộ cho AI Tutor (ADR-017, quyết định góp ý thầy 1A–4A, 06/11/2026).

multilingual-e5-small (118 triệu tham số, 384 chiều, đọc 512 token) chạy bằng onnxruntime trên CPU, không cần torch,
không gọi mạng lúc chạy. Vì sao không dùng MiniLM của tài liệu 2.1: MiniLM chỉ đọc 128 token, 21/45 đoạn dài hơn
nên bị cắt đuôi; đo GĐ0 R@1 45,7% so với 85,7% của e5-small (docs/giai-doan/ai-gop-y/00_KIEM_KE_RAG.md).

e5 được huấn luyện với tiền tố "query: " cho câu hỏi và "passage: " cho đoạn; thiếu tiền tố thì điểm kém hẳn.
Vector = trung bình các token (bỏ token đệm) rồi chuẩn hóa độ dài 1, đúng cách của mô hình gốc.

File mô hình không nằm trong git (470 MB). Tải bằng `python -m app.ai.local_embedder download` (Dockerfile làm sẵn),
có kiểm SHA-256 để chắc đúng bản đã đo."""

from __future__ import annotations

import hashlib
import os
import sys
import urllib.request
from pathlib import Path
from typing import Sequence

from .embedder import EmbeddingUnavailable, normalize

HF_REPO = "intfloat/multilingual-e5-small"
HF_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"   # cố định bản đã đo GĐ0, không tự lên bản mới
FILES = {
    "model.onnx": ("onnx/model.onnx", "ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665"),
    "tokenizer.json": ("onnx/tokenizer.json", "0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39"),
}
MODEL_NAME = "multilingual-e5-small"
DIM = 384
MAX_TOKENS = 512
DEFAULT_DIR = Path(__file__).resolve().parents[2] / "models" / MODEL_NAME
PREFIX = {"RETRIEVAL_QUERY": "query: ", "RETRIEVAL_DOCUMENT": "passage: "}


def model_dir() -> Path:
    return Path(os.getenv("LOCAL_EMBED_DIR", str(DEFAULT_DIR)))


def available(path: Path | None = None) -> bool:
    p = path or model_dir()
    return all((p / name).exists() for name in FILES)


def model_name(path: Path) -> str:
    """Tên mô hình = khóa ngưỡng trong router_thresholds.json. Bản fine-tune GĐ2b ghi tên riêng trong model_info.json
    nên KHÔNG dùng nhầm ngưỡng của bản gốc (điểm hai bản khác thang)."""
    info = path / "model_info.json"
    if info.exists():
        import json

        return json.loads(info.read_text(encoding="utf-8")).get("name") or MODEL_NAME
    return MODEL_NAME


class LocalEmbedder:
    """Cùng giao diện Embedder (model, dim, embed) với GeminiEmbedder để retriever không phải biết khác nhau."""

    model = MODEL_NAME
    local = True            # retriever tự tính vector đoạn lúc dùng (không cần file tính sẵn)
    dim = DIM

    def __init__(self, path: Path | None = None, threads: int = 2):
        import onnxruntime as ort
        from tokenizers import Tokenizer

        p = path or model_dir()
        if not available(p):
            raise EmbeddingUnavailable("local_model_missing")
        self.model = model_name(p)
        self.tok = Tokenizer.from_file(str(p / "tokenizer.json"))
        self.tok.enable_truncation(MAX_TOKENS)
        self.tok.enable_padding(pad_id=1, pad_token="<pad>")
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = threads   # máy nhóm là laptop: không chiếm hết nhân CPU
        self.sess = ort.InferenceSession(str(p / "model.onnx"), opts, providers=["CPUExecutionProvider"])
        self._inputs = {i.name for i in self.sess.get_inputs()}

    def __repr__(self) -> str:
        return f"LocalEmbedder(model={self.model!r}, dim={self.dim})"

    def embed(self, texts: Sequence[str], task: str) -> list[list[float]]:
        import numpy as np

        prefix = PREFIX.get(task, "query: ")
        out: list[list[float]] = []
        for i in range(0, len(texts), 16):
            enc = self.tok.encode_batch([prefix + t for t in texts[i:i + 16]])
            ids = np.array([e.ids for e in enc], dtype=np.int64)
            mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
            feed = {"input_ids": ids, "attention_mask": mask}
            if "token_type_ids" in self._inputs:
                feed["token_type_ids"] = np.zeros_like(ids)
            hidden = self.sess.run(None, feed)[0]
            m = mask[..., None].astype(hidden.dtype)
            pooled = (hidden * m).sum(axis=1) / np.clip(m.sum(axis=1), 1e-9, None)
            out.extend(normalize(v.tolist()) for v in pooled)
        return out


_shared: dict[Path, LocalEmbedder] = {}


def get_local_embedder(path: Path | None = None) -> LocalEmbedder | None:
    """None khi chưa tải mô hình: AI Tutor lùi về BM25 như trước, không hỏng yêu cầu."""
    p = path or model_dir()
    if p not in _shared and available(p):
        try:
            _shared[p] = LocalEmbedder(p)
        except Exception:   # thiếu thư viện hoặc file hỏng: vẫn chạy được bằng BM25
            return None
    return _shared.get(p)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download(dest: Path | None = None) -> int:
    dest = dest or model_dir()
    dest.mkdir(parents=True, exist_ok=True)
    for name, (remote, digest) in FILES.items():
        target = dest / name
        if target.exists() and _sha256(target) == digest:
            print(f"{name}: đã có, đúng SHA-256")
            continue
        url = f"https://huggingface.co/{HF_REPO}/resolve/{HF_REVISION}/{remote}"
        print(f"Tải {url}")
        tmp = target.with_suffix(".part")
        urllib.request.urlretrieve(url, tmp)
        got = _sha256(tmp)
        if got != digest:
            tmp.unlink()
            print(f"{name}: SHA-256 sai ({got}), dừng.", file=sys.stderr)
            return 1
        tmp.replace(target)
    print(f"Mô hình sẵn sàng ở {dest}")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["download"]:
        raise SystemExit(download())
    print("Dùng: python -m app.ai.local_embedder download", file=sys.stderr)
    raise SystemExit(2)
