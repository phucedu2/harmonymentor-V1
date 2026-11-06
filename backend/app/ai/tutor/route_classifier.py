"""Tầng 1 của bộ định tuyến AI Tutor (ADR-017): đoán loại câu theo câu chữ, chạy cục bộ, miễn phí, < 5 ms.

4 nhãn: nhac_ly, huong_dan, chao_hoi, ngoai_pham_vi. Cùng kỹ thuật với intent.py (TF-IDF n-gram ký tự 2–4 +
LogisticRegression) vì đã chứng minh chịu được câu không dấu, gõ tắt. Bộ này là baseline để so với mô hình
fine-tune ở GĐ2b; dữ liệu train cũng là dữ liệu fine-tune.

Nhãn KHÔNG quyết định luồng A hay B: "Csus4 gồm nốt gì" và "C7 khác Cmaj7" đều là nhac_ly; kho có đoạn trả
lời được thì là A, không có thì là B. Phần đó do tầng 2 (điểm truy xuất + Music Engine) quyết."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .intent import _prep

DATA_PATH = Path(__file__).with_name("route_data.json")
LABELS = ("nhac_ly", "huong_dan", "chao_hoi", "ngoai_pham_vi")


@dataclass(frozen=True)
class RouteLabel:
    label: str
    confidence: float
    probs: dict[str, float]


def load_data(path: Path = DATA_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pairs(split: dict) -> tuple[list[str], list[str]]:
    xs, ys = [], []
    for label, rows in split.items():
        for r in rows:
            xs.append(_prep(r))
            ys.append(label)
    return xs, ys


def train(xs: list[str], ys: list[str]):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    pipe = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True, min_df=1),
                         LogisticRegression(C=10.0, max_iter=3000, random_state=0))
    pipe.fit(xs, ys)
    return pipe


@lru_cache(maxsize=1)
def model():
    return train(*pairs(load_data()["train"]))


def classify_route(text: str) -> RouteLabel:
    pipe = model()
    probs = pipe.predict_proba([_prep(text)])[0]
    best = int(probs.argmax())
    return RouteLabel(str(pipe.classes_[best]), round(float(probs[best]), 4),
                      {str(c): round(float(p), 4) for c, p in zip(pipe.classes_, probs)})
