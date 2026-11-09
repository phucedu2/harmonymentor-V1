"""Chấm và ghi lịch sử Luyện tập (phuc-music Bước 2, FR-LRN-08).

Trước đây trang Luyện tập gọi thẳng /engine/grade/* và không lưu gì. Nay mọi lượt đi qua đây: Music Engine
chấm, kết quả được ghi vào `practice_attempts` theo user_id lấy từ token. Không đụng tới mastery (xem model).
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from ..db.models import PracticeAttempt, User
from ..music_engine import grading


class PracticeQuestionInvalid(ValueError):
    """Đề thiếu trường bắt buộc cho dạng bài đã chọn."""


_REQUIRED = {
    "chord": ("symbol",),
    "interval": ("lower", "upper"),
    "scale": ("tonic", "scale_type"),
    "roman": ("key", "chord"),
}


def _as_list(answer: str | list[str]) -> list[str]:
    if isinstance(answer, list):
        return [str(item) for item in answer]
    return [part for part in answer.replace(",", " ").replace("–", " ").replace("-", " ").split() if part]


def _as_text(answer: str | list[str]) -> str:
    return " ".join(answer) if isinstance(answer, list) else answer.strip()


PIANO_KINDS = ("chord", "scale")


class PracticeInputInvalid(ValueError):
    """Dạng bài không trả lời bằng piano được (quãng, số La Mã cần gõ tên)."""


def grade_practice(kind: str, question: dict[str, Any], answer: str | list[str], input_mode: str = "text") -> dict[str, Any]:
    missing = [name for name in _REQUIRED[kind] if not isinstance(question.get(name), str) or not question[name]]
    if missing:
        raise PracticeQuestionInvalid(", ".join(missing))
    if input_mode == "piano" and kind not in PIANO_KINDS:
        raise PracticeInputInvalid(kind)
    # Bấm phím không thể hiện cách viết (C# hay Db), nên chỉ chấm lớp cao độ; vẫn do Music Engine chấm.
    mode = "pitch_class_only" if input_mode == "piano" else "strict_spelling"
    if kind == "chord":
        result = grading.grade_build_chord(question["symbol"], _as_list(answer), grading_mode=mode)
    elif kind == "scale":
        result = grading.grade_build_scale(question["tonic"], question["scale_type"], _as_list(answer), grading_mode=mode)
    elif kind == "interval":
        return grading.grade_identify_interval(question["lower"], question["upper"], _as_text(answer))
    else:
        return grading.grade_roman_numeral(question["key"], question["chord"], _as_text(answer))
    if input_mode == "piano" and result["correct"]:
        expected = " ".join(result["expected"]) if isinstance(result["expected"], list) else result["expected"]
        result = {**result, "message_vi": f"Đúng phím. Khi viết tên nốt, cách viết chuẩn là: {expected}."}
    return result


def record_practice(db: Session, user: User, kind: str, level: str | None, question: dict[str, Any],
                    answer: str | list[str], input_mode: str = "text") -> tuple[PracticeAttempt, dict[str, Any]]:
    result = grade_practice(kind, question, answer, input_mode)
    # Chỉ lưu đúng các trường của đề, không lưu thứ client gửi kèm. Lượt bấm piano ghi thêm "input" để lịch sử
    # biết lượt đó chấm theo lớp cao độ (dễ hơn chấm chính tả), không trộn lẫn khi thống kê.
    clean_question = {name: question[name] for name in _REQUIRED[kind]}
    if input_mode == "piano":
        clean_question["input"] = "piano"
    row = PracticeAttempt(
        id=str(uuid4()), user_id=user.id, kind=kind, level=level, question=clean_question, answer=answer,
        correct=bool(result["correct"]), primary_error=result.get("primary_error"), is_test=user.role == "admin",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row, result


def practice_history(db: Session, user_id: str, limit: int = 20) -> tuple[list[PracticeAttempt], list[dict[str, Any]]]:
    items = db.scalars(
        select(PracticeAttempt).where(PracticeAttempt.user_id == user_id)
        .order_by(PracticeAttempt.created_at.desc(), PracticeAttempt.id).limit(limit)
    ).all()
    rows = db.execute(
        select(PracticeAttempt.kind, func.count(), func.sum(case((PracticeAttempt.correct, 1), else_=0)))
        .where(PracticeAttempt.user_id == user_id).group_by(PracticeAttempt.kind)
    ).all()
    stats = [{"kind": kind, "attempts": int(total), "correct": int(correct or 0)} for kind, total, correct in rows]
    return list(items), sorted(stats, key=lambda item: ["chord", "interval", "scale", "roman"].index(item["kind"]))

