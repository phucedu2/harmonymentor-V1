"""Các phép đo thuần (không biết gì về chatbot) và kiểm hồi quy so với baseline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


def pct(xs: Iterable[bool]) -> float | None:
    xs = list(xs)
    return round(100 * sum(bool(x) for x in xs) / len(xs), 1) if xs else None


def percentile(xs: Sequence[float], p: float) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    return round(s[min(len(s) - 1, max(0, round(p * len(s)) - 1))], 1)


def rank_of(ids: Sequence[str], good: Iterable[str]) -> int | None:
    good = set(good)
    return next((i + 1 for i, b in enumerate(ids) if b in good), None)


def hit_rate_and_mrr(ranks: Sequence[int | None], k: int = 5) -> tuple[float | None, float | None]:
    """HitRate@k (%) và MRR@k: xếp hạng ngoài k coi như trượt."""
    if not ranks:
        return None, None
    hit = pct(r is not None and r <= k for r in ranks)
    mrr = round(sum(1 / r for r in ranks if r is not None and r <= k) / len(ranks), 3)
    return hit, mrr


def precision_recall(tp: int, fp: int, fn: int) -> tuple[float | None, float | None]:
    p = round(100 * tp / (tp + fp), 1) if tp + fp else None
    r = round(100 * tp / (tp + fn), 1) if tp + fn else None
    return p, r


def best_threshold(pos: Sequence[float], neg: Sequence[float], grid: Sequence[float]) -> list[dict]:
    """Với mỗi ngưỡng: tỉ lệ câu đúng chủ đề được nhận (TPR) và câu lạc đề lọt qua (FPR); độ chính xác cân bằng."""
    rows = []
    for t in grid:
        tpr = sum(x >= t for x in pos) / len(pos) if pos else 0.0
        fpr = sum(x >= t for x in neg) / len(neg) if neg else 0.0
        rows.append({"threshold": round(t, 3), "tpr": round(100 * tpr, 1), "fpr": round(100 * fpr, 1),
                     "balanced": round(100 * (tpr + 1 - fpr) / 2, 1)})
    return rows


# Chiều "tốt hơn" của từng chỉ số và dung sai trước khi coi là hồi quy. Độ trễ chỉ báo cáo, không chặn (máy chạy khác nhau).
HIGHER_BETTER = {"hit_rate_at_5": 2.0, "mrr": 0.03, "route_accuracy": 3.0, "offtopic_handled": 0.0, "attack_handled": 0.0,
                 "valid_citation_rate": 0.0, "bad_citation_caught": 0.0, "groundedness_structural": 2.0,
                 "gate_precision": 5.0, "gate_recall": 5.0, "gate_offtopic_reject": 5.0}


@dataclass
class Regression:
    metric: str
    baseline: float
    now: float
    tolerance: float

    def __str__(self) -> str:
        return f"{self.metric}: {self.now} < baseline {self.baseline} (dung sai {self.tolerance})"


def flatten(results: dict) -> dict[str, float]:
    """{"retrieval/qdrant_rerank/hit_rate_at_5": 93.0, ...}: chỉ các số đo cần chặn hồi quy."""
    out: dict[str, float] = {}
    for section, body in results.items():
        if not isinstance(body, dict) or section.startswith("_"):
            continue
        for name, inner in body.items():
            if name.startswith("_"):
                continue
            if isinstance(inner, dict):
                for k, v in inner.items():
                    if k in HIGHER_BETTER and isinstance(v, (int, float)):
                        out[f"{section}/{name}/{k}"] = v
            elif name in HIGHER_BETTER and isinstance(body.get(name), (int, float)):
                out[f"{section}/{name}"] = inner
    return out


def regressions(results: dict, baseline: dict[str, float]) -> list[Regression]:
    now = flatten(results)
    found = []
    for key, base in baseline.items():
        if key not in now:
            continue                                   # số đo không chạy được lần này (ví dụ thiếu e5): không so
        tol = HIGHER_BETTER[key.rsplit("/", 1)[-1]]
        if now[key] < base - tol - 1e-9:
            found.append(Regression(key, base, now[key], tol))
    return found
