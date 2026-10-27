from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import Session

from ..db.models import (
    Attempt,
    AttemptError,
    Exercise,
    ExerciseVersion,
    Lesson,
    LessonProgress,
    ReviewAttempt,
    ReviewItem,
    ReviewState,
    User,
)
from ..content import versioning
from .grading_service import GradeOutcome, grade_payload, is_self_check
from .review_scheduler import activate_lesson_reviews, apply_review_result


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Sai 2 lần thì hiện lời giải: đủ để người học tự thử lại, chưa đến mức bỏ cuộc.
EXPLANATION_AFTER_WRONG = 2


class LessonNotMastered(Exception):
    """Còn câu chưa từng trả lời đúng nên chưa thể hoàn thành bài."""

    def __init__(self, remaining: list[str]):
        super().__init__("LESSON_NOT_MASTERED")
        self.remaining = remaining


def require_user(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise LookupError("USER_NOT_FOUND")
    return user


class ExerciseVersionSuperseded(Exception):
    """Người học gửi bài vào phiên bản đã bị thay (trang cũ còn mở); không chấm theo đề cũ nữa (ADR-006)."""

    def __init__(self, version_id: str, current_version_id: str):
        super().__init__("EXERCISE_VERSION_SUPERSEDED")
        self.version_id = version_id
        self.current_version_id = current_version_id


def require_exercise_version(db: Session, version_id: str) -> tuple[ExerciseVersion, Exercise]:
    version = db.get(ExerciseVersion, version_id)
    statuses = versioning.visible_statuses()
    if version is None or version.status not in statuses:
        raise LookupError("EXERCISE_VERSION_NOT_FOUND")
    exercise = db.get(Exercise, version.exercise_id)
    current = versioning.current_version(exercise, statuses) if exercise is not None else None
    if current is None:
        # Câu đã xóa mềm, hoặc bản hiện hành không có ảnh chụp hợp lệ: không hiển thị và không chấm.
        raise LookupError("EXERCISE_NOT_FOUND")
    if current.id != version.id:
        raise ExerciseVersionSuperseded(version.id, current.id)
    return version, exercise


def wrong_attempt_count(db: Session, user_id: str, exercise_id: str) -> int:
    return len(db.scalars(
        select(Attempt.id)
        .join(ExerciseVersion, ExerciseVersion.id == Attempt.exercise_version_id)
        .where(Attempt.user_id == user_id, ExerciseVersion.exercise_id == exercise_id, Attempt.correct.is_(False))
    ).all())


def submit_attempt(db: Session, user_id: str, version_id: str, answer,
                   input_method: str = "text") -> tuple[Attempt, GradeOutcome]:
    require_user(db, user_id)
    version, exercise = require_exercise_version(db, version_id)
    # Cách chấm lấy từ ảnh chụp của phiên bản, không lấy từ exercises (HM-003: bản cũ rubric từng bị chấm bằng exact).
    outcome = grade_payload(version.grading_strategy, version.answer_key, version.grader_config, answer,
                            input_method=input_method)
    attempt = Attempt(
        id=str(uuid4()), user_id=user_id, exercise_version_id=version.id, answer=answer,
        correct=outcome.correct, score=outcome.score, primary_error=outcome.primary_error,
        feedback=outcome.feedback,
    )
    db.add(attempt)
    db.flush()
    for error in outcome.errors:
        code = error.get("code", "UNKNOWN")
        db.add(AttemptError(attempt_id=attempt.id, code=code, detail={k: v for k, v in error.items() if k != "code"}))
    db.commit()
    return attempt, outcome


def complete_lesson(db: Session, user_id: str, lesson_id: str) -> tuple[LessonProgress, list[ReviewState]]:
    require_user(db, user_id)
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise LookupError("LESSON_NOT_FOUND")
    now = utcnow()
    _insert_progress_if_missing(db, user_id, lesson_id, now)
    # Khóa dòng tiến độ: các lượt "Hoàn thành" song song chạy lần lượt, nên thẻ ôn không bị chèn trùng (HM-010).
    progress = db.scalar(select(LessonProgress).where(
        LessonProgress.user_id == user_id,
        LessonProgress.lesson_id == lesson_id,
    ).with_for_update())
    if progress.status != "completed":
        # Hoàn thành = mỗi câu đã đúng ít nhất một lần; chỉ "đã thử" thì gõ bừa cũng qua bài.
        correct_ids = set(db.scalars(
            select(ExerciseVersion.exercise_id)
            .join(Attempt, Attempt.exercise_version_id == ExerciseVersion.id)
            .where(Attempt.user_id == user_id, Attempt.correct.is_(True))
        ).all())
        # Chỉ tính câu đang hiện cho người học; đúng ở bất kỳ phiên bản nào của câu cũng được tính (6A).
        remaining = [e.id for e in sorted(lesson.exercises, key=lambda e: e.position)
                     if versioning.current_version(e) is not None and e.id not in correct_ids]
        if remaining:
            db.rollback()
            raise LessonNotMastered(remaining)
        progress.status = "completed"
        progress.completed_at = now
    # Bài đã hoàn thành thì giữ nguyên completed_at: bấm lại không được viết lại lịch sử học.
    states = activate_lesson_reviews(db, user_id, lesson_id, now)
    db.commit()
    return progress, states


def answer_review(db: Session, user_id: str, review_item_id: str, answer, rating: str, response_time_ms: int | None):
    require_user(db, user_id)
    item = db.get(ReviewItem, review_item_id)
    if item is None:
        raise LookupError("REVIEW_ITEM_NOT_FOUND")
    state = db.scalar(select(ReviewState).where(
        ReviewState.user_id == user_id,
        ReviewState.review_item_id == review_item_id,
    ))
    if state is None:
        raise LookupError("REVIEW_STATE_NOT_ACTIVE")
    if is_self_check(item.grading_strategy, item.grader_config) and rating != "auto":
        # Thẻ ý mở: người học lật thẻ rồi tự đánh giá, máy không đoán nghĩa câu tự luận.
        correct = rating != "again"
        outcome = GradeOutcome(correct, 1.0 if correct else 0.0, None if correct else "SELF_REPORTED_MISS",
                               f"Đáp án: {item.back}", [])
    else:
        outcome = grade_payload(item.grading_strategy, item.answer_key, item.grader_config, answer)
        if not outcome.correct:
            # Ôn tập khác bài kiểm tra: sai thì cho xem đáp án ngay để lần sau nhớ đúng.
            outcome.feedback = f"Đáp án: {item.back}."
    applied = apply_review_result(state, outcome.correct, rating)
    review_attempt = ReviewAttempt(
        id=str(uuid4()), review_state_id=state.id, answer=answer, correct=outcome.correct,
        rating=applied, response_time_ms=response_time_ms,
    )
    db.add(review_attempt)
    db.commit()
    return review_attempt, state, item, outcome, applied


def start_lesson(db: Session, user_id: str, lesson_id: str) -> LessonProgress:
    require_user(db, user_id)
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise LookupError("LESSON_NOT_FOUND")
    # Frontend có thể gọi start nhiều lần cùng lúc (StrictMode, mở lại bài); "đọc rồi thêm" sẽ đụng
    # uq_user_lesson_progress trên PostgreSQL (HM-010), nên chèn kiểu "có rồi thì bỏ qua".
    _insert_progress_if_missing(db, user_id, lesson_id, utcnow())
    db.commit()
    return db.scalar(select(LessonProgress).where(
        LessonProgress.user_id == user_id,
        LessonProgress.lesson_id == lesson_id,
    ))


def _insert_progress_if_missing(db: Session, user_id: str, lesson_id: str, now: datetime) -> None:
    """Tạo dòng tiến độ "started" nếu chưa có; dòng đã có (kể cả đã hoàn thành) giữ nguyên."""
    values = dict(user_id=user_id, lesson_id=lesson_id, status="started", started_at=now)
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        insert = postgresql.insert
    elif dialect == "sqlite":
        insert = sqlite.insert
    else:  # dự án chỉ chạy PostgreSQL (Docker) và SQLite (dev/test)
        raise RuntimeError(f"Chưa hỗ trợ chèn tiến độ an toàn cho CSDL {dialect}")
    db.execute(insert(LessonProgress).values(**values)
               .on_conflict_do_nothing(index_elements=["user_id", "lesson_id"]))


def learning_overview(db: Session, user_id: str) -> dict:
    require_user(db, user_id)
    lessons = db.scalars(select(Lesson).order_by(Lesson.order_index)).unique().all()
    progresses = {p.lesson_id: p for p in db.scalars(select(LessonProgress).where(LessonProgress.user_id == user_id)).all()}

    attempt_rows = db.execute(
        select(Attempt, ExerciseVersion, Exercise)
        .join(ExerciseVersion, ExerciseVersion.id == Attempt.exercise_version_id)
        .join(Exercise, Exercise.id == ExerciseVersion.exercise_id)
        .where(Attempt.user_id == user_id)
        .order_by(Attempt.created_at)
    ).all()
    by_lesson: dict[str, list[tuple[Attempt, ExerciseVersion, Exercise]]] = {}
    for attempt, version, exercise in attempt_rows:
        by_lesson.setdefault(exercise.lesson_id, []).append((attempt, version, exercise))

    now = utcnow()
    review_states = db.scalars(select(ReviewState).where(
        ReviewState.user_id == user_id, ReviewState.status == "active"
    )).all()

    def aware(value: datetime) -> datetime:
        # SQLite may deserialize timezone=True columns as naive datetimes. Normalize before
        # Python-side comparisons; PostgreSQL keeps the original offset-aware value.
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)

    due_reviews = sum(1 for state in review_states if aware(state.due_at) <= now)
    upcoming_reviews = len(review_states) - due_reviews

    lesson_rows = []
    for lesson in lessons:
        active_exercises = [exercise for exercise in lesson.exercises if versioning.current_version(exercise) is not None]
        rows = by_lesson.get(lesson.id, [])
        attempted_ids = sorted({exercise.id for _, _, exercise in rows})
        correct_ids = sorted({exercise.id for attempt, _, exercise in rows if attempt.correct})
        progress = progresses.get(lesson.id)
        status = progress.status if progress is not None else "not_started"
        exercise_count = len(active_exercises)
        attempted_count = len(attempted_ids)
        practice_percent = 0 if exercise_count == 0 else round(attempted_count / exercise_count * 100)
        if status == "completed":
            practice_percent = 100
        lesson_rows.append({
            "lesson_id": lesson.id,
            "order": lesson.order_index,
            "title": lesson.title,
            "track": lesson.track,
            "status": status,
            "started_at": progress.started_at if progress else None,
            "completed_at": progress.completed_at if progress else None,
            "exercise_count": exercise_count,
            "attempted_exercises": attempted_count,
            "correct_exercises": len(correct_ids),
            "attempt_count": len(rows),
            "correct_attempt_count": sum(1 for attempt, _, _ in rows if attempt.correct),
            "practice_progress_percent": practice_percent,
            "attempted_exercise_ids": attempted_ids,
            "correct_exercise_ids": correct_ids,
        })

    return {
        "user_id": user_id,
        "total_lessons": len(lessons),
        "started_lessons": sum(1 for row in lesson_rows if row["status"] in {"started", "completed"}),
        "completed_lessons": sum(1 for row in lesson_rows if row["status"] == "completed"),
        "due_reviews": due_reviews,
        "upcoming_reviews": upcoming_reviews,
        "lessons": lesson_rows,
    }
