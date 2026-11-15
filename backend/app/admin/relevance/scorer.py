"""Chấm điểm "liên quan nhạc lý/hòa âm" 0..1 cho một đoạn chữ.

Giao diện `RelevanceScorer` để G6 thay bộ chấm bằng mô hình tự huấn luyện qua RELEVANCE_SCORER (không đổi cổng).
v1 = từ vựng nhạc lý + độ gần về nghĩa (embedding) với tập câu neo."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Protocol, Sequence

from ...ai.embedder import Embedder
from ...core.ai_config import RelevanceConfig, relevance_config
from .anchors import ANCHORS
from .lexicon import count_hits

WINDOW_CHARS = 1200
MAX_WINDOWS = 4


@dataclass
class Score:
    value: float
    lexicon: float
    embedding: float | None
    detail: dict = field(default_factory=dict)


class RelevanceScorer(Protocol):
    name: str

    def score(self, text: str) -> Score: ...


def lexicon_score(text: str, cfg: RelevanceConfig | None = None) -> float:
    """Mật độ từ khóa nhạc lý trên 100 từ, nén về 0..1 bằng 1 - exp(-mật độ / thang)."""
    cfg = cfg or relevance_config()
    hits, words = count_hits(text)
    if words == 0:
        return 0.0
    density = hits / words * 100
    return 1 - math.exp(-density / cfg.lexicon_density_scale)


def windows(text: str) -> list[str]:
    text = text.strip()
    if len(text) <= WINDOW_CHARS:
        return [text] if text else []
    starts = sorted({round(i * (len(text) - WINDOW_CHARS) / (MAX_WINDOWS - 1)) for i in range(MAX_WINDOWS)})
    return [text[s:s + WINDOW_CHARS] for s in starts]


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class HybridScorer:
    """Điểm = w * từ vựng + (1 - w) * nhúng. Không có bộ nhúng (chưa tải mô hình) thì chỉ dùng từ vựng và ghi rõ."""

    name = "hybrid"

    def __init__(self, embedder: Embedder | None, cfg: RelevanceConfig | None = None):
        self.embedder, self.cfg = embedder, cfg or relevance_config()
        self._anchor_vecs: list[list[float]] | None = None

    def _anchors(self) -> list[list[float]]:
        if self._anchor_vecs is None:
            self._anchor_vecs = self.embedder.embed(ANCHORS, "RETRIEVAL_QUERY")
        return self._anchor_vecs

    def embedding_score(self, text: str) -> float:
        wins = windows(text)
        if not wins:
            return 0.0
        anchors = self._anchors()
        vecs = self.embedder.embed(wins, "RETRIEVAL_QUERY")
        best = [max(_dot(v, a) for a in anchors) for v in vecs]
        mean = sum(best) / len(best)
        cfg = self.cfg
        return max(0.0, min(1.0, (mean - cfg.emb_floor) / (cfg.emb_ceil - cfg.emb_floor)))

    def score(self, text: str) -> Score:
        lex = lexicon_score(text, self.cfg)
        if self.embedder is None:
            return Score(lex, lex, None, {"scorer": "lexicon", "note": "chưa có mô hình nhúng, chỉ dùng từ vựng"})
        emb = self.embedding_score(text)
        w = self.cfg.lexicon_weight
        return Score(w * lex + (1 - w) * emb, lex, emb, {"scorer": "hybrid"})


class LexiconScorer:
    name = "lexicon"

    def __init__(self, cfg: RelevanceConfig | None = None):
        self.cfg = cfg or relevance_config()

    def score(self, text: str) -> Score:
        lex = lexicon_score(text, self.cfg)
        return Score(lex, lex, None, {"scorer": "lexicon"})


@lru_cache(maxsize=1)
def _default_embedder():
    from ...ai.local_embedder import get_local_embedder

    return get_local_embedder()


def default_scorer(cfg: RelevanceConfig | None = None) -> RelevanceScorer:
    cfg = cfg or relevance_config()
    if cfg.scorer == "lexicon":
        return LexiconScorer(cfg)
    return HybridScorer(_default_embedder(), cfg)
