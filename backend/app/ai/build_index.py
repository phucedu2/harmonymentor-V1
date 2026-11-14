"""Tính vector cho kho đoạn bài học bằng Gemini và ghi app/content/lesson_embeddings.json (đề GĐ3 mục 1).

    cd backend && AI_ENABLED=1 GEMINI_API_KEY=... python -m app.ai.build_index
    cd backend && python -m app.ai.build_index rehash      # chỉ đổi hash khi văn bản không đổi, không gọi mạng

Chỉ văn bản lý thuyết đã phát hành được gửi đi (không đáp án, không nháp, không dữ liệu người dùng).
File ghi mô hình, số chiều và hash từng đoạn; retriever chỉ dùng vector khi hash khớp nội dung hiện tại.
Khóa đọc từ môi trường, không ghi ra file."""

from __future__ import annotations

import json
import sys

from ..core.config import settings
from .embedder import get_embedder
from .tutor.chunker import lesson_chunks, lesson_titles
from .tutor.retriever import INDEX_PATH

BATCH = 50


def main() -> int:
    embedder = get_embedder(settings)
    if embedder is None:
        print("Cần AI_ENABLED=1 và GEMINI_API_KEY để tính vector.", file=sys.stderr)
        return 2
    chunks, titles = lesson_chunks(), lesson_titles()
    texts = [c.embed_text(titles.get(c.lesson_id, "")) for c in chunks]
    vectors: list[list[float]] = []
    for i in range(0, len(texts), BATCH):
        vectors.extend(embedder.embed(texts[i:i + BATCH], "RETRIEVAL_DOCUMENT"))
    out = {
        "model": embedder.model, "dim": embedder.dim, "task_type": "RETRIEVAL_DOCUMENT", "normalized": True,
        "chunks": {c.chunk_id: {"lesson_id": c.lesson_id, "block_id": c.block_id, "title": c.title,
                                "hash": c.content_hash, "vector": [round(x, 7) for x in v]}
                   for c, v in zip(chunks, vectors)},
    }
    INDEX_PATH.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Đã ghi {len(chunks)} đoạn, {embedder.model} ({embedder.dim} chiều) vào {INDEX_PATH.name}")
    return 0


def rehash() -> int:
    """Đổi công thức hash (GĐ2: bỏ nguồn khỏi hash) mà không gọi Gemini. Một đoạn chỉ được nhận hash mới khi hash cũ
    trong file khớp đúng công thức GĐ1 (cùng id, tiêu đề, nội dung, nguồn cả bài): tức văn bản được nhúng không đổi,
    vector cũ vẫn đúng. Đoạn nào không khớp giữ nguyên để retriever tự rơi về BM25 tới khi chạy lại main()."""
    from ..content.curriculum_specs import LESSON_SPECS
    from ..content.source_registry import SOURCE_REGISTRY
    from .tutor.chunker import _hash, lesson_source

    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    whole = {s["id"]: lesson_source(s, SOURCE_REGISTRY) for s in LESSON_SPECS}
    moved = kept = 0
    for c in lesson_chunks():
        row = index["chunks"].get(c.chunk_id)
        if row and row["hash"] == c.content_hash:
            moved += 1          # đã đổi ở lần chạy trước
        elif row and row["hash"] == _hash(c.lesson_id, c.block_id, c.title, c.text, whole[c.lesson_id]):
            row["hash"] = c.content_hash
            moved += 1
        else:
            kept += 1
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Đổi hash {moved} đoạn (văn bản không đổi); {kept} đoạn không khớp, cần chạy lại build_index với Gemini.")
    return 0 if kept == 0 else 1


if __name__ == "__main__":
    raise SystemExit(rehash() if sys.argv[1:] == ["rehash"] else main())
