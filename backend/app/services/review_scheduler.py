"""Deterministic spaced-review scheduler for the MVP.

The schedule intentionally remains simple (1-3-7-14-30 days).  It is independent from mastery:
a learner can have high mastery while a review item is overdue.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import ReviewItem, ReviewState


REVIEW_INTERVALS_DAYS = [1, 3, 7, 14, 30]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def activate_lesson_reviews(db: Session, user_id: str, lesson_id: str, now: datetime | None = None) -> list[ReviewState]:
    now = now or utcnow()
    items = db.scalars(select(ReviewItem).where(ReviewItem.lesson_id == lesson_id).order_by(ReviewItem.id)).all()
    states: list[ReviewState] = []
    for item in items:
        state = db.scalar(select(ReviewState).where(
            ReviewState.user_id == user_id,
            ReviewState.review_item_id == item.id,
        ))
        if state is None:
            state = ReviewState(
                user_id=user_id,
                review_item_id=item.id,
                status="active",
                stage=0,
                interval_days=REVIEW_INTERVALS_DAYS[0],
                due_at=now + timedelta(days=REVIEW_INTERVALS_DAYS[0]),
            )
            db.add(state)
        states.append(state)
    db.flush()
    return states


def apply_review_result(state: ReviewState, correct: bool, rating: str, now: datetime | None = None) -> str:
    now = now or utcnow()
    applied = rating
    if rating == "auto":
        applied = "good" if correct else "again"

    if not correct or applied == "again":
        state.stage = 0
        state.interval_days = REVIEW_INTERVALS_DAYS[0]
        state.failure_count += 1
        state.success_streak = 0
        applied = "again"
    elif applied == "hard":
        state.interval_days = max(REVIEW_INTERVALS_DAYS[0], state.interval_days)
        state.success_streak += 1
    elif applied == "easy":
        state.stage = min(state.stage + 2, len(REVIEW_INTERVALS_DAYS) - 1)
        state.interval_days = REVIEW_INTERVALS_DAYS[state.stage]
        state.success_streak += 1
    else:  # good
        applied = "good"
        state.stage = min(state.stage + 1, len(REVIEW_INTERVALS_DAYS) - 1)
        state.interval_days = REVIEW_INTERVALS_DAYS[state.stage]
        state.success_streak += 1

    state.last_reviewed_at = now
    state.due_at = now + timedelta(days=state.interval_days)
    return applied
