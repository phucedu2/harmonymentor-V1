from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..contracts.learning import AttemptErrorOut, AttemptIn, AttemptOut
from ..auth.deps import get_current_user
from ..db.models import User
from ..db.session import get_db
from ..core.errors import AppError
from ..services.learning_service import (
    EXPLANATION_AFTER_WRONG,
    ExerciseVersionSuperseded,
    submit_attempt,
    wrong_attempt_count,
)
from ..db.models import ExerciseVersion

router = APIRouter(prefix="/api/v1/attempts", tags=["attempts"])


@router.post("", response_model=AttemptOut)
def create_attempt(body: AttemptIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        attempt, outcome = submit_attempt(db, user.id, body.exercise_version_id, body.answer, body.input_method)
    except ExerciseVersionSuperseded as exc:
        # Không chấm theo đề cũ; frontend tải lại bài để người học làm phiên bản hiện hành (ADR-006).
        raise AppError(409, "EXERCISE_VERSION_SUPERSEDED",
                       "Câu hỏi này vừa được cập nhật. Hãy tải lại câu hỏi và trả lời theo đề mới.",
                       fields={"exercise_version_id": exc.version_id,
                               "current_version_id": exc.current_version_id}) from exc
    except LookupError as exc:
        code = str(exc)
        raise HTTPException(status_code=404, detail={"code": code}) from exc
    version = db.get(ExerciseVersion, attempt.exercise_version_id)
    wrong = wrong_attempt_count(db, user.id, version.exercise_id)
    show_explanation = attempt.correct or wrong >= EXPLANATION_AFTER_WRONG
    return AttemptOut(
        attempt_id=attempt.id, user_id=attempt.user_id, exercise_version_id=attempt.exercise_version_id,
        correct=attempt.correct, score=attempt.score, primary_error=attempt.primary_error,
        feedback=attempt.feedback,
        errors=[AttemptErrorOut(code=e.get("code", "UNKNOWN"), detail={k: v for k, v in e.items() if k != "code"})
                for e in outcome.errors],
        explanation=version.explanation if show_explanation else None,
        wrong_attempts=wrong,
    )
