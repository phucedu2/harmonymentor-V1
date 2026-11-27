"""Tầng truy xuất Qdrant cục bộ / dịch vụ cho toàn khóa L01–L08 (Mốc 7).

Chỉ kích hoạt khi TUTOR_VECTOR_BACKEND=qdrant. Tự kiểm tra khớp model nhúng, trạng thái published
và content_hash của từng đoạn so với knowledge_base() hiện hành; lệch hash hoặc lỗi kết nối đều trả None
để retriever.py tự lùi an toàn về vector nội bộ / BM25."""

from __future__ import annotations

import atexit
import logging
import os
from pathlib import Path
from typing import Any

from ..embedder import Embedder
from .chunker import Chunk

log = logging.getLogger("harmonymentor.qdrant")

_clients: dict[tuple[str, str], Any] = {}


def _close_all() -> None:
    for client in list(_clients.values()):
        try:
            client.close()
        except Exception:  # noqa: BLE001
            pass
    _clients.clear()


atexit.register(_close_all)


def close_qdrant_clients() -> None:
    """Đóng kết nối Qdrant cục bộ (hữu ích trong kiểm thử hoặc khi tắt ứng dụng)."""
    _close_all()


def _get_client(local_path: str, url: str):
    from qdrant_client import QdrantClient

    key = (str(Path(local_path).resolve()) if local_path else "", url or "")
    if key not in _clients:
        if key[0]:
            if not Path(key[0]).exists():
                return None
            _clients[key] = QdrantClient(path=key[0])
        elif key[1]:
            _clients[key] = QdrantClient(url=key[1], api_key=os.getenv("QDRANT_API_KEY") or None)
        else:
            return None
    return _clients[key]


def query_qdrant(
    query: str,
    embedder: Embedder,
    kb_chunks: tuple[Chunk, ...],
    *,
    top_k: int = 4,
    min_score: float = 0.35,
    allowed_lessons: set[str] | None = None,
    local_path: str = "",
    url: str = "",
    collection: str = "hm_lessons_L01_L08_e5_v1",
):
    """Truy vấn Qdrant trên kho bài học đã xuất bản; trả về (hits_pairs, best_score) hoặc None nếu cần fallback."""
    try:
        from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

        client = _get_client(local_path, url)
        if client is None or not client.collection_exists(collection):
            return None

        by_id = {c.chunk_id: c for c in kb_chunks}
        q_vec = embedder.embed([query], "RETRIEVAL_QUERY")[0]
        must = [
            FieldCondition(key="embedding_model", match=MatchValue(value=embedder.model)),
            FieldCondition(key="status", match=MatchValue(value="published")),
            FieldCondition(key="doc_type", match=MatchValue(value="lesson")),
        ]
        if allowed_lessons is not None:
            must.append(FieldCondition(key="lesson_id", match=MatchAny(any=sorted(allowed_lessons))))

        # Lấy dư số lượng để đảm bảo thứ tự tie-break theo chunk_id và kiểm tra tính đồng bộ hash.
        limit = max(top_k, len(kb_chunks) if allowed_lessons is None else 32)
        pts = client.query_points(
            collection_name=collection,
            query=q_vec,
            query_filter=Filter(must=must),
            limit=limit,
            with_payload=True,
        ).points
        if not pts:
            return [], 0.0

        scored: list[tuple[Chunk, float]] = []
        for p in pts:
            payload = p.payload or {}
            cid = payload.get("chunk_id")
            chunk = by_id.get(cid)
            if chunk is None or payload.get("content_hash") != chunk.content_hash:
                log.warning("qdrant_index_stale collection=%s chunk_id=%s", collection, cid)
                return None
            scored.append((chunk, float(p.score)))

        scored.sort(key=lambda item: (-item[1], item[0].chunk_id))
        best = round(scored[0][1], 4) if scored else 0.0
        kept = [(c, round(s, 4)) for c, s in scored[:top_k] if s >= min_score]
        return kept, best
    except Exception as exc:  # noqa: BLE001
        log.warning("qdrant_unavailable collection=%s type=%s", collection, type(exc).__name__)
        return None
