"""Quản trị viên soạn thẻ ôn (FR-ADM-31..34, Phúc 6A, 25/11/2026).

Thẻ ôn đi theo lịch Leitner (ADR-002): một thẻ gồm mặt trước (câu hỏi), mặt sau (đáp án) và cách chấm. Thẻ seed (L01-F01…)
do curriculum_specs sinh lại mỗi lần khởi động nên chỉ xem; thẻ Quản trị viên soạn (id `<bài>-R01…`) thêm/sửa/xóa mềm được
và gắn được vào MỌI bài, kể cả bài gốc (seed không đụng thẻ có id lạ). Sáu loại thẻ:

- recall: đáp án là một chuỗi, chấm đúng-sai chính xác;
- self_check: ý mở, người học lật thẻ rồi tự đánh giá (máy không đoán nghĩa);
- build_chord / build_scale / interval / roman: đáp án do Music Engine tính, Quản trị viên không tự gõ đáp án nên
  không có chuyện Engine tính khác người soạn; đề phải nêu đúng ký hiệu đưa cho Engine (cùng luật câu luyện tập).

Sửa thẻ ghi đè tại chỗ (thẻ ôn không có phiên bản như câu luyện tập; lượt ôn cũ chỉ lưu đúng/sai) và ghi nhật ký giá trị cũ.
Thêm thẻ mới vào bài mà người học đã hoàn thành thì kích hoạt thẻ đó cho họ (đến hạn ngay), vì kích hoạt thẻ chỉ chạy lúc
hoàn thành bài.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import LessonProgress, ReviewItem, User
from ..services.review_scheduler import activate_lesson_reviews
from . import ai_questions as aq
from . import lesson_admin as la
from .content_service import AdminContentError, audit

KINDS = ("recall", "self_check", "build_chord", "build_scale", "interval", "roman")
ENGINE_KINDS = {"build_chord": "build_chord", "build_scale": "build_scale", "interval": "short", "roman": "short"}
_META_KEYS = ("difficulty", "source")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _s(value: Any, size: int) -> str:
    return str(value or "").strip()[:size]


def _engine_back(q: dict[str, Any]) -> str:
    out = la._engine_answer(q)
    if isinstance(out, list):
        return "–".join(out)
    return str(out) if out else ""


def _normalize(db: Session, item: Any) -> dict[str, Any]:
    """Chuẩn hóa form thẻ thành các cột ReviewItem. Mọi lỗi người soạn nhập là AdminContentError nói rõ sửa gì."""
    if not isinstance(item, dict):
        raise AdminContentError("CARD_INVALID", "Thẻ không hợp lệ.")
    kind, front = item.get("kind"), _s(item.get("front"), 600)
    skill = _s(item.get("skill_id"), 64)
    if kind not in KINDS:
        raise AdminContentError("CARD_KIND", "Loại thẻ phải là: " + ", ".join(KINDS) + ".")
    if not front:
        raise AdminContentError("CARD_INCOMPLETE", "Thẻ cần mặt trước (câu hỏi).")
    if skill not in la._skills(db):
        raise AdminContentError("CARD_SKILL", f"Kỹ năng “{skill}” không có trong hệ thống.")
    form: dict[str, Any] = {"kind": kind, "front": front, "skill_id": skill}
    if kind in ("recall", "self_check"):
        back = _s(item.get("back"), 600)
        if not back:
            raise AdminContentError("CARD_INCOMPLETE", "Thẻ cần mặt sau (đáp án).")
        form["back"] = back
        if kind == "recall":
            expected = _s(item.get("expected"), 300) or back
            cs = bool(item.get("case_sensitive", True))
            form.update(expected=expected, case_sensitive=cs)
            return {"mode": "recall", "back": back, "strategy": "exact", "answer_key": {"expected": expected},
                    "grader_config": {"case_sensitive": cs, "form": form}, "skill": skill}
        keywords = [k for k in (_s(x, 80) for x in (item.get("keywords") or []) if isinstance(x, str)) if k][:12] or [back]
        form["keywords"] = keywords
        return {"mode": "context", "back": back, "strategy": "rubric", "answer_key": {"accepted": [k.lower() for k in keywords]},
                "grader_config": {"mode": "contains_any", "strip_accents": True, "form": form}, "skill": skill}
    # Loại do Engine tính: dựng như câu luyện tập rồi lấy cách chấm và đáp án chuẩn.
    raw: dict[str, Any] = {"kind": ENGINE_KINDS[kind], "prompt": front, "skill_id": skill, "level": "hieu", "page": 1,
                           "reviewed": True}
    if kind == "build_chord":
        raw["symbol"] = _s(item.get("symbol"), 40)
    elif kind == "build_scale":
        raw.update(tonic=_s(item.get("tonic"), 8), scale_type=_s(item.get("scale_type"), 40))
    else:
        check = item.get("check")
        raw["check"] = check if isinstance(check, dict) else {}
        raw["check"] = {**raw["check"], "type": "interval" if kind == "interval" else "roman"}
    q, why = aq.normalize_question(raw, la._skills(db), lambda p: 1, trust_review=True)
    if q is None:
        raise AdminContentError("CARD_INVALID", f"Thẻ chưa lưu được: {la.human_why(why)}.")
    spec = aq.exercise_spec("card", q, la.ADMIN_WORK_ID)
    back = _s(item.get("back"), 600) or _engine_back(q)
    if not back:
        raise AdminContentError("CARD_ENGINE", "Music Engine không tính được đáp án cho thẻ này, kiểm lại ký hiệu.")
    for key in ("symbol", "tonic", "scale_type"):
        if q.get(key):
            form[key] = q[key]
    if q.get("check"):
        form["check"] = q["check"]
    form["back"] = back
    config = {k: v for k, v in spec["grader_config"].items() if k not in _META_KEYS}
    return {"mode": "build" if kind.startswith("build") else "recall", "back": back, "strategy": spec["strategy"],
            "answer_key": spec["answer_key"], "grader_config": {**config, "form": form}, "skill": skill}


def _is_admin_card(card: ReviewItem) -> bool:
    return any(p.get("source_id") == la.ADMIN_WORK_ID for p in (card.provenance or []))


def _view(card: ReviewItem) -> dict[str, Any]:
    editable = _is_admin_card(card)
    form = (card.grader_config or {}).get("form") if editable else None
    return {"id": card.id, "front": card.front, "back": card.back, "skill_id": card.skill_id, "mode": card.mode,
            "editable": editable, "form": form}


def list_cards(db: Session, lesson_id: str) -> dict[str, Any]:
    lesson = la._lesson(db, lesson_id)
    rows = [c for c in sorted(lesson.review_items, key=lambda x: x.id) if c.deleted_at is None]
    return {"cards": [_view(c) for c in rows], "skills": sorted(la._skills(db)), "kinds": list(KINDS)}


def _next_id(db: Session, lesson_id: str) -> str:
    # Số lớn nhất đã từng dùng + 1, kể cả thẻ đã xóa mềm: id không tái dùng.
    ids = db.scalars(select(ReviewItem.id).where(ReviewItem.lesson_id == lesson_id)).all()
    nums = [int(i.rsplit("-R", 1)[1]) for i in ids if "-R" in i and i.rsplit("-R", 1)[1].isdigit()]
    return f"{lesson_id}-R{max(nums, default=0) + 1:02d}"


def activate_for_completed(db: Session, lesson_id: str) -> int:
    """Người học đã hoàn thành bài từ trước sẽ không bao giờ chạy lại lúc "hoàn thành": kích hoạt thẻ mới cho họ.
    Dùng chung cho form và nhập file; trả số người được kích hoạt."""
    done = db.scalars(select(LessonProgress.user_id).join(User, User.id == LessonProgress.user_id)
                      .where(LessonProgress.lesson_id == lesson_id, LessonProgress.status == "completed",
                             User.email.is_not(None))).all()
    for uid in done:
        activate_lesson_reviews(db, uid, lesson_id)
    return len(done)


def add_card(db: Session, admin: User, lesson_id: str, item: Any) -> dict[str, Any]:
    lesson = la._lesson(db, lesson_id)
    n = _normalize(db, item)
    la._ensure_work(db)
    card = ReviewItem(id=_next_id(db, lesson.id), lesson_id=lesson.id, skill_id=n["skill"], mode=n["mode"], front=n["grader_config"]["form"]["front"],
                      back=n["back"], grading_strategy=n["strategy"], answer_key=n["answer_key"], grader_config=n["grader_config"],
                      provenance=[{"source_id": la.ADMIN_WORK_ID, "locator": None, "note": "Quản trị viên soạn bằng form"}])
    db.add(card)
    db.flush()
    done = activate_for_completed(db, lesson.id)
    audit(db, admin, "card.create", "review_item", card.id, {"lesson": lesson.id, "kind": item.get("kind"), "activated_for": done})
    db.commit()
    return {**_view(card), "activated_for": done}


def _card(db: Session, card_id: str) -> ReviewItem:
    card = db.get(ReviewItem, card_id)
    if card is None or card.deleted_at is not None:
        raise AdminContentError("CARD_NOT_FOUND", "Không có thẻ này.", 404)
    if not _is_admin_card(card):
        raise AdminContentError("SEED_CARD", "Thẻ gốc của hệ thống: đổi trong curriculum_specs (seed ghi lại mỗi lần khởi động).", 409)
    return card


def update_card(db: Session, admin: User, card_id: str, item: Any) -> dict[str, Any]:
    card = _card(db, card_id)
    n = _normalize(db, item)
    before = {"front": card.front, "back": card.back, "skill_id": card.skill_id}
    card.skill_id, card.mode, card.front, card.back = n["skill"], n["mode"], n["grader_config"]["form"]["front"], n["back"]
    card.grading_strategy, card.answer_key, card.grader_config = n["strategy"], n["answer_key"], n["grader_config"]
    audit(db, admin, "card.update", "review_item", card.id, {"from": before, "to": {"front": card.front, "back": card.back, "skill_id": card.skill_id}})
    db.commit()
    return _view(card)


def delete_card(db: Session, admin: User, card_id: str) -> dict[str, Any]:
    card = _card(db, card_id)
    card.deleted_at = _now()   # xóa mềm: lượt ôn và mastery cũ giữ nguyên
    audit(db, admin, "card.delete", "review_item", card.id, {"front": card.front})
    db.commit()
    return {"id": card.id, "deleted": True}
