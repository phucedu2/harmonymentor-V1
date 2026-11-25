"""Mẫu câu hỏi có tham số (FR-ADM-30, Phúc 6A, 25/11/2026).

Quản trị viên chọn mẫu ("Hợp âm {gốc}{loại} gồm những nốt nào?"), điền danh sách tham số, xem trước rồi lưu thành câu thật.
Đề, đáp án và lời giải đều do Music Engine dựng từ tham số: không có AI, không có đáp án gõ tay, nên không thể lệch Engine.
Câu lưu ra là câu luyện tập bình thường (phiên bản 1, bất biến theo ADR-006), cùng đường lưu với form soạn câu.
Tổ hợp tham số nào Engine không dựng được (ví dụ hợp âm ngoài giọng) thì bị loại và nói rõ lý do, không lưu nửa vời.
"""

from __future__ import annotations

from itertools import product
from typing import Any

from sqlalchemy.orm import Session

from ..db.models import User
from ..music_engine.scale import SCALE_TYPES
from . import lesson_admin as la
from .content_service import AdminContentError, audit

MAX_COMBOS = 30
MAX_VALUES = 12
SCALE_VI = {"major": "trưởng", "natural_minor": "thứ tự nhiên", "harmonic_minor": "thứ hòa thanh",
            "melodic_minor": "thứ giai điệu", "dorian": "Dorian", "mixolydian": "Mixolydian"}

TEMPLATES: dict[str, dict[str, Any]] = {
    "chord_tones": {
        "title": "Nốt của hợp âm", "pattern": "Hợp âm {gốc}{loại} gồm những nốt nào?", "skill_hint": "chord.",
        "params": [{"key": "roots", "label": "Gốc", "example": "C, G, F#, Eb"},
                   {"key": "qualities", "label": "Loại (gõ - cho hợp âm trưởng thường)", "example": "-, m, 7, maj7"}]},
    "scale_notes": {
        "title": "Nốt của âm giai", "pattern": "Âm giai {chủ âm} {loại} gồm những nốt nào?", "skill_hint": "scale.",
        "params": [{"key": "tonics", "label": "Chủ âm", "example": "C, D, Bb"},
                   {"key": "scale_types", "label": "Loại âm giai", "example": ", ".join(SCALE_TYPES)}]},
    "interval_name": {
        "title": "Tên quãng", "pattern": "Quãng từ {dưới} lên {trên} là quãng gì?", "skill_hint": "interval.",
        "params": [{"key": "lowers", "label": "Nốt dưới", "example": "C, D"},
                   {"key": "uppers", "label": "Nốt trên", "example": "E, G, A"}]},
    "roman_numeral": {
        "title": "Số La Mã trong giọng", "pattern": "Trong giọng {giọng} trưởng, hợp âm {hợp âm} là bậc mấy?", "skill_hint": "roman.",
        "params": [{"key": "keys", "label": "Giọng trưởng", "example": "C, G"},
                   {"key": "chords", "label": "Hợp âm", "example": "Dm7, G7, Am"}]},
}


def catalogue() -> list[dict[str, Any]]:
    return [{"id": k, **v} for k, v in TEMPLATES.items()]


def _values(raw: Any, label: str) -> list[str]:
    if isinstance(raw, str):
        raw = raw.split(",")
    vals = list(dict.fromkeys(str(x).strip() for x in (raw or []) if str(x).strip()))[: MAX_VALUES + 1]
    if not vals:
        raise AdminContentError("TEMPLATE_PARAM", f"“{label}” cần ít nhất một giá trị.")
    if len(vals) > MAX_VALUES:
        raise AdminContentError("TEMPLATE_PARAM", f"“{label}” tối đa {MAX_VALUES} giá trị.")
    return vals


def _item(tid: str, combo: tuple[str, ...]) -> dict[str, Any]:
    if tid == "chord_tones":
        root, quality = combo[0], ("" if combo[1] == "-" else combo[1])
        sym = root + quality
        return {"kind": "build_chord", "symbol": sym, "prompt": f"Hợp âm {sym} gồm những nốt nào?"}
    if tid == "scale_notes":
        tonic, st = combo
        return {"kind": "build_scale", "tonic": tonic, "scale_type": st,
                "prompt": f"Âm giai {tonic} {SCALE_VI.get(st, st)} gồm những nốt nào?"}
    if tid == "interval_name":
        lo, up = combo
        return {"kind": "short", "check": {"type": "interval", "lower": lo, "upper": up},
                "prompt": f"Quãng từ {lo} lên {up} là quãng gì?"}
    key, chord = combo
    return {"kind": "short", "check": {"type": "roman", "key": key, "chord": chord},
            "prompt": f"Trong giọng {key} trưởng, hợp âm {chord} là bậc mấy?"}


def _explain(tid: str, item: dict[str, Any], answer: Any) -> str:
    text = "–".join(answer) if isinstance(answer, list) else str(answer)
    if tid == "chord_tones":
        return f"Music Engine dựng hợp âm {item['symbol']} gồm các nốt {text}."
    if tid == "scale_notes":
        return f"Music Engine dựng âm giai {item['tonic']} {SCALE_VI.get(item['scale_type'], item['scale_type'])}: {text}."
    if tid == "interval_name":
        c = item["check"]
        return f"Từ {c['lower']} lên {c['upper']} là quãng {text} (Music Engine tính theo tên nốt và số nửa cung)."
    c = item["check"]
    return f"Trong giọng {c['key']} trưởng, hợp âm {c['chord']} là bậc {text} (Music Engine tính)."


def generate(db: Session, template_id: str, params: Any, skill_id: str, level: str) -> dict[str, Any]:
    """Dựng danh sách câu để xem trước (không ghi gì)."""
    tpl = TEMPLATES.get(template_id)
    if tpl is None:
        raise AdminContentError("TEMPLATE_NOT_FOUND", "Không có mẫu này.", 404)
    if not isinstance(params, dict):
        raise AdminContentError("TEMPLATE_PARAM", "Thiếu tham số của mẫu.")
    lists = [_values(params.get(p["key"]), p["label"]) for p in tpl["params"]]
    combos = list(product(*lists))
    if len(combos) > MAX_COMBOS:
        raise AdminContentError("TEMPLATE_TOO_MANY", f"Tổ hợp sinh {len(combos)} câu, tối đa {MAX_COMBOS}. Bớt giá trị tham số.")
    if skill_id not in la._skills(db):
        raise AdminContentError("TEMPLATE_SKILL", f"Kỹ năng “{skill_id}” không có trong hệ thống.")
    items, skipped = [], []
    for combo in combos:
        raw = _item(template_id, combo)
        raw.update(skill_id=skill_id, level=level)
        label = raw["prompt"]
        try:
            # Lời giải cần đáp án Engine: dựng thử không lời giải để lấy đáp án, rồi ghép lời giải.
            raw["explanation"] = "tạm"
            q = la._normalize(db, raw)
            answer = la._engine_answer(q)
            if not answer:
                raise AdminContentError("TEMPLATE_ENGINE", "Music Engine không tính được đáp án.")
            raw["explanation"] = _explain(template_id, raw, answer)
            q = la._normalize(db, raw)
        except AdminContentError as e:
            skipped.append({"prompt": label, "reason": e.message})
            continue
        items.append({"prompt": q["prompt"], "answer": "–".join(answer) if isinstance(answer, list) else str(answer),
                      "explanation": q["explanation"], "form": raw})
    return {"template": template_id, "items": items, "skipped": skipped}


def save(db: Session, admin: User, lesson_id: str, template_id: str, params: Any, skill_id: str, level: str) -> dict[str, Any]:
    lesson = la._lesson(db, lesson_id)
    la._editable(lesson)
    preview = generate(db, template_id, params, skill_id, level)
    have = {v.prompt for v in (la.current_version(e) for e in lesson.exercises) if v is not None}
    taken = {e.id for e in lesson.exercises}
    added, dup = [], []
    n = 1
    for it in preview["items"]:
        if it["prompt"] in have:
            dup.append(it["prompt"])
            continue
        while f"{lesson_id}-M{n:02d}" in taken:
            n += 1
        ex_id = f"{lesson_id}-M{n:02d}"
        taken.add(ex_id)
        la._insert_exercise(db, lesson, ex_id, la._normalize(db, it["form"]))
        db.flush()
        db.refresh(lesson)
        added.append(ex_id)
    if not added and not dup:
        raise AdminContentError("TEMPLATE_EMPTY", "Không có câu nào dựng được để lưu.")
    audit(db, admin, "exercise.from_template", "lesson", lesson_id, {"template": template_id, "added": added, "duplicates": dup})
    db.commit()
    return {"added": added, "duplicates": dup, "skipped": preview["skipped"]}
