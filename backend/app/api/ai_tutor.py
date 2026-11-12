"""API AI Tutor (04 Bảng 9: /chat/*). user_id luôn lấy từ token (nguyên tắc 4).

Đề GĐ3 ghi /tutor/explain-attempt; theo nguyên tắc "tài liệu thắng", dùng đường dẫn của 04: /chat/explain-attempt."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..ai.embedder import Embedder, get_embedder
from ..ai.local_embedder import get_local_embedder
from ..ai.tutor.llm import LLMProvider, get_provider
from ..auth.deps import get_current_user
from ..contracts.ai import (ChatHistoryItem, ChatMessageIn, ChatRatingIn, ChatReplyOut, ChatSessionOut,
                            ExplainAttemptIn)
from ..core.config import settings
from ..core.errors import AppError
from ..db.models import User
from ..db.session import get_db
from ..services import ai_tutor_service as ts

router = APIRouter(prefix="/api/v1/chat", tags=["ai-tutor"])

_provider_cache: dict[tuple, LLMProvider | None] = {}


def embedder_dep() -> Embedder | None:
    """Mặc định e5-small cục bộ (ADR-017); thiếu file mô hình thì None → BM25, không hỏng yêu cầu."""
    choice = settings.tutor_embedder.lower()
    if choice == "gemini":
        return get_embedder(settings)
    if choice == "bm25":
        return None
    return get_local_embedder()


def warm_up() -> None:
    """Nạp trước mô hình nhúng và bộ phân loại để câu hỏi đầu tiên sau khi khởi động không quá giờ (mô hình e5 nạp
    mất hơn 1 phút trên máy yếu). Chạy nền, lỗi thì bỏ qua: câu hỏi đầu vẫn tự nạp như cũ."""
    try:
        from ..ai.tutor.route_classifier import model
        emb = embedder_dep()
        if emb is not None:
            emb.embed(["khởi động"], "RETRIEVAL_QUERY")
        model()
    except Exception:  # noqa: BLE001 - chỉ là bước làm nóng
        pass


if settings.ai_enabled:  # AI tắt thì không có gì để làm nóng (và test mặc định không chạy luồng nền)
    import threading
    threading.Thread(target=warm_up, name="tutor-warm-up", daemon=True).start()


def provider_dep() -> LLMProvider | None:
    """Tách thành dependency để test thay bằng FakeProvider, không gọi mạng."""
    key = (settings.ai_enabled, bool(settings.gemini_api_key), settings.gemini_model, settings.gemini_fallback_model)
    if key not in _provider_cache:
        _provider_cache[key] = get_provider(settings)
    return _provider_cache[key]


def _quota_error(exc: ts.QuotaExceeded) -> AppError:
    return AppError(429, "AI_QUOTA_EXCEEDED",
                    f"Bạn đã dùng hết {exc.quota} lượt hỏi AI hôm nay. Tin nhắn đã được lưu; ngày mai thử lại nhé.",
                    retryable=True)


@router.post("/sessions", response_model=ChatSessionOut, status_code=201)
def new_session(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = ts.create_session(db, user.id)
    db.commit()
    return s


@router.get("/sessions", response_model=list[ChatSessionOut])
def sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ts.list_sessions(db, user.id)


@router.get("/history/{session_id}", response_model=list[ChatHistoryItem])
def history(session_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return ts.history(db, user.id, session_id)
    except ts.ChatNotFound:
        raise AppError(404, "CHAT_SESSION_NOT_FOUND", "Không tìm thấy phiên chat.") from None


@router.post("/message", response_model=ChatReplyOut)
def message(body: ChatMessageIn, user: User = Depends(get_current_user), db: Session = Depends(get_db),
            embedder: Embedder | None = Depends(embedder_dep), provider: LLMProvider | None = Depends(provider_dep)):
    try:
        return ts.handle_message(db, user, body.message, session_id=body.session_id,
                                 context=body.context.model_dump() if body.context else None,
                                 embedder=embedder, provider=provider)
    except ts.ChatNotFound:
        raise AppError(404, "CHAT_SESSION_NOT_FOUND", "Không tìm thấy phiên chat.") from None
    except ts.QuotaExceeded as exc:
        raise _quota_error(exc) from None


@router.post("/explain-attempt", response_model=ChatReplyOut)
def explain(body: ExplainAttemptIn, user: User = Depends(get_current_user), db: Session = Depends(get_db),
            embedder: Embedder | None = Depends(embedder_dep), provider: LLMProvider | None = Depends(provider_dep)):
    try:
        return ts.explain_attempt(db, user, body.attempt_id, hint_level=body.hint_level,
                                  session_id=body.session_id, embedder=embedder, provider=provider)
    except (ts.AttemptNotFound, ts.ChatNotFound):
        raise AppError(404, "ATTEMPT_NOT_FOUND", "Không tìm thấy lượt làm này.") from None
    except ts.AttemptNotWrong:
        raise AppError(409, "ATTEMPT_NOT_WRONG", "Lượt làm này đã đúng, không có lỗi để giải thích.") from None
    except ts.QuotaExceeded as exc:
        raise _quota_error(exc) from None


@router.post("/messages/{message_id}/rating", status_code=204)
def rate(message_id: int, body: ChatRatingIn, user: User = Depends(get_current_user),
         db: Session = Depends(get_db)) -> Response:
    try:
        ts.rate_message(db, user.id, message_id, body.stars, body.comment)
    except ts.ChatNotFound:
        raise AppError(404, "CHAT_MESSAGE_NOT_FOUND", "Không tìm thấy tin nhắn.") from None
    return Response(status_code=204)
