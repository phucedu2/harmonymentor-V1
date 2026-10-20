from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..contracts.learning import LearningOverviewOut
from ..auth.deps import get_current_user
from ..db.models import User
from ..db.session import get_db
from ..services.learning_service import learning_overview

router = APIRouter(prefix="/api/v1/learning", tags=["learning"])


@router.get("/overview", response_model=LearningOverviewOut)
def get_learning_overview(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return LearningOverviewOut(**learning_overview(db, user.id))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail={"code": str(exc)}) from exc
