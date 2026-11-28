"""Bộ phân loại "liên quan nhạc lý" tự huấn luyện (G6, góp ý thầy T6). Chạy được trên CPU, không cần torch/sklearn lúc chạy.

Hai mô hình, huấn luyện bằng app/ml/relevance_train.py, lưu ở backend/models/relevance/ cùng manifest.json (phiên bản, SHA-256, số đo):
  tfidf   TF-IDF n-gram ký tự (2–4, trong ranh giới từ, đã bỏ dấu) + hồi quy logistic. Chỉ cần chữ, rất nhanh.
  e5      hồi quy logistic trên vector multilingual-e5-small (mô hình nhúng đã có sẵn cho AI Tutor).
Tệp mô hình là JSON thuần (không dùng pickle: tải pickle là chạy mã tùy ý) và được kiểm SHA-256 với manifest trước khi dùng.
Điểm trả về là xác suất 0..1 nên dùng chung ngưỡng LOW/HIGH của cổng G2."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Sequence

from ...ai.embedder import Embedder
from ...ai.tutor.bm25 import strip_accents
from ...core.ai_config import RelevanceConfig, relevance_config
from .scorer import Score, lexicon_score, windows

log = logging.getLogger("harmonymentor.relevance")
KINDS = ("tfidf", "e5")
FILES = {"tfidf": "tfidf-logreg.json", "e5": "e5-logreg.json"}
_WS = re.compile(r"\s+")


class ModelError(RuntimeError):
    """Thiếu tệp, sai SHA-256 hoặc định dạng lạ: bên gọi lùi về bộ chấm hybrid."""


def prep(text: str) -> str:
    """Hạ chữ và bỏ dấu để câu gõ có dấu và không dấu cho cùng đặc trưng."""
    return strip_accents(" ".join(text.lower().split()))


def char_wb_ngrams(text: str, lo: int = 2, hi: int = 4) -> list[str]:
    """Y hệt analyzer="char_wb" của scikit-learn (kiểm bằng test so với bản sklearn)."""
    out: list[str] = []
    for w in _WS.sub(" ", text).split():
        w = f" {w} "
        for n in range(lo, hi + 1):
            offset = 0
            out.append(w[offset:offset + n])
            while offset + n < len(w):
                offset += 1
                out.append(w[offset:offset + n])
            if offset == 0:        # từ ngắn hơn n chỉ tính một lần
                break
    return out


def sigmoid(z: float) -> float:
    return 1 / (1 + math.exp(-z)) if z >= 0 else math.exp(z) / (1 + math.exp(z))


class TfidfLogReg:
    kind = "tfidf"

    def __init__(self, spec: dict):
        self.lo, self.hi = spec["ngram"]
        self.index = {t: i for i, t in enumerate(spec["terms"])}
        self.idf, self.coef, self.bias = spec["idf"], spec["coef"], spec["intercept"]
        self.sublinear = spec.get("sublinear_tf", True)

    def predict(self, text: str) -> float:
        counts: dict[int, int] = {}
        for g in char_wb_ngrams(prep(text), self.lo, self.hi):
            i = self.index.get(g)
            if i is not None:
                counts[i] = counts.get(i, 0) + 1
        if not counts:
            return sigmoid(self.bias)
        vals = {i: ((1 + math.log(c)) if self.sublinear else c) * self.idf[i] for i, c in counts.items()}
        norm = math.sqrt(sum(v * v for v in vals.values())) or 1.0
        return sigmoid(sum(v / norm * self.coef[i] for i, v in vals.items()) + self.bias)


class E5LogReg:
    kind = "e5"

    def __init__(self, spec: dict, embedder: Embedder):
        self.embedder, self.task = embedder, spec.get("task", "RETRIEVAL_DOCUMENT")
        self.coef, self.bias, self.dim = spec["coef"], spec["intercept"], spec["dim"]
        if getattr(embedder, "dim", self.dim) != self.dim:
            raise ModelError(f"Mô hình e5 cần vector {self.dim} chiều, bộ nhúng hiện tại có {embedder.dim}.")

    def predict(self, text: str) -> float:
        v = self.embedder.embed([text], self.task)[0]
        return sigmoid(sum(a * b for a, b in zip(v, self.coef)) + self.bias)


@dataclass(frozen=True)
class Manifest:
    version: str
    recommended: str
    files: dict
    raw: dict


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def read_manifest(model_dir: Path) -> Manifest:
    path = model_dir / "manifest.json"
    if not path.exists():
        raise ModelError(f"Chưa có {path}. Chạy: python -m app.ml.relevance_train")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return Manifest(raw["version"], raw.get("recommended", "tfidf"), raw["files"], raw)


def load_spec(model_dir: Path, kind: str) -> dict:
    man = read_manifest(model_dir)
    info = man.files.get(FILES[kind])
    path = model_dir / FILES[kind]
    if info is None or not path.exists():
        raise ModelError(f"Thiếu mô hình {kind} trong {model_dir}.")
    if sha256_file(path) != info["sha256"]:
        raise ModelError(f"{path.name} sai SHA-256 so với manifest (tệp bị sửa hoặc hỏng).")
    return json.loads(path.read_text(encoding="utf-8"))


class ClassifierScorer:
    """Giao diện RelevanceScorer của G2: điểm = xác suất liên quan nhạc lý (trung bình theo cửa sổ nếu đoạn dài)."""

    def __init__(self, model, version: str, cfg: RelevanceConfig | None = None):
        self.model, self.version, self.cfg = model, version, cfg or relevance_config()
        self.name = f"classifier:{model.kind}@{version}"

    def score(self, text: str) -> Score:
        wins = windows(text)
        if not wins:
            return Score(0.0, 0.0, None, {"scorer": self.name})
        p = sum(self.model.predict(w) for w in wins) / len(wins)
        return Score(p, lexicon_score(text, self.cfg), None, {"scorer": self.name})


def build_scorer(cfg: RelevanceConfig, embedder: Embedder | None) -> ClassifierScorer:
    """Dựng bộ chấm từ thư mục mô hình. Ném ModelError nếu không dùng được."""
    model_dir = Path(cfg.model_dir)
    man = read_manifest(model_dir)
    want = man.recommended if cfg.classifier_model == "auto" else cfg.classifier_model
    if want not in KINDS:
        raise ModelError(f"RELEVANCE_MODEL={cfg.classifier_model!r} không hợp lệ (auto, tfidf, e5).")
    if want == "e5" and embedder is None:
        if cfg.classifier_model == "e5":
            raise ModelError("RELEVANCE_MODEL=e5 nhưng chưa có mô hình nhúng e5.")
        want = "tfidf"                                  # auto: máy không có e5 thì dùng bản chỉ cần chữ
    spec = load_spec(model_dir, want)
    model = TfidfLogReg(spec) if want == "tfidf" else E5LogReg(spec, embedder)
    return ClassifierScorer(model, man.version, cfg)


@lru_cache(maxsize=4)
def _cached(model_dir: str, choice: str, has_e5: bool, mtime: float):
    from .scorer import _default_embedder

    cfg = relevance_config()
    return build_scorer(cfg, _default_embedder() if has_e5 else None)


def classifier_scorer(cfg: RelevanceConfig, embedder: Embedder | None) -> ClassifierScorer | None:
    """None (và ghi cảnh báo) khi không dùng được mô hình: cổng vẫn chạy bằng bộ chấm hybrid, không hỏng việc tải tài liệu."""
    try:
        manifest = Path(cfg.model_dir) / "manifest.json"
        return _cached(cfg.model_dir, cfg.classifier_model, embedder is not None,
                       manifest.stat().st_mtime if manifest.exists() else 0.0)
    except (ModelError, OSError, KeyError, ValueError) as exc:
        log.warning("relevance_classifier_unavailable reason=%s", exc)
        return None
