from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth.deps import get_current_user
from ..contracts.practice import (
    PracticeAttemptIn,
    PracticeAttemptOut,
    PracticeHistoryItem,
    PracticeHistoryOut,
    PracticeKindStat,
)
from ..core.errors import AppError
from ..db.models import User
from ..db.session import get_db
from ..services.practice_service import PracticeInputInvalid, PracticeQuestionInvalid, practice_history, record_practice

router = APIRouter(prefix="/api/v1/practice", tags=["practice"])


@router.post("/attempts", response_model=PracticeAttemptOut)
def submit_practice(body: PracticeAttemptIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        row, result = record_practice(db, user, body.kind, body.level, body.question, body.answer, body.input)
    except PracticeQuestionInvalid as exc:
        raise AppError(422, "PRACTICE_QUESTION_INVALID", f"Đề luyện tập thiếu trường: {exc}.") from exc
    except PracticeInputInvalid as exc:
        raise AppError(422, "PRACTICE_INPUT_INVALID", f"Dạng bài {exc} chỉ trả lời bằng chữ, không bấm piano.") from exc
    return PracticeAttemptOut(
        id=row.id, kind=row.kind, correct=row.correct, expected=result["expected"], message_vi=result["message_vi"],
        primary_error=result.get("primary_error"), errors=result.get("errors", []),
        convention_verified=result.get("convention_verified"),
    )


@router.get("/history", response_model=PracticeHistoryOut)
def get_practice_history(limit: int = Query(default=20, ge=1, le=100), user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    items, stats = practice_history(db, user.id, limit)
    return PracticeHistoryOut(
        items=[PracticeHistoryItem(id=i.id, kind=i.kind, level=i.level, question=i.question, answer=i.answer,
                                   correct=i.correct, primary_error=i.primary_error, created_at=i.created_at) for i in items],
        stats=[PracticeKindStat(**item) for item in stats],
    )
