"""Huấn luyện bộ phân loại "liên quan nhạc lý" (G6, T6).   cd backend && python -m app.ml.relevance_train

Dữ liệu: câu của các bài học đã phát hành (nhãn 1, nhóm theo bài) + data/relevance/handwritten.jsonl (Claude soạn: văn bản nhạc lý
nhiều chủ đề, tiếng Việt/Anh, nhãn 1; văn bản lạc đề 14 lĩnh vực và loại "âm nhạc nhưng không phải nhạc lý", nhãn 0).
Đo: kiểm chéo theo NHÓM (cả một bài học hoặc cả một lĩnh vực nằm ngoài tập huấn luyện ở mỗi lượt), so với bộ chấm hybrid của G2
trên đúng các câu đó; rồi qua cổng G2 thật trên 16 tài liệu của eval/cases.jsonl (không dùng để huấn luyện, kiểm trùng).
Ghi: backend/models/relevance/{tfidf-logreg.json, e5-logreg.json, manifest.json} và docs/giai-doan/gop-y-thay/G6_DO_LUONG.json."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
HANDWRITTEN = ROOT / "data" / "relevance" / "handwritten.jsonl"
MODEL_DIR = ROOT / "backend" / "models" / "relevance"
RESULT = ROOT / "docs" / "giai-doan" / "gop-y-thay" / "G6_DO_LUONG.json"
VERSION = "1.0.0"
LOW, HIGH = 0.35, 0.60


def lesson_samples() -> list[dict]:
    """Các cặp câu liên tiếp của đoạn bài đã phát hành, nhóm theo bài (để kiểm chéo giữ nguyên cả bài ra ngoài)."""
    from ..ai.tutor.chunker import lesson_chunks, split_sentences

    out = []
    for c in lesson_chunks():
        sents = [s for s in split_sentences(c.text) if len(s) >= 20]
        for i in range(0, len(sents), 2):
            text = " ".join(sents[i:i + 2])
            if len(text) >= 40:
                out.append({"label": 1, "group": f"pos:{c.lesson_id}", "source": f"bài {c.lesson_id}", "text": text})
    return out


def build_dataset() -> list[dict]:
    hand = [json.loads(line) for line in HANDWRITTEN.read_text(encoding="utf-8").splitlines() if line.strip()]
    return lesson_samples() + hand


def dataset_hash(rows: list[dict]) -> str:
    h = hashlib.sha256()
    for r in sorted(rows, key=lambda r: (r["label"], r["group"], r["text"])):
        h.update(f'{r["label"]}|{r["group"]}|{r["text"]}\n'.encode("utf-8"))
    return h.hexdigest()


def trigrams(text: str) -> set[str]:
    from ..admin.relevance.classifier import prep

    t = re.sub(r"[^a-z0-9 ]+", " ", prep(text))
    t = " ".join(t.split())
    return {t[i:i + 3] for i in range(len(t) - 2)}


def max_overlap(held_out: list[str], train: list[str]) -> float:
    """Jaccard 3-gram lớn nhất giữa một tài liệu thử và bất kỳ mẫu huấn luyện: > 0,8 là rò rỉ dữ liệu."""
    tr = [trigrams(t) for t in train]
    best = 0.0
    for d in held_out:
        a = trigrams(d)
        for b in tr:
            if a and b:
                best = max(best, len(a & b) / len(a | b))
    return round(best, 3)


def metrics(y, p, low=LOW, high=HIGH) -> dict:
    from sklearn.metrics import roc_auc_score

    pos = [pi for yi, pi in zip(y, p) if yi == 1]
    neg = [pi for yi, pi in zip(y, p) if yi == 0]
    tp = sum(x >= 0.5 for x in pos)
    fp = sum(x >= 0.5 for x in neg)
    return {"n": len(y), "auc": round(float(roc_auc_score(y, p)), 4),
            "accuracy": round((tp + sum(x < 0.5 for x in neg)) / len(y), 4),
            "precision": round(tp / (tp + fp), 4) if tp + fp else None, "recall": round(tp / len(pos), 4),
            # Theo luật cổng G2: dưới LOW từ chối, từ HIGH nhận.
            "gate": {"neg_rejected": round(sum(x < low for x in neg) / len(neg), 4),
                     "neg_accepted": round(sum(x >= high for x in neg) / len(neg), 4),
                     "pos_accepted": round(sum(x >= high for x in pos) / len(pos), 4),
                     "pos_rejected": round(sum(x < low for x in pos) / len(pos), 4)}}


def fit_tfidf(texts: list[str], y: list[int]):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    from ..admin.relevance.classifier import prep

    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True, min_df=2, max_features=15000, preprocessor=prep)
    x = vec.fit_transform(texts)
    lr = LogisticRegression(C=10.0, class_weight="balanced", max_iter=3000, random_state=0).fit(x, y)
    return vec, lr


def fit_e5(vectors, y: list[int]):
    from sklearn.linear_model import LogisticRegression

    return LogisticRegression(C=4.0, class_weight="balanced", max_iter=3000, random_state=0).fit(vectors, y)


def cross_validate(rows: list[dict], vectors) -> dict:
    import numpy as np
    from sklearn.model_selection import GroupKFold

    texts, y, groups = [r["text"] for r in rows], np.array([r["label"] for r in rows]), np.array([r["group"] for r in rows])
    oof = {"tfidf": np.zeros(len(rows)), "e5": np.zeros(len(rows))}
    for tr, te in GroupKFold(n_splits=5).split(texts, y, groups):
        vec, lr = fit_tfidf([texts[i] for i in tr], y[tr].tolist())
        oof["tfidf"][te] = lr.predict_proba(vec.transform([texts[i] for i in te]))[:, 1]
        oof["e5"][te] = fit_e5(vectors[tr], y[tr].tolist()).predict_proba(vectors[te])[:, 1]
    return {k: metrics(y.tolist(), v.tolist()) for k, v in oof.items()}, {k: v.tolist() for k, v in oof.items()}


def export_models(vec, lr_t, lr_e, dim: int) -> dict[str, dict]:
    tfidf = {"type": "tfidf_logreg", "analyzer": "char_wb", "ngram": [2, 4], "sublinear_tf": True,
             "terms": vec.get_feature_names_out().tolist(), "idf": [round(float(x), 6) for x in vec.idf_],
             "coef": [round(float(x), 6) for x in lr_t.coef_[0]], "intercept": round(float(lr_t.intercept_[0]), 6)}
    e5 = {"type": "embedding_logreg", "embedder": "multilingual-e5-small", "task": "RETRIEVAL_DOCUMENT", "dim": dim,
          "coef": [round(float(x), 6) for x in lr_e.coef_[0]], "intercept": round(float(lr_e.intercept_[0]), 6)}
    return {"tfidf-logreg.json": tfidf, "e5-logreg.json": e5}


def gate_eval(scorer) -> dict:
    """Cổng G2 thật trên các tài liệu của eval/cases.jsonl, với bộ chấm được cắm vào."""
    from ..admin.relevance.errors import RelevanceError
    from ..admin.relevance.gate import evaluate_pasted_text
    from ..eval.cases import load_cases

    rows = []
    for c in (c for c in load_cases() if c["type"] == "gate"):
        try:
            res = evaluate_pasted_text(c["text"], scorer=scorer)
            rows.append((c["id"], c["label"], res.status, res.score))
        except RelevanceError:
            rows.append((c["id"], c["label"], "rejected", 0.0))
    rel = [r for r in rows if r[1] == "relevant"]
    irr = [r for r in rows if r[1] == "irrelevant"]
    tp, fp = sum(r[2] == "accepted" for r in rel), sum(r[2] == "accepted" for r in irr)
    return {"precision_accepted": round(100 * tp / (tp + fp), 1) if tp + fp else None,
            "recall_not_rejected": round(100 * sum(r[2] != "rejected" for r in rel) / len(rel), 1),
            "offtopic_rejected": round(100 * sum(r[2] == "rejected" for r in irr) / len(irr), 1),
            "scores": {r[0]: f"{r[1]}→{r[2]} ({r[3]})" for r in rows}}


def main(argv=None) -> int:
    import numpy as np

    from ..admin.relevance.classifier import ClassifierScorer, E5LogReg, TfidfLogReg, sha256_file
    from ..admin.relevance.scorer import HybridScorer
    from ..ai.local_embedder import get_local_embedder
    from ..eval.cases import load_cases

    ap = argparse.ArgumentParser(prog="python -m app.ml.relevance_train", description=__doc__)
    ap.add_argument("--out", default=str(MODEL_DIR))
    args = ap.parse_args(argv)
    embedder = get_local_embedder()
    if embedder is None:
        print("Cần mô hình e5: python -m app.ai.local_embedder download", flush=True)
        return 2
    rows = build_dataset()
    texts, y = [r["text"] for r in rows], [r["label"] for r in rows]
    gate_docs = [c["text"] for c in load_cases() if c["type"] == "gate"]
    overlap = max_overlap(gate_docs, texts)
    if overlap > 0.8:
        raise SystemExit(f"Rò rỉ dữ liệu: tài liệu thử trùng mẫu huấn luyện (Jaccard {overlap}).")

    vectors = np.array(embedder.embed(texts, "RETRIEVAL_DOCUMENT"))
    cv, oof = cross_validate(rows, vectors)
    hybrid = HybridScorer(embedder)
    cv["hybrid_g2"] = metrics(y, [hybrid.score(t).value for t in texts])
    per_group = {}
    for g in sorted({r["group"] for r in rows}):
        idx = [i for i, r in enumerate(rows) if r["group"] == g]
        per_group[g] = {"n": len(idx), "label": rows[idx[0]]["label"],
                        "tfidf_mean": round(float(np.mean([oof["tfidf"][i] for i in idx])), 3),
                        "e5_mean": round(float(np.mean([oof["e5"][i] for i in idx])), 3)}

    vec, lr_t = fit_tfidf(texts, y)
    lr_e = fit_e5(vectors, y)
    specs = export_models(vec, lr_t, lr_e, int(vectors.shape[1]))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, spec in specs.items():
        path = out / name
        path.write_text(json.dumps(spec, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        files[name] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}

    scorers = {"tfidf": ClassifierScorer(TfidfLogReg(specs["tfidf-logreg.json"]), VERSION),
               "e5": ClassifierScorer(E5LogReg(specs["e5-logreg.json"], embedder), VERSION), "hybrid_g2": hybrid}
    gate = {k: gate_eval(s) for k, s in scorers.items()}
    # Luật chọn đặt trước: mô hình có AUC kiểm chéo cao hơn; bằng nhau thì chọn tfidf (không cần e5, nhanh hơn).
    recommended = "e5" if cv["e5"]["auc"] > cv["tfidf"]["auc"] else "tfidf"
    manifest = {"name": "hm-relevance", "version": VERSION, "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "recommended": recommended, "labels": {"1": "liên quan nhạc lý/hòa âm", "0": "không liên quan"},
                "data": {"n": len(rows), "positives": sum(y), "negatives": len(y) - sum(y), "sha256": dataset_hash(rows),
                         "groups": len({r["group"] for r in rows}), "handwritten_file": "data/relevance/handwritten.jsonl",
                         "max_overlap_with_gate_docs": overlap},
                "files": files, "cv_group_5fold": cv, "gate_16_docs": {k: {kk: vv for kk, vv in v.items() if kk != "scores"} for k, v in gate.items()},
                "thresholds": {"low": LOW, "high": HIGH}, "trainer": "scikit-learn LogisticRegression, random_state=0"}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps({"cv": cv, "per_group_mean_prob": per_group, "gate": gate, "dataset": manifest["data"],
                                  "recommended": recommended}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"data": manifest["data"], "cv": {k: {kk: v[kk] for kk in ("auc", "accuracy", "precision", "recall")}
                                                         for k, v in cv.items()}, "recommended": recommended}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
