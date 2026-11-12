"""Tính vector cho mô tả kỹ năng MVP bằng Gemini và ghi app/content/skill_embeddings.json.

    cd backend && AI_ENABLED=1 GEMINI_API_KEY=... python -m app.ai.build_skill_embeddings

Chỉ mô tả kỹ năng (văn bản công khai của chương trình) được gửi đi. Khóa đọc từ môi trường, không ghi ra file.
Kỹ năng post_mvp không được gợi ý (R4) nên không cần vector."""

from __future__ import annotations

import json
import sys

from ..content import skill_descriptions as sd
from ..core.config import settings
from .embedder import get_embedder
from .skill_mapping import is_mvp


def main() -> int:
    embedder = get_embedder(settings)
    if embedder is None:
        print("Cần AI_ENABLED=1 và GEMINI_API_KEY để tính vector.", file=sys.stderr)
        return 2
    rows = {k: v for k, v in sd.load_descriptions().items() if is_mvp(k)}
    skills = sorted(rows)
    vectors = embedder.embed([rows[s]["text"] for s in skills], "RETRIEVAL_DOCUMENT")
    out = {
        "model": embedder.model, "dim": embedder.dim, "task_type": "RETRIEVAL_DOCUMENT", "normalized": True,
        "skills": {s: {"hash": sd.description_hash(rows[s]["text"]), "vector": [round(x, 7) for x in v]}
                   for s, v in zip(skills, vectors)},
    }
    sd.EMBEDDINGS_PATH.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Đã ghi {len(skills)} vector {embedder.model} ({embedder.dim} chiều) vào {sd.EMBEDDINGS_PATH.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
