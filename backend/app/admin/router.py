from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..auth.deps import require_admin
from ..core.errors import AppError
from ..db.models import AdminAuditLog, Attempt, LessonProgress, User
from ..db.session import get_db
from . import content_service, stats_service
from .content_service import AdminContentError

# Mọi route /api/v1/admin/* gắn require_admin ở cấp router để không route nào quên kiểm tra quyền.
router = APIRouter(prefix="/api/v1/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _wrap(exc: AdminContentError) -> AppError:
    return AppError(exc.status, exc.code, exc.message)


@router.get("/ping")
def admin_ping(user: User = Depends(require_admin)):
    return {"ok": True, "user_id": user.id}


# --- bài học ------------------------------------------------------------------------------------

class SaveDraftIn(BaseModel):
    payload: dict[str, Any]
    note: str | None = Field(default=None, max_length=500)


class PublishIn(BaseModel):
    acknowledge_engine_flags: bool = False


class RestoreIn(BaseModel):
    revision_id: str | None = None


class VisibilityIn(BaseModel):
    hidden: bool


@router.get("/lessons")
def list_lessons(db: Session = Depends(get_db)):
    return content_service.lesson_list(db)


@router.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: str, db: Session = Depends(get_db)):
    try:
        return content_service.lesson_detail(db, lesson_id)
    except AdminContentError as exc:
        raise _wrap(exc) from exc


@router.put("/lessons/{lesson_id}/blocks/{block_id}")
def save_block_draft(lesson_id: str, block_id: str, body: SaveDraftIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        return content_service.save_draft(db, admin, lesson_id, block_id, body.payload, body.note)
    except AdminContentError as exc:
        raise _wrap(exc) from exc


@router.get("/lessons/{lesson_id}/blocks/{block_id}/history")
def block_history(lesson_id: str, block_id: str, db: Session = Depends(get_db)):
    try:
        return content_service.history(db, lesson_id, block_id)
    except AdminContentError as exc:
        raise _wrap(exc) from exc


@router.post("/lessons/{lesson_id}/blocks/{block_id}/restore")
def restore_block(lesson_id: str, block_id: str, body: RestoreIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        return content_service.restore(db, admin, lesson_id, block_id, body.revision_id)
    except AdminContentError as exc:
        raise _wrap(exc) from exc


@router.post("/revisions/{revision_id}/publish")
def publish_revision(revision_id: str, body: PublishIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        return content_service.publish(db, admin, revision_id, body.acknowledge_engine_flags)
    except AdminContentError as exc:
        raise _wrap(exc) from exc


@router.post("/lessons/{lesson_id}/visibility")
def lesson_visibility(lesson_id: str, body: VisibilityIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        return content_service.set_hidden(db, admin, lesson_id, body.hidden)
    except AdminContentError as exc:
        raise _wrap(exc) from exc


# --- người dùng ---------------------------------------------------------------------------------

class UserPatchIn(BaseModel):
    is_active: bool


@router.get("/users")
def list_users(q: str = Query("", max_length=80), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
               db: Session = Depends(get_db)):
    """Danh sách tài khoản thật (không gồm người học mô phỏng). Không trả mật khẩu hay token."""
    stmt = select(User).where(User.is_synthetic.is_(False), User.email.is_not(None))
    if q.strip():
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(User.email).like(like), func.lower(User.display_name).like(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    users = db.scalars(stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)).all()
    ids = [u.id for u in users]
    attempts = dict(db.execute(select(Attempt.user_id, func.count()).where(Attempt.user_id.in_(ids), Attempt.is_test.is_(False))
                               .group_by(Attempt.user_id)).all()) if ids else {}
    last = dict(db.execute(select(Attempt.user_id, func.max(Attempt.created_at)).where(Attempt.user_id.in_(ids), Attempt.is_test.is_(False))
                           .group_by(Attempt.user_id)).all()) if ids else {}
    done = dict(db.execute(select(LessonProgress.user_id, func.count()).where(LessonProgress.user_id.in_(ids), LessonProgress.status == "completed")
                           .group_by(LessonProgress.user_id)).all()) if ids else {}
    return {"total": total, "items": [{
        "id": u.id, "email": u.email, "display_name": u.display_name, "role": u.role, "is_active": u.is_active, "created_at": u.created_at,
        "lessons_completed": done.get(u.id, 0), "attempts": attempts.get(u.id, 0), "last_activity": last.get(u.id),
    } for u in users]}


@router.patch("/users/{user_id}")
def patch_user(user_id: str, body: UserPatchIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Khóa hoặc mở khóa tài khoản. Không đổi vai trò qua web (tạo admin chỉ bằng lệnh seed_admin) và không tự khóa mình."""
    target = db.get(User, user_id)
    if target is None or target.is_synthetic:
        raise AppError(404, "USER_NOT_FOUND", "Không có người dùng này.")
    if target.id == admin.id:
        raise AppError(409, "CANNOT_LOCK_SELF", "Bạn không thể tự khóa tài khoản của mình.")
    target.is_active = body.is_active
    content_service.audit(db, admin, "user.unlock" if body.is_active else "user.lock", "user", target.id)
    db.commit()
    return {"id": target.id, "is_active": target.is_active}


# --- thống kê và nhật ký --------------------------------------------------------------------------

@router.get("/stats")
def stats(days: int = Query(30, ge=7, le=90), db: Session = Depends(get_db)):
    return stats_service.overview(db, days=days)


@router.get("/audit")
def audit_log(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    rows = db.scalars(select(AdminAuditLog).order_by(AdminAuditLog.id.desc()).limit(limit)).all()
    return [{"id": r.id, "actor_id": r.actor_id, "action": r.action, "target_type": r.target_type, "target_id": r.target_id,
             "detail": r.detail, "created_at": r.created_at} for r in rows]
