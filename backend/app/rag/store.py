"""Lớp mỏng quanh Qdrant: tạo collection, upsert idempotent, xóa theo nguồn, thống kê, tìm kiếm có bộ lọc và ngưỡng điểm."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Sequence

from qdrant_client import QdrantClient, models

from ..core.ai_config import RagConfig, rag_config
from .errors import RagError

NAMESPACE = uuid.UUID("5d0f6b6e-3a1c-4d0e-9d57-6a0f5c6f2b11")
INDEXED_FIELDS = ("source", "lesson_id", "lang", "block_id")


def point_id(source: str, key: str, chunk_idx: int, content_hash: str) -> str:
    """Id tất định: nạp lại cùng nội dung ra cùng id nên upsert ghi đè chứ không nhân đôi."""
    return str(uuid.uuid5(NAMESPACE, f"{source}|{key}|{chunk_idx}|{content_hash}"))


@dataclass
class Record:
    id: str
    text: str                              # văn bản đem nhúng (tiêu đề + đoạn)
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class Hit:
    id: str
    score: float
    payload: dict[str, Any]


def make_client(cfg: RagConfig | None = None) -> QdrantClient:
    cfg = cfg or rag_config()
    if not cfg.qdrant_url:
        raise RagError("Chưa đặt QDRANT_URL (Docker compose: http://qdrant:6333).")
    return QdrantClient(url=cfg.qdrant_url, timeout=30)


class QdrantStore:
    def __init__(self, client: QdrantClient, collection: str, dim: int):
        self.client, self.collection, self.dim = client, collection, dim

    def ensure_collection(self, recreate: bool = False) -> None:
        exists = self.client.collection_exists(self.collection)
        if exists and recreate:
            self.client.delete_collection(self.collection)
            exists = False
        if exists:
            size = self.client.get_collection(self.collection).config.params.vectors.size
            if size != self.dim:
                raise RagError(f"Collection {self.collection!r} có {size} chiều, mô hình nhúng hiện tại {self.dim}. "
                               "Chạy lại với --recreate để dựng lại (sẽ nạp lại toàn bộ).")
            return
        self.client.create_collection(self.collection, vectors_config=models.VectorParams(size=self.dim, distance=models.Distance.COSINE))
        for name in INDEXED_FIELDS:
            self.client.create_payload_index(self.collection, name, models.PayloadSchemaType.KEYWORD)

    def upsert(self, records: Sequence[Record], vectors: Sequence[Sequence[float]], batch: int = 64) -> int:
        if len(records) != len(vectors):
            raise RagError("Số vector khác số đoạn.")
        for i in range(0, len(records), batch):
            self.client.upsert(self.collection, points=[
                models.PointStruct(id=r.id, vector=list(v), payload=r.payload)
                for r, v in zip(records[i:i + batch], vectors[i:i + batch])])
        return len(records)

    def delete_source(self, source: str) -> None:
        self.client.delete(self.collection, points_selector=models.FilterSelector(filter=self._filter({"source": source})))

    def delete_stale(self, source: str, keep_ids: set[str]) -> int:
        """Xóa điểm cũ của nguồn mà lần nạp này không còn (nội dung đã sửa/xóa)."""
        stale, offset = [], None
        while True:
            points, offset = self.client.scroll(self.collection, scroll_filter=self._filter({"source": source}), limit=256,
                                                with_payload=False, offset=offset)
            stale += [str(p.id) for p in points if str(p.id) not in keep_ids]
            if offset is None:
                break
        if stale:
            self.client.delete(self.collection, points_selector=models.PointIdsList(points=stale))
        return len(stale)

    def count(self, filters: dict[str, str] | None = None) -> int:
        return self.client.count(self.collection, count_filter=self._filter(filters), exact=True).count

    def stats(self) -> dict[str, Any]:
        sources = {}
        for src in ("lessons", "corpus"):
            sources[src] = self.count({"source": src})
        return {"collection": self.collection, "dim": self.dim, "total": self.count(), "by_source": sources}

    @staticmethod
    def _filter(filters: dict[str, str | Sequence[str]] | None):
        if not filters:
            return None
        must = []
        for k, v in filters.items():
            if not v:
                continue
            match = models.MatchValue(value=v) if isinstance(v, str) else models.MatchAny(any=list(v))
            must.append(models.FieldCondition(key=k, match=match))
        return models.Filter(must=must) if must else None

    def search(self, vector: Sequence[float], *, top_k: int, min_score: float, filters: dict[str, str | Sequence[str]] | None = None) -> list[Hit]:
        res = self.client.query_points(self.collection, query=list(vector), limit=top_k, score_threshold=min_score,
                                       query_filter=self._filter(filters), with_payload=True)
        return [Hit(str(p.id), float(p.score), dict(p.payload or {})) for p in res.points]
