"""GĐ2b: fine-tune multilingual-e5-small cho AI Tutor, chạy CPU, seed cố định (quyết định GĐ2 6A, 7A, 07/11/2026).

    cd backend && python ../scripts/ai/gop_y/finetune_e5.py --out models/multilingual-e5-small-hm

Vì sao: điểm cosine của e5 gốc bị nén, câu A và câu B/C cùng nằm quanh 0,83–0,86 (GĐ0, GĐ1), nên không ngưỡng nào
tách được. Mục tiêu fine-tune là KÉO câu A về đúng đoạn bài và ĐẨY câu B/C/D/G ra xa mọi đoạn bài, để một ngưỡng tách
được hai nhóm, mà không làm hỏng việc chọn đoạn (R@1 trên bộ chuẩn GĐ4).

Hàm mất mát (mỗi bước, cả kho 42 đoạn bài + 18 mục hướng dẫn được mã hóa lại có gradient):
  1. InfoNCE: câu A/D phải chọn đúng đoạn dương trong toàn bộ đoạn (nhiệt độ 0,05).
     Đoạn dương của câu A = đoạn điểm cao nhất CỦA ĐÚNG BÀI được gán nhãn (theo mô hình gốc, tính một lần);
     của câu D = mục hướng dẫn được gán nhãn.
  2. Tách ngưỡng (hinge, biên m): điểm câu A với đoạn dương > t + m; điểm cao nhất của câu B/C/D/G với đoạn bài
     < t − m. t là tham số học được (khởi đầu 0,85).
Chỉ train trên scripts/ai/data/gd2/train.json. Chọn epoch tốt nhất trên dev.json (AUC tách A khỏi B/C và R@1 bộ
chuẩn GĐ4 không được giảm so với bản gốc). KHÔNG đụng test_tam.json.
Đóng băng lớp nhúng từ (96 triệu tham số, phần lớn là từ vựng 250 nghìn token): chỉ chỉnh 12 lớp transformer, nhanh
hơn trên CPU và ít "quên" ngôn ngữ khác.

Xuất ONNX (input_ids, attention_mask → last_hidden_state) + tokenizer.json + model_info.json, đúng giao diện
LocalEmbedder, nên đổi mô hình chỉ cần LOCAL_EMBED_DIR.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

GD2 = ROOT / "scripts" / "ai" / "data" / "gd2"
GOLD = ROOT / "scripts" / "ai" / "data" / "rag_gold.json"
HF_REPO = "intfloat/multilingual-e5-small"
HF_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
NEG_FLOWS = ("B", "C", "D", "G")


def seed_all(seed: int) -> None:
    import numpy as np
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def load(name: str) -> list[dict]:
    return json.loads((GD2 / f"{name}.json").read_text(encoding="utf-8"))["items"]


class Encoder:
    def __init__(self, path: str):
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(path)
        self.model = AutoModel.from_pretrained(path)

    def __call__(self, texts: list[str], prefix: str, max_len: int):
        torch = self.torch
        b = self.tok([prefix + t for t in texts], padding=True, truncation=True, max_length=max_len,
                     return_tensors="pt")
        out = self.model(input_ids=b["input_ids"], attention_mask=b["attention_mask"]).last_hidden_state
        m = b["attention_mask"].unsqueeze(-1).to(out.dtype)
        v = (out * m).sum(1) / m.sum(1).clamp(min=1e-9)
        return torch.nn.functional.normalize(v, dim=-1)


def passages():
    from app.ai.tutor.chunker import lesson_titles
    from app.ai.tutor.retriever import help_base, knowledge_base

    titles = lesson_titles()
    lessons = list(knowledge_base())
    helps = list(help_base())
    texts = [c.embed_text(titles.get(c.lesson_id, "")) for c in lessons] + [c.embed_text("") for c in helps]
    return lessons, helps, texts


@__import__("functools").lru_cache(maxsize=1)
def _gold():
    return json.loads(GOLD.read_text(encoding="utf-8"))["concept"]


def evaluate(enc, lessons, texts, dev: list[dict]) -> dict:
    """AUC tách A khỏi B/C (điểm cao nhất với đoạn bài) trên dev, lỗi cân bằng ở ngưỡng tốt nhất, R@1 bộ chuẩn GĐ4."""
    torch = enc.torch
    n_les = len(lessons)
    with torch.no_grad():
        P = torch.cat([enc(texts[i:i + 16], "passage: ", 512) for i in range(0, len(texts), 16)])[:n_les]
        rows = [r for r in dev if r["flow"] in ("A", "B", "C")]
        Q = torch.cat([enc([r["q"] for r in rows[i:i + 32]], "query: ", 64) for i in range(0, len(rows), 32)])
        best = (Q @ P.T).max(1).values.tolist()
        gold = _gold()
        G = torch.cat([enc([g["q"] for g in gold[i:i + 32]], "query: ", 64) for i in range(0, len(gold), 32)])
        top = (G @ P.T).argmax(1).tolist()
    pos = [s for s, r in zip(best, rows) if r["flow"] == "A"]
    neg = [s for s, r in zip(best, rows) if r["flow"] != "A"]
    auc = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))
    ber = min((sum(p < t for p in pos) / len(pos) + sum(n >= t for n in neg) / len(neg)) / 2 for t in pos + neg)
    hit = sum(1 for g, i in zip(gold, top) if lessons[i].block_id in set(g["blocks"])) / len(gold)
    return {"auc": round(auc, 4), "balanced_error": round(ber, 4), "r_at_1": round(hit, 4),
            "a_mean": round(sum(pos) / len(pos), 4), "bc_mean": round(sum(neg) / len(neg), 4)}


def export_onnx(enc, out: Path) -> None:
    torch = enc.torch
    enc.model.eval()

    class Wrap(torch.nn.Module):
        """Gọi bằng tên tham số: BertModel.forward nhận nhiều tham số vị trí, truyền thẳng sẽ lệch chỗ."""

        def __init__(self, m):
            super().__init__()
            self.m = m

        def forward(self, input_ids, attention_mask):
            return self.m(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state

    dummy = enc.tok(["query: xin chào"], return_tensors="pt")
    torch.onnx.export(Wrap(enc.model), (dummy["input_ids"], dummy["attention_mask"]), str(out / "model.onnx"),
                      input_names=["input_ids", "attention_mask"], output_names=["last_hidden_state"],
                      dynamic_axes={"input_ids": {0: "b", 1: "s"}, "attention_mask": {0: "b", 1: "s"},
                                    "last_hidden_state": {0: "b", 1: "s"}},
                      opset_version=17, dynamo=False)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def finish(tmp: Path, out: Path, src: str) -> None:
    """Xuất ONNX từ bản đã chọn (thư mục .tmp), chép tokenizer gốc, ghi SHA-256 vào model_info.json."""
    enc = Encoder(str(tmp))
    export_onnx(enc, out)
    shutil.copy(Path(src) / "tokenizer.json", out / "tokenizer.json")
    info = json.loads((out / "model_info.json").read_text(encoding="utf-8"))
    info["files"] = {n: sha(out / n) for n in ("model.onnx", "tokenizer.json")}
    (out / "model_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.rmtree(tmp)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--name", default="multilingual-e5-small-hm-gd2b", help="tên mô hình ghi vào model_info.json (khóa ngưỡng định tuyến)")
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--seed", type=int, default=20261107)
    ap.add_argument("--batch-pos", type=int, default=24)
    ap.add_argument("--batch-neg", type=int, default=16)
    ap.add_argument("--margin", type=float, default=0.03)
    ap.add_argument("--hinge-weight", type=float, default=1.0)
    ap.add_argument("--grad-ckpt", action="store_true", help="checkpoint gradient: bớt RAM (kho 76 đoạn × 256 token vượt 14 GB), chậm hơn ~30%, kết quả toán học như nhau")
    args = ap.parse_args(argv)
    seed_all(args.seed)

    import torch
    from huggingface_hub import snapshot_download

    torch.set_num_threads(4)
    src = snapshot_download(HF_REPO, revision=HF_REVISION, local_files_only=True)
    enc = Encoder(src)
    for p in enc.model.embeddings.parameters():
        p.requires_grad = False
    if args.grad_ckpt:
        enc.model.gradient_checkpointing_enable()

    lessons, helps, texts = passages()
    n_les = len(lessons)
    help_idx = {c.title: n_les + i for i, c in enumerate(helps)}
    train, dev = load("train"), load("dev")

    # Đoạn dương của câu A: đoạn điểm cao nhất trong ĐÚNG BÀI gán nhãn, theo mô hình gốc (tính một lần, cố định).
    enc.model.eval()
    with torch.no_grad():
        P0 = torch.cat([enc(texts[i:i + 16], "passage: ", 512) for i in range(0, len(texts), 16)])
        a_rows = [r for r in train if r["flow"] == "A"]
        QA = torch.cat([enc([r["q"] for r in a_rows[i:i + 32]], "query: ", 64) for i in range(0, len(a_rows), 32)])
        S0 = QA @ P0[:n_les].T
    for r, s in zip(a_rows, S0):
        allowed = [i for i, c in enumerate(lessons) if c.lesson_id == r["lesson"]]
        r["_pos"] = max(allowed, key=lambda i: float(s[i]))
    for r in train:
        if r["flow"] == "D":
            r["_pos"] = help_idx[r["help"]]
    pos_rows = [r for r in train if "_pos" in r]
    neg_rows = [r for r in train if r["flow"] in NEG_FLOWS]

    base = evaluate(enc, lessons, texts, dev)
    print("gốc", base, flush=True)
    t = torch.nn.Parameter(torch.tensor(0.85))
    opt = torch.optim.AdamW([{"params": [p for p in enc.model.parameters() if p.requires_grad], "lr": args.lr},
                             {"params": [t], "lr": 1e-2, "weight_decay": 0.0}], weight_decay=0.01)
    steps = (len(pos_rows) + args.batch_pos - 1) // args.batch_pos
    history, best = [{"epoch": 0, **base}], None
    tmp = args.out.with_name(args.out.name + ".tmp")
    for epoch in range(1, args.epochs + 1):
        enc.model.train()
        rng = random.Random(args.seed + epoch)
        rng.shuffle(pos_rows)
        t0 = time.time()
        for k in range(steps):
            bp = pos_rows[k * args.batch_pos:(k + 1) * args.batch_pos]
            bn = rng.sample(neg_rows, min(args.batch_neg, len(neg_rows)))
            P = enc(texts, "passage: ", 256)
            Qp = enc([r["q"] for r in bp], "query: ", 64)
            Qn = enc([r["q"] for r in bn], "query: ", 64)
            target = torch.tensor([r["_pos"] for r in bp])
            sp = Qp @ P.T
            ce = torch.nn.functional.cross_entropy(sp / 0.05, target)
            a_mask = torch.tensor([r["flow"] == "A" for r in bp])
            s_pos = sp[torch.arange(len(bp)), target][a_mask]
            s_neg = (Qn @ P[:n_les].T).max(1).values
            hinge = (torch.relu(t + args.margin - s_pos).mean() if len(s_pos) else 0) + \
                torch.relu(s_neg - t + args.margin).mean()
            loss = ce + args.hinge_weight * hinge
            opt.zero_grad()
            loss.backward()
            opt.step()
            if k % 5 == 0:
                print(f"epoch {epoch} bước {k + 1}/{steps} loss {loss.item():.4f} ce {ce.item():.4f} "
                      f"hinge {float(hinge):.4f} t {t.item():.3f}", flush=True)
        enc.model.eval()
        m = evaluate(enc, lessons, texts, dev)
        m.update({"epoch": epoch, "t": round(t.item(), 4), "seconds": round(time.time() - t0)})
        history.append(m)
        print("dev", m, flush=True)
        # Chọn: R@1 bộ chuẩn GĐ4 không thấp hơn bản gốc; trong đó lỗi cân bằng thấp nhất.
        if m["r_at_1"] >= base["r_at_1"] and (best is None or m["balanced_error"] < best["balanced_error"]):
            best = m
            if tmp.exists():
                shutil.rmtree(tmp)
            enc.model.save_pretrained(tmp)
            enc.tok.save_pretrained(tmp)

    args.out.mkdir(parents=True, exist_ok=True)
    info = {"name": args.name, "base": f"{HF_REPO}@{HF_REVISION}", "seed": args.seed,
            "args": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()},
            "train_sha256": sha(GD2 / "train.json"), "dev_sha256": sha(GD2 / "dev.json"),
            "history": history, "chosen": best,
            "note": "Sinh bởi scripts/ai/gop_y/finetune_e5.py. Chỉ train trên gd2/train.json, chọn epoch trên dev.json."}
    if best is None:
        info["chosen"] = None
        (args.out / "model_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Không epoch nào giữ được R@1 của bản gốc: không xuất mô hình.")
        return 1
    (args.out / "model_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    finish(tmp, args.out, src)
    print("Đã xuất", args.out, json.dumps(best, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
