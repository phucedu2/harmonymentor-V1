from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..contracts.learning import AttemptErrorOut, AttemptIn, AttemptOut
from ..auth.deps import get_current_user
from ..db.models import User
from ..db.session import get_db
from ..services.learning_service import submit_attempt

router = APIRouter(prefix="/api/v1/attempts", tags=["attempts"])


@router.post("", response_model=AttemptOut)
def create_attempt(body: AttemptIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        attempt, outcome = submit_attempt(db, user.id, body.exercise_version_id, body.answer)
    except LookupError as exc:
        code = str(exc)
        raise HTTPException(status_code=404, detail={"code": code}) from exc
    return AttemptOut(
        attempt_id=attempt.id, user_id=attempt.user_id, exercise_version_id=attempt.exercise_version_id,
        correct=attempt.correct, score=attempt.score, primary_error=attempt.primary_error,
        feedback=attempt.feedback,
        errors=[AttemptErrorOut(code=e.get("code", "UNKNOWN"), detail={k: v for k, v in e.items() if k != "code"})
                for e in outcome.errors],
    )
