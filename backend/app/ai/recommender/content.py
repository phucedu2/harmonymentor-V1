"""Tầng nội dung: content = max(0, cosine(vector mục tiêu, vector mô tả kỹ năng)).

Không có mục tiêu hoặc không có embedding (AI tắt, Gemini lỗi, khác mô hình): content = 0 và response ghi
`content_source: none`, không gán số nào khác (đề GĐ2 mục 2). Các tầng còn lại vẫn chạy (nguyên tắc 3)."""

from __future__ import annotations

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
