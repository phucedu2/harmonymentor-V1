"""RS-27: "mình nên học bài nào tiếp" là câu tư vấn lộ trình, trả lời bằng hệ gợi ý (không từ chối, không gọi AI)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.ai.tutor.router import study_advice
from app.api import ai_tutor
from app.db.models import User
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import auth

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def _schema_and_seed():
    with TestClient(app):
        yield


@pytest.fixture(autouse=True)
def _no_ai():
    app.dependency_overrides[ai_tutor.embedder_dep] = lambda: None
    app.dependency_overrides[ai_tutor.provider_dep] = lambda: None
    yield
    app.dependency_overrides.pop(ai_tutor.embedder_dep, None)
    app.dependency_overrides.pop(ai_tutor.provider_dep, None)


@pytest.mark.parametrize("q", ["mình nên học bài nào tiếp", "minh nen hoc bai nao tiep", "học gì tiếp bây giờ",
                               "bài tiếp theo là bài nào", "gợi ý bài cho mình", "lộ trình học của mình"])
def test_nhan_ra_cau_hoi_lo_trinh(q):
    assert study_advice(q)


@pytest.mark.parametrize("q", ["hợp âm là gì", "C la not gi vay", "ii-V-I là gì", "thời tiết hôm nay thế nào"])
def test_khong_nham_cau_khac(q):
    assert not study_advice(q)


def test_tra_loi_bang_he_goi_y():
    uid = "rs27-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="RS-27", email=f"{uid}@example.test"))
        db.commit()
    r = client.post("/api/v1/chat/message", json={"message": "mình nên học bài nào tiếp"}, headers=auth(uid))
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["flow"] == "D" and j["intent"] == "study_advice" and j["status"] == "ok"
    assert "Mình chỉ là trợ lý âm nhạc" not in j["reply"]
    # Người mới chưa học bài nào: gợi ý phải có ít nhất một bài, và bài gợi ý là bài thật.
    assert j["suggested_lesson"]["lesson_id"].startswith("L")
    assert j["suggested_lesson"]["lesson_id"] in j["reply"]
