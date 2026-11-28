"""Lớp bản sửa nội dung bài học (ADR-023): đặt bản sửa đã xuất bản của Quản trị viên lên trên nội dung seed.

Seed vẫn là nguồn gốc và chạy mỗi lần khởi động; bản sửa nằm ở bảng riêng nên không bị ghi đè. Học viên chỉ thấy bản
`published`; bản `draft` chỉ Quản trị viên xem trước. Câu hỏi KHÔNG đi qua lớp này: câu đã phát hành bất biến và chỉ đổi
bằng `version` trong curriculum_specs (ADR-006).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import ContentRevision, Lesson, LessonBlock

LESSON_TARGET = "@lesson"


def _latest(rows: list[ContentRevision]) -> ContentRevision | None:
    return max(rows, key=lambda r: (r.published_at or r.created_at, r.created_at), default=None)


def published_by_target(db: Session, lesson_id: str) -> dict[str, ContentRevision]:
    rows = db.scalars(select(ContentRevision).where(
        ContentRevision.lesson_id == lesson_id, ContentRevision.kind == "block", ContentRevision.status == "published"
    )).all()
    grouped: dict[str, list[ContentRevision]] = {}
    for row in rows:
        grouped.setdefault(row.target, []).append(row)
    return {target: _latest(items) for target, items in grouped.items()}  # type: ignore[misc]


def draft_by_target(db: Session, lesson_id: str) -> dict[str, ContentRevision]:
    rows = db.scalars(select(ContentRevision).where(
        ContentRevision.lesson_id == lesson_id, ContentRevision.kind == "block", ContentRevision.status == "draft"
    )).all()
    grouped: dict[str, list[ContentRevision]] = {}
    for row in rows:
        grouped.setdefault(row.target, []).append(row)
    return {target: max(items, key=lambda r: r.created_at) for target, items in grouped.items()}


def hidden_lesson_ids(db: Session) -> set[str]:
    """Bài người học không thấy: bản `visibility` mới nhất có hidden = true, hoặc bài đã xóa mềm (FR-ADM-15).
    Gộp chung một chỗ để mọi nơi đang lọc bài ẩn (lộ trình, quiz, gợi ý, kho AI Tutor) cũng lọc luôn bài đã xóa."""
    rows = db.scalars(select(ContentRevision).where(ContentRevision.kind == "visibility")).all()
    per_lesson: dict[str, list[ContentRevision]] = {}
    for row in rows:
        per_lesson.setdefault(row.lesson_id, []).append(row)
    hidden = {lesson_id for lesson_id, items in per_lesson.items()
              if max(items, key=lambda r: r.created_at).payload.get("hidden") is True}
    return hidden | deleted_lesson_ids(db)


def deleted_lesson_ids(db: Session) -> set[str]:
    return set(db.scalars(select(Lesson.id).where(Lesson.deleted_at.is_not(None))).all())


def lesson_sort_key():
    """Thứ tự bài: thứ tự Quản trị viên đặt (FR-ADM-16), chưa đặt thì theo seed. order_index*10 để bài seed mới thêm sau
    khi đã sắp xếp vẫn chen vào đúng khoảng (sort_key được đặt theo bước 10)."""
    from sqlalchemy import func
    return func.coalesce(Lesson.sort_key, Lesson.order_index * 10)


def lesson_hidden(db: Session, lesson_id: str) -> bool:
    return lesson_id in hidden_lesson_ids(db)


def effective_blocks(db: Session, lesson: Lesson, include_drafts: bool = False) -> list[tuple[LessonBlock, dict[str, Any]]]:
    """(khối gốc, payload hiệu lực) theo thứ tự vị trí. include_drafts=True cho Quản trị viên xem trước."""
    published = published_by_target(db, lesson.id)
    drafts = draft_by_target(db, lesson.id) if include_drafts else {}
    out = []
    for block in sorted(lesson.blocks, key=lambda b: b.position):
        revision = drafts.get(block.id) or published.get(block.id)
        out.append((block, dict(revision.payload) if revision is not None else dict(block.payload or {})))
    return out
