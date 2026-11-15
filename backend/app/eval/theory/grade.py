"""Chấm tự động câu trả lời trong eval/theory/answers.jsonl, ghi eval/theory/grade.md.

Chạy: python -m app.eval.theory.grade [--answers <tệp>] [--review eval/theory/review.jsonl]
Hai lớp tự động, chỉ để khoanh vùng cho người chấm (không thay người chấm):
  1. Music Engine quét lại câu trả lời (hợp âm + nốt, âm giai + nốt, quãng, số La Mã): có mục "contradicted" là sai chắc.
  2. Đối chiếu đáp án của câu hỏi: nốt bắt buộc (notes_all), cụm chấp nhận (any), số La Mã (roman_any).
Kết luận cuối lấy từ review.jsonl (người chấm ghi: dung | sai | tranh_luan | khong_tra_loi, kèm ghi chú)."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from ...ai.tutor.bm25 import strip_accents
from ...ai.tutor.guardrail import scan_reply
from ...ai.tutor.notes import solfege_to_letters
from .build import OUT as QUESTIONS
from .probe import DEFAULT_OUT, load

REVIEW = QUESTIONS.parent / "review.jsonl"
REPORT = QUESTIONS.parent / "grade.md"
_ACC = str.maketrans({"♭": "b", "♯": "#", "𝄫": "bb", "𝄪": "##", "–": "-", "—": "-"})
NOTE_TOKEN = re.compile(r"(?<![\w#])([A-G](?:bb|b|##|#)?)(?![\w#])")
SYMBOLISH = re.compile(r"^[A-G](?:bb|b|##|#)?\S*$")


def norm(text: str) -> str:
    return solfege_to_letters(text).translate(_ACC)


def notes_in(text: str) -> set[str]:
    return set(NOTE_TOKEN.findall(norm(text)))


def has_phrase(text: str, phrase: str) -> bool:
    t = norm(text)
    p = phrase.translate(_ACC)
    if SYMBOLISH.match(p):                     # ký hiệu hợp âm/nốt: phân biệt hoa thường, đứng riêng
        return re.search(rf"(?<![\w#]){re.escape(p)}(?![\w#])", t) is not None
    flat = " " + strip_accents(t.lower()) + " "
    return strip_accents(p.lower()) in flat


def has_roman(text: str, rn: str) -> bool:
    t = text.translate(_ACC)
    return re.search(rf"(?<![\w/]){re.escape(rn)}(?![\w°ø])", t) is not None


def auto_check(q: dict, a: dict) -> dict:
    reply = a.get("reply") or ""
    problems = []
    if a.get("error"):
        return {"auto": "loi", "problems": [a["error"]]}
    if a.get("status") != "ok":
        problems.append(f"không phải câu AI trả lời bình thường: status={a.get('status')} lý do={a.get('fallback_reason')}")
    contradicted = [c for c in scan_reply(reply) if c.status == "contradicted"]
    contradicted += [c for c in (a.get("claims") or []) if isinstance(c, dict) and c.get("status") == "contradicted"]
    for c in contradicted:
        c = c if isinstance(c, dict) else c.as_dict()
        problems.append(f"Engine bác: {c['tool']} {c['args']} AI ghi '{c['claimed']}', Engine: '{c['engine']}'")
    exp = q.get("expect", {})
    found = notes_in(reply)
    missing = [n for n in exp.get("notes_all", []) if n not in found]
    if missing:
        problems.append(f"thiếu nốt {missing}")
    for group in exp.get("any", []):
        if not any(has_phrase(reply, p) for p in group):
            problems.append(f"không thấy cụm nào trong {group[:4]}{'…' if len(group) > 4 else ''}")
    if exp.get("roman_any") and not any(has_roman(reply, r) for r in exp["roman_any"]):
        problems.append(f"không thấy số La Mã {exp['roman_any']}")
    return {"auto": "dat" if not problems else "can_xem", "problems": problems, "engine_contradicted": len(contradicted)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m app.eval.theory.grade")
    ap.add_argument("--answers", default=str(DEFAULT_OUT))
    ap.add_argument("--review", default=str(REVIEW))
    ap.add_argument("--out", default=str(REPORT))
    args = ap.parse_args(argv)
    qs = {q["id"]: q for q in load(QUESTIONS)}
    answers = {a["id"]: a for a in load(Path(args.answers))}
    review = {r["id"]: r for r in load(Path(args.review))}
    rows = []
    for qid, a in answers.items():
        q = qs.get(qid)
        if q is None:
            continue
        r = auto_check(q, a)
        r.update(id=qid, group=q["group"], topic=q["topic"], trap=q["trap"], flow=a.get("flow"),
                 verdict=review.get(qid, {}).get("verdict"), note=review.get(qid, {}).get("note", ""))
        rows.append(r)
    auto = Counter(r["auto"] for r in rows)
    verdict = Counter(r["verdict"] or "chua_cham" for r in rows)
    lines = ["# Chấm độ đúng nhạc lý câu trả lời AI Tutor", "",
             f"Câu đã có trả lời: {len(rows)}/{len(qs)}. Tự động: {dict(auto)}. Người chấm: {dict(verdict)}.", "",
             "| Nhóm | Số câu | Sai (người chấm) | Tranh luận | Tự động cần xem |", "|---|---|---|---|---|"]
    for g in ("bai", "ngoai"):
        sub = [r for r in rows if r["group"] == g]
        lines.append(f"| {g} | {len(sub)} | {sum(r['verdict'] == 'sai' for r in sub)} | "
                     f"{sum(r['verdict'] == 'tranh_luan' for r in sub)} | {sum(r['auto'] != 'dat' for r in sub)} |")
    lines += ["", "## Câu sai hoặc cần xem", ""]
    for r in rows:
        if r["auto"] != "dat" or r["verdict"] in ("sai", "tranh_luan"):
            q, a = qs[r["id"]], answers[r["id"]]
            lines += [f"### {r['id']} [{r['topic']}{', bẫy' if r['trap'] else ''}] luồng {r['flow']} · người chấm: "
                      f"{r['verdict'] or 'chưa'}", f"- Hỏi: {q['q']}", f"- Đáp án: {q['answer']}",
                      f"- AI: {(a.get('reply') or a.get('error') or '').strip()[:600]}"]
            lines += [f"- Tự động: {p}" for p in r["problems"]]
            if r["note"]:
                lines.append(f"- Ghi chú người chấm: {r['note']}")
            lines.append("")
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(rows)} câu. Tự động {dict(auto)}. Người chấm {dict(verdict)}. Ghi {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
