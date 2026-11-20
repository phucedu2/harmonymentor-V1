"""Embedder (Gemini/Fake), chuẩn hóa vector, bộ nhớ đệm theo hash, mô tả kỹ năng và tầng nội dung.
Không gọi mạng: lớp Gemini được thử bằng client giả."""

from __future__ import annotations

import json
import math
from types import SimpleNamespace

import pytest

from app.ai import embedder as emb
from app.ai.recommender import content as ct
from app.ai.skill_mapping import SKILL_MAPPING, is_mvp
from app.content import skill_descriptions as sd
from app.core.config import Settings, check_runtime_settings


def norm(v):
    return math.sqrt(sum(x * x for x in v))


def test_normalize_unit_length_and_zero_rejected():
    assert norm(emb.normalize([3.0, 4.0])) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        emb.normalize([0.0, 0.0])


def test_fake_embedder_deterministic_unit_vectors():
    a, b = emb.FakeEmbedder(), emb.FakeEmbedder()
    va, vb = a.embed(["đệm hát pop"], "RETRIEVAL_QUERY")[0], b.embed(["đệm hát pop"], "RETRIEVAL_QUERY")[0]
    assert va == vb and len(va) == a.dim and norm(va) == pytest.approx(1.0)
    assert a.embed(["jazz"], "RETRIEVAL_QUERY")[0] != va


class _FakeModels:
    def __init__(self):
        self.calls = []

    def embed_content(self, *, model, contents, config):
        self.calls.append((model, list(contents), config.task_type, config.output_dimensionality))
        # Gemini trả vector chưa chuẩn hóa ở 768 chiều (GĐ0 đã đo).
        return SimpleNamespace(embeddings=[SimpleNamespace(values=[2.0] * config.output_dimensionality)
                                           for _ in contents])


def test_gemini_embedder_normalizes_and_sends_only_texts():
    models = _FakeModels()
    g = emb.GeminiEmbedder(api_key="k", model="gemini-embedding-001", dim=768,
                           client=SimpleNamespace(models=models))
    out = g.embed(["đệm hát pop"], "RETRIEVAL_QUERY")
    assert norm(out[0]) == pytest.approx(1.0) and len(out[0]) == 768
    assert models.calls == [("gemini-embedding-001", ["đệm hát pop"], "RETRIEVAL_QUERY", 768)]


def test_gemini_errors_become_unavailable():
    class Boom:
        def embed_content(self, **_):
            raise RuntimeError("503")
    g = emb.GeminiEmbedder(api_key="k", model="m", dim=8, client=SimpleNamespace(models=Boom()))
    with pytest.raises(emb.EmbeddingUnavailable):
        g.embed(["x"], "RETRIEVAL_QUERY")


def test_cache_by_hash_avoids_second_call():
    fake = emb.FakeEmbedder()
    cached = emb.CachedEmbedder(fake)
    cached.embed(["a", "b"], "RETRIEVAL_QUERY")
    cached.embed(["b", "a", "c"], "RETRIEVAL_QUERY")
    assert fake.calls == [(["a", "b"], "RETRIEVAL_QUERY"), (["c"], "RETRIEVAL_QUERY")]
    assert emb.text_hash("m", "T", "a") != emb.text_hash("m", "T2", "a")


def test_factory_off_without_flag_or_key():
    assert emb.get_embedder(Settings(ai_enabled=False, gemini_api_key="k")) is None
    assert emb.get_embedder(Settings(ai_enabled=True, gemini_api_key="")) is None


def test_key_never_in_repr():
    g = emb.GeminiEmbedder(api_key="SECRET-KEY-123", model="m", dim=8, client=SimpleNamespace(models=None))
    assert "SECRET" not in repr(g) and "SECRET" not in str(vars(g).get("model"))


# --- Mô tả kỹ năng ----------------------------------------------------------------------------

def test_descriptions_cover_every_skill_and_are_draft_with_source():
    rows = sd.load_descriptions()
    assert set(rows) == set(SKILL_MAPPING)
    for skill, row in rows.items():
        assert row["status"] in {"draft", "approved"}, skill
        assert 30 <= len(row["text"]) <= 600, skill
        assert row["source"], skill


def test_skill_embeddings_match_descriptions():
    # Sửa mô tả mà quên chạy lại build_skill_embeddings thì test này báo.
    store = sd.load_embeddings()
    rows = sd.load_descriptions()
    assert store["dim"] == len(next(iter(store["skills"].values()))["vector"])
    for skill in rows:
        if not is_mvp(skill):
            continue
        assert store["skills"][skill]["hash"] == sd.description_hash(rows[skill]["text"]), skill
        assert norm(store["skills"][skill]["vector"]) == pytest.approx(1.0, abs=1e-4)


def test_usable_descriptions_respect_status():
    rows = {"a": {"text": "x" * 40, "status": "draft", "source": "s"},
            "b": {"text": "y" * 40, "status": "approved", "source": "s"}}
    assert set(sd.usable(rows, allow_draft=False)) == {"b"}
    assert set(sd.usable(rows, allow_draft=True)) == {"a", "b"}


def test_production_rejects_draft_descriptions():
    with pytest.raises(RuntimeError, match="ALLOW_DRAFT_SKILL_DESCRIPTIONS"):
        check_runtime_settings(Settings(app_env="production", allow_draft_skill_descriptions=True))


# --- Tầng nội dung ----------------------------------------------------------------------------

def test_cosine_content_clamped_to_unit_interval():
    goal = emb.normalize([1.0, 0.0])
    scores = ct.embedding_content(goal, {"same": [1.0, 0.0], "opposite": [-1.0, 0.0], "half": emb.normalize([1.0, 1.0])})
    assert scores["same"] == pytest.approx(1.0)
    assert scores["opposite"] == 0.0
    assert scores["half"] == pytest.approx(math.sqrt(0.5))


def test_embeddings_file_is_valid_json_without_key():
    raw = sd.EMBEDDINGS_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    assert data["model"] and "AIza" not in raw
