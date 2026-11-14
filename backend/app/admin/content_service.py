"""Quản trị nội dung bài học (ADR-023): sửa khối lý thuyết thành bản nháp, soát bằng Music Engine, xuất bản, khôi phục.

Chỉ sửa được CHỮ của khối (tiêu đề, đoạn văn, ý, thuật ngữ). Loại khối, mã bài tập gắn kèm, danh sách hợp âm, nút mở
Harmony Lab… phải giữ nguyên, để một lỗi gõ không làm vỡ giao diện hay đổi đáp án. Câu hỏi không sửa ở đây (ADR-006).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..ai.tutor.guardrail import scan_reply
from ..content import overrides
from ..db.models import AdminAuditLog, ContentRevision, Exercise, Lesson, User
from ..content.versioning import current_version

MAX_TEXT = 4000
MAX_ITEMS = 40
TEXT_KEYS = ("title", "prompt", "note", "intro", "kicker")
LIST_KEYS = ("paragraphs", "items")
TERM_FIELDS = ("symbol", "term", "definition", "example")


class AdminContentError(Exception):
    def __init__(self, code: str, message: str, status: int = 422):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def audit(db: Session, actor: User, action: str, target_type: str, target_id: str, detail: dict[str, Any] | None = None) -> None:
    db.add(AdminAuditLog(actor_id=actor.id, action=action, target_type=target_type, target_id=target_id, detail=detail or {}))


def _texts(payload: Any) -> list[str]:
    if isinstance(payload, str):
        return [payload]
    if isinstance(payload, dict):
        return [t for v in payload.values() for t in _texts(v)]
    if isinstance(payload, list):
        return [t for v in payload for t in _texts(v)]
    return []


def engine_report(payload: dict[str, Any]) -> dict[str, Any]:
    """Soát mọi nốt, quãng, hợp âm, số La Mã mà lời văn khẳng định bằng Music Engine (không dùng AI)."""
    claims = scan_reply("\n".join(_texts(payload)))
    contradicted = [c.as_dict() for c in claims if c.status == "contradicted"]
    return {"checked": len(claims), "verified": sum(1 for c in claims if c.status == "verified"),
            "contradicted": contradicted, "unsupported": sum(1 for c in claims if c.status == "unsupported")}


def validate_edit(base: dict[str, Any], new: Any) -> dict[str, Any]:
    """Chỉ cho đổi các trường chữ; mọi trường khác phải giống hệt bản gốc."""
    if not isinstance(new, dict):
        raise AdminContentError("PAYLOAD_INVALID", "Nội dung khối phải là một đối tượng.")
    if set(new) != set(base):
        raise AdminContentError("PAYLOAD_KEYS_CHANGED", "Không được thêm hoặc bớt trường của khối: " + ", ".join(sorted(set(new) ^ set(base))))
    out: dict[str, Any] = {}
    for key, old in base.items():
        value = new[key]
        if key in TEXT_KEYS and isinstance(old, str):
            if not isinstance(value, str) or len(value) > MAX_TEXT:
                raise AdminContentError("TEXT_INVALID", f"Trường “{key}” phải là chữ, tối đa {MAX_TEXT} ký tự.")
            out[key] = value
        elif key in LIST_KEYS and isinstance(old, list) and all(isinstance(x, str) for x in old):
            if not isinstance(value, list) or len(value) > MAX_ITEMS or not all(isinstance(x, str) and len(x) <= MAX_TEXT for x in value):
                raise AdminContentError("LIST_INVALID", f"Trường “{key}” phải là danh sách chữ (tối đa {MAX_ITEMS} mục).")
            out[key] = value
        elif key == "terms" and isinstance(old, list):
            if not isinstance(value, list) or len(value) > MAX_ITEMS:
                raise AdminContentError("TERMS_INVALID", "Danh sách thuật ngữ không hợp lệ.")
            cleaned = []
            for item in value:
                if not isinstance(item, dict) or not set(item) <= set(TERM_FIELDS) or not all(isinstance(v, str) and len(v) <= MAX_TEXT for v in item.values()):
                    raise AdminContentError("TERMS_INVALID", "Mỗi thuật ngữ chỉ gồm chữ ở các trường symbol, term, definition, example.")
                cleaned.append(item)
            out[key] = cleaned
        else:
            if value != old:
                raise AdminContentError("FIELD_LOCKED", f"Trường “{key}” không sửa được ở đây.")
            out[key] = old
    return out


def _block(db: Session, lesson_id: str, block_id: str):
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise AdminContentError("LESSON_NOT_FOUND", "Không có bài này.", 404)
    block = next((b for b in lesson.blocks if b.id == block_id), None)
    if block is None:
        raise AdminContentError("BLOCK_NOT_FOUND", "Không có khối này trong bài.", 404)
    return lesson, block


def lesson_list(db: Session) -> list[dict[str, Any]]:
    hidden = overrides.hidden_lesson_ids(db)
    lessons = db.scalars(select(Lesson).order_by(Lesson.order_index)).unique().all()
    published_counts = dict(db.execute(select(ContentRevision.lesson_id, func.count(func.distinct(ContentRevision.target)))
                                       .where(ContentRevision.kind == "block", ContentRevision.status == "published")
                                       .group_by(ContentRevision.lesson_id)).all())
    draft_counts = dict(db.execute(select(ContentRevision.lesson_id, func.count(func.distinct(ContentRevision.target)))
                                   .where(ContentRevision.kind == "block", ContentRevision.status == "draft")
                                   .group_by(ContentRevision.lesson_id)).all())
    return [{
        "id": lesson.id, "order": lesson.order_index, "track": lesson.track, "title": lesson.title, "status": lesson.status,
        "hidden": lesson.id in hidden, "block_count": len(lesson.blocks),
        "exercise_count": len([e for e in lesson.exercises if current_version(e) is not None]),
        "edited_blocks": published_counts.get(lesson.id, 0), "draft_blocks": draft_counts.get(lesson.id, 0),
    } for lesson in lessons]


def lesson_detail(db: Session, lesson_id: str) -> dict[str, Any]:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise AdminContentError("LESSON_NOT_FOUND", "Không có bài này.", 404)
    published = overrides.published_by_target(db, lesson.id)
    drafts = overrides.draft_by_target(db, lesson.id)
    blocks = []
    for block in sorted(lesson.blocks, key=lambda b: b.position):
        working = drafts.get(block.id) or published.get(block.id)
        payload = dict(working.payload) if working is not None else dict(block.payload or {})
        blocks.append({
            "id": block.id, "position": block.position, "block_type": block.block_type, "payload": payload,
            "base_payload": block.payload or {}, "edited": block.id in published, "draft_revision_id": drafts[block.id].id if block.id in drafts else None,
            "engine": engine_report(payload),
        })
    exercises = []
    for exercise in sorted(lesson.exercises, key=lambda x: x.position):
        version = current_version(exercise)
        if version is not None:
            exercises.append({"id": exercise.id, "version": version.version, "skill_id": exercise.skill_id, "kind": version.kind,
                              "prompt": version.prompt, "status": version.status})
    summary = next(item for item in lesson_list(db) if item["id"] == lesson.id)
    return {"lesson": summary, "objectives": lesson.objectives or [], "blocks": blocks, "exercises": exercises}


def save_draft(db: Session, actor: User, lesson_id: str, block_id: str, payload: Any, note: str | None) -> dict[str, Any]:
    lesson, block = _block(db, lesson_id, block_id)
    current = overrides.published_by_target(db, lesson.id).get(block.id)
    base = dict(current.payload) if current is not None else dict(block.payload or {})
    clean = validate_edit(base, payload)
    # Mỗi khối chỉ giữ một bản nháp: lưu lại thì thay bản nháp cũ.
    for old in db.scalars(select(ContentRevision).where(ContentRevision.lesson_id == lesson.id, ContentRevision.target == block.id,
                                                       ContentRevision.kind == "block", ContentRevision.status == "draft")):
        db.delete(old)
    revision = ContentRevision(id=str(uuid4()), lesson_id=lesson.id, kind="block", target=block.id, payload=clean, status="draft",
                               note=(note or "")[:500] or None, created_by=actor.id)
    db.add(revision)
    audit(db, actor, "content.save_draft", "lesson_block", f"{lesson.id}/{block.id}", {"revision": revision.id})
    db.commit()
    return {"revision_id": revision.id, "engine": engine_report(clean)}


def publish(db: Session, actor: User, revision_id: str, acknowledge_engine_flags: bool) -> dict[str, Any]:
    revision = db.get(ContentRevision, revision_id)
    if revision is None or revision.kind != "block":
        raise AdminContentError("REVISION_NOT_FOUND", "Không có bản sửa này.", 404)
    report = engine_report(revision.payload)
    if report["contradicted"] and not acknowledge_engine_flags:
        raise AdminContentError("ENGINE_FLAGS", "Music Engine báo có chỗ có thể sai nhạc lý. Hãy sửa, hoặc xác nhận đã xem rồi xuất bản.", 409)
    revision.status = "published"
    revision.published_by = actor.id
    revision.published_at = datetime.now(timezone.utc)
    audit(db, actor, "content.publish", "lesson_block", f"{revision.lesson_id}/{revision.target}",
          {"revision": revision.id, "engine_flags": len(report["contradicted"])})
    db.commit()
    return {"revision_id": revision.id, "engine": report}


def restore(db: Session, actor: User, lesson_id: str, block_id: str, revision_id: str | None) -> dict[str, Any]:
    """Khôi phục một bản cũ (hoặc nội dung gốc khi revision_id rỗng): tạo bản MỚI đã xuất bản, không xóa lịch sử."""
    lesson, block = _block(db, lesson_id, block_id)
    if revision_id:
        source = db.get(ContentRevision, revision_id)
        if source is None or source.lesson_id != lesson.id or source.target != block.id or source.kind != "block":
            raise AdminContentError("REVISION_NOT_FOUND", "Không có bản sửa này của khối.", 404)
        payload = dict(source.payload)
    else:
        payload = dict(block.payload or {})
    now = datetime.now(timezone.utc)
    revision = ContentRevision(id=str(uuid4()), lesson_id=lesson.id, kind="block", target=block.id, payload=payload, status="published",
                               note="Khôi phục " + (f"bản {revision_id[:8]}" if revision_id else "nội dung gốc"), created_by=actor.id,
                               published_by=actor.id, published_at=now)
    db.add(revision)
    for old in db.scalars(select(ContentRevision).where(ContentRevision.lesson_id == lesson.id, ContentRevision.target == block.id,
                                                       ContentRevision.kind == "block", ContentRevision.status == "draft")):
        db.delete(old)
    audit(db, actor, "content.restore", "lesson_block", f"{lesson.id}/{block.id}", {"from": revision_id or "seed"})
    db.commit()
    return {"revision_id": revision.id}


def history(db: Session, lesson_id: str, block_id: str) -> list[dict[str, Any]]:
    _block(db, lesson_id, block_id)
    rows = db.scalars(select(ContentRevision).where(ContentRevision.lesson_id == lesson_id, ContentRevision.target == block_id,
                                                   ContentRevision.kind == "block").order_by(ContentRevision.created_at.desc())).all()
    return [{"id": r.id, "status": r.status, "note": r.note, "created_by": r.created_by, "created_at": r.created_at,
             "published_at": r.published_at, "payload": r.payload} for r in rows]


def set_hidden(db: Session, actor: User, lesson_id: str, hidden: bool) -> dict[str, Any]:
    if db.get(Lesson, lesson_id) is None:
        raise AdminContentError("LESSON_NOT_FOUND", "Không có bài này.", 404)
    now = datetime.now(timezone.utc)
    db.add(ContentRevision(id=str(uuid4()), lesson_id=lesson_id, kind="visibility", target=overrides.LESSON_TARGET,
                           payload={"hidden": bool(hidden)}, status="published", created_by=actor.id, published_by=actor.id, published_at=now))
    audit(db, actor, "content.hide" if hidden else "content.show", "lesson", lesson_id)
    db.commit()
    return {"id": lesson_id, "hidden": bool(hidden)}
