"""Tầng nội dung: content = cosine(vector mục tiêu, vector mô tả kỹ năng), kẹp về [0, 1].

Khi không có embedding (AI tắt, Gemini lỗi, hoặc mô hình của mục tiêu khác mô hình của mô tả),
dùng TF-IDF ký tự cục bộ làm dự phòng có ghi nhãn `tfidf`, để AI_ENABLED=false vẫn chạy trọn vòng."""

from __future__ import annotations

import unicodedata
from typing import Mapping, Sequence

import numpy as np


def embedding_content(goal_vec: Sequence[float], skill_vecs: Mapping[str, Sequence[float]]) -> dict[str, float]:
    g = np.asarray(goal_vec, dtype=float)
    gn = float(np.linalg.norm(g))
    out = {}
    for skill, v in skill_vecs.items():
        sv = np.asarray(v, dtype=float)
        denom = gn * float(np.linalg.norm(sv))
        # Cosine âm nghĩa là "ngược mục tiêu"; điểm nội dung là mức phù hợp nên không xuống dưới 0.
        out[skill] = 0.0 if denom == 0 else max(0.0, min(1.0, float(g @ sv / denom)))
    return out


def _norm_text(text: str) -> str:
    return unicodedata.normalize("NFC", text).lower()


def tfidf_content(goal_text: str | None, texts: Mapping[str, str]) -> dict[str, float]:
    if not goal_text or not goal_text.strip() or not texts:
        return {skill: 0.0 for skill in texts}
    from sklearn.feature_extraction.text import TfidfVectorizer

    skills = sorted(texts)
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), preprocessor=_norm_text)
    matrix = vec.fit_transform([texts[s] for s in skills] + [goal_text])
    sims = (matrix[:-1] @ matrix[-1].T).toarray().ravel()  # TF-IDF đã chuẩn hóa L2 nên tích vô hướng = cosine
    return {s: float(max(0.0, min(1.0, x))) for s, x in zip(skills, sims)}
