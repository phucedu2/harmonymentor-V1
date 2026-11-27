"""Lời giải và giải thích từng phương án sai do Music Engine viết (Phúc chốt 27/11/2026, câu 4A và 5A).

Vì sao Engine viết chứ không để Gemini viết: câu tính được (quãng, số La Mã, nốt hợp âm, âm giai, tên hợp âm) thì Engine
đã biết đáp án đúng và biết cách đếm ra nó, nên lời giải theo mẫu luôn đúng, không tốn lượt Gemini và không cần người
duyệt lại chữ. Câu khái niệm Engine không kiểm được thì vẫn để Gemini viết lời giải trong cùng lần soạn (không thêm lượt).

Mọi số liệu (số nửa cung, tên quãng, nốt) lấy từ Engine; module này chỉ ghép câu chữ. Không đổi hành vi Engine.
"""

from __future__ import annotations

from typing import Any

from ..ai.tutor.guardrail import scan_reply
from ..music_engine import tools as engine
from ..music_engine.chord import parse_chord_symbol
from ..music_engine.errors import MusicEngineError
from ..music_engine.grading import (_iv_vi, grade_build_chord, grade_build_scale, grade_identify_chord,
                                    grade_identify_interval, grade_roman_numeral)
from ..music_engine.interval import interval_between, parse_interval
from ..music_engine.pitch import parse_note
from ..music_engine.roman import roman_numeral

LETTERS = "CDEFGAB"
SCALE_STEPS = {"major": ("trưởng", "1 – 1 – ½ – 1 – 1 – 1 – ½"), "natural_minor": ("thứ tự nhiên", "1 – ½ – 1 – 1 – ½ – 1 – 1")}
_ERRORS = (MusicEngineError, ValueError, KeyError, IndexError, AttributeError, TypeError)


def _letters(lower: str, upper: str, count: int) -> str:
    # Ngăn bằng dấu phẩy: "C D E" liền nhau bị bộ soát chữ (guardrail) đọc thành "hợp âm E gồm C D E".
    start = LETTERS.index(parse_note(lower).letter)
    return ", ".join(LETTERS[(start + i) % 7] for i in range(count))


def interval_text(lower: str, upper: str) -> str | None:
    """"Đếm chữ cái C D E → quãng 3; C lên E cách 4 nửa cung → quãng 3 trưởng (M3)." Quãng kép nói rõ +7 (MUS-INT-010)."""
    try:
        iv = interval_between(lower, upper)
        lo, up = parse_note(lower).name, parse_note(upper).name
        simple = iv.simple_number
        simple_iv = parse_interval(f"{iv.quality}{simple}")
        text = (f"Đếm chữ cái từ {lo} tới {up} được {simple} chữ cái ({_letters(lower, upper, simple)}) → quãng {simple}. "
                f"Khoảng cách {simple_iv.semitones} nửa cung → {_iv_vi(simple_iv)} ({simple_iv.name}).")
        if iv.is_compound:
            text += (f" {up} nằm ở quãng tám phía trên nên đây là quãng kép: {simple} + 7 = {iv.number}, tính chất giữ "
                     f"nguyên → {_iv_vi(iv)} ({iv.name}).")
        return text
    except _ERRORS:
        return None


def _formula(symbol: str) -> tuple[str, list[str]] | None:
    try:
        chord = parse_chord_symbol(symbol)
        out = engine.get_chord_tones(symbol=symbol)
    except _ERRORS:
        return None
    if not out.get("ok"):
        return None
    parts = [_iv_vi(parse_interval(i)) for i in chord.type.intervals if i != "P1"]
    return chord.root.name, [f"{', '.join(parts)} tính từ {chord.root.name}", " ".join(out["notes"])]


def chord_text(symbol: str) -> str | None:
    f = _formula(symbol)
    if f is None:
        return None
    root, (formula, notes) = f
    return f"{symbol} có nốt gốc {root}, chồng thêm {formula} → {notes}."


def scale_text(tonic: str, scale_type: str) -> str | None:
    if scale_type not in SCALE_STEPS:
        return None
    try:
        out = engine.get_scale(tonic=tonic, scale_type=scale_type)
    except _ERRORS:
        return None
    if not out.get("ok"):
        return None
    name, steps = SCALE_STEPS[scale_type]
    return (f"Âm giai {tonic} {name} đi theo khoảng cách {steps} cung, mỗi chữ cái dùng đúng một lần: "
            f"{' '.join(out['notes'])}.")


def roman_text(key: str, chord: str) -> str | None:
    try:
        rn = roman_numeral(key, chord)
    except _ERRORS:
        return None
    ivs = set(rn.chord.type.intervals)
    if "m3" in ivs and "d5" in ivs:
        look = "quãng 3 thứ và quãng 5 giảm nên viết chữ thường kèm " + ("ø" if "m7" in ivs else "°")
    elif "m3" in ivs:
        look = "quãng 3 thứ nên viết chữ thường"
    elif "A5" in ivs:
        look = "quãng 3 trưởng và quãng 5 tăng nên viết chữ hoa kèm +"
    else:
        look = "quãng 3 trưởng nên viết chữ hoa"
    seventh = any(i.endswith("7") for i in ivs)
    return (f"Trong giọng {key}, {rn.chord.root.name} là bậc {rn.degree}. {chord} có {look}"
            f"{', thêm số 7 vì là hợp âm bảy' if seventh else ''} → {rn.numeral.replace('M7', 'maj7')}.")


def chord_name_text(notes: list[str]) -> str | None:
    try:
        expected = grade_identify_chord(notes, "C")["expected"]
    except _ERRORS:
        return None
    if not expected:
        return None
    body = chord_text(expected[0])
    return f"Xếp {' '.join(notes)} thành chồng quãng ba: {body}" if body else None


def check_text(check: dict[str, str]) -> str | None:
    t = check.get("type")
    if t == "interval":
        return interval_text(check["lower"], check["upper"])
    if t == "roman":
        return roman_text(check["key"], check["chord"])
    if t == "chord_tones":
        return chord_text(check["symbol"])
    if t == "scale":
        return scale_text(check["tonic"], check["scale_type"])
    if t == "chord_name":
        return chord_name_text(check["notes"].replace(",", " ").split())
    return None


def _claim_text(tool: str, args: dict[str, str]) -> str | None:
    if tool == "identify_interval":
        return interval_text(args["lower"], args["upper"])
    if tool == "get_chord_tones":
        return chord_text(args["symbol"])
    if tool == "get_scale":
        return scale_text(args["tonic"], args["scale_type"])
    if tool == "get_roman_numeral":
        return roman_text(args["key"], args["chord"])
    return None


def statement_text(statement: str, truth: bool) -> str | None:
    """Câu Đúng/Sai Engine đã quyết: giải thích từng vế Engine kiểm (vế sai nêu trước)."""
    claims = sorted(scan_reply(statement), key=lambda c: c.status != "contradicted")
    parts = [p for p in (_claim_text(c.tool, c.args) for c in claims) if p]
    if not parts:
        return None
    return ("Câu này đúng. " if truth else "Câu này sai. ") + " ".join(parts)


def explanation_for(q: dict[str, Any]) -> str | None:
    """Lời giải Engine viết cho câu đã được Engine kiểm; None khi câu không tính được (để Gemini/người viết)."""
    if not q.get("engine_verified"):
        return None
    kind = q["kind"]
    if kind == "build_chord":
        return chord_text(q["symbol"])
    if kind == "build_scale":
        return scale_text(q["tonic"], q["scale_type"])
    if kind == "true_false":
        return statement_text(q["prompt"], q["answer"] == "Đúng")
    check = q.get("check")
    if not check:
        return None
    body = check_text(check)
    if body is None:
        return None
    if kind == "multi_select":
        return f"{body} Vì vậy chọn: {', '.join(q['answers'])}."
    return body


def _grade(check: dict[str, str], answer: str) -> dict | None:
    notes = answer.replace(",", " ").split()
    try:
        t = check["type"]
        if t == "interval":
            return grade_identify_interval(check["lower"], check["upper"], answer)
        if t == "roman":
            return grade_roman_numeral(check["key"], check["chord"], answer)
        if t == "chord_tones":
            return grade_build_chord(check["symbol"], notes)
        if t == "scale":
            return grade_build_scale(check["tonic"], check["scale_type"], notes)
        if t == "chord_name":
            return grade_identify_chord(check["notes"].replace(",", " ").split(), answer)
    except _ERRORS:
        return None
    return None


def wrong_option_feedback(q: dict[str, Any]) -> dict[str, str]:
    """Câu trắc nghiệm Engine kiểm: mỗi phương án sai kèm lời Engine chỉ ra sai ở đâu (cùng câu chữ học sinh thấy khi
    tự gõ sai ở bài tự luận). Phương án Engine không giải thích được thì để trống, giữ lời AI nếu có."""
    check = q.get("check")
    if q["kind"] != "mcq" or not q.get("engine_verified") or not check:
        return {}
    out: dict[str, str] = {}
    for option in q["options"]:
        if option == q["answer"]:
            continue
        graded = _grade(check, option)
        msg = (graded or {}).get("message_vi") or ""
        if graded and not graded.get("correct") and msg:
            out[option] = msg
    return out
