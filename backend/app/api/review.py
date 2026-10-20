from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..contracts.learning import ReviewAnswerIn, ReviewAnswerOut, ReviewStateOut
from ..auth.deps import get_current_user
from ..db.models import ReviewItem, ReviewState, User
from ..db.session import get_db
from ..services.grading_service import is_self_check
from ..services.learning_service import answer_review
from ..services.review_scheduler import leitner_box

# ADR-002: mỗi lượt ôn tối đa 20 thẻ, quá hạn lâu nhất lên trước.
DUE_QUEUE_LIMIT = 20

router = APIRouter(prefix="/api/v1/review", tags=["review"])


@router.get("/due", response_model=list[ReviewStateOut])
def due_reviews(
    user: User = Depends(get_current_user),
    include_future: bool = Query(False, description="Debug/MVP flag: include active future cards."),
    db: Session = Depends(get_db),
):
    stmt = select(ReviewState, ReviewItem).join(ReviewItem, ReviewItem.id == ReviewState.review_item_id).where(
        ReviewState.user_id == user.id,
        ReviewState.status == "active",
    )
    if not include_future:
        stmt = stmt.where(ReviewState.due_at <= datetime.now(timezone.utc))
    stmt = stmt.order_by(ReviewState.due_at, ReviewItem.id)
    if not include_future:
        stmt = stmt.limit(DUE_QUEUE_LIMIT)
    rows = db.execute(stmt).all()
    out = []
    for state, item in rows:
        self_check = is_self_check(item.grading_strategy, item.grader_config)
        out.append(ReviewStateOut(
            review_item_id=item.id, lesson_id=item.lesson_id, front=item.front, mode=item.mode,
            skill_id=item.skill_id, stage=state.stage, interval_days=state.interval_days,
            due_at=state.due_at, status=state.status, leitner_box=leitner_box(state.stage),
            self_check=self_check, back=item.back if self_check else None,
        ))
    return out


@router.post("/{review_item_id}/answer", response_model=ReviewAnswerOut)
def submit_review_answer(review_item_id: str, body: ReviewAnswerIn, user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    try:
        review_attempt, state, item, outcome, applied = answer_review(
            db, user.id, review_item_id, body.answer, body.rating, body.response_time_ms,
        )
    except LookupError as exc:
        code = str(exc)
        status = 409 if code == "REVIEW_STATE_NOT_ACTIVE" else 404
        raise HTTPException(status_code=status, detail={"code": code}) from exc
    return ReviewAnswerOut(
        review_attempt_id=review_attempt.id, review_item_id=item.id, correct=outcome.correct,
        rating_applied=applied, next_stage=state.stage, interval_days=state.interval_days,
        next_due_at=state.due_at, feedback=outcome.feedback, leitner_box=leitner_box(state.stage),
    )
