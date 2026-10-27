from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
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
from ..content.versioning import current_version
from ..db.models import Lesson, LessonSource, SourceWork, User
from ..db.session import get_db
from ..core.errors import AppError
from ..services.learning_service import LessonNotMastered, complete_lesson, start_lesson

router = APIRouter(prefix="/api/v1/lessons", tags=["lessons"])


def _summary(lesson: Lesson) -> LessonSummaryOut:
    return LessonSummaryOut(
        id=lesson.id, order=lesson.order_index, track=lesson.track, title=lesson.title,
        status=lesson.status, objectives=lesson.objectives or [], block_count=len(lesson.blocks),
        exercise_count=len([x for x in lesson.exercises if current_version(x) is not None]),
        review_item_count=len(lesson.review_items),
    )


@router.get("", response_model=list[LessonSummaryOut])
def list_lessons(db: Session = Depends(get_db)):
    lessons = db.scalars(select(Lesson).order_by(Lesson.order_index)).unique().all()
    return [_summary(lesson) for lesson in lessons]


@router.get("/{lesson_id}", response_model=LessonDetailOut)
def get_lesson(lesson_id: str, db: Session = Depends(get_db)):
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
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
        ))

    base = _summary(lesson).model_dump()
    return LessonDetailOut(
        **base,
        blocks=[LessonBlockOut(id=b.id, position=b.position, block_type=b.block_type, payload=b.payload)
                for b in sorted(lesson.blocks, key=lambda x: x.position)],
        exercises=exercises,
        review_items=[ReviewItemOut(id=r.id, mode=r.mode, front=r.front, back=r.back, skill_id=r.skill_id)
                      for r in sorted(lesson.review_items, key=lambda x: x.id)],
        sources=[SourceRefOut(source_id=work.id, title=work.title, author=work.author, locator=link.locator,
                              note=link.note, url=work.url) for link, work in sources],
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
    except LookupError as exc:
        code = str(exc)
        raise HTTPException(status_code=404, detail={"code": code}) from exc
    first_due = min((s.due_at for s in states), default=None)
    return CompleteLessonOut(
        lesson_id=lesson_id, user_id=user.id, status=progress.status,
        completed_at=progress.completed_at, activated_review_items=len(states), first_review_due_at=first_due,
    )
