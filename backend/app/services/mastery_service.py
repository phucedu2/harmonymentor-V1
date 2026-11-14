"""Cập nhật mastery trong CÙNG giao dịch với lượt làm / lượt ôn / bài kiểm tra đầu vào.

Hàm ở đây không commit: người gọi (learning_service) commit một lần, nên không có lượt làm nào
được ghi mà mastery không đổi theo, hoặc ngược lại.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..ai import mastery as m
from ..ai.skill_mapping import is_mvp
from ..db.models import (
    Attempt,
    Exercise,
    ExerciseVersion,
    MasteryEvent,
    MasteryState,
    PlacementResult,
    ReviewAttempt,
    ReviewItem,
    ReviewState,
)
from .grading_service import is_self_check


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _state(db: Session, user_id: str, skill_id: str) -> MasteryState | None:
    return db.scalar(select(MasteryState).where(MasteryState.user_id == user_id, MasteryState.skill_id == skill_id))


def _apply(db: Session, *, user_id: str, skill_id: str, source: str, source_id: str, result: float | None,
           now: datetime, error_code: str | None = None, set_to: float | None = None) -> MasteryState:
    """Ghi một sự kiện. result=None: tăng attempts_count nhưng giữ điểm (đúng lặp lại)."""
    state = _state(db, user_id, skill_id)
    if state is None:
        state = MasteryState(user_id=user_id, skill_id=skill_id, score=0.0, attempts_count=0)
        db.add(state)
        before = None
    else:
        before = state.score
    old = state.score or 0.0
    if set_to is not None:
        new = set_to
    elif result is not None:
        new = m.ema(old, result)
    else:
        new = old
    state.score = new
    state.attempts_count = (state.attempts_count or 0) + 1
    if error_code is not None:
        state.last_error_code = error_code
    state.updated_at = now
    db.add(MasteryEvent(user_id=user_id, skill_id=skill_id, source=source, source_id=source_id,
                        result=set_to if set_to is not None else result,
                        counted=result is not None or set_to is not None,
                        score_before=before, score_after=new, vn_day=m.vn_day(now), created_at=now))
    db.flush()
    return state


def record_attempt(db: Session, attempt: Attempt, exercise_id: str, skill_id: str, now: datetime) -> None:
    if attempt.is_test or not is_mvp(skill_id):
        return  # S11 (post_mvp không tạo dòng), S13 (is_test không tính)
    history = [c for (c,) in db.execute(
        select(Attempt.correct)
        .join(ExerciseVersion, ExerciseVersion.id == Attempt.exercise_version_id)
        .where(Attempt.user_id == attempt.user_id, ExerciseVersion.exercise_id == exercise_id,
               Attempt.is_test.is_(False), Attempt.id != attempt.id, Attempt.created_at <= attempt.created_at)
        .order_by(Attempt.created_at, Attempt.id)
    )]
    _apply(db, user_id=attempt.user_id, skill_id=skill_id, source="attempt", source_id=attempt.id,
           result=m.exercise_result(history, attempt.correct), now=now,
           error_code=None if attempt.correct else (attempt.primary_error or "WRONG"))


def _counted_review_today(db: Session, user_id: str, skill_id: str, day: str) -> bool:
    return db.scalar(select(MasteryEvent.id).where(
        MasteryEvent.user_id == user_id, MasteryEvent.skill_id == skill_id, MasteryEvent.source == "review",
        MasteryEvent.counted.is_(True), MasteryEvent.vn_day == day).limit(1)) is not None


def record_review(db: Session, *, user_id: str, item: ReviewItem, review_attempt_id: str, correct: bool,
                  due_before: datetime, now: datetime) -> None:
    """Luật 2A. `due_before` là ngày hẹn TRƯỚC khi áp kết quả Leitner."""
    if not is_mvp(item.skill_id):
        return
    counts = m.review_counts(self_check=is_self_check(item.grading_strategy, item.grader_config),
                             due_at=_aware(due_before), now=now,
                             already_counted_today=_counted_review_today(db, user_id, item.skill_id, m.vn_day(now)))
    if counts:
        _apply(db, user_id=user_id, skill_id=item.skill_id, source="review", source_id=review_attempt_id,
               result=m.review_result(correct), now=now, error_code=None if correct else "REVIEW_MISS")


def apply_placement(db: Session, user_id: str, graded: list[dict], now: datetime) -> None:
    """UC-06: đúng → 0,65, sai → 0; câu không trả lời: chưa đánh giá.

    Kỹ năng đã có lịch sử học thật thì giữ nguyên: làm lại bài kiểm tra không được xóa kết quả học.
    """
    for row in graded:
        skill_id = row["skill_id"]
        if not is_mvp(skill_id):
            continue
        learned = db.scalar(select(MasteryEvent.id).where(
            MasteryEvent.user_id == user_id, MasteryEvent.skill_id == skill_id,
            MasteryEvent.source != "placement").limit(1))
        if learned is not None:
            continue
        _apply(db, user_id=user_id, skill_id=skill_id, source="placement", source_id=row["exercise_version_id"],
               result=None, set_to=m.PLACEMENT_SCORE if row["correct"] else 0.0, now=now)


def rebuild_user(db: Session, user_id: str) -> dict[str, tuple[float, int]]:
    """Tính lại mastery của một người từ lịch sử thật (placement → attempts → review_attempts theo thời gian).

    Tất định: cùng lịch sử luôn cho cùng kết quả. Xóa rồi ghi lại mastery_states/mastery_events của người đó.
    """
    db.execute(delete(MasteryEvent).where(MasteryEvent.user_id == user_id))
    db.execute(delete(MasteryState).where(MasteryState.user_id == user_id))
    db.flush()
    timeline: list[tuple[datetime, int, str, object]] = []
    placement = db.get(PlacementResult, user_id)
    if placement is not None and placement.status == "completed":
        timeline.append((_aware(placement.completed_at), 0, "placement", placement))
    for attempt, exercise_id, skill_id in db.execute(
        select(Attempt, ExerciseVersion.exercise_id, Exercise.skill_id)
        .join(ExerciseVersion, ExerciseVersion.id == Attempt.exercise_version_id)
        .join(Exercise, Exercise.id == ExerciseVersion.exercise_id)
        .where(Attempt.user_id == user_id)
    ).all():
        timeline.append((_aware(attempt.created_at), 1, attempt.id, (attempt, exercise_id, skill_id)))
    review_rows = db.execute(
        select(ReviewAttempt, ReviewItem)
        .join(ReviewState, ReviewState.id == ReviewAttempt.review_state_id)
        .join(ReviewItem, ReviewItem.id == ReviewState.review_item_id)
        .where(ReviewState.user_id == user_id)
    ).all()
    for review_attempt, item in review_rows:
        timeline.append((_aware(review_attempt.created_at), 2, review_attempt.id, (review_attempt, item)))
    timeline.sort(key=lambda t: (t[0], t[1], t[2]))
    for moment, kind, _, payload in timeline:
        if kind == 0:
            apply_placement(db, user_id, payload.answers, moment)
        elif kind == 1:
            attempt, exercise_id, skill_id = payload
            record_attempt(db, attempt, exercise_id, skill_id, moment)
        else:
            review_attempt, item = payload
            if review_attempt.due_before is None:
                continue  # lượt ôn trước GĐ1 không lưu ngày hẹn cũ: không đoán, không tính
            record_review(db, user_id=user_id, item=item, review_attempt_id=review_attempt.id,
                          correct=review_attempt.correct, due_before=review_attempt.due_before, now=moment)
    return {s.skill_id: (round(s.score, 9), s.attempts_count)
            for s in db.scalars(select(MasteryState).where(MasteryState.user_id == user_id))}
