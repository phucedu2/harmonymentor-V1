"""Phân loại ý định câu hỏi chạy cục bộ (quyết định 7A, kế hoạch AI Tutor 02/11).

TF-IDF n-gram ký tự (2–4, trong ranh giới từ) + LogisticRegression, huấn luyện lúc dùng lần đầu từ
intent_data.json (~150 câu, dưới 1 giây). n-gram ký tự chịu được gõ không dấu và sai chính tả nhẹ, việc
mà tách từ tiếng Việt đơn giản làm kém. Kết quả dùng để: chặn câu ngoài phạm vi trước khi gọi LLM,
và đối chiếu với intent LLM trả về (LLM không được tự nâng câu ngoài phạm vi thành câu nhạc lý)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .bm25 import strip_accents

DATA_PATH = Path(__file__).with_name("intent_data.json")
INTENTS = ("concept", "explain_error", "quiz", "study_advice", "composition", "out_of_scope")


@dataclass(frozen=True)
class IntentResult:
    intent: str
    confidence: float


def _prep(text: str) -> str:
    # Gộp bản có dấu và bản bỏ dấu để câu gõ không dấu gần với câu mẫu có dấu.
    low = " ".join(text.lower().split())
    return f"{low} | {strip_accents(low)}"


def load_data(path: Path = DATA_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _pairs(split: dict) -> tuple[list[str], list[str]]:
    xs, ys = [], []
    for label, rows in split.items():
        for r in rows:
            xs.append(_prep(r))
            ys.append(label)
    return xs, ys


@lru_cache(maxsize=1)
def model():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    xs, ys = _pairs(load_data()["train"])
    pipe = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True, min_df=1),
                         LogisticRegression(C=10.0, max_iter=2000, random_state=0))
    pipe.fit(xs, ys)
    return pipe


def classify(text: str) -> IntentResult:
    pipe = model()
    probs = pipe.predict_proba([_prep(text)])[0]
    best = int(probs.argmax())
    return IntentResult(str(pipe.classes_[best]), round(float(probs[best]), 4))


def evaluate() -> dict:
    """Độ chính xác trên tập test cố định, để ghi vào báo cáo."""
    xs, ys = _pairs(load_data()["test"])
    pred = model().predict(xs)
    wrong = [(x.split(" | ")[0], y, p) for x, y, p in zip(xs, ys, pred) if y != p]
    return {"n": len(ys), "accuracy": round(1 - len(wrong) / len(ys), 4), "wrong": wrong}
