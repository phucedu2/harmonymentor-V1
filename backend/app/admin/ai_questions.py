"""Câu luyện tập do AI soạn từ tài liệu (ADR-028): chuẩn hóa, Music Engine kiểm đáp án, đổi thành đặc tả câu hỏi.

Vì sao tách khỏi ai_service: phần này quyết định câu nào được tin. Luật (Phúc chốt 18/11/2026, câu 4A):
- Câu tính được (quãng, số La Mã, nốt hợp âm, nốt âm giai, tên hợp âm) thì ĐÁP ÁN DO ENGINE CHỌN. AI chỉ viết đề và phương án;
  nếu AI chọn sai, Engine sửa và ghi lại; nếu không phương án nào đúng (hoặc nhiều hơn một), câu bị loại.
- Câu khái niệm Engine không kiểm được thì `needs_review=True`; xuất bản bị chặn tới khi Quản trị viên tick đã duyệt từng câu.
- Câu mở (tự luận dài) luôn cần duyệt, chấm bằng rubric, KHÔNG tính mastery (câu 3C).

Đợt 3 (ADR-033, Phúc chốt 22/11/2026):
- N1: Engine chỉ tin `check` khi ký hiệu trong ĐỀ khớp `check` (đề "C lên E" mà check D–F thì loại câu). Đề không nêu ký
  hiệu nào thì giữ câu nhưng bắt duyệt (4A).
- Engine phải SỬA đáp án AI chọn thì câu vẫn giữ nhưng bắt duyệt: AI đã hiểu sai, người phải đọc lại đề và lời giải.
- N2: câu Đúng/Sai chỉ do Engine quyết khi MỌI phần của câu được kiểm; còn từ phủ định/khái niệm chưa kiểm thì bắt duyệt.
- H3 (5A): câu Engine kiểm mà kỹ năng AI chọn không khớp loại kiểm (quãng ↔ kỹ năng quãng...) thì bắt duyệt.
- N3: câu gắn với khối lý thuyết qua `block_ref` (số thứ tự khối, từ 1); thiếu hoặc sai thì bắt duyệt.

Đợt 27/11/2026 (Phúc 3A–6A):
- Câu Engine kiểm được mà thiếu lời giải thì Engine tự viết (ai_explain); câu trắc nghiệm có thêm lời Engine chỉ ra vì
  sao từng phương án sai. Chỉ câu khái niệm mới còn phải nhờ Gemini/người viết lời giải.
- Quản trị viên đã sửa câu (cờ `edited` do giao diện gửi khi đổi đề/đáp án/lời giải) thì coi như đã duyệt: sửa tức là đã đọc.
- Đề hỏi quãng kép mà phần kiểm chỉ có hai tên nốt (không quãng tám) thì Engine tính theo quãng kép (C–D → C4–D5 = M9),
  không để Engine trả quãng đơn M2 cho câu hỏi quãng kép.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from ..ai.tutor import notes as _nt
from . import ai_explain
from ..ai.tutor.guardrail import scan_reply
from ..music_engine import tools as engine
from ..music_engine.errors import MusicEngineError
from ..music_engine.grading import (grade_build_chord, grade_build_scale, grade_identify_chord, grade_identify_interval,
                                    grade_roman_numeral)
from ..music_engine.interval import interval_between
from ..music_engine.pitch import parse_note
from ..music_engine.roman import roman_numeral

KINDS = ("mcq", "true_false", "multi_select", "short", "build_chord", "build_scale", "open")
LEVELS = ("nho", "hieu", "van_dung")          # Bloom rút gọn: nhớ / hiểu / vận dụng (câu 8A)
LEVEL_TO_PRACTICE = {"nho": "de", "hieu": "vua", "van_dung": "kho"}
SCALE_TYPES = {"major", "natural_minor"}
CHECK_TYPES = ("interval", "roman", "chord_tones", "scale", "chord_name")
SHORT_CHECKS = ("interval", "roman", "chord_name")
TRUE, FALSE = "Đúng", "Sai"


def _s(value: Any, limit: int = 2000) -> str:
    return value.strip()[:limit] if isinstance(value, str) else ""


def _notes(text: str) -> list[str]:
    return [p for p in text.replace(",", " ").replace("–", " ").replace("-", " ").split() if p]


# --- Engine kiểm -----------------------------------------------------------------------------------

def clean_check(raw: Any) -> dict[str, str] | None:
    """Giữ đúng các trường của loại kiểm; thiếu trường hoặc Engine không hiểu → None."""
    if not isinstance(raw, dict) or raw.get("type") not in CHECK_TYPES:
        return None
    kind = raw["type"]
    fields = {"interval": ("lower", "upper"), "roman": ("key", "chord"), "chord_tones": ("symbol",),
              "scale": ("tonic", "scale_type"), "chord_name": ("notes",)}[kind]
    out = {"type": kind, **{f: _s(raw.get(f), 40) for f in fields}}
    if any(not out[f] for f in fields):
        return None
    if kind == "scale" and out["scale_type"] not in SCALE_TYPES:
        return None
    return out if engine_answer_for_check(out) is not None else None


def engine_answer_for_check(check: dict[str, str]) -> str | None:
    """Đáp án chuẩn do Engine tính, dạng chữ để hiển thị cho Quản trị viên và lưu làm đáp án mẫu."""
    try:
        t = check["type"]
        if t == "interval":
            return interval_between(check["lower"], check["upper"]).name
        if t == "roman":
            return roman_numeral(check["key"], check["chord"]).numeral.replace("M7", "maj7")
        if t == "chord_tones":
            out = engine.get_chord_tones(symbol=check["symbol"])
            return " ".join(out["notes"]) if out.get("ok") else None
        if t == "scale":
            out = engine.get_scale(tonic=check["tonic"], scale_type=check["scale_type"])
            return " ".join(out["notes"]) if out.get("ok") else None
        if t == "chord_name":
            expected = grade_identify_chord(_notes(check["notes"]), "C")["expected"]
            return expected[0] if expected else None
    except (MusicEngineError, ValueError, KeyError, IndexError):
        return None
    return None


def engine_accepts(check: dict[str, str], answer: str) -> bool:
    """Engine chấm một câu trả lời theo đúng luật chấm của người học (chính tả nốt chặt)."""
    try:
        t = check["type"]
        if t == "interval":
            return bool(grade_identify_interval(check["lower"], check["upper"], answer)["correct"])
        if t == "roman":
            return bool(grade_roman_numeral(check["key"], check["chord"], answer)["correct"])
        if t == "chord_tones":
            return bool(grade_build_chord(check["symbol"], _notes(answer))["correct"])
        if t == "scale":
            return bool(grade_build_scale(check["tonic"], check["scale_type"], _notes(answer))["correct"])
        if t == "chord_name":
            return bool(grade_identify_chord(_notes(check["notes"]), answer)["correct"])
    except (MusicEngineError, ValueError, KeyError, IndexError):
        return False
    return False


def _member_notes(check: dict[str, str]) -> set[str] | None:
    """Tập tên nốt (đúng chính tả) cho câu chọn nhiều 'chọn các nốt thuộc ...'."""
    if check["type"] == "chord_tones":
        out = engine.get_chord_tones(symbol=check["symbol"])
    elif check["type"] == "scale":
        out = engine.get_scale(tonic=check["tonic"], scale_type=check["scale_type"])
    else:
        return None
    return set(out["notes"]) if out.get("ok") else None


# Mẫu khẳng định mà scan_reply kiểm được (cùng danh sách như trong guardrail.scan_reply).
_CLAIM_PATTERNS = (_nt.CHORD_WITH_NOTES, _nt.SHELL_LIST_AFTER, _nt.SCALE_WITH_NOTES, _nt.INTERVAL_WITH_NAME,
                   _nt.INTERVAL_PAIR_WITH_NAME, _nt.INTERVAL_SIZE_CLAIM, _nt.NOTES_SEMITONE_CLAIM,
                   _nt.ROMAN_IN_KEY_IS_CHORD, _nt.CHORD_IS_ROMAN_IN_KEY)
# Từ làm đổi nghĩa cả câu (phủ định, lượng từ, "hoặc", "nếu"): có thì Engine không kết luận được câu đúng hay sai.
_FLIP = re.compile(r"(?<!\w)(không|chẳng|chưa|chỉ|luôn|mọi|tất cả|đều|hoặc|nếu|trừ|ngoại trừ|not|never|only|always|or)(?!\w)",
                   re.IGNORECASE)
# Khái niệm nhạc lý Engine không kiểm khi đứng ngoài một khẳng định đã bắt được ("... và là hợp âm thứ").
_CONCEPT = re.compile(r"(?<!\w)(trưởng|thứ|giảm|tăng|bậc|chức năng|át|chủ|hạ át|ổn định|căng|nghịch|thuận|giải quyết|đảo|"
                      r"hóa biểu|nốt nhạy|sáng|tối|buồn|vui|major|minor|dominant|tonic|subdominant|diminished|augmented|"
                      r"cadence|kết)(?!\w)", re.IGNORECASE)


def _residual(text: str) -> str:
    """Phần câu còn lại sau khi bỏ mọi đoạn Engine đã kiểm."""
    spans = sorted(m.span() for pat in _CLAIM_PATTERNS for m in pat.finditer(text))
    out, at = [], 0
    for a, b in spans:
        if a > at:
            out.append(text[at:a])
        at = max(at, b)
    out.append(text[at:])
    return " ".join(out)


def statement_truth(statement: str) -> bool | None:
    """Câu Đúng/Sai: True/False khi Engine kiểm được MỌI khẳng định trong câu; None (cần người duyệt) khi còn phần chưa kiểm.

    N2 (ADR-033): "Hợp âm C gồm C E G và là hợp âm thứ" từng bị chấm là Đúng vì Engine chỉ thấy vế đầu. Giờ:
    - còn từ phủ định/lượng từ/"hoặc" ở ngoài khẳng định → None (nghĩa của cả câu có thể ngược lại);
    - có vế sai → False (một vế sai thì cả câu "A và B" sai), kể cả khi vế khác là khái niệm chưa kiểm;
    - mọi vế đúng nhưng còn khái niệm chưa kiểm (trưởng/thứ/bậc/chức năng...) → None."""
    claims = scan_reply(statement)
    if not claims:
        return None
    rest = _residual(_nt.solfege_to_letters(statement))
    if _FLIP.search(rest):
        return None
    if any(c.status == "contradicted" for c in claims):
        return False
    if all(c.status == "verified" for c in claims) and not _CONCEPT.search(rest):
        return True
    return None


# --- N1: ký hiệu trong đề phải khớp phần kiểm -------------------------------------------------------

_SOLF_ONE = re.compile(r"(?<!\w)(Đô|Rê|Mi|Fa|Sol|La|Si)(?:\s+(thăng|giáng)(\s+kép)?)?(?!\w)")
_SOLF_MAP = {"Đô": "C", "Rê": "D", "Mi": "E", "Fa": "F", "Sol": "G", "La": "A", "Si": "B"}
_TOKEN = re.compile(r"(?<![\w#♯♭])(?P<root>[A-G](?:##|#|bb|b|♯|♭)?)"
                    r"(?P<qual>maj7|maj9|M7|m7b5|ø7|ø|dim7|°7|dim|°|aug|\+|mM7|m7|min7|min|m9|m|add9|sus2|sus4|13|11|9|7|6)?"
                    r"(?![\w#♯♭])")


def prompt_symbols(prompt: str) -> list[str]:
    """Tên nốt/ký hiệu hợp âm xuất hiện trong đề, theo thứ tự (đổi Đô/Mi/Sol sang chữ cái, ♯/♭ sang #/b)."""
    def solf(m: re.Match) -> str:
        acc = {"thăng": "#", "giáng": "b"}.get(m.group(2) or "", "")
        return _SOLF_MAP[m.group(1)] + (acc * 2 if m.group(3) else acc)

    text = _SOLF_ONE.sub(solf, _nt.solfege_to_letters(prompt))
    return [_nt.norm_accidentals(m["root"]) + (m["qual"] or "") for m in _TOKEN.finditer(text)]


def _root(symbol: str) -> str:
    m = _TOKEN.match(symbol)
    return _nt.norm_accidentals(m["root"]) if m else symbol


def _note(text: str) -> str:
    return _nt.norm_accidentals(re.sub(r"[0-9]", "", text.strip()))


def _tones(symbol: str) -> tuple[str, ...] | None:
    try:
        out = engine.get_chord_tones(symbol=symbol)
    except (MusicEngineError, ValueError, KeyError):
        return None
    return tuple(out["notes"]) if out.get("ok") else None


def _has_chord(symbols: list[str], symbol: str) -> bool:
    want = _tones(symbol)
    return want is not None and any(_tones(s) == want for s in symbols)


def prompt_match(check: dict[str, str], prompt: str) -> str:
    """"ok" khi ký hiệu của `check` có trong đề; "absent" khi đề không nêu ký hiệu nào; "mismatch" khi đề nêu ký hiệu khác.

    Vì sao: Engine tính đáp án theo `check` do AI tự ghi. AI ghi lệch đề (đề "C lên E", check D–F) thì Engine "sửa" đáp
    án đúng thành sai mà câu lại được miễn duyệt (N1, ADR-033)."""
    symbols = prompt_symbols(prompt)
    if not symbols:
        return "absent"
    roots = {_root(s) for s in symbols}
    t = check["type"]
    if t == "interval":
        ok = _note(check["lower"]) in roots and _note(check["upper"]) in roots
    elif t == "roman":
        ok = _note(check["key"]) in roots and _has_chord(symbols, check["chord"])
    elif t == "chord_tones":
        ok = _has_chord(symbols, check["symbol"])
    elif t == "scale":
        ok = _note(check["tonic"]) in roots
    elif t == "chord_name":
        ok = set(_notes(_nt.norm_accidentals(check["notes"]))) <= roots
    else:
        ok = False
    return "ok" if ok else "mismatch"


# H3 (5A): loại kiểm của Engine phải khớp nhóm kỹ năng thì mới tin kỹ năng AI chọn.
SKILL_FAMILY = {"interval": ("interval.",), "roman": ("roman.", "function."), "chord_tones": ("chord.",),
                "chord_name": ("chord.",), "scale": ("scale.", "chord_scale.", "key."),
                "build_chord": ("chord.",), "build_scale": ("scale.", "chord_scale.", "key.")}


def skill_matches(q: dict[str, Any]) -> bool:
    family = q["kind"] if q["kind"] in ("build_chord", "build_scale") else (q.get("check") or {}).get("type")
    if family is None:
        return True   # câu không có phần kiểm: kỹ năng do người duyệt xem
    return q["skill_id"].startswith(SKILL_FAMILY.get(family, ()))


EXPLANATION_NOTE = "Câu chưa có lời giải: viết lời giải (vì sao đáp án đúng) rồi mới duyệt."

# Đề hỏi quãng kép (lớn hơn quãng tám): "quãng kép", "quãng 9".."quãng 15", "quãng chín/mười...", "compound".
_COMPOUND = re.compile(r"quãng\s+kép|compound|quãng\s+(?:9|1[0-5])(?!\d)|quãng\s+(?:chín|mười)", re.IGNORECASE)


def compound_check(check: dict[str, str], prompt: str) -> dict[str, str] | None:
    """Đề hỏi quãng kép mà phần kiểm là hai tên nốt không có quãng tám → phần kiểm mới có quãng tám, quãng = quãng đơn + 7.

    Vì sao: interval_between("C", "D") luôn ra quãng đơn M2 (MUS-INT-010 chỉ tính quãng kép khi có số quãng tám), nên
    câu "quãng 2 trưởng mở rộng thành quãng kép nào?" từng có đáp án Engine M2 thay vì M9. None = không cần đổi."""
    if check["type"] != "interval" or not _COMPOUND.search(prompt):
        return None
    try:
        lo, up = parse_note(check["lower"]), parse_note(check["upper"])
    except (MusicEngineError, ValueError):
        return None
    if lo.octave is not None or up.octave is not None:
        return None
    for octave in (4, 5):   # nốt trên thấp hơn về chữ cái (A lên C) thì quãng đơn nằm sang quãng tám kế tiếp
        try:
            simple = interval_between(f"{check['lower']}4", f"{check['upper']}{octave}")
        except (MusicEngineError, ValueError):
            continue
        if 2 <= simple.number <= 7:
            return {**check, "lower": f"{check['lower']}4", "upper": f"{check['upper']}{octave + 1}"}
    return None


# --- chuẩn hóa từng câu ----------------------------------------------------------------------------

def normalize_question(item: Any, skills: set[str], clamp: Callable[[Any], int], *,
                       trust_review: bool = False, blocks: int | None = None) -> tuple[dict[str, Any] | None, str]:
    """Trả (câu đã chuẩn hóa, "") hoặc (None, lý do loại). `trust_review` chỉ bật khi Quản trị viên sửa bản nháp:
    AI không được tự đánh dấu câu là đã duyệt. `blocks` = số khối lý thuyết của bản nháp (None: không kiểm block_ref)."""
    if not isinstance(item, dict):
        return None, "không phải đối tượng"
    kind, prompt = item.get("kind"), _s(item.get("prompt"), 600)
    skill = _s(item.get("skill_id"), 64)
    level = item.get("level") if item.get("level") in LEVELS else "hieu"
    base: dict[str, Any] = {"kind": kind, "prompt": prompt, "skill_id": skill, "level": level,
                            "explanation": _s(item.get("explanation"), 800), "page": clamp(item.get("page"))}
    if isinstance(item.get("page_claimed"), int):
        base["page_claimed"] = item["page_claimed"]   # trang AI ghi nằm ngoài phần (N4), giữ để người duyệt thấy
    elif isinstance(item.get("page"), int) and item["page"] != base["page"]:
        base["page_claimed"] = item["page"]
    short = prompt[:40]
    if not prompt:
        return None, "thiếu đề"
    if kind not in KINDS:
        return None, f"“{short}”: loại câu “{kind}” không hỗ trợ"
    if skill not in skills:
        return None, f"“{short}”: kỹ năng “{skill}” không có trong hệ thống"
    check = clean_check(item.get("check"))
    review_notes: list[str] = []
    compound = compound_check(check, prompt) if check is not None else None
    if compound is not None:
        review_notes.append(f"Đề hỏi quãng kép: Engine tính theo {compound['lower']}–{compound['upper']} = "
                            f"{engine_answer_for_check(compound)}. Kiểm lại đề có đúng ý này không.")
        check = compound
    if check is not None and kind != "true_false":
        match = prompt_match(check, prompt)
        if match == "mismatch":
            return None, f"“{short}”: ký hiệu trong đề không khớp phần kiểm của AI ({_check_text(check)})"
        if match == "absent":
            review_notes.append(f"Đề không nêu ký hiệu nào nên máy không đối chiếu được với phần kiểm ({_check_text(check)}).")
    q, why = _BUILDERS[kind](item, base, check, short)
    if q is None:
        return None, why
    q.setdefault("engine_verified", False)
    if kind in ("build_chord", "build_scale"):
        match = prompt_match({"type": "chord_tones", "symbol": q["symbol"]} if kind == "build_chord"
                             else {"type": "scale", "tonic": q["tonic"], "scale_type": q["scale_type"]}, prompt)
        if match == "mismatch":
            return None, f"“{short}”: ký hiệu trong đề không khớp ký hiệu AI đưa cho Engine"
        if match == "absent":
            review_notes.append("Đề không nêu ký hiệu nào nên máy không đối chiếu được với ký hiệu Engine dựng.")
    if q.get("engine_note"):
        review_notes.append("Engine phải sửa đáp án AI chọn: đọc lại đề và lời giải.")
    if q["engine_verified"] and not skill_matches(q):
        review_notes.append(f"Kỹ năng “{skill}” không khớp loại câu Engine kiểm: chọn lại kỹ năng hoặc xác nhận.")
    if blocks is not None:
        ref = item.get("block_ref")
        if isinstance(ref, int) and not isinstance(ref, bool) and 1 <= ref <= blocks:
            q["block_ref"] = ref
        else:
            q["block_ref"] = None
            review_notes.append("Câu chưa gắn với khối lý thuyết nào của bài.")
    if "page_claimed" in q:
        review_notes.append(f"AI ghi trang {q['page_claimed']}, nằm ngoài các trang của phần này.")
    fill_explanations(q)
    if kind != "open" and not q.get("explanation"):
        # 8A (zip thầy, 23/11): học sinh làm sai mà không có lời giải thì câu chỉ chấm, không dạy. Câu mở có rubric riêng.
        review_notes.append(EXPLANATION_NOTE)
    q["review_notes"] = review_notes
    q["needs_review"] = not q["engine_verified"] or bool(review_notes)
    # 3A (27/11): Quản trị viên sửa câu rồi lưu = đã đọc câu, không bắt tick thêm. Vẫn phải có lời giải (trừ câu mở).
    edited = trust_review and item.get("edited") is True
    if edited:
        q["edited"] = True
    auto_ok = edited and (kind == "open" or bool(q.get("explanation")))
    q["reviewed"] = bool(trust_review and q["needs_review"] and (item.get("reviewed") is True or auto_ok))
    return q, ""


def fill_explanations(q: dict[str, Any]) -> None:
    """Engine viết lời giải và lời giải thích phương án sai còn thiếu (4A, 5A). Lời AI đã có thì giữ (guardrail soát khi
    xuất bản), Engine chỉ điền chỗ trống, để không thay một lời giải đúng bằng câu chữ khô hơn."""
    text = ai_explain.explanation_for(q)
    if not q.get("explanation") and text:
        q["explanation"] = text[:800]
    if text and q.get("explanation") == text[:800]:
        q["explanation_source"] = "engine"   # để giao diện ghi "Lời giải do Music Engine viết"; sửa chữ thì mất nhãn
    feedback = ai_explain.wrong_option_feedback(q)
    if feedback:
        q["option_feedback"] = {**feedback, **(q.get("option_feedback") or {})}


def _check_text(check: dict[str, str]) -> str:
    return ", ".join(f"{k}={v}" for k, v in check.items() if k != "type") or check["type"]


def _option_feedback(item: dict[str, Any], options: list[str]) -> dict[str, str]:
    raw = item.get("option_feedback")
    if isinstance(raw, list):   # schema Gemini không có map tự do: AI trả danh sách {option, why}
        raw = {(_s(r.get("option"), 200)): r.get("why") for r in raw if isinstance(r, dict)}
    if not isinstance(raw, dict):
        return {}
    return {o: _s(raw.get(o), 400) for o in options if _s(raw.get(o), 400)}


def _mcq(item, base, check, short):
    options = [_s(o, 200) for o in (item.get("options") or []) if _s(o, 200)]
    if not 3 <= len(options) <= 5 or len(set(options)) != len(options):
        return None, f"“{short}”: cần 3–5 phương án khác nhau"
    answer = _s(item.get("answer"), 200)
    q = {**base, "options": options, "option_feedback": _option_feedback(item, options)}
    if check is not None:
        accepted = [o for o in options if engine_accepts(check, o)]
        if len(accepted) != 1:
            return None, f"“{short}”: Engine thấy {len(accepted)} phương án đúng (cần đúng 1)"
        q.update(answer=accepted[0], check=check, engine_verified=True)
        if answer != accepted[0]:
            q["engine_note"] = f"AI chọn “{answer or '(trống)'}”, Engine sửa thành “{accepted[0]}”."
        return q, ""
    if answer not in options:
        return None, f"“{short}”: đáp án không nằm trong phương án"
    return {**q, "answer": answer}, ""


def _true_false(item, base, check, short):
    raw = item.get("answer")
    ai = True if raw in (True, "true", TRUE, "Đúng", "dung") else False if raw in (False, "false", FALSE, "sai") else None
    truth = statement_truth(base["prompt"])
    if truth is None and ai is None:
        return None, f"“{short}”: thiếu đáp án Đúng/Sai"
    q = {**base, "options": [TRUE, FALSE], "option_feedback": {}}
    if truth is not None:
        q.update(answer=TRUE if truth else FALSE, engine_verified=True)
        if ai is not None and ai != truth:
            q["engine_note"] = f"AI cho là “{TRUE if ai else FALSE}”, Engine kiểm thấy câu này {TRUE.lower() if truth else FALSE.lower()}."
        return q, ""
    return {**q, "answer": TRUE if ai else FALSE}, ""


def _multi(item, base, check, short):
    options = [_s(o, 200) for o in (item.get("options") or []) if _s(o, 200)]
    if not 4 <= len(options) <= 6 or len(set(options)) != len(options):
        return None, f"“{short}”: câu chọn nhiều cần 4–6 phương án khác nhau"
    q = {**base, "options": options, "option_feedback": _option_feedback(item, options)}
    members = _member_notes(check) if check is not None else None
    ai = [_s(a, 200) for a in (item.get("answers") or []) if _s(a, 200) in options]
    if members is not None:
        answers = [o for o in options if o in members]
        if not 1 <= len(answers) < len(options):
            return None, f"“{short}”: Engine thấy {len(answers)}/{len(options)} phương án đúng"
        q.update(answers=answers, check=check, engine_verified=True)
        if sorted(ai) != sorted(answers):
            q["engine_note"] = f"AI chọn {', '.join(ai) or '(trống)'}, Engine sửa thành {', '.join(answers)}."
        return q, ""
    if not 1 <= len(set(ai)) < len(options):
        return None, f"“{short}”: đáp án chọn nhiều không hợp lệ"
    return {**q, "answers": sorted(set(ai), key=options.index)}, ""


def _short(item, base, check, short):
    if check is None or check["type"] not in SHORT_CHECKS:
        return None, f"“{short}”: câu tự luận ngắn phải có phần kiểm (quãng, số La Mã hoặc tên hợp âm) để Engine chấm"
    return {**base, "check": check, "engine_verified": True}, ""


def _build_chord(item, base, check, short):
    symbol = _s(item.get("symbol"), 16)
    out = engine.get_chord_tones(symbol=symbol)
    if not symbol or not out.get("ok"):
        return None, f"“{short}”: Engine không hiểu hợp âm “{symbol}”"
    return {**base, "symbol": symbol, "engine_verified": True}, ""


def _build_scale(item, base, check, short):
    tonic, st = _s(item.get("tonic"), 4), _s(item.get("scale_type"), 20)
    out = engine.get_scale(tonic=tonic, scale_type=st) if st in SCALE_TYPES else {"ok": False}
    if not out.get("ok"):
        return None, f"“{short}”: Engine không dựng được âm giai {tonic} {st}"
    return {**base, "tonic": tonic, "scale_type": st, "engine_verified": True}, ""


def _open(item, base, check, short):
    model = _s(item.get("model_answer"), 1500)
    rubric = [_s(r, 300) for r in (item.get("rubric") or []) if _s(r, 300)][:5]
    if not model or len(rubric) < 2:
        return None, f"“{short}”: câu mở cần đáp án mẫu và 2–5 ý chấm"
    return {**base, "model_answer": model, "rubric": rubric}, ""


_BUILDERS = {"mcq": _mcq, "true_false": _true_false, "multi_select": _multi, "short": _short,
             "build_chord": _build_chord, "build_scale": _build_scale, "open": _open}


# --- hiển thị và soát chữ ---------------------------------------------------------------------------

def engine_answer(q: dict[str, Any]) -> list[str] | str | None:
    """Đáp án Engine tính để Quản trị viên đối chiếu (None = câu Engine không kiểm được)."""
    if q["kind"] == "build_chord":
        out = engine.get_chord_tones(symbol=q["symbol"])
        return list(out["notes"]) if out.get("ok") else None
    if q["kind"] == "build_scale":
        out = engine.get_scale(tonic=q["tonic"], scale_type=q["scale_type"])
        return list(out["notes"]) if out.get("ok") else None
    if q["kind"] == "short":
        return engine_answer_for_check(q["check"])
    if q["kind"] in ("mcq", "true_false") and q.get("engine_verified"):
        return q["answer"]
    if q["kind"] == "multi_select" and q.get("engine_verified"):
        return list(q["answers"])
    return None


def texts_for_scan(q: dict[str, Any]) -> list[str]:
    """Mọi chữ người học sẽ đọc, để guardrail soát (câu Đúng/Sai cố ý sai thì không soát đề, xem ADR-028)."""
    parts = [q.get("explanation", ""), *q.get("options", []), *q.get("option_feedback", {}).values()]
    if q["kind"] != "true_false":
        parts.insert(0, q["prompt"])
    if q["kind"] == "mcq":
        parts.append(q["answer"])
    if q["kind"] == "open":
        parts += [q["model_answer"], *q["rubric"]]
    return [p for p in parts if p]


# --- đặc tả câu hỏi khi xuất bản ---------------------------------------------------------------------

def exercise_spec(item_id: str, q: dict[str, Any], work_id: str) -> dict[str, Any]:
    provenance = [{"source_id": work_id, "locator": f"trang {q['page']}", "note": None}]
    common = {"id": item_id, "version": None, "status": "published", "retired": False, "prompt": q["prompt"], "skill": q["skill_id"],
              "explanation": q.get("explanation") or None, "provenance": provenance}
    meta = {"difficulty": q.get("level", "hieu"), "source": "ai_document"}
    kind = q["kind"]
    if kind in ("mcq", "true_false"):
        return {**common, "kind": kind, "strategy": "exact", "answer_key": {"expected": q["answer"]}, "options": q["options"],
                "grader_config": {**meta, "case_sensitive": True, "option_feedback": q.get("option_feedback") or {}}}
    if kind == "multi_select":
        return {**common, "kind": kind, "strategy": "exact", "answer_key": {"expected": list(q["answers"])}, "options": q["options"],
                "grader_config": {**meta, "case_sensitive": True, "unordered": True, "allowed_input_methods": ["multi_choice"],
                                  "option_feedback": q.get("option_feedback") or {}}}
    if kind == "short":
        c = q["check"]
        config = {"interval": {"kind": "identify_interval", "lower": c.get("lower"), "upper": c.get("upper")},
                  "roman": {"kind": "roman_numeral", "key": c.get("key"), "chord": c.get("chord")},
                  "chord_name": {"kind": "identify_chord", "notes": c.get("notes")}}[c["type"]]
        return {**common, "kind": "short", "strategy": "music_engine", "answer_key": {"expected": engine_answer_for_check(c)},
                "grader_config": {**meta, **config}, "options": None}
    if kind == "build_chord":
        return {**common, "kind": "build", "strategy": "music_engine", "answer_key": {"expected": engine_answer(q)},
                "grader_config": {**meta, "kind": "build_chord", "symbol": q["symbol"]}, "options": None}
    if kind == "build_scale":
        return {**common, "kind": "build", "strategy": "music_engine", "answer_key": {"expected": engine_answer(q)},
                "grader_config": {**meta, "kind": "build_scale", "tonic": q["tonic"], "scale_type": q["scale_type"]}, "options": None}
    return {**common, "kind": "open", "strategy": "open_rubric", "options": None,
            "answer_key": {"model_answer": q["model_answer"], "rubric": list(q["rubric"])},
            "grader_config": {**meta, "allowed_input_methods": ["text"]}}
