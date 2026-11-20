"""Lịch ôn Leitner 5 hộp (ADR-002, tài liệu 04 mục 6.4): hộp 1..5 = 1, 2, 4, 8, 16 ngày.

Thẻ mới đến hạn ngay. Đúng khi đến hạn lên 1 hộp (tối đa hộp 5); đúng khi chưa đến hạn giữ hộp
và ngày hẹn; sai lúc nào cũng về hộp 1, hẹn sau 1 ngày. Cột `stage` 0..4 chính là hộp - 1 nên
không cần migration. Lịch ôn độc lập với mastery: mastery cao vẫn có thể có thẻ quá hạn.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import ReviewItem, ReviewState


REVIEW_INTERVALS_DAYS = [1, 2, 4, 8, 16]


def leitner_box(stage: int) -> int:
    return stage + 1


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    # SQLite đọc lại cột timezone=True thành giờ không múi; PostgreSQL giữ nguyên.
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


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
                # 04 mục 6.4: thẻ mới đến hạn ngay để người học ôn được trong cùng buổi.
                due_at=now,
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
    elif _aware(state.due_at) > now:
        # Đúng khi chưa đến hạn (thẻ kỹ năng yếu được đưa vào sớm, hoặc bấm lại liền tay): giữ hộp
        # và ngày hẹn cũ, nếu không người học bấm "Đã nhớ" liên tục là lên hộp 5 trong vài giây.
        applied = applied if applied in ("hard", "easy") else "good"
        state.success_streak += 1
        state.last_reviewed_at = now
        return applied
    elif applied == "hard":
        # Đúng nhưng còn chật vật: giữ nguyên hộp, ôn lại sau khoảng của hộp hiện tại.
        state.interval_days = REVIEW_INTERVALS_DAYS[state.stage]
        state.success_streak += 1
    else:  # good, easy: Leitner chỉ lên đúng 1 hộp
        applied = "easy" if applied == "easy" else "good"
        state.stage = min(state.stage + 1, len(REVIEW_INTERVALS_DAYS) - 1)
        state.interval_days = REVIEW_INTERVALS_DAYS[state.stage]
        state.success_streak += 1

    state.last_reviewed_at = now
    state.due_at = now + timedelta(days=state.interval_days)
    return applied
