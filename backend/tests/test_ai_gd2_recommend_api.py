"""GĐ2 qua API thật: GET /api/v1/recommend (ba danh sách G-3 cách B), PUT /api/v1/me/goal,
nhật ký gợi ý, xác thực, V7 (lượt is_test) và quy tắc chỉ gửi mục tiêu cho dịch vụ embedding."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.ai.embedder import FakeEmbedder
from app.api import ai_recommend
from app.db.models import MasteryState, RecommendationLog, ReviewItem, ReviewState, User
from app.db.session import SessionLocal
from app.main import app
from app.services import recommendation_service as rs
from tests.auth_helpers import answer_lesson_correctly, auth

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def _schema_and_seed():
    with TestClient(app):
        yield


def make_user(role: str = "learner", synthetic: bool = False, **mastery: float) -> str:
    uid = ("syn-" if synthetic else "gd2-") + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="GĐ2", role=role, is_synthetic=synthetic,
                    email=None if synthetic else f"{uid}@example.test"))
        for skill, score in mastery.items():
            db.add(MasteryState(user_id=uid, skill_id=skill.replace("__", "."), score=score, attempts_count=3))
        db.commit()
    return uid


def get(uid: str, role: str = "learner", **params):
    r = client.get("/api/v1/recommend", headers=auth(uid, role), params=params)
    assert r.status_code == 200, r.text
    return r.json()


def ids(items):
    return [x["lesson_id"] for x in items]


def test_requires_login():
    assert client.get("/api/v1/recommend").status_code == 401
    assert client.put("/api/v1/me/goal", json={"goal_text": "x"}).status_code == 401


def test_new_learner_cold_start_only_l01():
    body = get(make_user())
    assert ids(body["next"]) == ["L01"]
    assert body["few_eligible"] is True
    assert body["weights_mode"] == "cold" and body["fallback_reason"] == "no_assessed_dims"
    item = body["next"][0]
    assert item["reason_code"] in {"mastery", "content", "due", "cf"} and item["reason"]
    assert set(item["components"]) == {"content", "mastery", "due", "cf"}
    assert item["components"]["cf"] is None
    assert body["continue"] == [] and body["review"] == []


def test_k_param_bounds():
    uid = make_user()
    assert client.get("/api/v1/recommend", headers=auth(uid), params={"k": 6}).status_code == 422
    assert client.get("/api/v1/recommend", headers=auth(uid), params={"k": 0}).status_code == 422
    assert len(get(uid, k=1)["next"]) <= 1


def test_r2_prereq_gate_through_api():
    # L02 cần pitch.spelling và chord.triad_build ≥ 0,60.
    blocked = get(make_user(pitch__spelling=0.9, chord__triad_build=0.59))
    assert "L02" not in ids(blocked["next"])
    opened = get(make_user(pitch__spelling=0.9, chord__triad_build=0.60))
    assert "L02" in ids(opened["next"])


def test_g3_three_lists():
    uid = make_user()
    headers = auth(uid)
    assert client.post("/api/v1/lessons/L01/start", headers=headers).status_code == 200
    body = get(uid)
    assert ids(body["continue"]) == ["L01"] and "L01" not in ids(body["next"])

    answer_lesson_correctly(client, "L01", headers)
    assert client.post("/api/v1/lessons/L01/complete", headers=headers).status_code == 200
    body = get(uid)
    assert body["continue"] == []
    assert "L01" not in ids(body["next"])
    # L01 mới làm đúng một lượt mỗi câu nên chưa kỹ năng nào đạt 0,80 → còn để ôn.
    assert ids(body["review"]) == ["L01"] and body["review"][0]["label"] == "Ôn lại"


def test_v7_admin_attempts_do_not_create_vector():
    uid = make_user(role="admin")
    headers = auth(uid, "admin")
    answer_lesson_correctly(client, "L01", headers)
    with SessionLocal() as db:
        assert db.scalars(select(MasteryState).where(MasteryState.user_id == uid)).all() == []
        assert rs.user_vector(db, uid) == rs.build_vector({})


def test_due_card_marks_skill_due():
    uid = make_user(pitch__spelling=0.7, interval__naming=0.7, chord__triad_formula=0.7, chord__triad_build=0.7)
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        item = db.scalar(select(ReviewItem).where(ReviewItem.lesson_id == "L01",
                                                  ReviewItem.skill_id == "interval.naming"))
        db.add(ReviewState(user_id=uid, review_item_id=item.id, due_at=now - timedelta(hours=1)))
        db.commit()
        assert "interval.naming" in rs.due_skills(db, uid, now)


def test_knn_uses_synthetic_pool_when_few_real_users():
    vec = dict(pitch__spelling=0.7, interval__naming=0.6, chord__triad_formula=0.65, chord__triad_build=0.7)
    for _ in range(3):
        make_user(synthetic=True, scale__major=0.8, **vec)
    body = get(make_user(**vec))
    assert body["cf_source"] == "synthetic"
    assert body["weights_mode"] == "full" and body["neighbors_count"] >= 3
    l02 = next(x for x in body["next"] if x["lesson_id"] == "L02")
    assert l02["components"]["cf"] is not None


def test_recommendation_log_and_click():
    uid = make_user()
    body = get(uid)
    with SessionLocal() as db:
        log = db.get(RecommendationLog, body["log_id"])
        assert log.user_id == uid and log.lesson_ids == ids(body["next"])
    r = client.post(f"/api/v1/recommend/{body['log_id']}/click", headers=auth(uid), json={"lesson_id": "L01"})
    assert r.status_code == 204
    with SessionLocal() as db:
        assert db.get(RecommendationLog, body["log_id"]).clicked_lesson_id == "L01"
    other = make_user()
    r = client.post(f"/api/v1/recommend/{body['log_id']}/click", headers=auth(other), json={"lesson_id": "L01"})
    assert r.status_code == 404


def test_click_on_lesson_not_in_list_rejected():
    uid = make_user()
    body = get(uid)
    r = client.post(f"/api/v1/recommend/{body['log_id']}/click", headers=auth(uid), json={"lesson_id": "L04"})
    assert r.status_code == 422


# --- Mục tiêu ---------------------------------------------------------------------------------

def test_goal_roundtrip_and_limits():
    uid = make_user()
    h = auth(uid)
    assert client.put("/api/v1/me/goal", headers=h, json={"goal_text": "a" * 501}).status_code == 422
    r = client.put("/api/v1/me/goal", headers=h, json={"goal_text": "  Đệm hát nhạc pop  "})
    assert r.status_code == 200 and r.json()["goal_text"] == "Đệm hát nhạc pop"
    assert client.get("/api/v1/me/goal", headers=h).json()["goal_text"] == "Đệm hát nhạc pop"
    r = client.put("/api/v1/me/goal", headers=h, json={"goal_text": "   "})
    assert r.status_code == 200 and r.json()["goal_text"] is None


def test_goal_ai_disabled_never_embeds(monkeypatch):
    monkeypatch.setattr(rs, "settings", replace(rs.settings, ai_enabled=False, gemini_api_key="k"))
    uid = make_user()
    r = client.put("/api/v1/me/goal", headers=auth(uid), json={"goal_text": "đệm hát pop"})
    assert r.json()["embedded"] is False
    with SessionLocal() as db:
        assert db.get(User, uid).goal_embedding is None


def test_goal_embedding_payload_is_goal_only():
    fake = FakeEmbedder()
    app.dependency_overrides[ai_recommend.embedder_dep] = lambda: fake
    try:
        uid = make_user()
        r = client.put("/api/v1/me/goal", headers=auth(uid), json={"goal_text": "đệm hát pop"})
        assert r.json()["embedded"] is True
    finally:
        app.dependency_overrides.pop(ai_recommend.embedder_dep, None)
    # Chỉ đúng văn bản mục tiêu được gửi đi: không email, tên hay user_id (SRS 03 Bảng 3).
    assert fake.calls == [(["đệm hát pop"], "RETRIEVAL_QUERY")]
    with SessionLocal() as db:
        user = db.get(User, uid)
        assert user.goal_embedding_model == fake.model and len(user.goal_embedding) == fake.dim


def test_goal_drives_content_with_local_fallback(monkeypatch):
    # AI tắt + mô tả kỹ năng còn nháp: chỉ dùng khi bật ALLOW_DRAFT_SKILL_DESCRIPTIONS.
    monkeypatch.setattr(rs, "settings", replace(rs.settings, allow_draft_skill_descriptions=True))
    uid = make_user()
    client.put("/api/v1/me/goal", headers=auth(uid), json={"goal_text": "quãng và tên nốt"})
    body = get(uid)
    assert body["content_source"] == "tfidf" and body["draft_descriptions"] is True
    assert body["next"][0]["components"]["content"] > 0


def test_draft_descriptions_off_means_no_content(monkeypatch):
    monkeypatch.setattr(rs, "settings", replace(rs.settings, allow_draft_skill_descriptions=False))
    uid = make_user()
    client.put("/api/v1/me/goal", headers=auth(uid), json={"goal_text": "quãng và tên nốt"})
    body = get(uid)
    assert body["content_source"] == "none"
    assert body["next"][0]["components"]["content"] == 0
