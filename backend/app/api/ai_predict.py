"""GET /api/v1/me/predictions: xác suất làm đúng câu mới tiếp theo của từng kỹ năng (ADR-031).

user_id lấy từ token (nguyên tắc 4). Cờ PREDICT_ENABLED tắt → 404 như thể chưa có tính năng.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth.deps import get_current_user
from ..core.errors import AppError
from ..db.models import User
from ..db.session import get_db
from ..ml.correctness import predictor

router = APIRouter(prefix="/api/v1", tags=["ai-predict"])


@router.get("/me/predictions")
def my_predictions(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    if not predictor.enabled():
        raise AppError(404, "PREDICT_DISABLED", "Tính năng dự đoán đang tắt (PREDICT_ENABLED=0).")
    try:
        return predictor.predict_for_user(db, user.id)
    except predictor.ModelUnavailable as exc:
        raise AppError(503, "PREDICT_MODEL_UNAVAILABLE", str(exc)) from None
