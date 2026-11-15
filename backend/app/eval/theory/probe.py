"""Hỏi AI Tutor (Gemini thật) từng câu trong eval/theory/questions.jsonl, lưu câu trả lời để chấm nhạc lý.

Chạy trên máy có khóa (Docker):  docker compose exec api python -m app.eval.theory.probe
  --only T001,T005   chỉ hỏi vài câu       --pause 4   giây nghỉ giữa hai câu (gói miễn phí giới hạn số lượt/phút)
  --out <tệp>        mặc định eval/theory/answers.jsonl; chạy lại thì BỎ QUA câu đã có (tiếp tục được khi đứt giữa chừng)
  --fresh            hỏi lại từ đầu (ghi đè tệp)
Mỗi câu hỏi độc lập (không có lịch sử chat), đi đúng pipeline người học dùng (định tuyến, Qdrant, Gemini, Music Engine)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from .build import OUT as QUESTIONS

DEFAULT_OUT = QUESTIONS.parent / "answers.jsonl"


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m app.eval.theory.probe", description=__doc__)
    ap.add_argument("--only", default="")
    ap.add_argument("--pause", type=float, default=4.0)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--fresh", action="store_true")
    args = ap.parse_args(argv)
    os.environ["CHAT_RATE_LIMIT_PER_MIN"] = "0"            # giới hạn tốc độ của người học không áp cho lần đo

    from ...ai.tutor.llm import get_provider
    from ...api.ai_tutor import embedder_dep
    from ...core.config import settings
    from ...db.models import User
    from ...db.session import SessionLocal, create_schema
    from ...services import ai_tutor_service as ts

    provider = get_provider(settings)
    if provider is None:
        print("Cần AI_ENABLED=true và GEMINI_API_KEY trong .env", file=sys.stderr)
        return 2
    questions = load(QUESTIONS)
    if args.only:
        want = {x.strip() for x in args.only.split(",") if x.strip()}
        questions = [q for q in questions if q["id"] in want]
    out = Path(args.out)
    if args.fresh and out.exists():
        out.unlink()
    done = {a["id"] for a in load(out)}
    todo = [q for q in questions if q["id"] not in done]
    print(f"{len(todo)} câu cần hỏi ({len(done)} đã có trong {out.name}). Mô hình: {settings.gemini_model}", flush=True)
    embedder = embedder_dep()
    create_schema()
    limited = 0
    with SessionLocal() as db:
        if db.get(User, "eval-user") is None:
            db.add(User(id="eval-user", display_name="eval", email="eval@example.test", is_synthetic=True))
            db.commit()
        user = db.get(User, "eval-user")
        with out.open("a", encoding="utf-8") as f:
            for i, q in enumerate(todo, 1):
                t0 = time.perf_counter()
                try:
                    draft, meta = ts.answer_question(db, user, q["q"], [], embedder, provider, ts._now(None))
                    row = {"id": q["id"], "q": q["q"], "reply": draft.reply, "flow": draft.flow, "route": draft.route,
                           "status": draft.status, "fallback_reason": draft.fallback_reason,
                           "source_label": draft.source_label, "citations": draft.citations, "claims": draft.claims,
                           "llm_calls": draft.llm_calls, "model": getattr(draft.llm, "model", None),
                           "ms": round((time.perf_counter() - t0) * 1000)}
                except Exception as exc:  # noqa: BLE001 - ghi lại lỗi để chấm, không dừng cả lượt
                    db.rollback()
                    row = {"id": q["id"], "q": q["q"], "error": f"{type(exc).__name__}: {exc}"[:300]}
                if row.get("fallback_reason") == "rate_limited":
                    limited += 1
                    if limited >= 3:
                        print("Gemini báo hết lượt 3 lần liền. Dừng; chạy lại lệnh sau ít phút để tiếp tục.", flush=True)
                        return 3
                    continue                                  # không ghi: lần sau hỏi lại câu này
                limited = 0
                f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
                f.flush()
                print(f"[{i}/{len(todo)}] {q['id']} {row.get('flow', '?')} {row.get('status', row.get('error', ''))[:40]}",
                      flush=True)
                time.sleep(args.pause)
    print(f"Xong. Gửi tệp {out} cho người chấm.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
