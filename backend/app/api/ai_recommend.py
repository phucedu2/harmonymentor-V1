"""API gợi ý bài học và mục tiêu học (GĐ2). user_id luôn lấy từ token (nguyên tắc 4)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from ..ai.embedder import Embedder, get_embedder
from ..auth.deps import get_current_user
from ..contracts.ai import GoalIn, GoalOut, RecClickIn, RecommendOut
from ..core.errors import AppError
from ..db.models import User
from ..db.session import get_db
from ..services import recommendation_service as rs

router = APIRouter(prefix="/api/v1", tags=["ai-recommend"])


def embedder_dep() -> Embedder | None:
    """Tách thành dependency để test thay bằng FakeEmbedder, không gọi mạng."""
    return get_embedder(rs.settings)


@router.get("/recommend", response_model=RecommendOut)
def get_recommendations(k: int = Query(5, ge=1, le=5), user: User = Depends(get_current_user),
                        db: Session = Depends(get_db), embedder: Embedder | None = Depends(embedder_dep)):
    return rs.recommend_for_user(db, user, k=k, embedder=embedder)


@router.post("/recommend/{log_id}/click", status_code=204)
def click_recommendation(log_id: str, body: RecClickIn, user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)) -> Response:
    try:
        rs.record_click(db, user.id, log_id, body.lesson_id)
    except rs.LogNotFound:
        raise AppError(404, "RECOMMENDATION_NOT_FOUND", "Không tìm thấy lần gợi ý này.") from None
    except ValueError:
        raise AppError(422, "LESSON_NOT_IN_RECOMMENDATION", "Bài này không có trong lần gợi ý.") from None
    return Response(status_code=204)


@router.get("/me/goal", response_model=GoalOut)
def get_goal(user: User = Depends(get_current_user)) -> GoalOut:
    return GoalOut(goal_text=user.goal_text, embedded=user.goal_embedding is not None,
                   embedding_model=user.goal_embedding_model)


@router.put("/me/goal", response_model=GoalOut)
def put_goal(body: GoalIn, user: User = Depends(get_current_user), db: Session = Depends(get_db),
             embedder: Embedder | None = Depends(embedder_dep)) -> GoalOut:
    embedded = rs.set_goal(db, user, body.goal_text, embedder)
    return GoalOut(goal_text=user.goal_text, embedded=embedded, embedding_model=user.goal_embedding_model)
