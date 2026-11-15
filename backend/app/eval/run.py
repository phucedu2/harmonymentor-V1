"""Chạy bộ đánh giá: python -m app.eval.run [--live] [--out eval/report.md] [--update-baseline]

Đo (T2):
  retrieval  HitRate@5 và MRR của 4 cấu hình truy xuất: BM25, e5 trong bộ nhớ (đường cũ), Qdrant, Qdrant + rerank.
  e2e        chạy cả pipeline chatbot: độ đúng luồng, xử lý lạc đề/tấn công, tỉ lệ trích dẫn hợp lệ, bám nguồn (cấu trúc), độ trễ.
  gate       cổng nhạc lý Admin (G2): precision của tài liệu được nhận, recall của tài liệu liên quan, tỉ lệ từ chối tài liệu lạc đề.
Chế độ mặc định chạy OFFLINE: LLM là bản giả tất định (trích nguyên văn câu đầu của đoạn đứng đầu), nên các số về "bám nguồn" chỉ
chứng minh các lớp kiểm của máy chủ hoạt động, KHÔNG phải chất lượng Gemini. Muốn đo Gemini thật: --live (cần AI_ENABLED=1, khóa).
Kết thúc với mã 1 nếu có số đo tụt quá dung sai so với eval/baseline.json (kiểm hồi quy)."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from .cases import BASELINE_PATH, CASES_PATH, REPORT_PATH, load_cases
from .metrics import (best_threshold, flatten, hit_rate_and_mrr, pct, percentile, precision_recall, rank_of,
                      regressions)

TOP_K = 5
POSITIVE = ("retrieval", "followup")
NEGATIVE = ("offtopic", "attack")
SENT = re.compile(r"[.!?…]")


class ScriptedProvider:
    """LLM giả tất định cho chế độ offline (xem docstring đầu tệp)."""

    model = "eval-scripted"

    def __init__(self, bogus: bool = False):
        self.bogus, self.calls = bogus, 0

    def generate(self, system, user, schema, max_output_tokens=None):
        from ..ai.tutor.llm import LLMResult

        self.calls += 1
        base = {"citations": [], "engine_claims": [], "hint_level": 0, "suggested_actions": []}
        if "MODE: off_topic" in user:
            body = {**base, "reply": "Mình không có thông tin chắc chắn về chuyện này. Bạn nên xem nguồn chính thống. "
                                     "Ngoài ra còn nhiều chi tiết khác nữa.", "intent": "out_of_scope"}
        elif "MODE: general_music" in user:
            body = {**base, "reply": "Đây là kiến thức âm nhạc chung, mình chưa kiểm chứng chi tiết.", "intent": "concept"}
        else:
            m = re.search(r'kind="LESSON_CHUNKS">>>\n(.*?)\n<<<HM_END>>>', user, re.S)
            rows = json.loads(m.group(1)) if m else []
            if rows:
                top = rows[0]
                first = re.split(r"(?<=[.!?])\s", top["text"].strip())[0][:300]
                block = "L99-B99" if self.bogus else top["block_id"]
                body = {**base, "reply": first, "intent": "concept",
                        "citations": [{"lesson_id": block.split("-")[0], "block_id": block, "title": top["title"]}]}
            else:
                body = {**base, "reply": "Mình không biết câu này.", "intent": "concept"}
        text = json.dumps(body, ensure_ascii=False)
        return LLMResult(text, self.model, len(user) // 4, len(text) // 4, 1)


@contextmanager
def env(**kv: str):
    old = {k: os.environ.get(k) for k in kv}
    os.environ.update(kv)
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def uniq(xs):
    seen, out = set(), []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


# --- Truy xuất ------------------------------------------------------------------------------------------------------

def build_store(embedder):
    from qdrant_client import QdrantClient

    from ..core.ai_config import RagConfig
    from ..rag.ingest import ingest
    from ..rag.store import QdrantStore

    cfg = dataclasses.replace(RagConfig(), dim=embedder.dim)
    store = QdrantStore(QdrantClient(":memory:"), "eval", embedder.dim)
    store.ensure_collection()
    ingest(store, embedder, ["lessons"], cfg)
    return store


def retrieval_section(cases, embedder, store):
    from ..ai.tutor.retriever import retrieve
    from ..core.ai_config import pipeline_config
    from ..services.ai_pipeline import _to_hit, rerank, rewrite_query

    pc = pipeline_config()
    rows = [c for c in cases if c["type"] in POSITIVE]

    def query(c):
        return rewrite_query(c["q"], [tuple(t) for t in c.get("turns", [])]) if c["type"] == "followup" else c["q"]

    def bm25(q):
        return [h.chunk.block_id for h in retrieve(q, None, top_k=30, min_score=-1, bm25_min_score=-1).hits]

    def legacy(q):
        return [h.chunk.block_id for h in retrieve(q, embedder, top_k=30, min_score=-1, bm25_min_score=-1).hits]

    def qdrant_raw(q):
        vec = embedder.embed([q], "RETRIEVAL_QUERY")[0]
        return [_to_hit(h) for h in store.search(vec, top_k=pc.rerank_pool, min_score=-1.0, filters={"source": ["lessons"]})]

    fns = {"bm25": bm25}
    if embedder is not None:
        fns["e5_in_memory"] = legacy
        fns["qdrant"] = lambda q: [h.chunk.block_id for h in qdrant_raw(q)]
        fns["qdrant_rerank"] = lambda q: [h.chunk.block_id for h in rerank(q, qdrant_raw(q), pc.rerank_weight, TOP_K)]
    out: dict[str, Any] = {}
    sweep: dict[str, Any] = {}
    if embedder is not None:                     # rerank có ích không? Thử vài trọng số trên cùng bộ ca (chỉ để quyết định bật/tắt)
        for w in (0.0, 0.02, 0.05, 0.1, 0.15):
            ranks = [rank_of(uniq([h.chunk.block_id for h in rerank(query(c), qdrant_raw(query(c)), w, TOP_K)])[:TOP_K], c["blocks"])
                     for c in rows]
            sweep[str(w)] = dict(zip(("hit_rate_at_5", "mrr"), hit_rate_and_mrr(ranks, TOP_K)))
    out["_rerank_sweep"] = sweep
    for name, fn in fns.items():
        ranks, per = [], []
        for c in rows:
            ids = uniq(fn(query(c)))
            r = rank_of(ids[:TOP_K], c["blocks"])
            ranks.append(r)
            per.append({"id": c["id"], "rank": r, "top": ids[:3]})
        hit, mrr = hit_rate_and_mrr(ranks, TOP_K)
        f_ranks = [r for r, c in zip(ranks, rows) if c["type"] == "followup"]
        out[name] = {"hit_rate_at_5": hit, "mrr": mrr, "n": len(rows),
                     "followup_hit_rate": hit_rate_and_mrr(f_ranks, TOP_K)[0], "misses": [p["id"] for p in per if p["rank"] is None]}
    return out


def calibration_section(cases, embedder, store):
    """Ngưỡng điểm cosine tối thiểu (QDRANT_MIN_SCORE) tách câu đúng chủ đề khỏi câu lạc đề/tấn công."""
    if embedder is None or store is None:
        return {"note": "NOT EVALUATED (thiếu mô hình e5)"}

    def top1(q):
        hits = store.search(embedder.embed([q], "RETRIEVAL_QUERY")[0], top_k=1, min_score=-1.0, filters={"source": ["lessons"]})
        return hits[0].score if hits else 0.0

    pos = [top1(c["q"]) for c in cases if c["type"] in POSITIVE]
    neg = [top1(c["q"]) for c in cases if c["type"] in NEGATIVE]
    rows = best_threshold(pos, neg, [round(0.70 + 0.01 * i, 2) for i in range(26)])
    best = max(rows, key=lambda r: (r["balanced"], -r["threshold"]))
    return {"positive_top1": {"min": round(min(pos), 3), "median": round(sorted(pos)[len(pos) // 2], 3)},
            "negative_top1": {"max": round(max(neg), 3), "median": round(sorted(neg)[len(neg) // 2], 3)},
            "table": rows, "recommended": best}


# --- Toàn pipeline ------------------------------------------------------------------------------------------------

def e2e_run(db, user, cases, embedder, provider_factory, label, live=False, pause=0.0):
    from ..ai.tutor.retriever import knowledge_base
    from ..services import ai_tutor_service as ts

    chunk_block = {c.chunk_id: c.block_id for c in knowledge_base()}
    rows = []
    for c in cases:
        if c["type"] == "gate" or (live and c["type"] == "bad_citation"):
            continue
        provider = provider_factory(c)
        if live:
            time.sleep(pause)
        t0 = time.perf_counter()
        draft, meta = ts.answer_question(db, user, c["q"], [tuple(t) for t in c.get("turns", [])], embedder, provider, ts._now(None))
        ms = round((time.perf_counter() - t0) * 1000, 1)
        retrieved = {chunk_block.get(x, x) for x in (meta.get("retrieval") or {}).get("chunks", [])}
        cites = [x["block_id"] for x in draft.citations]
        rows.append({"id": c["id"], "type": c["type"], "expect": c["flow"], "flow": draft.flow, "route": draft.route,
                     "cites": cites, "retrieved": sorted(retrieved), "llm_calls": getattr(provider, "calls", draft.llm_calls),
                     "ms": ms, "gold": c.get("blocks", []), "reply": draft.reply,
                     "contradicted": any(x.get("status") == "contradicted" for x in draft.claims),
                     "source": (meta.get("retrieval") or {}).get("source")})
    return {"label": label, "rows": rows, "metrics": e2e_metrics(rows)}


def e2e_metrics(rows):
    by = lambda *types: [r for r in rows if r["type"] in types]  # noqa: E731
    cite_total = sum(len(r["cites"]) for r in rows if r["flow"] == "A")
    cite_valid = sum(sum(b in r["retrieved"] for b in r["cites"]) for r in rows if r["flow"] == "A")
    answered = [r for r in by(*POSITIVE) if r["flow"] == "A"]
    grounded = [r for r in answered if r["cites"] and all(b in r["retrieved"] for b in r["cites"]) and not r["contradicted"]]
    brief = [r for r in by("offtopic") if r["route"] == "out_of_scope_brief"]
    steer_ok = [len(SENT.findall(r["reply"].split(" Mình là trợ lý âm nhạc")[0])) <= 2 for r in brief]
    return {
        "n": len(rows),
        "route_accuracy": pct(r["flow"] == r["expect"] for r in rows),
        "route_accuracy_by_type": {t: pct(r["flow"] == r["expect"] for r in by(t)) for t in sorted({r["type"] for r in rows})},
        "wrong_routes": [f'{r["id"]}:{r["expect"]}→{r["flow"]}' for r in rows if r["flow"] != r["expect"]],
        "offtopic_handled": pct(r["flow"] == "C" for r in by("offtopic")),
        "offtopic_brief_within_2_sentences": pct(steer_ok) if steer_ok else None,
        "attack_handled": pct(r["flow"] == "C" and r["llm_calls"] == 0 for r in by("attack")),
        "concept_wrongly_blocked": pct(r["flow"] == "C" for r in by(*POSITIVE)),
        "valid_citation_rate": round(100 * cite_valid / cite_total, 1) if cite_total else None,
        "citations_total": cite_total,
        "bad_citation_caught": pct("L99-B99" not in r["cites"] and r["flow"] == "A" for r in by("bad_citation")),
        "cites_gold_block": pct(bool(set(r["cites"]) & set(r["gold"])) for r in answered),
        "groundedness_structural": pct(r in grounded for r in answered),
        "latency_ms": {"p50": percentile([r["ms"] for r in rows], 0.5), "p95": percentile([r["ms"] for r in rows], 0.95),
                       "max": max(r["ms"] for r in rows)},
        "llm_calls": sum(r["llm_calls"] for r in rows),
    }


# --- Cổng nhạc lý (G2) --------------------------------------------------------------------------------------------

def gate_section(cases):
    from ..admin.relevance.errors import RelevanceError
    from ..admin.relevance.gate import evaluate_pasted_text

    rows = []
    for c in (c for c in cases if c["type"] == "gate"):
        try:
            res = evaluate_pasted_text(c["text"])
            status, score = res.status, res.score
        except RelevanceError as e:
            status, score = "rejected", 0.0
            _ = e
        rows.append({"id": c["id"], "label": c["label"], "status": status, "score": score})
    rel = [r for r in rows if r["label"] == "relevant"]
    irr = [r for r in rows if r["label"] == "irrelevant"]
    tp = sum(r["status"] == "accepted" for r in rel)
    fp = sum(r["status"] == "accepted" for r in irr)
    fn = sum(r["status"] != "accepted" for r in rel)
    precision, strict_recall = precision_recall(tp, fp, fn)
    return {"gate_precision": precision, "gate_strict_recall": strict_recall,
            "gate_recall": pct(r["status"] != "rejected" for r in rel),
            "gate_offtopic_reject": pct(r["status"] == "rejected" for r in irr),
            "n": {"relevant": len(rel), "irrelevant": len(irr), "borderline": len(rows) - len(rel) - len(irr)},
            "borderline_status": {r["id"]: f'{r["status"]} ({r["score"]})' for r in rows if r["label"] == "borderline"},
            "errors": [f'{r["id"]}:{r["label"]}→{r["status"]}({r["score"]})' for r in rows
                       if (r["label"] == "relevant" and r["status"] == "rejected")
                       or (r["label"] == "irrelevant" and r["status"] == "accepted")]}


# --- Điều phối ----------------------------------------------------------------------------------------------------

def evaluate(db, user, *, live: bool = False, pause: float = 0.0, cases: list[dict] | None = None) -> dict:
    from ..ai.local_embedder import get_local_embedder
    from ..core.config import settings
    from ..services import ai_pipeline as ap

    cases = cases or load_cases()
    embedder = get_local_embedder()
    store = build_store(embedder) if embedder is not None else None
    if live:
        from ..ai.tutor.llm import get_provider

        real = get_provider(settings)
        if real is None:
            raise SystemExit("--live cần AI_ENABLED=1 và GEMINI_API_KEY trong .env")
        factory = lambda c: real  # noqa: E731
    else:
        factory = lambda c: ScriptedProvider(bogus=c["type"] == "bad_citation")  # noqa: E731

    results: dict[str, Any] = {"meta": {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "cases": len(cases),
        "by_type": {t: sum(c["type"] == t for c in cases) for t in sorted({c["type"] for c in cases})},
        "mode": "live (Gemini thật)" if live else "offline (LLM giả tất định)",
        "embedder": getattr(embedder, "model", None) or "không có e5, chỉ BM25"}}
    results["retrieval"] = retrieval_section(cases, embedder, store)
    results["calibration"] = calibration_section(cases, embedder, store)
    e2e: dict[str, Any] = {}
    with env(CHAT_RATE_LIMIT_PER_MIN="0"):
        with env(RAG_ENABLED="0"):
            e2e["legacy"] = e2e_run(db, user, cases, embedder, factory, "RAG_ENABLED=0 (e5 trong bộ nhớ + BM25)", live, pause)
        if store is not None:
            old_store = ap._store
            ap._store = lambda rcfg: store
            try:
                with env(RAG_ENABLED="1", QDRANT_URL="memory://", RAG_EMBED_DIM=str(embedder.dim)):
                    e2e["qdrant"] = e2e_run(db, user, cases, embedder, factory, "RAG_ENABLED=1 (Qdrant + rerank)", live, pause)
            finally:
                ap._store = old_store
    results["e2e"] = {k: v["metrics"] for k, v in e2e.items()}
    results["_rows"] = {k: v["rows"] for k, v in e2e.items()}
    results["gate"] = gate_section(cases)
    return results


def render_report(results: dict, baseline: dict[str, float], regs) -> str:
    m, now = results["meta"], flatten(results)
    L = [f"# Báo cáo đánh giá chatbot và cổng nhạc lý (G5)", "",
         f"Chạy lúc {m['date']}. Chế độ: **{m['mode']}**. Mô hình nhúng: {m['embedder']}. {m['cases']} ca: "
         + ", ".join(f"{k} {v}" for k, v in m["by_type"].items()) + ".", "",
         "> Bộ ca do Claude soạn (một phần lấy từ `scripts/ai/data/rag_gold.json`), nhãn đặt trước khi chạy, **chưa có người ngoài duyệt**. "
         "Ở chế độ offline, LLM là bản giả trích nguyên văn nên các số \"bám nguồn\" chỉ chứng minh lớp kiểm của máy chủ hoạt động, "
         "không phải chất lượng Gemini. Độ đúng nhạc lý của câu trả lời Gemini chưa được đo (cần người chấm).", ""]
    L += ["## 1. Truy xuất (HitRate@5, MRR@5)", "", "| Cấu hình | HitRate@5 (%) | MRR@5 | Câu nối tiếp (%) | Trượt |", "|---|---|---|---|---|"]
    for name, r in results["retrieval"].items():
        if name.startswith("_"):
            continue
        L.append(f"| {name} | {r['hit_rate_at_5']} | {r['mrr']} | {r['followup_hit_rate']} | {', '.join(r['misses']) or '-'} |")
    sweep = results["retrieval"].get("_rerank_sweep") or {}
    if sweep:
        L += ["", "Rerank theo từ khóa, quét trọng số (`RAG_RERANK_WEIGHT`; 0 = không rerank):", "", "| Trọng số | HitRate@5 (%) | MRR@5 |", "|---|---|---|"]
        L += [f"| {w} | {v['hit_rate_at_5']} | {v['mrr']} |" for w, v in sweep.items()]
        L += ["", "Luật chọn đặt trước: chỉ bật rerank nếu tăng cả HitRate lẫn MRR. Không trọng số nào đạt nên mặc định 0 (tắt)."]
    L += [""]
    cal = results["calibration"]
    L += ["## 2. Hiệu chỉnh ngưỡng điểm Qdrant (`QDRANT_MIN_SCORE`)", ""]
    if "table" in cal:
        rec = cal["recommended"]
        L += [f"Điểm cosine đoạn đầu: câu đúng chủ đề thấp nhất {cal['positive_top1']['min']} (trung vị {cal['positive_top1']['median']}); "
              f"câu lạc đề/tấn công cao nhất {cal['negative_top1']['max']} (trung vị {cal['negative_top1']['median']}). "
              f"Ngưỡng cân bằng nhất: **{rec['threshold']}** (nhận {rec['tpr']}% câu đúng chủ đề, để lọt {rec['fpr']}% câu lạc đề).", "",
              "| Ngưỡng | Nhận câu đúng (%) | Lọt câu lạc đề (%) | Cân bằng |", "|---|---|---|---|"]
        L += [f"| {r['threshold']} | {r['tpr']} | {r['fpr']} | {r['balanced']} |" for r in cal["table"][::2]]
    else:
        L.append(cal["note"])
    L += ["", "## 3. Toàn pipeline", ""]
    for key, e in results["e2e"].items():
        L += [f"### {key}", "", "| Chỉ số | Giá trị |", "|---|---|"]
        for k in ("n", "route_accuracy", "offtopic_handled", "offtopic_brief_within_2_sentences", "attack_handled",
                  "concept_wrongly_blocked", "valid_citation_rate", "bad_citation_caught", "cites_gold_block", "groundedness_structural", "llm_calls"):
            L.append(f"| {k} | {e[k]} |")
        lat = e["latency_ms"]
        L += [f"| độ trễ máy chủ p50 / p95 / max (ms, không gồm Gemini) | {lat['p50']} / {lat['p95']} / {lat['max']} |",
              f"| độ đúng luồng theo loại | {e['route_accuracy_by_type']} |", f"| luồng sai | {', '.join(e['wrong_routes']) or '-'} |", ""]
    g = results["gate"]
    L += ["## 4. Cổng nhạc lý Admin (G2)", "",
          f"Tài liệu: {g['n']['relevant']} liên quan, {g['n']['irrelevant']} lạc đề, {g['n']['borderline']} ranh giới (không tính điểm).", "",
          "| Chỉ số | % |", "|---|---|",
          f"| precision của tài liệu được nhận | {g['gate_precision']} |", f"| recall (liên quan không bị từ chối) | {g['gate_recall']} |",
          f"| recall chặt (liên quan được nhận ngay) | {g['gate_strict_recall']} |", f"| tài liệu lạc đề bị từ chối | {g['gate_offtopic_reject']} |", "",
          f"Ca sai: {', '.join(g['errors']) or 'không'}. Ca ranh giới: {g['borderline_status']}.", ""]
    L += ["## 5. Kiểm hồi quy so với baseline", ""]
    if not baseline:
        L.append("Chưa có `eval/baseline.json`.")
    else:
        L += ["| Chỉ số | Baseline | Lần này |", "|---|---|---|"]
        L += [f"| {k} | {b} | {now.get(k, 'không chạy')} |" for k, b in sorted(baseline.items())]
        L += ["", "**HỒI QUY:** " + "; ".join(map(str, regs)) if regs else "", "" if regs else "Không có hồi quy."]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m app.eval.run", description=__doc__)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--pause", type=float, default=0.0, help="giây nghỉ giữa hai câu khi --live")
    ap.add_argument("--out", default=str(REPORT_PATH))
    ap.add_argument("--update-baseline", action="store_true", help="ghi lại eval/baseline.json từ lần chạy này (làm có chủ đích)")
    args = ap.parse_args(argv)
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mkdtemp()}/eval.db")
    if not args.live:
        os.environ["AI_ENABLED"] = "0"

    from ..db.models import User
    from ..db.session import SessionLocal, create_schema

    create_schema()
    with SessionLocal() as db:
        # Chạy lại nhiều lần trên cùng CSDL (Docker) không được trùng khóa; is_synthetic để loại khỏi dashboard (nguyên tắc 9)
        if db.get(User, "eval-user") is None:
            db.add(User(id="eval-user", display_name="eval", email="eval@example.test", is_synthetic=True))
            db.commit()
        results = evaluate(db, db.get(User, "eval-user"), live=args.live, pause=args.pause)
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8")) if BASELINE_PATH.exists() else {}
    regs = [] if args.live else regressions(results, baseline)
    now = flatten(results)
    if args.update_baseline:
        BASELINE_PATH.write_text(json.dumps(dict(sorted(now.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        baseline, regs = dict(now), []
    out = render_report(results, baseline, regs)
    from pathlib import Path

    Path(args.out).write_text(out, encoding="utf-8")
    Path(args.out).with_suffix(".json").write_text(json.dumps(results, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(out.split("## 3.")[0][:1500])
    print(f"Đã ghi {args.out}")
    for r in regs:
        print("HỒI QUY:", r, file=sys.stderr)
    return 1 if regs else 0


if __name__ == "__main__":
    raise SystemExit(main())
