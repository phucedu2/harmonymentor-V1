"""Câu luyện tập do AI soạn từ tài liệu (ADR-028): chuẩn hóa, Music Engine kiểm đáp án, đổi thành đặc tả câu hỏi.

Vì sao tách khỏi ai_service: phần này quyết định câu nào được tin. Luật (Phúc chốt 18/11/2026, câu 4A):
- Câu tính được (quãng, số La Mã, nốt hợp âm, nốt âm giai, tên hợp âm) thì ĐÁP ÁN DO ENGINE CHỌN. AI chỉ viết đề và phương án;
  nếu AI chọn sai, Engine sửa và ghi lại; nếu không phương án nào đúng (hoặc nhiều hơn một), câu bị loại.
- Câu khái niệm Engine không kiểm được thì `needs_review=True`; xuất bản bị chặn tới khi Quản trị viên tick đã duyệt từng câu.
- Câu mở (tự luận dài) luôn cần duyệt, chấm bằng rubric, KHÔNG tính mastery (câu 3C).
"""

from __future__ import annotations

from typing import Any, Callable

from ..ai.tutor.guardrail import scan_reply
from ..music_engine import tools as engine
from ..music_engine.errors import MusicEngineError
from ..music_engine.grading import (grade_build_chord, grade_build_scale, grade_identify_chord, grade_identify_interval,
                                    grade_roman_numeral)
from ..music_engine.interval import interval_between
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


def statement_truth(statement: str) -> bool | None:
    """Câu Đúng/Sai: nếu Engine kiểm được mọi khẳng định trong câu thì biết câu đúng hay sai; không thì None."""
    claims = scan_reply(statement)
    if not claims:
        return None
    if any(c.status == "contradicted" for c in claims):
        return False
    if all(c.status == "verified" for c in claims):
        return True
    return None


# --- chuẩn hóa từng câu ----------------------------------------------------------------------------

def normalize_question(item: Any, skills: set[str], clamp: Callable[[Any], int], *,
                       trust_review: bool = False) -> tuple[dict[str, Any] | None, str]:
    """Trả (câu đã chuẩn hóa, "") hoặc (None, lý do loại). `trust_review` chỉ bật khi Quản trị viên sửa bản nháp:
    AI không được tự đánh dấu câu là đã duyệt."""
    if not isinstance(item, dict):
        return None, "không phải đối tượng"
    kind, prompt = item.get("kind"), _s(item.get("prompt"), 600)
    skill = _s(item.get("skill_id"), 64)
    level = item.get("level") if item.get("level") in LEVELS else "hieu"
    base: dict[str, Any] = {"kind": kind, "prompt": prompt, "skill_id": skill, "level": level,
                            "explanation": _s(item.get("explanation"), 800), "page": clamp(item.get("page"))}
    short = prompt[:40]
    if not prompt:
        return None, "thiếu đề"
    if kind not in KINDS:
        return None, f"“{short}”: loại câu “{kind}” không hỗ trợ"
    if skill not in skills:
        return None, f"“{short}”: kỹ năng “{skill}” không có trong hệ thống"
    check = clean_check(item.get("check"))
    q, why = _BUILDERS[kind](item, base, check, short)
    if q is None:
        return None, why
    q.setdefault("engine_verified", False)
    q["needs_review"] = not q["engine_verified"]
    q["reviewed"] = bool(trust_review and q["needs_review"] and item.get("reviewed") is True)
    return q, ""


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
