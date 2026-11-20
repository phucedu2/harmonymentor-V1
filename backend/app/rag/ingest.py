"""Nạp dữ liệu vào Qdrant.  python -m app.rag.ingest --source lessons|corpus|all [--dry-run] [--recreate] [--stats]

Chạy lại nhiều lần an toàn: id điểm tất định nên cùng nội dung chỉ ghi đè; đoạn không còn trong nguồn bị xóa."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from ..ai.embedder import Embedder
from ..core.ai_config import RagConfig, rag_config
from .chunker import TokenCounter
from .embedding import get_embedder, token_counter
from .errors import RagError
from .sources import corpus_records, lesson_records
from .store import QdrantStore, Record, make_client


def ingest(store: QdrantStore | None, embedder: Embedder, sources: Sequence[str], cfg: RagConfig,
           counter: TokenCounter | None = None, dry_run: bool = False) -> dict:
    counter = counter or token_counter(embedder)
    report: dict = {"dry_run": dry_run, "sources": {}, "warnings": []}
    for src in sources:
        if src == "lessons":
            records, warns = lesson_records(), []
        elif src == "corpus":
            records, warns = corpus_records(cfg, counter)
        else:
            raise RagError(f"Nguồn không hợp lệ: {src!r} (lessons, corpus, all).")
        report["warnings"] += warns
        info = {"chunks": len(records), "upserted": 0, "deleted_stale": 0}
        if records and not dry_run:
            assert store is not None
            vectors = _embed(embedder, records, cfg.upsert_batch)
            info["upserted"] = store.upsert(records, vectors, cfg.upsert_batch)
        if not dry_run and store is not None:
            info["deleted_stale"] = store.delete_stale(src, {r.id for r in records})
        report["sources"][src] = info
    return report


def _embed(embedder: Embedder, records: Sequence[Record], batch: int) -> list[list[float]]:
    out: list[list[float]] = []
    for i in range(0, len(records), batch):
        out += embedder.embed([r.text for r in records[i:i + batch]], "RETRIEVAL_DOCUMENT")
    return out


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m app.rag.ingest", description=__doc__)
    ap.add_argument("--source", choices=["lessons", "corpus", "all"], default="all")
    ap.add_argument("--dry-run", action="store_true", help="chỉ đếm đoạn, không nhúng, không ghi Qdrant")
    ap.add_argument("--recreate", action="store_true", help="xóa và dựng lại collection (cần khi đổi mô hình nhúng)")
    ap.add_argument("--stats", action="store_true", help="in thống kê collection rồi thoát")
    args = ap.parse_args(argv)
    cfg = rag_config()
    sources = ["lessons", "corpus"] if args.source == "all" else [args.source]
    try:
        embedder = get_embedder(cfg)
        store = None
        if not args.dry_run or args.stats:
            store = QdrantStore(make_client(cfg), cfg.collection, cfg.dim)
            store.ensure_collection(recreate=args.recreate and not args.stats)
        if args.stats:
            print(json.dumps(store.stats(), ensure_ascii=False, indent=2))
            return 0
        print(json.dumps(ingest(store, embedder, sources, cfg, dry_run=args.dry_run), ensure_ascii=False, indent=2))
        return 0
    except RagError as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
