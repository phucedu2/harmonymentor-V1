from __future__ import annotations

from typing import Any

from dataclasses import replace as dc_replace

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..auth.deps import require_admin
from ..core.errors import AppError
from ..db.models import AdminAuditLog, Attempt, LessonProgress, User
from ..db.session import SessionLocal, get_db
from ..ai.tutor.llm import LLMProvider, get_provider
from ..core.ai_config import relevance_config
from ..core import ai_switch
from ..core.config import settings
from ..db.models import SourceDocument
from . import ai_job, ai_service, content_import, content_service, lesson_admin, skill_admin, stats_service
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


# --- kỹ năng, tiên quyết, nguồn tài liệu (FR-ADM-18..22, FR-ADM-38) ------------------------------------

class SkillIn(BaseModel):
    slug: str = Field(default="", max_length=100)
    name: str = Field(min_length=1, max_length=200)
    domain: str = Field(default="theory", max_length=80)


class PrereqIn(BaseModel):
    prerequisite_id: str = Field(min_length=1, max_length=120)


class SourceIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    author: str | None = Field(default=None, max_length=200)
    url: str | None = Field(default=None, max_length=800)


class SourceLinkIn(BaseModel):
    source_id: str = Field(min_length=1, max_length=80)
    locator: str = Field(default="", max_length=300)
    note: str | None = Field(default=None, max_length=1000)


# --- tạo/xóa/sắp xếp bài, câu luyện tập bằng form (FR-ADM-13/15/16/24..29) ---------------------------

class LessonCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    objectives: list[str] = Field(default_factory=list, max_length=10)
    block_title: str = Field(min_length=1, max_length=200)
    paragraphs: list[str] = Field(min_length=1, max_length=30)


class BlockCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    paragraphs: list[str] = Field(min_length=1, max_length=30)


class ReorderIn(BaseModel):
    lesson_ids: list[str] = Field(min_length=1, max_length=500)


class LessonMetaIn(BaseModel):
    title: str | None = Field(default=None, max_length=240)
    objectives: list[str] = Field(default_factory=list, max_length=10)
    reset: bool = False


class BlockOrderIn(BaseModel):
    block_ids: list[str] = Field(min_length=1, max_length=200)


def _do(fn, *args):
    try:
        return fn(*args)
    except AdminContentError as exc:
        raise _wrap(exc) from exc


_sk = _do   # cùng cách đổi lỗi AdminContentError → HTTP


@router.get("/skills")
def list_skills(db: Session = Depends(get_db)):
    return skill_admin.list_skills(db)


@router.post("/skills", status_code=201)
def create_skill(body: SkillIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return _sk(skill_admin.create_skill, db, admin, body.slug, body.name, body.domain)


@router.put("/skills/{skill_id}")
def update_skill(skill_id: str, body: SkillIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return _sk(skill_admin.update_skill, db, admin, skill_id, body.name, body.domain)


@router.delete("/skills/{skill_id}", status_code=204)
def delete_skill(skill_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    _sk(skill_admin.delete_skill, db, admin, skill_id)


@router.post("/skills/{skill_id}/prerequisites", status_code=201)
def add_prerequisite(skill_id: str, body: PrereqIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return _sk(skill_admin.add_prerequisite, db, admin, skill_id, body.prerequisite_id)


@router.delete("/skills/{skill_id}/prerequisites/{prerequisite_id}", status_code=204)
def remove_prerequisite(skill_id: str, prerequisite_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    _sk(skill_admin.remove_prerequisite, db, admin, skill_id, prerequisite_id)


@router.get("/sources")
def list_sources(db: Session = Depends(get_db)):
    return skill_admin.list_sources(db)


@router.post("/sources", status_code=201)
def create_source(body: SourceIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return _sk(skill_admin.create_source, db, admin, body.title, body.author, body.url)


@router.put("/sources/{source_id}")
def update_source(source_id: str, body: SourceIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return _sk(skill_admin.update_source, db, admin, source_id, body.title, body.author, body.url)


@router.post("/lessons/{lesson_id}/sources", status_code=201)
def link_source(lesson_id: str, body: SourceLinkIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return _sk(skill_admin.link_source, db, admin, lesson_id, body.source_id, body.locator, body.note)


@router.delete("/lesson-sources/{link_id}", status_code=204)
def unlink_source(link_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    _sk(skill_admin.unlink_source, db, admin, link_id)


@router.post("/lessons", status_code=201)
def create_lesson(body: LessonCreateIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return _do(lesson_admin.create_lesson, db, admin, body.title, body.objectives, body.block_title, body.paragraphs)


@router.post("/lessons/reorder")
def reorder_lessons(body: ReorderIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {"order": _do(lesson_admin.reorder, db, admin, body.lesson_ids)}


@router.delete("/lessons/{lesson_id}")
def delete_lesson(lesson_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return _do(lesson_admin.delete_lesson, db, admin, lesson_id)


@router.post("/lessons/{lesson_id}/restore")
def restore_lesson(lesson_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return _do(lesson_admin.restore_lesson, db, admin, lesson_id)


@router.post("/lessons/{lesson_id}/blocks", status_code=201)
def add_block(lesson_id: str, body: BlockCreateIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return _do(lesson_admin.add_block, db, admin, lesson_id, body.title, body.paragraphs)


@router.put("/lessons/{lesson_id}")
def update_lesson_meta(lesson_id: str, body: LessonMetaIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return _do(lesson_admin.update_lesson_meta, db, admin, lesson_id, body.title, body.objectives, body.reset)


@router.delete("/lessons/{lesson_id}/blocks/{block_id}")
def delete_block(lesson_id: str, block_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return _do(lesson_admin.delete_block, db, admin, lesson_id, block_id)


@router.post("/lessons/{lesson_id}/blocks/reorder")
def reorder_blocks(lesson_id: str, body: BlockOrderIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {"order": _do(lesson_admin.reorder_blocks, db, admin, lesson_id, body.block_ids)}


@router.get("/import/template")
def import_template():
    # Trả JSON để trang Quản trị dùng chung apiCall (có token); trình duyệt tự dựng file tải về.
    return {"filename": "mau-nhap-noi-dung.yaml", "content": content_import.TEMPLATE}


@router.post("/import")
async def import_content(file: UploadFile = File(...), dry_run: bool = Form(default=False),
                         admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """FR-ADM-39: nhập bài/khối/câu/nguồn từ JSON hoặc YAML. dry_run=true chỉ kiểm và báo sẽ đổi gì."""
    name = file.filename or "noi-dung.yaml"
    if not name.lower().endswith((".json", ".yaml", ".yml")):
        raise AppError(422, "IMPORT_TYPE", "Chỉ nhận file .json, .yaml hoặc .yml.")
    raw = await file.read(content_import.MAX_BYTES + 1)
    return _do(content_import.import_content, db, admin, raw, name, dry_run)


@router.get("/lessons/{lesson_id}/exercises")
def list_exercises(lesson_id: str, db: Session = Depends(get_db)):
    return _do(lesson_admin.list_exercises, db, lesson_id)


@router.post("/lessons/{lesson_id}/exercises", status_code=201)
def add_exercise(lesson_id: str, body: dict[str, Any], admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return _do(lesson_admin.add_exercise, db, admin, lesson_id, body)


@router.put("/exercises/{exercise_id}")
def update_exercise(exercise_id: str, body: dict[str, Any], admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return _do(lesson_admin.update_exercise, db, admin, exercise_id, body)


@router.delete("/exercises/{exercise_id}")
def retire_exercise(exercise_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return _do(lesson_admin.retire_exercise, db, admin, exercise_id)


# --- người dùng ---------------------------------------------------------------------------------

class UserPatchIn(BaseModel):
    is_active: bool | None = None
    role: str | None = Field(default=None, pattern="^(admin|learner)$")


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
    """Khóa/mở khóa tài khoản và đổi vai trò (ADR-036, Phúc 7A). Không tự khóa và không tự đổi vai trò của mình, nên
    hệ thống luôn còn ít nhất người đang thao tác là Quản trị viên. Mọi thay đổi ghi nhật ký."""
    target = db.get(User, user_id)
    if target is None or target.is_synthetic or target.email is None:
        raise AppError(404, "USER_NOT_FOUND", "Không có người dùng này.")
    if body.is_active is None and body.role is None:
        raise AppError(422, "NOTHING_TO_CHANGE", "Không có gì để đổi.")
    if target.id == admin.id:
        if body.is_active is False:
            raise AppError(409, "CANNOT_LOCK_SELF", "Bạn không thể tự khóa tài khoản của mình.")
        if body.role is not None and body.role != admin.role:
            raise AppError(409, "CANNOT_CHANGE_OWN_ROLE", "Bạn không thể tự đổi vai trò của mình. Nhờ Quản trị viên khác.")
    if body.is_active is not None and body.is_active != target.is_active:
        target.is_active = body.is_active
        content_service.audit(db, admin, "user.unlock" if body.is_active else "user.lock", "user", target.id)
    if body.role is not None and body.role != target.role:
        content_service.audit(db, admin, "user.role", "user", target.id, {"from": target.role, "to": body.role})
        target.role = body.role
    db.commit()
    return {"id": target.id, "is_active": target.is_active, "role": target.role}


# --- thống kê và nhật ký --------------------------------------------------------------------------

@router.get("/stats")
def stats(days: int = Query(30, ge=7, le=90), db: Session = Depends(get_db)):
    return stats_service.overview(db, days=days)


@router.get("/audit")
def audit_log(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    rows = db.scalars(select(AdminAuditLog).order_by(AdminAuditLog.id.desc()).limit(limit)).all()
    return [{"id": r.id, "actor_id": r.actor_id, "action": r.action, "target_type": r.target_type, "target_id": r.target_id,
             "detail": r.detail, "created_at": r.created_at} for r in rows]


# --- AI tóm tắt tài liệu thành bản nháp (ADR-025) ------------------------------------------------------
# Bản nháp bài dài hơn câu trả lời của Tutor nên cho Gemini chờ lâu hơn (60 giây).

_draft_provider_cache: dict[tuple, LLMProvider | None] = {}


def draft_provider_dep() -> LLMProvider | None:
    """Tách thành dependency để test thay bằng FakeProvider, không gọi mạng. Công tắc AI tắt (ADR-036) → None."""
    if not ai_switch.switch_on():
        return None
    key = (settings.ai_enabled, bool(settings.gemini_api_key), settings.gemini_model)
    if key not in _draft_provider_cache:
        _draft_provider_cache[key] = get_provider(dc_replace(settings, ai_timeout_seconds=max(settings.ai_timeout_seconds, 60.0)))
    return _draft_provider_cache[key]


class DraftIn(BaseModel):
    page_from: int = Field(ge=1)
    page_to: int = Field(ge=1)
    topic: str | None = Field(default=None, max_length=200)


class DraftEditIn(BaseModel):
    title: str = Field(max_length=200)
    objectives: list[str] = Field(default_factory=list, max_length=6)
    blocks: list[dict[str, Any]] = Field(default_factory=list, max_length=8)
    questions: list[dict[str, Any]] = Field(default_factory=list, max_length=20)
    expansion: bool | None = None
    # ADR-033: id các cờ (trang sai, bám nguồn, chép nguyên văn, hình...) Quản trị viên đã đối chiếu. None = giữ như cũ.
    acknowledged_flags: list[str] | None = Field(default=None, max_length=200)


@router.get("/ai/status")
def ai_status(provider: LLMProvider | None = Depends(draft_provider_dep)):
    # ADR-036: env_ready = .env có AI_ENABLED + khóa; switch_on = công tắc Quản trị viên. AI chạy khi cả hai cùng bật.
    return {"enabled": provider is not None, "env_ready": bool(settings.ai_enabled and settings.gemini_api_key),
            "switch_on": ai_switch.switch_on()}


class AiSwitchIn(BaseModel):
    on: bool


@router.put("/ai/switch")
def set_ai_switch(body: AiSwitchIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """FR-ADM-AI-04 (Phúc 8A): bật/tắt mọi lệnh gọi Gemini. Chỉ lưu cờ; khóa API vẫn chỉ ở .env."""
    from ..db.models import AppSetting
    row = db.get(AppSetting, ai_switch.SETTING_KEY)
    if row is None:
        row = AppSetting(key=ai_switch.SETTING_KEY, value={})
        db.add(row)
    row.value, row.updated_by = {"on": body.on}, admin.id
    content_service.audit(db, admin, "ai.switch.on" if body.on else "ai.switch.off", "setting", ai_switch.SETTING_KEY)
    db.commit()
    ai_switch.reset_cache()
    return {"switch_on": body.on, "env_ready": bool(settings.ai_enabled and settings.gemini_api_key)}


@router.post("/ai/documents")
def upload_document(file: UploadFile = File(...), source_title: str = Form(...), source_note: str | None = Form(default=None),
                    consent: bool = Form(default=False), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    # Đọc dư 1 byte để biết tệp vượt giới hạn mà không nạp cả tệp khổng lồ vào bộ nhớ.
    data = file.file.read(relevance_config().max_bytes + 1)
    try:
        doc = ai_service.add_document(db, admin, file.filename or "tai-lieu", data, source_title, source_note, consent)
    except AdminContentError as exc:
        raise _wrap(exc) from exc
    return ai_service.document_info(doc)


class PasteIn(BaseModel):
    text: str
    source_title: str = Field(max_length=300)
    source_note: str | None = Field(default=None, max_length=300)
    consent: bool = False


@router.post("/ai/documents/text")
def paste_document(body: PasteIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        doc = ai_service.add_pasted_text(db, admin, body.text, body.source_title, body.source_note, body.consent)
    except AdminContentError as exc:
        raise _wrap(exc) from exc
    return ai_service.document_info(doc)


@router.get("/ai/documents")
def list_documents(status: str | None = Query(default=None, pattern="^(accepted|pending)$"), db: Session = Depends(get_db)):
    query = select(SourceDocument).where(SourceDocument.deleted_at.is_(None))
    if status:
        query = query.where(SourceDocument.relevance_status == status)
    rows = db.scalars(query.order_by(SourceDocument.created_at.desc()).limit(50)).all()
    return [ai_service.document_info(d) for d in rows]


class ReviewIn(BaseModel):
    decision: str = Field(pattern="^(approve|reject)$")
    note: str | None = Field(default=None, max_length=300)


@router.post("/ai/documents/{doc_id}/review")
def review_document(doc_id: str, body: ReviewIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        doc = ai_service.review_document(db, admin, doc_id, body.decision, body.note)
    except AdminContentError as exc:
        raise _wrap(exc) from exc
    return ai_service.document_info(doc)


@router.post("/ai/documents/{doc_id}/draft")
def make_draft(doc_id: str, body: DraftIn, admin: User = Depends(require_admin), db: Session = Depends(get_db),
               provider: LLMProvider | None = Depends(draft_provider_dep)):
    try:
        draft = ai_service.generate_draft(db, admin, provider, doc_id, body.page_from, body.page_to, body.topic)
    except AdminContentError as exc:
        raise _wrap(exc) from exc
    return ai_service.draft_view(db, draft)


# --- Tóm tắt CẢ tài liệu, chạy nền (ADR-029) -------------------------------------------------------------------

def job_starter_dep():
    """Chạy nền bằng luồng; test thay bằng hàm chạy đồng bộ để kết quả không phụ thuộc thời gian."""
    return lambda job_id, provider: ai_job.start_job(job_id, provider, SessionLocal)


@router.post("/ai/documents/{doc_id}/summarize")
def summarize_document(doc_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db),
                       provider: LLMProvider | None = Depends(draft_provider_dep), start=Depends(job_starter_dep)):
    """Bỏ chọn trang (Phúc 18/11/2026): AI tóm tắt toàn bộ tài liệu, chia theo chương, mỗi phần một bản nháp."""
    try:
        job = ai_job.create_job(db, admin, provider, doc_id)
    except AdminContentError as exc:
        raise _wrap(exc) from exc
    if job.status == "running":
        start(job.id, provider)
    db.expire_all()
    return ai_job.job_view(db, ai_job.get_job(db, job.id))


@router.get("/ai/jobs")
def list_jobs(db: Session = Depends(get_db)):
    return ai_job.latest_jobs(db)


@router.get("/ai/jobs/{job_id}")
def read_job(job_id: str, db: Session = Depends(get_db)):
    try:
        return ai_job.job_view(db, ai_job.get_job(db, job_id))
    except AdminContentError as exc:
        raise _wrap(exc) from exc


@router.post("/ai/jobs/{job_id}/resume")
def resume_job(job_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db),
               provider: LLMProvider | None = Depends(draft_provider_dep), start=Depends(job_starter_dep)):
    try:
        job = ai_job.resume_job(db, admin, provider, job_id)
    except AdminContentError as exc:
        raise _wrap(exc) from exc
    start(job.id, provider)
    db.expire_all()
    return ai_job.job_view(db, ai_job.get_job(db, job_id))


@router.post("/ai/jobs/{job_id}/cancel")
def cancel_job(job_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        return ai_job.job_view(db, ai_job.cancel_job(db, admin, job_id))
    except AdminContentError as exc:
        raise _wrap(exc) from exc


class MoreQuestionsIn(BaseModel):
    kinds: list[str] = Field(default_factory=list, max_length=7)


@router.post("/ai/drafts/{draft_id}/questions")
def more_questions(draft_id: str, body: MoreQuestionsIn, admin: User = Depends(require_admin), db: Session = Depends(get_db),
                   provider: LLMProvider | None = Depends(draft_provider_dep)):
    """AI soạn thêm câu luyện tập cho bản nháp (ADR-028); câu mới vẫn chờ Quản trị viên duyệt rồi mới xuất bản."""
    try:
        return ai_service.draft_view(db, ai_service.generate_more_questions(db, admin, provider, draft_id, body.kinds))
    except AdminContentError as exc:
        raise _wrap(exc) from exc


@router.get("/ai/drafts")
def list_drafts(db: Session = Depends(get_db)):
    return ai_service.list_drafts(db)


@router.get("/ai/drafts/{draft_id}")
def get_draft(draft_id: str, db: Session = Depends(get_db)):
    try:
        return ai_service.draft_view(db, ai_service._draft(db, draft_id))
    except AdminContentError as exc:
        raise _wrap(exc) from exc


@router.put("/ai/drafts/{draft_id}")
def edit_draft(draft_id: str, body: DraftEditIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        return ai_service.draft_view(db, ai_service.update_draft(db, admin, draft_id, body.model_dump()))
    except AdminContentError as exc:
        raise _wrap(exc) from exc


@router.post("/ai/drafts/{draft_id}/publish")
def publish_ai_draft(draft_id: str, body: PublishIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        lesson = ai_service.publish_draft(db, admin, draft_id, body.acknowledge_engine_flags)
    except AdminContentError as exc:
        raise _wrap(exc) from exc
    return {"lesson_id": lesson.id, "title": lesson.title}


@router.post("/ai/drafts/{draft_id}/reject")
def reject_ai_draft(draft_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        ai_service.reject_draft(db, admin, draft_id)
    except AdminContentError as exc:
        raise _wrap(exc) from exc
    return {"id": draft_id, "status": "rejected"}
