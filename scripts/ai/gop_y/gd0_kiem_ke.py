"""GĐ0 góp ý thầy (G4): kiểm kê kho RAG và đo lại truy xuất, định tuyến của AI Tutor hiện tại.

    cd backend && python ../scripts/ai/gop_y/gd0_kiem_ke.py --out ../docs/giai-doan/ai-gop-y/gd0_ket_qua.json

Không gọi Gemini (chưa có khóa trong máy cloud). Mô hình cục bộ tải từ Hugging Face để so sánh, CHƯA fine-tune.
Phần đo:
1. Kho: số đoạn theo bài/khối, số từ, số token theo bộ tách từ của mô hình nhúng, trùng/gần trùng, đoạn nhắc khái
   niệm mà bài sau mới dạy.
2. Truy xuất: Recall@1/@4, MRR trên bộ chuẩn GĐ4 (30 câu + 5 câu demo) và câu dò luồng A, cho BM25 (đường đang
   chạy khi không có khóa) và 2 mô hình mở.
3. Định tuyến: chạy đúng answer_question của dịch vụ (AI tắt embedding → BM25, LLM giả ghi lời gọi) trên câu dò
   A/B/C/D/G để xem hôm nay hệ thống làm gì với từng loại câu.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
GOLD = ROOT / "scripts" / "ai" / "data" / "rag_gold.json"
PROBE = ROOT / "scripts" / "ai" / "data" / "gd0_cau_do_luong.json"

LOCAL_MODELS = {
    # tên ngắn: (mã HF, tiền tố câu hỏi, tiền tố đoạn). e5 được huấn luyện với tiền tố "query: "/"passage: ".
    "minilm_l12": ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "", ""),
    "e5_small": ("intfloat/multilingual-e5-small", "query: ", "passage: "),
}

# Khái niệm → bài đầu tiên dạy nó (theo tiêu đề và mục tiêu bài). Dùng để tìm đoạn "nói trước" khái niệm bài sau.
CONCEPTS = {
    r"hợp âm bảy|seventh chord|\bmaj7\b|\bm7\b|ø7": "L02",
    r"âm giai|\bscale\b": "L02",
    r"số la mã|roman numeral": "L02",
    r"chức năng|predominant|subdominant|\bdominant\b|tiền át": "L03",
    r"ii[–-]v[–-]i|guide[ -]tone|voice leading": "L04",
    r"secondary dominant|át phụ": "L05",
    r"modal interchange|mượn hợp âm": "L06",
    r"tension|\bmode\b|điệu thức": "L07",
    r"shell voicing": "L08",
}


def pct(xs):
    xs = list(xs)
    return round(100 * sum(xs) / len(xs), 1) if xs else None


def ngrams(text: str, n: int = 5) -> set[str]:
    t = re.sub(r"\s+", " ", text.lower())
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))}


def inventory(chunks, titles, tokenizers) -> dict:
    from app.content.curriculum_specs import LESSON_SPECS

    status = {s["id"]: s.get("status") for s in LESSON_SPECS}
    rows = []
    for c in chunks:
        text = c.embed_text(titles.get(c.lesson_id, ""))
        row = {"chunk_id": c.chunk_id, "lesson": c.lesson_id, "block": c.block_id, "title": c.title,
               "words": len(c.text.split()), "lesson_status": status.get(c.lesson_id), "source": c.source}
        for name, (tok, prefix) in tokenizers.items():
            row[f"tokens_{name}"] = len(tok(prefix + text)["input_ids"])
        rows.append(row)

    # Trùng chính xác (cùng hash nội dung) và gần trùng (Jaccard 5-gram ký tự ≥ 0,6) giữa hai khối khác nhau.
    by_hash = defaultdict(list)
    for c in chunks:
        by_hash[c.content_hash].append(c.chunk_id)
    exact = [v for v in by_hash.values() if len(v) > 1]
    grams = [ngrams(c.text) for c in chunks]
    near = []
    for i in range(len(chunks)):
        for j in range(i + 1, len(chunks)):
            if chunks[i].block_id == chunks[j].block_id:
                continue
            a, b = grams[i], grams[j]
            jac = len(a & b) / len(a | b) if a | b else 0
            if jac >= 0.6:
                near.append({"a": chunks[i].chunk_id, "b": chunks[j].chunk_id, "jaccard": round(jac, 2)})

    forward = []
    for c in chunks:
        low = c.text.lower() + " " + c.title.lower()
        for pat, teach in CONCEPTS.items():
            if c.lesson_id < teach and re.search(pat, low):
                forward.append({"chunk_id": c.chunk_id, "concept": pat.split("|")[0].replace("\\b", ""),
                                "taught_in": teach})

    per_lesson = {}
    for lid in sorted({r["lesson"] for r in rows}):
        rs = [r for r in rows if r["lesson"] == lid]
        w = [r["words"] for r in rs]
        per_lesson[lid] = {"chunks": len(rs), "blocks": len({r["block"] for r in rs}), "words_total": sum(w),
                           "words_min": min(w), "words_median": statistics.median(w), "words_max": max(w),
                           "status": rs[0]["lesson_status"]}
    for s in LESSON_SPECS:
        per_lesson.setdefault(s["id"], {"chunks": 0, "blocks": 0, "words_total": 0, "status": s.get("status")})

    w = [r["words"] for r in rows]
    summary = {
        "chunks": len(rows), "words_total": sum(w),
        "under_60_words": sum(x < 60 for x in w), "under_30_words": sum(x < 30 for x in w),
        "in_80_100": sum(80 <= x <= 100 for x in w), "over_100_words": sum(x > 100 for x in w),
        "empty": sum(x == 0 for x in w), "exact_duplicates": exact, "near_duplicates": near,
        "forward_references": forward,
        "sources_distinct": sorted({r["source"] for r in rows}),
    }
    for name in tokenizers:
        t = [r[f"tokens_{name}"] for r in rows]
        summary[f"tokens_{name}"] = {"min": min(t), "median": statistics.median(t), "max": max(t),
                                     "over_128": sum(x > 128 for x in t), "over_512": sum(x > 512 for x in t)}
    return {"summary": summary, "per_lesson": per_lesson, "rows": rows}


def retrieval_metrics(items, ranked_fn) -> dict:
    r1, r4, rr, rows = [], [], [], []
    for g in items:
        ids = ranked_fn(g["q"])
        good = set(g["blocks"])
        # Bỏ trùng block (nhiều đoạn cùng khối) trước khi tính hạng, giống cách người đọc thấy trích dẫn.
        seen, uniq = set(), []
        for b in ids:
            if b not in seen:
                seen.add(b)
                uniq.append(b)
        rank = next((i + 1 for i, b in enumerate(uniq) if b in good), None)
        r1.append(rank == 1)
        r4.append(rank is not None and rank <= 4)
        rr.append(1 / rank if rank else 0.0)
        rows.append({"id": g["id"], "q": g["q"], "top": uniq[:4], "rank": rank})
    return {"n": len(items), "recall@1": pct(r1), "recall@4": pct(r4), "mrr": round(sum(rr) / len(rr), 3),
            "misses_at_1": [r for r in rows if r["rank"] != 1]}


class LocalEmbedder:
    """Bọc sentence-transformers theo giao diện Embedder của dự án (chỉ dùng trong script đo GĐ0)."""

    def __init__(self, hf_id: str, q_prefix: str, p_prefix: str):
        from sentence_transformers import SentenceTransformer

        self.st = SentenceTransformer(hf_id, device="cpu")
        self.model, self.q, self.p = hf_id, q_prefix, p_prefix
        self.dim = self.st.get_sentence_embedding_dimension()

    def embed(self, texts, task):
        pre = self.q if task == "RETRIEVAL_QUERY" else self.p
        return self.st.encode([pre + t for t in texts], normalize_embeddings=True).tolist()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    tmp = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/gd0.db"
    os.environ["AI_ENABLED"] = "0"

    import sentence_transformers
    import torch
    import transformers
    from transformers import AutoTokenizer

    from app.ai.tutor.intent import classify
    from app.ai.tutor.llm import FakeProvider
    from app.ai.tutor.retriever import knowledge_base, retrieve
    from app.ai.tutor.chunker import lesson_titles
    from app.core.config import settings
    from app.db.models import User
    from app.db.session import SessionLocal, create_schema
    from app.services import ai_tutor_service as ts

    chunks = list(knowledge_base())
    titles = lesson_titles()
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    probe = json.loads(PROBE.read_text(encoding="utf-8"))
    concept = gold["concept"] + [{"id": d["id"], "q": d["q"], "blocks": d["blocks"]} for d in gold["demo_1011"]["items"]]
    probe_a = [p for p in probe["items"] if p["flow"] == "A"]

    out: dict = {"ran_at": time.strftime("%Y-%m-%d %H:%M"), "versions": {
        "sentence_transformers": sentence_transformers.__version__, "transformers": transformers.__version__,
        "torch": torch.__version__}, "settings": {"rag_min_score": settings.rag_min_score,
                                                   "rag_bm25_min_score": settings.rag_bm25_min_score,
                                                   "rag_top_k": settings.rag_top_k}}

    # 1. Kho.
    toks = {}
    for name, (hf, _q, p) in LOCAL_MODELS.items():
        tk = AutoTokenizer.from_pretrained(hf)
        toks[name] = (tk, p)
    out["inventory"] = inventory(chunks, titles, toks)

    # max_seq_length thật của từng mô hình (đề GĐ0: đoạn quá dài so với giới hạn token).
    embedders = {name: LocalEmbedder(*cfg) for name, cfg in LOCAL_MODELS.items()}
    out["max_seq_length"] = {name: e.st.max_seq_length for name, e in embedders.items()}

    # 2. Truy xuất.
    def bm25_rank(q):
        return [h.chunk.block_id for h in retrieve(q, None, top_k=len(chunks), min_score=-1, bm25_min_score=-1).hits]

    vecs = {}
    for name, e in embedders.items():
        t0 = time.perf_counter()
        vecs[name] = e.embed([c.embed_text(titles.get(c.lesson_id, "")) for c in chunks], "RETRIEVAL_DOCUMENT")
        out.setdefault("index_seconds", {})[name] = round(time.perf_counter() - t0, 2)

    def emb_rank(name):
        def f(q):
            return [h.chunk.block_id for h in retrieve(q, embedders[name], top_k=len(chunks), min_score=-1,
                                                        vectors=vecs[name]).hits]
        return f

    def best_score(name, q):
        return retrieve(q, embedders[name], top_k=1, min_score=-1, vectors=vecs[name]).best_score

    sets = {"gd4_concept_35": concept, "probe_A": probe_a}
    out["retrieval"] = {}
    for sname, items in sets.items():
        out["retrieval"][sname] = {"bm25": retrieval_metrics(items, bm25_rank)}
        for name in embedders:
            out["retrieval"][sname][name] = retrieval_metrics(items, emb_rank(name))
    out["retrieval"]["gemini"] = "NOT EVALUATED trong phiên này (không có khóa). Số GĐ4 04/11: R@1 93,3%, R@4 100%."

    # Điểm cao nhất theo luồng: tách được câu trong bài (A) với câu B/C/D bằng ngưỡng không?
    groups = defaultdict(list)
    for g in concept:
        groups["A"].append(g["q"])
    for p in probe["items"]:
        groups[p["flow"]].append(p["q"])
    for q in gold["out_of_scope"]:
        groups["C"].append(q)
    sep = {}
    for name in embedders:
        sc = {f: [best_score(name, q) for q in qs] for f, qs in groups.items()}
        a = sc["A"]
        others = [s for f in ("B", "C", "D", "G") for s in sc[f]]
        # Ngưỡng tốt nhất trên chính các câu này (chỉ để xem có tách được không, KHÔNG dùng làm ngưỡng thật).
        cands = sorted(set(a + others))
        best = max(cands, key=lambda t: (sum(x >= t for x in a) + sum(x < t for x in others)))
        sep[name] = {f: {"min": round(min(v), 3), "median": round(statistics.median(v), 3), "max": round(max(v), 3),
                         "n": len(v)} for f, v in sc.items()}
        sep[name]["best_split"] = {"threshold": round(best, 3),
                                   "A_kept": pct(x >= best for x in a), "others_rejected": pct(x < best for x in others)}
    bm = {f: [retrieve(q, None, top_k=1, min_score=-1, bm25_min_score=-1).best_score for q in qs] for f, qs in groups.items()}
    sep["bm25"] = {f: {"min": round(min(v), 2), "median": round(statistics.median(v), 2), "max": round(max(v), 2), "n": len(v)}
                   for f, v in bm.items()}
    sep["bm25"]["current_threshold"] = settings.rag_bm25_min_score
    sep["bm25"]["A_kept_at_threshold"] = pct(x >= settings.rag_bm25_min_score for x in bm["A"])
    sep["bm25"]["others_above_threshold"] = pct(x >= settings.rag_bm25_min_score
                                                for f in ("B", "C", "D", "G") for x in bm[f])
    out["score_separation"] = sep

    # 3. Định tuyến hôm nay: đúng luồng dịch vụ, không khóa (BM25), LLM giả ghi lời gọi.
    create_schema()
    routes = []
    with SessionLocal() as db:
        db.add(User(id="gd0", display_name="gd0", email="gd0@example.test"))
        db.commit()
        user = db.get(User, "gd0")
        for p in probe["items"] + [{"id": g["id"], "flow": "A", "q": g["q"], "blocks": g["blocks"]} for g in concept]:
            fake = FakeProvider(['{"reply":"x","citations":[],"engine_claims":[],"hint_level":0,'
                                 '"suggested_actions":[],"intent":"concept"}'])
            draft, meta = ts.answer_question(db, user, p["q"], [], None, fake, ts._now(None))
            it = classify(p["q"])
            routes.append({"id": p["id"], "flow": p["flow"], "q": p["q"], "route": draft.route,
                           "llm_called": bool(fake.calls), "intent": it.intent, "intent_conf": it.confidence,
                           "chunks": (meta.get("retrieval") or {}).get("chunks"),
                           "engine_facts": [f["args"] for f in meta.get("engine", [])]})
    by_flow = defaultdict(Counter)
    for r in routes:
        by_flow[r["flow"]][r["route"]] += 1
    out["routing_today"] = {"summary": {f: dict(c) for f, c in by_flow.items()},
                            "llm_called_by_flow": {f: sum(r["llm_called"] for r in routes if r["flow"] == f)
                                                   for f in by_flow},
                            "rows": routes}

    text = json.dumps(out, ensure_ascii=False, indent=1)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    short = {k: v for k, v in out.items() if k not in ("inventory", "retrieval", "routing_today")}
    short["inventory"] = out["inventory"]["summary"] | {"per_lesson": out["inventory"]["per_lesson"]}
    short["retrieval"] = {s: {m: {k: v for k, v in r.items() if k != "misses_at_1"} if isinstance(r, dict) else r
                              for m, r in d.items()} if isinstance(d, dict) else d for s, d in out["retrieval"].items()}
    short["routing_today"] = {k: v for k, v in out["routing_today"].items() if k != "rows"}
    print(json.dumps(short, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
