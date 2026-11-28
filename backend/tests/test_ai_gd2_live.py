"""Kiểm tầng nội dung với Gemini thật (đánh dấu live, CI không chạy).

    cd backend && RUN_LIVE=1 AI_ENABLED=1 GEMINI_API_KEY=... pytest -q -m live tests/test_ai_gd2_live.py
"""

from __future__ import annotations

import os

import pytest

from app.ai.embedder import get_embedder
from app.ai.recommender.content import embedding_content
from app.content import skill_descriptions as sd
from app.core.config import Settings

pytestmark = [pytest.mark.live,
              pytest.mark.skipif(os.getenv("RUN_LIVE") != "1", reason="cần RUN_LIVE=1 và khóa Gemini")]

# Mục tiêu → kỹ năng phải nằm trong top 3 theo nghĩa (không phải theo chữ trùng).
CASES = [
    ("Mình muốn đệm hát nhạc pop bằng guitar", {"chord.triad_build", "function.progression", "chord.seventh_build",
                                                "chord.triad_formula"}),
    ("Tôi muốn chơi piano jazz", {"progression.ii_v_i", "chord.seventh_quality", "chord.seventh_build"}),
    ("Học đọc tên nốt thăng giáng trên bản nhạc", {"pitch.spelling"}),
]


@pytest.mark.parametrize("goal,expected", CASES)
def test_goal_matches_relevant_skills(goal, expected):
    embedder = get_embedder(Settings())
    assert embedder is not None and embedder.model == sd.load_embeddings()["model"]
    goal_vec = embedder.embed([goal], "RETRIEVAL_QUERY")[0]
    vecs = {s: r["vector"] for s, r in sd.load_embeddings()["skills"].items()}
    scores = embedding_content(goal_vec, vecs)
    top3 = sorted(scores, key=scores.get, reverse=True)[:3]
    assert set(top3) & expected, (goal, [(s, round(scores[s], 3)) for s in top3])
