"""Đọc mô tả kỹ năng và vector embedding đã tính sẵn của chúng (tầng nội dung, 04 mục 6.5 bước 2).

Vector được tính một lần bằng `python -m app.ai.build_skill_embeddings` rồi commit, để lúc chạy
không phải gọi Gemini cho 26 mô tả và AI_ENABLED=false vẫn đọc được."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).parent
DESCRIPTIONS_PATH = HERE / "skill_descriptions.json"
EMBEDDINGS_PATH = HERE / "skill_embeddings.json"


def description_hash(text: str) -> str:
    return hashlib.sha256(unicodedata.normalize("NFC", text).encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def _descriptions_cached() -> dict[str, dict[str, Any]]:
    return json.loads(DESCRIPTIONS_PATH.read_text(encoding="utf-8"))["skills"]


def load_descriptions() -> dict[str, dict[str, Any]]:
    return dict(_descriptions_cached())


@lru_cache(maxsize=1)
def load_embeddings() -> dict[str, Any]:
    if not EMBEDDINGS_PATH.exists():
        return {"model": None, "dim": 0, "skills": {}}
    return json.loads(EMBEDDINGS_PATH.read_text(encoding="utf-8"))


def usable(rows: Mapping[str, Mapping[str, Any]], *, allow_draft: bool) -> dict[str, Mapping[str, Any]]:
    """Mô tả được phép dùng cho gợi ý: đã duyệt, hoặc nháp khi bật cờ dev/demo."""
    ok = {"approved", "draft"} if allow_draft else {"approved"}
    return {k: v for k, v in rows.items() if v.get("status") in ok}
