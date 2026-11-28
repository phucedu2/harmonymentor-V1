from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..contracts.learning import (
    CompleteLessonOut,
    ExerciseOut,
    LessonBlockOut,
    LessonDetailOut,
    LessonSummaryOut,
    ReviewItemOut,
    SourceRefOut,
    StartLessonOut,
)
from ..auth.deps import get_current_user
from ..content.external_resources import resources_for
from ..content.versioning import block_visible, current_version, lesson_visible
from ..db.models import Lesson, LessonSource, SourceWork, User
from ..db.session import get_db
from ..content.overrides import effective_blocks, lesson_hidden
from ..core.errors import AppError
from ..services.grading_service import allowed_input_methods
from ..services.mastery_service import counts_for_mastery
from ..services.quiz_service import AI_TRACK
from ..services.learning_service import (
    LessonHasNoExercises,
    LessonNotMastered,
    complete_lesson,
    display_order,
    start_lesson,
    visible_lessons,
)

router = APIRouter(prefix="/api/v1/lessons", tags=["lessons"])


def _visible_blocks(lesson: Lesson, db: Session) -> list:
    """(khối, payload hiệu lực): payload gốc, hoặc bản sửa đã xuất bản của Quản trị viên (ADR-023)."""
    return [(b, payload) for b, payload in effective_blocks(db, lesson) if block_visible(payload)]


def _summary(lesson: Lesson, order: int, db: Session) -> LessonSummaryOut:
    versions = [v for v in (current_version(x) for x in lesson.exercises) if v is not None]
    ai_generated = lesson.track == AI_TRACK
    return LessonSummaryOut(
        id=lesson.id, order=order, track=lesson.track, title=lesson.title,
        status=lesson.status, objectives=lesson.objectives or [], block_count=len(_visible_blocks(lesson, db)),
        exercise_count=len(versions),
        review_item_count=len([r for r in lesson.review_items if r.deleted_at is None]),
        ai_generated=ai_generated,
        # Bài "Mở rộng" khi xuất bản đã ghi counts_for_mastery=false vào mọi câu; suy từ đó, không cần cột mới.
        expansion=ai_generated and bool(versions) and all(not counts_for_mastery(v.grader_config) for v in versions),
        published_at=lesson.created_at if ai_generated else None,
    )


@router.get("", response_model=list[LessonSummaryOut])
def list_lessons(db: Session = Depends(get_db)):
    lessons = visible_lessons(db)
    orders = display_order(lessons)
    return [_summary(lesson, orders[lesson.id], db) for lesson in lessons]


def _preview_admin(request: Request, db: Session) -> bool:
    """?preview=1 kèm token Quản trị viên: xem bài đang ẩn đúng như học sinh sẽ thấy (ADR-033, 7B). Không phải admin thì bỏ qua."""
    try:
        return get_current_user(request, db).role == "admin"
    except AppError:
        return False


@router.get("/{lesson_id}", response_model=LessonDetailOut)
def get_lesson(lesson_id: str, request: Request, preview: bool = False, db: Session = Depends(get_db)):
    lesson = db.get(Lesson, lesson_id)
    hidden = lesson is not None and lesson_hidden(db, lesson_id)
    if lesson is None or lesson.deleted_at is not None or not lesson_visible(lesson) or (hidden and not (preview and _preview_admin(request, db))):
        raise HTTPException(status_code=404, detail={"code": "LESSON_NOT_FOUND"})

    sources = db.execute(
        select(LessonSource, SourceWork)
        .join(SourceWork, SourceWork.id == LessonSource.source_work_id)
        .where(LessonSource.lesson_id == lesson_id)
        .order_by(LessonSource.id)
    ).all()
    exercises = []
    for exercise in sorted(lesson.exercises, key=lambda x: x.position):
        version = current_version(exercise)
        if version is None:
            continue
        # Đề, lựa chọn và cách chấm lấy từ ảnh chụp của phiên bản hiện hành (ADR-006).
        exercises.append(ExerciseOut(
            id=exercise.id, version_id=version.id, version=version.version, position=exercise.position,
            kind=version.kind, prompt=version.prompt, options=version.options,
            grading_strategy=version.grading_strategy, skill_id=exercise.skill_id,
            allowed_input_methods=allowed_input_methods(version.options, version.grader_config),
        ))

    # Bài đang ẩn (Quản trị viên xem trước) không có số thứ tự trong lộ trình của học sinh.
    base = _summary(lesson, display_order(visible_lessons(db)).get(lesson.id, 0), db).model_dump()
    return LessonDetailOut(
        **base,
        blocks=[LessonBlockOut(id=b.id, position=b.position, block_type=b.block_type, payload=payload)
                for b, payload in _visible_blocks(lesson, db)],
        exercises=exercises,
        review_items=[ReviewItemOut(id=r.id, mode=r.mode, front=r.front, back=r.back, skill_id=r.skill_id)
                      for r in sorted(lesson.review_items, key=lambda x: x.id) if r.deleted_at is None],
        sources=[SourceRefOut(source_id=work.id, title=work.title, author=work.author, locator=link.locator,
                              note=link.note, url=work.url) for link, work in sources],
        external_resources=resources_for(lesson_id),
    )


@router.post("/{lesson_id}/start", response_model=StartLessonOut)
def mark_lesson_started(lesson_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        progress = start_lesson(db, user.id, lesson_id)
    except LookupError as exc:
        code = str(exc)
        raise HTTPException(status_code=404, detail={"code": code}) from exc
    return StartLessonOut(
        lesson_id=lesson_id, user_id=user.id, status=progress.status,
        started_at=progress.started_at, completed_at=progress.completed_at,
    )


@router.post("/{lesson_id}/complete", response_model=CompleteLessonOut)
def mark_lesson_complete(lesson_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        progress, states = complete_lesson(db, user.id, lesson_id)
    except LessonNotMastered as exc:
        raise AppError(409, "LESSON_NOT_MASTERED",
                       f"Còn {len(exc.remaining)} câu chưa trả lời đúng. Hãy làm đúng tất cả các câu rồi hoàn thành bài.",
                       fields={"remaining": ",".join(exc.remaining)}) from exc
    except LessonHasNoExercises as exc:
        raise AppError(409, "LESSON_HAS_NO_EXERCISES",
                       "Bài này hiện chưa có câu hỏi nào để làm, nên chưa thể hoàn thành.") from exc
    except LookupError as exc:
        code = str(exc)
        raise HTTPException(status_code=404, detail={"code": code}) from exc
    first_due = min((s.due_at for s in states), default=None)
    return CompleteLessonOut(
        lesson_id=lesson_id, user_id=user.id, status=progress.status,
        completed_at=progress.completed_at, activated_review_items=len(states), first_review_due_at=first_due,
    )
