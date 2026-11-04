"""Truy xuất đoạn bài học cho AI Tutor (04 mục 6.6, đề GĐ3 mục 2).

Đường chính: cosine giữa vector câu hỏi (Gemini, RETRIEVAL_QUERY) và vector đoạn đã tính sẵn trong
lesson_embeddings.json, giữ top_k=4 đoạn có điểm >= ngưỡng. Kho nhỏ (vài chục đoạn) nên tính trong
bộ nhớ, không cần pgvector hay dịch vụ riêng.

Dự phòng: BM25 khi tắt AI, Gemini lỗi, hoặc file vector lệch mô hình/hash với nội dung hiện tại. Đoạn
nào đổi nội dung mà chưa chạy lại build_index thì không có vector, nên cả lần đó dùng BM25 cho an toàn.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Sequence

from ..embedder import Embedder, EmbeddingUnavailable
from .bm25 import BM25
from .chunker import Chunk, lesson_chunks, lesson_titles

INDEX_PATH = Path(__file__).resolve().parents[2] / "content" / "lesson_embeddings.json"


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


@dataclass(frozen=True)
class Retrieval:
    hits: list[Hit]
    method: str          # "embedding" | "bm25"
    best_score: float    # điểm cao nhất kể cả dưới ngưỡng, để ghi log và hiệu chỉnh ngưỡng
    fallback_reason: str | None = None

    @property
    def block_ids(self) -> set[str]:
        return {h.chunk.block_id for h in self.hits}


@lru_cache(maxsize=1)
def knowledge_base() -> tuple[Chunk, ...]:
    return tuple(lesson_chunks())


@lru_cache(maxsize=1)
def _bm25() -> BM25:
    titles = lesson_titles()
    return BM25([c.embed_text(titles.get(c.lesson_id, "")) for c in knowledge_base()])


def load_index(path: Path = INDEX_PATH) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def index_vectors(index: dict | None, chunks: Sequence[Chunk], model: str) -> list[list[float]] | None:
    """Vector khớp từng đoạn hiện tại, hoặc None nếu file cũ/lệch mô hình."""
    if not index or index.get("model") != model:
        return None
    by_id = index.get("chunks", {})
    out = []
    for c in chunks:
        row = by_id.get(c.chunk_id)
        if not row or row.get("hash") != c.content_hash:
            return None
        out.append(row["vector"])
    return out


@lru_cache(maxsize=4)
def _cached_vectors(model: str) -> tuple[tuple[float, ...], ...] | None:
    vecs = index_vectors(load_index(), knowledge_base(), model)
    return tuple(tuple(v) for v in vecs) if vecs is not None else None


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _top(chunks: Sequence[Chunk], scores: Sequence[float], top_k: int, min_score: float) -> list[Hit]:
    order = sorted(range(len(chunks)), key=lambda i: (-scores[i], chunks[i].chunk_id))
    return [Hit(chunks[i], round(scores[i], 4)) for i in order[:top_k] if scores[i] >= min_score]


def retrieve(query: str, embedder: Embedder | None, *, top_k: int = 4, min_score: float = 0.35,
             bm25_min_score: float = 2.0, chunks: Sequence[Chunk] | None = None,
             vectors: Sequence[Sequence[float]] | None = None) -> Retrieval:
    chunks = list(chunks if chunks is not None else knowledge_base())
    reason = None
    if embedder is None:
        reason = "ai_disabled"
    else:
        if vectors is None:
            vectors = _cached_vectors(embedder.model)
        if vectors is None:
            reason = "index_stale"
        else:
            try:
                q = embedder.embed([query], "RETRIEVAL_QUERY")[0]
                scores = [_dot(q, v) for v in vectors]
                return Retrieval(_top(chunks, scores, top_k, min_score), "embedding",
                                 round(max(scores, default=0.0), 4))
            except EmbeddingUnavailable:
                reason = "embedding_unavailable"
    bm = _bm25() if chunks == list(knowledge_base()) else BM25([c.embed_text() for c in chunks])
    scores = bm.scores(query)
    best = max(scores, default=0.0)
    return Retrieval(_top(chunks, scores, top_k, bm25_min_score), "bm25", round(best, 4), reason)


def retrieve_for_skill(query: str, embedder: Embedder | None, lesson_ids: Sequence[str], *,
                       top_k: int = 3) -> Retrieval:
    """Cho giải thích lỗi: chỉ tìm trong bài dạy kỹ năng của câu sai, không lọc ngưỡng (đã biết chủ đề).
    Nếu điểm đều bằng 0 (BM25 không khớp từ nào) thì lấy các đoạn đầu của bài theo thứ tự trên trang."""
    allowed = set(lesson_ids)
    kb = list(knowledge_base())
    idx = [i for i, c in enumerate(kb) if c.lesson_id in allowed]
    if not idx:
        return Retrieval([], "none", 0.0, "no_lesson_chunks")
    chunks = [kb[i] for i in idx]
    vectors = None
    if embedder is not None:
        full = _cached_vectors(embedder.model)
        vectors = [full[i] for i in idx] if full is not None else None
        if vectors is None:
            embedder = None
    r = retrieve(query, embedder, top_k=top_k, min_score=-1.0, bm25_min_score=0.0, chunks=chunks, vectors=vectors)
    if r.best_score <= 0:
        return Retrieval([Hit(c, 0.0) for c in chunks[:top_k]], r.method, 0.0, "lesson_order")
    return r
