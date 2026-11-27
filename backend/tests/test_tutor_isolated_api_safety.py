"""Synthetic HTTP regression; only runs against an explicitly named SQLite test file."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def isolated_client(monkeypatch):
    expected = os.environ.get("HM_ISOLATED_TEST_DB", "")
    url = os.environ.get("DATABASE_URL", "")
    if not expected or not Path(expected).name.startswith("hm_tutor_isolated_"):
        pytest.skip("Requires explicitly isolated synthetic SQLite database")
    if url != "sqlite:///" + expected.replace("\\", "/"):
        pytest.fail("Refusing to use a non-isolated database")
    from app.api import ai_tutor
    from app.db.models import User
    from app.db.session import SessionLocal
    from app.main import app
    from app.services import ai_tutor_service as ts
    from tests.auth_helpers import auth

    facts = SimpleNamespace(facts=[], context_note=None)
    lesson = SimpleNamespace(method="synthetic", best_score=0, fallback_reason=None)
    decision = SimpleNamespace(engine=facts, lesson=lesson, hits=[], flow="B", kind="unknown",
                               later_lesson=None, nearest_lesson=None, log=lambda: {})
    monkeypatch.setattr(ts, "decide", lambda *args, **kwargs: decision)
    monkeypatch.setattr(ts, "lesson_titles", lambda: {})
    monkeypatch.setattr(ts.supplemental, "answer", lambda question: None)
    monkeypatch.setattr(ts, "classify", lambda question: SimpleNamespace(intent="concept", confidence=1.0))
    app.dependency_overrides[ai_tutor.embedder_dep] = lambda: None
    with TestClient(app) as client:
        uid = "synthetic-" + uuid4().hex
        with SessionLocal() as db:
            # The application blocks login for is_synthetic=True; this account is still
            # entirely fabricated and exists only in the isolated test database.
            db.add(User(id=uid, display_name="Người thử tổng hợp", email=uid + "@example.test", is_synthetic=False))
            db.commit()
        yield client, auth(uid), app, ai_tutor
    app.dependency_overrides.clear()


def test_fake_model_unsupported_lesson_claim_falls_back(isolated_client):
    from app.ai.tutor.llm import FakeProvider
    client, headers, app, ai_tutor = isolated_client
    response = json.dumps({"reply": "Bài học chưa có nội dung về fugue.", "citations": [],
                           "engine_claims": [], "hint_level": 0, "suggested_actions": [], "intent": "concept"},
                          ensure_ascii=False)
    provider = FakeProvider([response, response])
    app.dependency_overrides[ai_tutor.provider_dep] = lambda: provider
    result = client.post("/api/v1/chat/message", headers=headers,
                         json={"message": "Bài học của mình nói gì về fugue?"})
    assert result.status_code == 200, result.text
    data = result.json()
    assert len(provider.calls) == 2
    assert "Bài học chưa có nội dung về fugue" not in data["reply"]
    assert data["citations"] == []
    assert data["fallback_reason"] == "lesson_ungrounded"
