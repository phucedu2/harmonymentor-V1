"""Chấm bài và chẩn đoán lỗi (SRS 4.5, 4.9).

Thứ tự ưu tiên chẩn đoán (báo cáo v1 §6.4, CHỜ DUYỆT vì là quyết định sư phạm):
ENHARMONIC_SPELLING → WRONG_ROOT → MISSING_TONE / EXTRA_TONE → THIRD → FIFTH → SEVENTH → NOT_IN_KEY.
Trả về mọi mã phát hiện được; mã đầu tiên dùng cho lời giải thích chính.

Mỗi mã có sẵn một câu tiếng Việt để hệ thống vẫn giải thích được khi AI tắt (SRS NFR-08).
Mã trong PROPOSED_CODES là mã mình đề xuất thêm, chưa có trong bảng SRS 4.5.
"""

from __future__ import annotations

from collections import Counter
from typing import Optional

from .chord import ChordSymbol, chord_member, identify_chord, parse_chord_symbol
from .errors import MusicEngineError
from .interval import Interval, interval_between, parse_interval, transpose
from .pitch import Note, parse_note
from .roman import CONVENTION_ID as ROMAN_CONVENTION, roman_numeral
from .scale import build_scale

ENGINE_VERSION = "0.2.0-dev"
GRADING_MODES = ("strict_spelling", "pitch_class_only")

PRIORITY = [
    "ENHARMONIC_SPELLING", "WRONG_ROOT", "MISSING_TONE", "EXTRA_TONE",
    "THIRD_QUALITY", "FIFTH_QUALITY", "SEVENTH_QUALITY", "NOT_IN_KEY",
    "WRONG_INTERVAL_SIZE", "WRONG_INTERVAL_QUALITY", "WRONG_OCTAVE",
    "NOT_ROOT_POSITION", "WRONG_SCALE_DEGREE_ORDER", "ROMAN_DEGREE", "ROMAN_QUALITY_MARK",
]
PROPOSED_CODES = {"WRONG_INTERVAL_QUALITY", "WRONG_OCTAVE", "NOT_ROOT_POSITION",
                  "WRONG_SCALE_DEGREE_ORDER", "ROMAN_DEGREE", "ROMAN_QUALITY_MARK", "EXTRA_TAP"}

_ROLE_VI = {"root": "nốt gốc", "third": "quãng 3", "fifth": "quãng 5", "seventh": "quãng 7",
            "second": "quãng 2", "fourth": "quãng 4"}
_QUALITY_VI = {"P": "đúng", "M": "trưởng", "m": "thứ", "A": "tăng", "d": "giảm",
               "AA": "tăng kép", "dd": "giảm kép"}


def _iv_vi(iv: Interval) -> str:
    return f"quãng {iv.number} {_QUALITY_VI[iv.quality]}"


def _result(correct: bool, expected, codes: list[dict], convention_id: Optional[str] = None,
            **extra) -> dict:
    codes = sorted(codes, key=lambda c: PRIORITY.index(c["code"]) if c["code"] in PRIORITY else 99)
    return {
        "correct": correct,
        "expected": expected,
        "errors": codes,
        "primary_error": codes[0]["code"] if codes else None,
        "message_vi": codes[0]["message_vi"] if codes else "Chính xác!",
        "engine_version": ENGINE_VERSION,
        "convention_id": convention_id,
        **extra,
    }


def _err(code: str, message_vi: str, **details) -> dict:
    return {"code": code, "message_vi": message_vi, "proposed": code in PROPOSED_CODES, **details}


def _check_mode(mode: str) -> None:
    if mode not in GRADING_MODES:
        raise MusicEngineError("grading_mode không hợp lệ", mode=mode)


# --- Hợp âm ------------------------------------------------------------------------

def _note_counter(notes: list[Note], grading_mode: str) -> Counter:
    """Multiset representation used only for objective correctness.

    A build-chord exercise is a full chord-tone inventory, not a voicing exercise: order does
    not matter, but missing, extra, or duplicated tones do. Keeping this check separate from
    diagnostics prevents a diagnostic miss from turning an objectively wrong answer into a pass.
    """
    if grading_mode == "strict_spelling":
        return Counter((n.letter, n.accidental) for n in notes)
    return Counter(n.pitch_class for n in notes)


def _diagnose_chord(expected: ChordSymbol, answer: list[Note]) -> list[dict]:
    """Diagnose a chord answer after objective correctness has already failed.

    Matching is deterministic and order-independent: exact spellings are consumed first, then a
    same-letter tone is used for quality diagnosis. Only the selected answer tone is consumed; any
    remaining tone is reported as extra.
    """
    exp_tones = expected.notes
    errors: list[dict] = []

    # 1. Correct keys but wrong note names. Counter is essential: an extra note must not vanish.
    if len(answer) == len(exp_tones) and Counter(n.pitch_class for n in answer) == Counter(
            t.pitch_class for t in exp_tones):
        wrong = [str(n) for n in answer if not any(n.same_spelling(t) for t in exp_tones)]
        if wrong:
            return [_err("ENHARMONIC_SPELLING",
                         f"Bạn bấm đúng phím nhưng viết sai tên nốt ({', '.join(wrong)}). Trong "
                         f"{expected.symbol}, các nốt được gọi tên theo quãng tính từ nốt gốc: "
                         f"{' '.join(str(t) for t in exp_tones)}.", wrong_notes=wrong)]

    # 2. Correct chord quality but wrong root. Only meaningful for the same cardinality.
    if len(answer) == len(exp_tones):
        try:
            for m in identify_chord(answer):
                if m.chord.type.id == expected.type.id and m.spelled_exactly \
                        and not m.chord.root.same_spelling(expected.root):
                    return [_err("WRONG_ROOT",
                                 f"Bạn dựng đúng loại hợp âm {expected.type.display or 'trưởng'} nhưng trên "
                                 f"nốt {m.chord.root.name}, không phải {expected.root.name}.",
                                 answered_root=m.chord.root.name)]
        except MusicEngineError:
            pass

    # 3-4. Match one answer tone to each expected role. Exact spelling wins over same-letter.
    unused = set(range(len(answer)))
    for tone in exp_tones:
        role = chord_member(expected, tone)
        exact = [i for i in unused if answer[i].same_spelling(tone)]
        if exact:
            unused.remove(exact[0])
            continue

        same_letter = [i for i in unused if answer[i].letter == tone.letter]
        if not same_letter:
            errors.append(_err("MISSING_TONE", f"Thiếu {_ROLE_VI[role]} ({tone.name}).",
                               role=role, missing=tone.name))
            continue

        i = same_letter[0]
        unused.remove(i)
        if role == "root":
            errors.append(_err("WRONG_ROOT", f"Nốt gốc phải là {tone.name}, không phải {answer[i].name}.",
                               answered=answer[i].name))
            continue

        code = {"third": "THIRD_QUALITY", "fifth": "FIFTH_QUALITY",
                "seventh": "SEVENTH_QUALITY"}.get(role, "EXTRA_TONE")
        exp_iv = interval_between(expected.root, tone)
        try:
            got_iv = interval_between(expected.root, answer[i].with_octave(None))
            got_txt = _iv_vi(got_iv)
        except MusicEngineError:
            got_txt = f"nốt {answer[i].name}"
        errors.append(_err(code, f"Bạn đang dùng {got_txt} thay vì {_iv_vi(exp_iv)} "
                                 f"({answer[i].name} → {tone.name}).",
                           role=role, answered=answer[i].name, expected_note=tone.name))

    for i in sorted(unused):
        n = answer[i]
        errors.append(_err("EXTRA_TONE", f"Nốt {n.name} không thuộc hợp âm {expected.symbol} "
                                         "hoặc đã được nhập thừa.", extra=n.name))
    return errors


def grade_build_chord(symbol: str, answer: list[str], grading_mode: str = "strict_spelling",
                      root_position_only: bool = False) -> dict:
    """Build-chord exercise: full chord-tone inventory.

    Order is ignored. Missing, extra and duplicated tones are not accepted. Voicing exercises will
    use a separate rubric in a later module because valid jazz voicings may intentionally omit or
    double tones.
    """
    _check_mode(grading_mode)
    expected = parse_chord_symbol(symbol)
    notes = [parse_note(a) for a in answer]
    plain = [n.with_octave(None) for n in notes]
    exp_tones = expected.notes
    exp_names = [str(t) for t in exp_tones]

    ok = _note_counter(plain, grading_mode) == _note_counter(exp_tones, grading_mode)

    codes: list[dict] = []
    if ok and root_position_only and plain and plain[_lowest_index(notes)].pitch_class != expected.root.pitch_class:
        codes.append(_err("NOT_ROOT_POSITION", "Bài này yêu cầu nốt gốc ở bass (thể gốc).",
                          expected_bass=expected.root.name))
    if not ok:
        codes = _diagnose_chord(expected, plain)
    return _result(ok and not codes, exp_names, codes, grading_mode=grading_mode)


def _lowest_index(notes: list[Note]) -> int:
    """Nốt bass: nốt thấp nhất nếu có quãng tám, nếu không thì nốt đầu tiên."""
    if all(n.octave is not None for n in notes):
        return min(range(len(notes)), key=lambda i: notes[i].midi)
    return 0


def grade_identify_chord(notes: list[str], answer: str) -> dict:
    """Bài identify_chord: các nốt → "Am7". Chấp nhận mọi bí danh và mọi tên hợp lệ của tập nốt."""
    candidates = identify_chord(notes)
    try:
        ans = parse_chord_symbol(answer)
    except MusicEngineError as e:
        return _result(False, [m.chord.symbol for m in candidates],
                       [_err(e.code, f"Không đọc được ký hiệu hợp âm '{answer}'.")])
    expected_symbols = [m.chord.symbol for m in candidates if m.spelled_exactly]
    for m in candidates:
        if m.spelled_exactly and m.chord.root.same_spelling(ans.root) and m.chord.type.id == ans.type.id:
            if ans.bass is None or (m.chord.bass or m.chord.root).same_spelling(ans.bass):
                return _result(True, expected_symbols, [])
    best = candidates[0].chord
    codes = _diagnose_chord(best, ans.notes)
    if not codes:
        codes = [_err("WRONG_ROOT", f"Tập nốt này là {best.symbol}.")]
    return _result(False, expected_symbols, codes)


# --- Âm giai -----------------------------------------------------------------------

def grade_build_scale(tonic: str, scale_type: str, answer: list[str],
                      grading_mode: str = "strict_spelling") -> dict:
    """Bài build_scale: 7 tên nốt theo đúng thứ tự bậc.

    A note that belongs to the scale but appears at the wrong degree is diagnosed separately from
    a genuinely out-of-key note so adaptive learning does not infer the wrong weakness.
    """
    _check_mode(grading_mode)
    expected = build_scale(tonic, scale_type)
    exp_names = [str(n) for n in expected]
    got = [parse_note(a).with_octave(None) for a in answer]
    codes: list[dict] = []
    if len(got) < 7:
        codes.append(_err("MISSING_TONE", f"Âm giai cần 7 nốt, bạn mới viết {len(got)}."))
    if len(got) > 7:
        codes.append(_err("EXTRA_TONE", "Âm giai chỉ có 7 nốt (không cần lặp lại chủ âm)."))

    wrong_degrees = []
    expected_pitch_classes = {n.pitch_class for n in expected}
    for deg, (e, g) in enumerate(zip(expected, got), start=1):
        same = e.same_spelling(g) if grading_mode == "strict_spelling" else e.enharmonic_to(g)
        if same:
            continue

        wrong_degrees.append(deg)
        if grading_mode == "strict_spelling" and e.enharmonic_to(g):
            codes.append(_err("ENHARMONIC_SPELLING",
                              f"Bậc {deg}: {g.name} nghe đúng nhưng phải viết là {e.name} "
                              f"(mỗi chữ cái chỉ xuất hiện một lần trong âm giai).",
                              degree=deg, answered=g.name, expected_note=e.name))
            continue

        matching_degree = next(
            (i for i, tone in enumerate(expected, start=1)
             if (tone.same_spelling(g) if grading_mode == "strict_spelling" else tone.enharmonic_to(g))),
            None,
        )
        if matching_degree is not None:
            codes.append(_err(
                "WRONG_SCALE_DEGREE_ORDER",
                f"{g.name} thuộc âm giai nhưng đang ở sai vị trí: bạn đặt ở bậc {deg}; "
                f"nốt đúng tại đây là {e.name} (còn {g.name} thuộc bậc {matching_degree}).",
                degree=deg, answered=g.name, expected_note=e.name, belongs_to_degree=matching_degree,
            ))
        elif g.pitch_class in expected_pitch_classes:
            codes.append(_err(
                "WRONG_SCALE_DEGREE_ORDER",
                f"Bậc {deg}: cao độ {g.name} thuộc âm giai ở một bậc khác; nốt đúng tại đây là {e.name}.",
                degree=deg, answered=g.name, expected_note=e.name,
            ))
        else:
            codes.append(_err("NOT_IN_KEY", f"Bậc {deg}: {g.name} không thuộc âm giai; phải là {e.name}.",
                              degree=deg, answered=g.name, expected_note=e.name))
    return _result(not codes, exp_names, codes, wrong_degrees=wrong_degrees, grading_mode=grading_mode)


# --- Quãng -------------------------------------------------------------------------

def grade_build_interval(root: str, interval: str, answer: str) -> dict:
    """Bài build_interval: {root: "C4", interval: "M3"} → "E4". Đúng chính xác cao độ và tên."""
    r = parse_note(root)
    iv = parse_interval(interval)
    expected = transpose(r, iv)
    got = parse_note(answer)
    if got.octave is None and expected.octave is not None:
        got = got.with_octave(expected.octave)
    if got == expected:
        return _result(True, str(expected), [])
    codes = []
    if got.midi == expected.midi:
        codes.append(_err("ENHARMONIC_SPELLING",
                          f"Đúng phím nhưng sai tên: {_iv_vi(iv)} trên {r.name} phải viết là {expected.name}.",
                          answered=str(got)))
    else:
        steps = got.diatonic_index - r.diatonic_index
        if steps + 1 != iv.number and (steps % 7) != (iv.number - 1) % 7:
            codes.append(_err("WRONG_INTERVAL_SIZE",
                              f"Sai số của quãng: {got.name} cách {r.name} một quãng {steps % 7 + 1}, "
                              f"cần quãng {iv.number}.", answered=str(got)))
        elif got.same_spelling(expected):
            codes.append(_err("WRONG_OCTAVE", f"Đúng tên nốt {expected.name} nhưng sai quãng tám.",
                              answered=str(got)))
        else:
            codes.append(_err("WRONG_INTERVAL_QUALITY",
                              f"Đúng số quãng nhưng sai tính chất: cần {_iv_vi(iv)} → {expected.name}.",
                              answered=str(got)))
    return _result(False, str(expected), codes)


def grade_identify_interval(lower: str, upper: str, answer: str) -> dict:
    """Bài identify_interval: hai nốt → "m7". A4 ≠ d5 (SRS 4.9). Nhận cả +4/°5 (QĐ-2.1)."""
    expected = interval_between(lower, upper)
    try:
        got = parse_interval(answer)
    except MusicEngineError as e:
        return _result(False, expected.name, [_err(e.code, f"Không đọc được tên quãng '{answer}'.")])
    if got == expected:
        return _result(True, expected.name, [])
    if got.number != expected.number:
        msg = f"Sai số của quãng: đếm chữ cái từ {parse_note(lower).name} tới {parse_note(upper).name} được quãng {expected.number}."
        if got.semitones == expected.semitones:
            msg += f" {got.name} và {expected.name} cùng {expected.semitones} nửa cung nhưng là hai quãng khác nhau."
        return _result(False, expected.name, [_err("WRONG_INTERVAL_SIZE", msg, answered=got.name)])
    return _result(False, expected.name, [_err(
        "WRONG_INTERVAL_QUALITY",
        f"Đúng số quãng nhưng sai tính chất: đây là {_iv_vi(expected)} ({expected.semitones} nửa cung).",
        answered=got.name)])


# --- Số La Mã ----------------------------------------------------------------------

def _normalize_roman(text: str) -> str:
    return (text.strip().replace("o", "°").replace("∅", "ø").replace("Ø", "ø")
            .replace("dim", "°"))


def grade_roman_numeral(key: str, chord: str, answer: str) -> dict:
    """Bài roman_numeral: {key: "C", chord: "Dm7"} → "ii7". Hoa/thường và ký hiệu phải khớp."""
    expected = roman_numeral(key, chord)
    got = _normalize_roman(answer)
    if got == expected.numeral:
        return _result(True, expected.numeral, [], convention_id=ROMAN_CONVENTION,
                       convention_verified=expected.convention_verified)
    letters = "".join(ch for ch in got if ch.upper() in "IV")
    exp_letters = "".join(ch for ch in expected.numeral if ch.upper() in "IV")
    if letters.upper() != exp_letters.upper():
        code = _err("ROMAN_DEGREE", f"{expected.chord.symbol} nằm trên bậc {expected.degree} của giọng "
                                    f"{expected.key} trưởng.", answered=answer)
    else:
        code = _err("ROMAN_QUALITY_MARK",
                    f"Đúng bậc nhưng sai ký hiệu chất lượng: chữ hoa = trưởng, chữ thường = thứ, ° = giảm. "
                    f"Đáp án: {expected.numeral}.", answered=answer)
    return _result(False, expected.numeral, [code], convention_id=ROMAN_CONVENTION,
                   convention_verified=expected.convention_verified)
