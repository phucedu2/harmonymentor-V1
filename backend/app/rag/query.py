"""Truy vấn kho Qdrant: lọc theo nguồn/bài/ngôn ngữ, top-k, ngưỡng điểm.  python -m app.rag.query "câu hỏi" [--source lessons]"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from ..ai.embedder import Embedder
from ..core.ai_config import RagConfig, rag_config
from .embedding import get_embedder
from .errors import RagError
from .store import Hit, QdrantStore, make_client


def search(store: QdrantStore, embedder: Embedder, question: str, *, cfg: RagConfig | None = None, top_k: int | None = None,
           min_score: float | None = None, source: str = "", lesson_id: str = "", lang: str = "") -> list[Hit]:
    """Trả tối đa top_k đoạn có điểm >= min_score (mặc định theo cấu hình), đã sắp giảm dần."""
    cfg = cfg or rag_config()
    if not question.strip():
        return []
    vec = embedder.embed([question], "RETRIEVAL_QUERY")[0]
    hits = store.search(vec, top_k=top_k or cfg.top_k, min_score=cfg.min_score if min_score is None else min_score,
                        filters={"source": source, "lesson_id": lesson_id, "lang": lang})
    return sorted(hits, key=lambda h: -h.score)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m app.rag.query")
    ap.add_argument("question")
    ap.add_argument("--source", default="")
    ap.add_argument("--lesson", default="")
    ap.add_argument("--top-k", type=int, default=None)
    ap.add_argument("--min-score", type=float, default=None)
    args = ap.parse_args(argv)
    cfg = rag_config()
    try:
        store = QdrantStore(make_client(cfg), cfg.collection, cfg.dim)
        hits = search(store, get_embedder(cfg), args.question, cfg=cfg, top_k=args.top_k, min_score=args.min_score,
                      source=args.source, lesson_id=args.lesson)
    except RagError as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        return 2
    for h in hits:
        p = h.payload
        print(f"{h.score:.3f}  [{p.get('source')}] {p.get('lesson_id')}/{p.get('block_id')} — {p.get('title')}")
    if not hits:
        print("Không có đoạn nào đạt ngưỡng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
