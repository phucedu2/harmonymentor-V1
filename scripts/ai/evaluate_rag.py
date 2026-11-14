"""Đánh giá RAG và AI Tutor trên bộ chuẩn GĐ4 (04 mục 8.3, Bảng 28).

    cd backend && python ../scripts/ai/evaluate_rag.py                       # chỉ phần không gọi mạng (BM25, chặn, guardrail)
    cd backend && AI_ENABLED=1 GEMINI_API_KEY=... python ../scripts/ai/evaluate_rag.py --live --out ../docs/giai-doan/ai-gd4/ket_qua_rag.json

Bộ chuẩn: scripts/ai/data/rag_gold.json (Claude soạn và tự duyệt, chưa có người duyệt độc lập).
Đo:
- Truy xuất: Recall@1, Recall@4, MRR (một câu "trúng" khi có ít nhất một block_id đúng), Gemini so với BM25.
- Chặn: tỷ lệ từ chối đúng câu ngoài phạm vi và câu tấn công; tỷ lệ câu khái niệm bị chặn nhầm. Đo bằng
  đúng luồng của dịch vụ với một LLM ghi lại lời gọi: câu bị chặn thì không có lời gọi nào.
- Guardrail: số câu cài lỗi bị bắt, số câu đúng bị báo nhầm.
- (--live) Trả lời đầy đủ bằng Gemini: tỷ lệ có ≥ 1 trích dẫn đúng bài, tỷ lệ trích dẫn hợp lệ (thuộc bộ đúng),
  tỷ lệ câu có khẳng định sai Engine sau kiểm, tỷ lệ nhãn, p50/p95 độ trễ, số lượt gọi Gemini.
Không đánh giá "đúng nhạc lý so với đáp án tham chiếu" tự động: cần người chấm (ghi NOT EVALUATED).
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
GOLD = ROOT / "scripts" / "ai" / "data" / "rag_gold.json"


def pct(xs):
    xs = list(xs)
    return round(100 * sum(xs) / len(xs), 1) if xs else None


def p95(xs):
    s = sorted(xs)
    return s[max(0, round(0.95 * len(s)) - 1)] if s else None


def retrieval_metrics(gold, retrieve_fn):
    r1, r4, rr, rows = [], [], [], []
    for g in gold:
        ids = [h.chunk.block_id for h in retrieve_fn(g["q"]).hits]
        good = set(g["blocks"])
        rank = next((i + 1 for i, b in enumerate(ids) if b in good), None)
        r1.append(rank == 1)
        r4.append(rank is not None and rank <= 4)
        rr.append(1 / rank if rank else 0.0)
        rows.append({"id": g["id"], "top": ids[:4], "rank": rank})
    return {"recall@1": pct(r1), "recall@4": pct(r4), "mrr": round(sum(rr) / len(rr), 3), "rows": rows}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="gọi Gemini thật (cần AI_ENABLED=1 và khóa)")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--pause", type=float, default=0.0,
                    help="giây nghỉ giữa hai câu khi --live (gói Gemini miễn phí giới hạn số lượt/phút)")
    args = ap.parse_args()

    tmp = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/rag.db"
    if not args.live:
        os.environ["AI_ENABLED"] = "0"

    from app.ai.embedder import get_embedder
    from app.ai.tutor.guardrail import run_tool, scan_reply
    from app.ai.tutor.llm import FakeProvider, get_provider
    from app.ai.tutor.retriever import retrieve
    from app.core.config import settings
    from app.db.models import User
    from app.db.session import SessionLocal, create_schema
    from app.services import ai_tutor_service as ts

    data = json.loads(GOLD.read_text(encoding="utf-8"))
    gold = data["concept"]
    out: dict = {"pause_s": args.pause, "gold": {"concept": len(gold), "out_of_scope": len(data["out_of_scope"]),
                          "attacks": len(data["attacks"]), "seeded": len(data["seeded_errors"]),
                          "author": "Claude soạn và tự duyệt 04/11/2026, chưa có người duyệt độc lập"},
                 "settings": {"rag_min_score": settings.rag_min_score, "rag_top_k": settings.rag_top_k,
                              "embed_model": settings.gemini_embed_model, "llm": settings.gemini_model}}

    # 0. Đáp án tham chiếu có nội dung nhạc lý phải khớp Music Engine.
    checks = [(g["id"], run_tool(g["engine"]["tool"], g["engine"]["args"])[0] == g["engine"]["expect"])
              for g in gold if g.get("engine")]
    out["gold_engine_checked"] = {"n": len(checks), "ok": sum(ok for _, ok in checks)}

    # 1. Truy xuất.
    out["retrieval"] = {"bm25": retrieval_metrics(gold, lambda q: retrieve(q, None, min_score=-1, bm25_min_score=-1))}
    embedder = get_embedder(settings) if args.live else None
    calls = {"embed": 0, "llm": 0}
    if embedder is not None:
        inner = embedder.embed

        def counted(texts, task):
            calls["embed"] += 1
            return inner(texts, task)

        embedder.embed = counted  # type: ignore[method-assign]
        out["retrieval"]["gemini"] = retrieval_metrics(gold, lambda q: retrieve(q, embedder, min_score=-1))
        above = [retrieve(g["q"], embedder, min_score=settings.rag_min_score).hits != [] for g in gold]
        out["retrieval"]["gemini"]["concept_above_threshold"] = pct(above)
    else:
        out["retrieval"]["gemini"] = "NOT EVALUATED (chạy với --live)"

    # 2. Chặn ngoài phạm vi và tấn công: đúng luồng dịch vụ, LLM giả ghi lời gọi.
    create_schema()
    with SessionLocal() as db:
        db.add(User(id="eval-rag", display_name="eval", email="eval@example.test"))
        db.commit()
        user = db.get(User, "eval-rag")

        def gated(q: str) -> bool:
            probe = FakeProvider(['{"reply":"x","citations":[],"engine_claims":[],"hint_level":0,'
                                  '"suggested_actions":[],"intent":"concept"}'])
            draft, _ = ts.answer_question(db, user, q, [], embedder, probe, ts._now(None))
            return not probe.calls and draft.route in {"refused_injection", "out_of_scope", "unsure"}

        out["gating"] = {
            "out_of_scope_refused": pct(gated(q) for q in data["out_of_scope"]),
            "attacks_refused": pct(gated(q) for q in data["attacks"]),
            "concept_wrongly_blocked": pct(gated(g["q"]) for g in gold),
            "mode": "embedding" if embedder else "bm25",
        }

    # 3. Guardrail trên câu trả lời cài lỗi.
    tp = fp = fn = tn = 0
    for s in data["seeded_errors"]:
        caught = any(c.status == "contradicted" for c in scan_reply(s["reply"]))
        tp += caught and s["wrong"]
        fn += (not caught) and s["wrong"]
        fp += caught and not s["wrong"]
        tn += (not caught) and not s["wrong"]
    out["guardrail"] = {"caught": tp, "missed": fn, "false_alarm": fp, "clean_passed": tn}

    # 4. Trả lời đầy đủ bằng Gemini.
    provider = get_provider(settings) if args.live else None
    if provider is not None:
        rows, lat = [], []
        with SessionLocal() as db:
            user = db.get(User, "eval-rag")
            for g in gold:
                time.sleep(args.pause)
                t = time.perf_counter()
                res = ts.handle_message(db, user, g["q"], embedder=embedder, provider=provider)
                lat.append(round((time.perf_counter() - t) * 1000))
                cites = [c["block_id"] for c in res["citations"]]
                lessons = {b.split("-")[0] for b in g["blocks"]}
                rows.append({"id": g["id"], "status": res["status"], "intent": res["intent"], "cites": cites,
                             "cite_right_lesson": any(c.split("-")[0] in lessons for c in cites),
                             "cites_in_gold": all(c in g["blocks"] for c in cites) if cites else None,
                             "contradicted": any(c["status"] == "contradicted" for c in res["engine_claims"]),
                             "verified_label": res["verified"], "fallback_reason": res["fallback_reason"],
                             "ms": lat[-1], "reply": res["reply"]})
            from app.db.models import ChatMessage
            from sqlalchemy import select

            calls["llm"] = sum((m.tool_calls or {}).get("llm_calls", 0)
                               for m in db.scalars(select(ChatMessage).where(ChatMessage.role == "assistant")))
        out["answers"] = {
            "n": len(rows), "status_ok": pct(r["status"] == "ok" for r in rows),
            "cite_right_lesson": pct(r["cite_right_lesson"] for r in rows),
            "cites_all_in_gold": pct(bool(r["cites_in_gold"]) for r in rows),
            "contradicted_after_check": sum(r["contradicted"] for r in rows),
            "verified_label": pct(r["verified_label"] for r in rows),
            "latency_ms": {"p50": statistics.median(lat), "p95": p95(lat), "max": max(lat)},
            "api_calls": calls, "rows": rows,
            "musical_correctness_vs_reference": "NOT EVALUATED (cần người chấm; Đạt lấy mẫu 10 câu)",
        }
    else:
        out["answers"] = "NOT EVALUATED (chạy với --live)"

    text = json.dumps(out, ensure_ascii=False, indent=1)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    summary = {k: v for k, v in out.items() if k != "answers"}
    for name in ("bm25", "gemini"):
        if isinstance(summary["retrieval"].get(name), dict):
            summary["retrieval"][name] = {k: v for k, v in summary["retrieval"][name].items() if k != "rows"}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    if isinstance(out["answers"], dict):
        print(json.dumps({k: v for k, v in out["answers"].items() if k != "rows"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
