"""Rà soát GĐ2 câu C8 (Thắng duyệt 04/11/2026): /recommend chạy thật trên PostgreSQL, không chỉ SQLite.

Cùng cách cô lập với HM-010: schema ngẫu nhiên trong CSDL tên kết thúc `_test`, xóa đúng schema đó khi xong.
Kiểm: người mới được gợi ý L01 (nền tảng); làm xong L01 thì /recommend vẫn 200 và ghi nhật ký; bấm gợi ý ghi
clicked_lesson_id; PUT /me/goal khi AI tắt lưu chữ, không lưu vector; làm xong L01 (không placement) thì L02 vào
danh sách "next".
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.orm import Session, sessionmaker

from app.api import ai_recommend
from app.core.config import settings
from app.db.base import Base
from app.db.models import RecommendationLog, User
from app.db.seed import seed_database
from app.db.session import get_db
from app.main import app
from tests.auth_helpers import answer_lesson_correctly, auth
from tests.pg_test_db import create_isolated_engine, drop_isolated_schema, new_schema_name, unsafe_reason

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")
UNSAFE_REASON = unsafe_reason(TEST_DATABASE_URL, settings.database_url)

pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(UNSAFE_REASON is not None, reason=UNSAFE_REASON or ""),
]


@pytest.fixture(scope="module")
def factory():
    schema = new_schema_name()
    engine = create_isolated_engine(TEST_DATABASE_URL, schema)
    try:
        with engine.connect() as conn:
            assert conn.execute(text("SELECT current_schema()")).scalar() == schema
        from app.db import models  # noqa: F401

        Base.metadata.create_all(engine)
        make = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)
        with make() as db:
            seed_database(db)
        yield make
    finally:
        engine.dispose()
        drop_isolated_schema(TEST_DATABASE_URL, schema)


@pytest.fixture()
def client(factory):
    def override_get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[ai_recommend.embedder_dep] = lambda: None  # không gọi mạng
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(ai_recommend.embedder_dep, None)


def new_user(factory) -> str:
    uid = "pgrec-" + uuid4().hex[:10]
    with factory() as db:
        db.add(User(id=uid, display_name="pg", email=f"{uid}@example.test"))
        db.commit()
    return uid


def recommend(client, uid):
    r = client.get("/api/v1/recommend", headers=auth(uid))
    assert r.status_code == 200, r.text
    return r.json()


def test_new_learner_gets_foundation_lesson(client, factory):
    body = recommend(client, new_user(factory))
    assert [x["lesson_id"] for x in body["next"]][:1] == ["L01"]
    assert body["next"][0]["reason_code"] == "foundation"


def test_after_l01_recommend_logs_and_click_is_recorded(client, factory):
    uid = new_user(factory)
    answer_lesson_correctly(client, "L01", auth(uid))
    assert client.post("/api/v1/lessons/L01/complete", headers=auth(uid)).status_code == 200
    body = recommend(client, uid)
    assert "L01" not in [x["lesson_id"] for x in body["next"]]
    shown = [x["lesson_id"] for x in body["next"] + body["review"]]
    assert shown, body
    r = client.post(f"/api/v1/recommend/{body['log_id']}/click", headers=auth(uid), json={"lesson_id": shown[0]})
    assert r.status_code == 204, r.text
    with factory() as db:
        log = db.get(RecommendationLog, body["log_id"])
        assert log.user_id == uid and log.clicked_lesson_id == shown[0] and log.clicked_at is not None
    # Lượt gợi ý của người khác → 404 (nguyên tắc 4).
    other = new_user(factory)
    r = client.post(f"/api/v1/recommend/{body['log_id']}/click", headers=auth(other), json={"lesson_id": shown[0]})
    assert r.status_code == 404


def test_goal_saved_without_vector_when_ai_off(client, factory):
    uid = new_user(factory)
    r = client.put("/api/v1/me/goal", headers=auth(uid), json={"goal_text": "đệm hát pop bằng piano"})
    assert r.status_code == 200 and r.json() == {"goal_text": "đệm hát pop bằng piano", "embedded": False,
                                                 "embedding_model": None}
    assert recommend(client, uid)["next"]


def test_l02_suggested_after_l01_without_placement(client, factory):
    # 6 câu demo 10/11 đã phát hành: pitch.spelling đủ 3 câu nên L02 mở mà không cần placement.
    uid = new_user(factory)
    answer_lesson_correctly(client, "L01", auth(uid))
    assert client.post("/api/v1/lessons/L01/complete", headers=auth(uid)).status_code == 200
    assert "L02" in [x["lesson_id"] for x in recommend(client, uid)["next"]]
