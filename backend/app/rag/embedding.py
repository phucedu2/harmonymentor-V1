"""Chọn mô hình nhúng cho kho Qdrant theo RAG_EMBEDDER: "e5" (cục bộ, mặc định) hoặc "fake" (test, không cần tải mô hình)."""

from __future__ import annotations

from ..ai.embedder import Embedder, FakeEmbedder
from ..core.ai_config import RagConfig, rag_config
from .chunker import TokenCounter, TokenizerCounter, WhitespaceCounter
from .errors import RagError


def get_embedder(cfg: RagConfig | None = None) -> Embedder:
    cfg = cfg or rag_config()
    if cfg.embedder == "fake":
        return FakeEmbedder(dim=cfg.dim)
    if cfg.embedder == "e5":
        from ..ai.local_embedder import get_local_embedder

        emb = get_local_embedder()
        if emb is None:
            raise RagError("Chưa có mô hình e5. Chạy: python -m app.ai.local_embedder download")
        return emb
    raise RagError(f"RAG_EMBEDDER={cfg.embedder!r} chưa được hỗ trợ (chỉ e5, fake).")


def token_counter(embedder: Embedder) -> TokenCounter:
    tok = getattr(embedder, "tok", None)
    return TokenizerCounter(tok) if tok is not None else WhitespaceCounter()
