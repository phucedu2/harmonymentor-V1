"""Đánh giá logic AI soạn bài (ADR-033) trên bộ `eval/ai_soan_bai/cases.jsonl`.

    cd backend && python ../scripts/ai/danh_gia_ai_soan_bai.py --out ../eval/ai_soan_bai/ket_qua_sau.json
    cd backend && AI_GROUND_E5=1 python ../scripts/ai/danh_gia_ai_soan_bai.py      # thêm e5 nếu máy có mô hình
    # Máy Phúc, Gemini thật (tốn 1 lượt/trang mẫu, tính vào ngân sách 12 lượt soạn bài/ngày):
    cd backend && AI_ENABLED=1 GEMINI_API_KEY=... python ../scripts/ai/danh_gia_ai_soan_bai.py --live \
        --live-out ../eval/ai_soan_bai/live_gemini.json

Bộ ca do Claude soạn trên 4 trang mẫu tự viết (không chép tài liệu có bản quyền), status "draft" đến khi Đạt duyệt.
Không phụ thuộc phiên bản code: chạy được cả trên code trước đợt 3 (thiếu ai_review thì coi như "không có cờ") để so trước/sau.

Đo:
- Câu hỏi: tỷ lệ LỌT ĐÁP ÁN SAI (câu được giữ, không cần duyệt, đáp án khác đáp án vàng; mục tiêu 0), số câu sai được giữ
  nhưng bắt duyệt, số câu bị loại kèm lý do.
- Khối: tỷ lệ trích trang đúng (page_ok), bám nguồn (P/R của cờ low_grounding so với nhãn "không bám"), chép nguyên văn,
  nhắc hình; quét ngưỡng bám nguồn và chọn ngưỡng thấp nhất có recall bắt khối bịa >= 95%.
- Chống trùng: P/R ở ngưỡng hiện tại và quét ngưỡng.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(os.getenv("HM_BACKEND", ROOT / "backend")).resolve()
sys.path.insert(0, str(BACKEND))
CASES = ROOT / "eval" / "ai_soan_bai" / "cases.jsonl"
SKILLS = {"interval.naming", "chord.seventh_build", "chord.triad_build", "scale.major", "function.dominant",
          "roman.major_seventh", "chord.triad_quality", "scale.minor", "rhythm.meter"}


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def pr(pred: list[bool], gold: list[bool]) -> dict:
    tp = sum(p and g for p, g in zip(pred, gold))
    fp = sum(p and not g for p, g in zip(pred, gold))
    fn = sum(g and not p for p, g in zip(pred, gold))
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision": round(tp / (tp + fp), 3) if tp + fp else None,
            "recall": round(tp / (tp + fn), 3) if tp + fn else None}


def _norm(ans) -> str:
    if isinstance(ans, list):
        return " ".join(str(a).strip().lower() for a in ans)
    return str(ans or "").strip().lower()


def eval_questions(cases: list[dict]) -> dict:
    from app.admin import ai_questions as aq

    rows, dropped = [], []
    for c in cases:
        item = {"level": "nho", **c["item"]}
        try:
            q, why = aq.normalize_question(item, SKILLS, lambda p: 1, blocks=1)
        except TypeError:   # code trước đợt 3: chưa có tham số blocks
            q, why = aq.normalize_question(item, SKILLS, lambda p: 1)
        gold = c["gold"].get("answer", c["gold"].get("answers"))
        if q is None:
            dropped.append({"id": c["id"], "reason": why})
            rows.append({"id": c["id"], "kept": False})
            continue
        ans = q.get("answer", q.get("answers"))
        if ans is None:
            ans = aq.engine_answer(q)
        wrong = _norm(ans) != _norm(gold)
        rows.append({"id": c["id"], "kept": True, "answer": ans, "wrong": wrong,
                     "needs_review": bool(q.get("needs_review")), "notes": q.get("review_notes", [])})
    kept = [r for r in rows if r["kept"]]
    leaks = [r["id"] for r in kept if r["wrong"] and not r["needs_review"]]
    return {"n": len(cases), "kept": len(kept), "dropped": dropped,
            "leak_ids": leaks, "leak_rate": round(len(leaks) / len(cases), 3),
            "wrong_kept_but_review": [r["id"] for r in kept if r["wrong"] and r["needs_review"]],
            "rows": rows}


def _page_acc(rows: list[dict]) -> float:
    pf = {"page_out_of_range", "low_grounding", "wrong_page"}
    rs = [r for r in rows if r["gold"]["grounded"] or not r["gold"]["page_ok"]]
    return round(sum((not (pf & set(r["flags"]))) == r["gold"]["page_ok"] for r in rs) / len(rs), 3)


def eval_blocks(cases: list[dict], backend: str) -> dict:
    os.environ["AI_GROUND_E5"] = "1" if backend == "e5" else "0"
    try:
        from app.admin import ai_review as rv
    except ImportError:
        rv = None
    rows, cited_scores = [], []
    for c in cases:
        pages = c["pages"]
        block = dict(c["block"])
        content = {"blocks": [block]}
        flags = rv.review_flags(pages, content, 1, len(pages)) if rv else []
        if rv:
            sc = rv.PageScorer({i + 1: t for i, t in enumerate(pages)})
            if backend == "e5" and sc.backend != "e5":
                return {"backend": "e5", "skipped": "máy không có mô hình e5"}
            body = " ".join(block.get("paragraphs", []))
            cited_scores.append((sc.scores(body).get(block.get("page"), 0.0), c["gold"]["grounded"]))
        types = {f["type"] for f in flags}
        rows.append({"id": c["id"], "flags": sorted(types), "gold": c["gold"]})
    g = [r["gold"] for r in rows]
    out = {
        "backend": backend if rv else "không có (code cũ)",
        # Trích trang đúng: trên khối có nhãn "bám nguồn" hoặc "sai trang" (khối bịa không có trang đúng để so).
        "page_ok_accuracy": _page_acc(rows),
        # Trích trang đúng trên bài XUẤT BẢN: khối sai trang mà không có cờ nào thì lọt tới học sinh.
        "wrong_page_unflagged": [r["id"] for r in rows if not r["gold"]["page_ok"]
                                 and not ({"page_out_of_range", "low_grounding", "wrong_page"} & set(r["flags"]))],
        "ungrounded_flag": pr([bool({"low_grounding", "wrong_page"} & set(r["flags"])) for r in rows], [not x["grounded"] for x in g]),
        "verbatim_flag": pr(["verbatim" in r["flags"] for r in rows], [x["verbatim"] for x in g]),
        "figure_flag": pr(["figure_ref" in r["flags"] for r in rows], [x["figure_ref"] for x in g]),
        "rows": rows,
    }
    if cited_scores:
        sweep = []
        for t in sorted({round(s, 3) for s, _ in cited_scores} | {0.05, 0.1, 0.12, 0.15, 0.2, 0.8, 0.85}):
            pred = [s < t for s, _ in cited_scores]
            sweep.append({"threshold": t, **pr(pred, [not gnd for _, gnd in cited_scores])})
        ok = [s for s in sweep if (s["recall"] or 0) >= 0.95]
        out["grounding_sweep"] = sweep
        out["chosen_threshold"] = min(ok, key=lambda s: (s["fp"], s["threshold"]))["threshold"] if ok else None
        out["current_threshold"] = rv.GROUND_MIN[backend]
        out["cited_scores"] = [{"id": c["id"], "score": s, "grounded": gnd} for c, (s, gnd) in zip(cases, cited_scores)]
    return out


def eval_pairs(cases: list[dict], backend: str) -> dict:
    os.environ["AI_DEDUP_E5"] = "1" if backend == "e5" else "0"
    from app.admin import ai_job

    scores = []
    for c in cases:
        sim = ai_job.Similarity([ai_job.Known("X", "x", "khối", c["a"], "block")])
        if backend == "e5" and sim.backend != "e5":
            return {"backend": "e5", "skipped": "máy không có mô hình e5"}
        scores.append((sim.best(c["b"], "block")[0], c["gold"]["duplicate"]))
    cur = ai_job.DUP_BLOCK[backend]
    sweep = [{"threshold": t, **pr([s >= t for s, _ in scores], [d for _, d in scores])}
             for t in sorted({round(s, 3) for s, _ in scores})]
    return {"backend": backend, "current_threshold": cur,
            "at_current": pr([s >= cur for s, _ in scores], [d for _, d in scores]), "sweep": sweep,
            "scores": [{"id": c["id"], "score": s, "duplicate": d} for c, (s, d) in zip(cases, scores)]}


def live(cases: list[dict], out_path: Path) -> None:
    """Gemini thật soạn bài từ 4 trang mẫu, ghi kết quả + cờ để Đạt gắn nhãn (không tự chấm đúng/sai nhạc lý)."""
    from app.admin import ai_review as rv
    from app.admin import ai_service
    from app.ai.provider import get_provider

    pages = next(c["pages"] for c in cases if c["type"] == "block")
    provider = get_provider()
    system, user = ai_service.SYSTEM_PROMPT, ai_service.user_prompt("\n\n".join(
        f"[Trang {i + 1}]\n{t}" for i, t in enumerate(pages)), 1, len(pages), ai_service.allowed_skills_text())
    raw = provider.generate(system=system, user=user, schema=ai_service.LESSON_SCHEMA, max_tokens=8192)
    content = json.loads(raw.text if hasattr(raw, "text") else raw)
    flags = rv.review_flags(pages, content, 1, len(pages))
    out_path.write_text(json.dumps({"content": content, "flags": flags,
                                    "label_me": "Đạt: ghi grounded/page_ok/answer_ok cho từng khối/câu"},
                                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã ghi {out_path} ({len(content.get('blocks', []))} khối, {len(flags)} cờ)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--live-out", type=Path, default=ROOT / "eval" / "ai_soan_bai" / "live_gemini.json")
    args = ap.parse_args()
    cases = load(CASES)
    if args.live:
        live(cases, args.live_out)
        return
    want_e5 = os.getenv("AI_GROUND_E5", "0") != "0"
    res = {"cases": len(cases), "questions": eval_questions([c for c in cases if c["type"] == "question"])}
    for backend in ("tfidf", "e5"):
        if backend == "e5" and not want_e5:
            continue
        res[f"blocks_{backend}"] = eval_blocks([c for c in cases if c["type"] == "block"], backend)
        res[f"dedup_{backend}"] = eval_pairs([c for c in cases if c["type"] == "pair"], backend)
    q = res["questions"]
    print(f"Câu hỏi: {q['n']} ca, giữ {q['kept']}, loại {len(q['dropped'])}, LỌT ĐÁP ÁN SAI {len(q['leak_ids'])} "
          f"({q['leak_rate']:.0%}) {q['leak_ids']}, sai nhưng bắt duyệt {q['wrong_kept_but_review']}")
    for k, v in res.items():
        if k.startswith("blocks_") and "skipped" not in v:
            print(f"Khối [{v['backend']}]: trang đúng {v['page_ok_accuracy']:.0%}, sai trang không cờ {v['wrong_page_unflagged']}, "
                  f"bịa P/R {v['ungrounded_flag']['precision']}/{v['ungrounded_flag']['recall']}, "
                  f"chép R {v['verbatim_flag']['recall']}, hình R {v['figure_flag']['recall']}, "
                  f"ngưỡng hiện {v.get('current_threshold')} chọn {v.get('chosen_threshold')}")
        if k.startswith("dedup_") and "skipped" not in v:
            print(f"Trùng [{v['backend']}] ngưỡng {v['current_threshold']}: P/R {v['at_current']['precision']}/{v['at_current']['recall']}")
    if args.out:
        args.out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
