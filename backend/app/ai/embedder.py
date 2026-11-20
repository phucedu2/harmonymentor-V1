"""Embedding văn bản: Gemini khi bật AI, FakeEmbedder trong test (không gọi mạng).

Chỉ văn bản được truyền vào mới được gửi đi; hàm không nhận user_id hay thông tin cá nhân nào
(SRS 03 Bảng 3). Gemini trả vector chưa chuẩn hóa khi rút chiều (768), nên mọi vector đều được
chuẩn hóa về độ dài 1 trước khi dùng."""

from __future__ import annotations

import hashlib
import math
from collections import OrderedDict
from typing import Any, Protocol, Sequence


class EmbeddingUnavailable(RuntimeError):
    """Gemini lỗi, hết hạn mức hoặc mạng hỏng. Bên gọi chuyển sang dự phòng, không làm hỏng yêu cầu."""


class Embedder(Protocol):
    model: str
    dim: int

    def embed(self, texts: Sequence[str], task: str) -> list[list[float]]: ...


def normalize(vec: Sequence[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in vec))
    if n == 0:
        raise ValueError("Vector độ dài 0, không chuẩn hóa được")
    return [x / n for x in vec]


def text_hash(model: str, task: str, text: str) -> str:
    return hashlib.sha256(f"{model}\x1f{task}\x1f{text}".encode("utf-8")).hexdigest()


class FakeEmbedder:
    """Vector tất định từ SHA-256 của văn bản. Không mang nghĩa ngữ nghĩa, chỉ để test luồng."""

    def __init__(self, dim: int = 64, model: str = "fake-embedder-v1"):
        self.dim, self.model = dim, model
        self.calls: list[tuple[list[str], str]] = []

    def embed(self, texts: Sequence[str], task: str) -> list[list[float]]:
        self.calls.append((list(texts), task))
        out = []
        for t in texts:
            raw: list[float] = []
            counter = 0
            while len(raw) < self.dim:
                digest = hashlib.sha256(f"{counter}:{t}".encode("utf-8")).digest()
                raw.extend((b - 127.5) / 127.5 for b in digest)
                counter += 1
            out.append(normalize(raw[: self.dim]))
        return out


class GeminiEmbedder:
    def __init__(self, *, api_key: str, model: str, dim: int, client: Any | None = None):
        self.model, self.dim = model, dim
        if client is None:
            from google import genai

            client = genai.Client(api_key=api_key)
        # Không giữ khóa trong thuộc tính của đối tượng: repr, log hay traceback không lộ khóa.
        self._client = client

    def __repr__(self) -> str:
        return f"GeminiEmbedder(model={self.model!r}, dim={self.dim})"

    def embed(self, texts: Sequence[str], task: str) -> list[list[float]]:
        from google.genai import types

        try:
            resp = self._client.models.embed_content(
                model=self.model, contents=list(texts),
                config=types.EmbedContentConfig(task_type=task, output_dimensionality=self.dim))
            return [normalize(e.values) for e in resp.embeddings]
        except Exception as exc:  # SDK có nhiều loại lỗi; với bên gọi, mọi lỗi đều là "không dùng được lúc này"
            raise EmbeddingUnavailable(type(exc).__name__) from None


class CachedEmbedder:
    """Đệm theo hash (mô hình, tác vụ, văn bản) để cùng một mục tiêu không bị tính lại."""

    def __init__(self, inner: Embedder, max_items: int = 2048):
        self.inner, self.model, self.dim = inner, inner.model, inner.dim
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._max = max_items

    def embed(self, texts: Sequence[str], task: str) -> list[list[float]]:
        keys = [text_hash(self.model, task, t) for t in texts]
        missing = [t for t, k in zip(texts, keys) if k not in self._cache]
        missing = list(dict.fromkeys(missing))
        if missing:
            for t, v in zip(missing, self.inner.embed(missing, task)):
                self._cache[text_hash(self.model, task, t)] = v
                if len(self._cache) > self._max:
                    self._cache.popitem(last=False)
        return [self._cache[k] for k in keys]


_shared: dict[tuple[str, int], CachedEmbedder] = {}


def get_embedder(cfg) -> Embedder | None:
    """None khi tắt AI hoặc thiếu khóa: bên gọi dùng dự phòng cục bộ (nguyên tắc 3)."""
    if not cfg.ai_enabled or not cfg.gemini_api_key:
        return None
    key = (cfg.gemini_embed_model, cfg.gemini_embed_dim)
    if key not in _shared:
        _shared[key] = CachedEmbedder(GeminiEmbedder(api_key=cfg.gemini_api_key, model=cfg.gemini_embed_model,
                                                     dim=cfg.gemini_embed_dim))
    return _shared[key]
