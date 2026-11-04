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
    assert body["mode"] == "cold_start"
    item = body["next"][0]
    # Đề GĐ2 mục 6: người mới chưa làm gì, chưa có mục tiêu → L01 "bắt đầu từ nền tảng".
    assert item["reason_code"] == "foundation" and "nền tảng" in item["reason"]
    assert set(item["components"]) == {"content", "mastery", "due", "cf"}
    assert item["components"]["cf"] is None
    assert body["continue"] == [] and body["review"] == []


def test_k_param_bounds():
    # Lỗi kiểm tra đầu vào của dự án trả 400 VALIDATION_ERROR (core/errors.py), không phải 422 mặc định.
    uid = make_user()
    assert client.get("/api/v1/recommend", headers=auth(uid), params={"k": 6}).status_code == 400
    assert client.get("/api/v1/recommend", headers=auth(uid), params={"k": 0}).status_code == 400
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


def test_knn_uses_synthetic_pool_when_few_real_users(monkeypatch):
    # CSDL dev dùng chung giữa các lần chạy tích lũy người thật từ test khác: ép "chưa đủ người thật" cho chắc.
    from app.services import recommendation_service as rs_mod

    monkeypatch.setattr(rs_mod, "settings", replace(rs_mod.settings, knn_real_min_users=10**6))
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
    assert client.put("/api/v1/me/goal", headers=h, json={"goal_text": "a" * 501}).status_code == 400
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


def _fake_store(fake):
    from app.content import skill_descriptions as sd
    from app.ai.skill_mapping import is_mvp

    rows = {k: v for k, v in sd.load_descriptions().items() if is_mvp(k)}
    vecs = fake.embed([rows[k]["text"] for k in sorted(rows)], "RETRIEVAL_DOCUMENT")
    return {"model": fake.model, "dim": fake.dim,
            "skills": {k: {"hash": sd.description_hash(rows[k]["text"]), "vector": v} for k, v in zip(sorted(rows), vecs)}}


def test_goal_embedding_drives_content(monkeypatch):
    fake = FakeEmbedder()
    monkeypatch.setattr(rs, "settings", replace(rs.settings, allow_draft_skill_descriptions=True))
    monkeypatch.setattr(rs.sd, "load_embeddings", lambda: _fake_store(fake))
    app.dependency_overrides[ai_recommend.embedder_dep] = lambda: fake
    # Vector giả không mang nghĩa, nên lấy đúng mô tả của pitch.spelling làm mục tiêu: cosine = 1 với kỹ năng đó.
    from app.content import skill_descriptions as sd

    goal = sd.load_descriptions()["pitch.spelling"]["text"]
    try:
        uid = make_user()
        client.put("/api/v1/me/goal", headers=auth(uid), json={"goal_text": goal})
        body = get(uid)
    finally:
        app.dependency_overrides.pop(ai_recommend.embedder_dep, None)
    # Đạt đã duyệt 26 mô tả (04/11) nên không còn dùng mô tả nháp.
    assert body["content_source"] == "embedding" and body["draft_descriptions"] is False
    l01 = body["next"][0]
    assert l01["lesson_id"] == "L01" and l01["components"]["content"] >= 0.25  # 4 kỹ năng, một kỹ năng = 1


def test_no_embedding_means_content_zero(monkeypatch):
    # AI tắt: có mục tiêu nhưng không có vector → content = 0, không gán số khác (đề GĐ2 mục 2).
    monkeypatch.setattr(rs, "settings", replace(rs.settings, allow_draft_skill_descriptions=True, ai_enabled=False))
    uid = make_user()
    client.put("/api/v1/me/goal", headers=auth(uid), json={"goal_text": "quãng và tên nốt"})
    body = get(uid)
    assert body["content_source"] == "none"
    assert body["next"][0]["components"]["content"] == 0


def test_draft_descriptions_off_means_no_content(monkeypatch):
    # Giả lập mọi mô tả còn nháp: tắt cờ thì tầng nội dung không được dùng chúng.
    fake = FakeEmbedder()
    real = rs.sd.load_descriptions()
    monkeypatch.setattr(rs.sd, "load_descriptions", lambda: {k: dict(v, status="draft") for k, v in real.items()})
    monkeypatch.setattr(rs, "settings", replace(rs.settings, allow_draft_skill_descriptions=False))
    monkeypatch.setattr(rs.sd, "load_embeddings", lambda: _fake_store(fake))
    app.dependency_overrides[ai_recommend.embedder_dep] = lambda: fake
    try:
        uid = make_user()
        client.put("/api/v1/me/goal", headers=auth(uid), json={"goal_text": "quãng và tên nốt"})
        body = get(uid)
    finally:
        app.dependency_overrides.pop(ai_recommend.embedder_dep, None)
    assert body["content_source"] == "none"
    assert body["next"][0]["components"]["content"] == 0


def test_cf_can_be_switched_off(monkeypatch):
    monkeypatch.setattr(rs, "settings", replace(rs.settings, reco_use_cf=False))
    vec = dict(pitch__spelling=0.7, interval__naming=0.6, chord__triad_formula=0.65, chord__triad_build=0.7)
    make_user(synthetic=True, **vec)
    body = get(make_user(**vec))
    assert body["mode"] == "fallback" and body["fallback_reason"] == "cf_disabled" and body["neighbors_count"] == 0


def test_weights_come_from_config(monkeypatch):
    monkeypatch.setattr(rs, "settings", replace(rs.settings, reco_weights="0.10,0.70,0.10,0.10"))
    body = get(make_user(pitch__spelling=0.5))
    l01 = body["next"][0]
    # Người chưa có láng giềng: content 0,10 + cf 0,10 = 0,20; (1 − mastery) nhân 0,70.
    c = l01["components"]
    assert l01["score"] == pytest.approx(0.20 * c["content"] + 0.70 * (1 - c["mastery"]) + 0.10 * c["due"], abs=1e-3)


# --- Rà soát GĐ1–GĐ2 (04/11, C3 Thắng duyệt): đổi mô hình hoặc số chiều embedding ---------------------------

def _user_with_goal_vector(model: str, dim: int) -> str:
    uid = make_user()
    with SessionLocal() as db:
        user = db.get(User, uid)
        user.goal_text, user.goal_embedding, user.goal_embedding_model = "đệm hát pop", [0.1] * dim, model
        db.commit()
    return uid


def test_r1_goal_vector_of_old_model_is_recomputed(monkeypatch):
    # Vector mục tiêu tính bằng mô hình cũ không so được với vector kỹ năng: phải tính lại một lần, không "none" mãi.
    fake = FakeEmbedder()
    store = _fake_store(fake)
    fake.calls.clear()
    monkeypatch.setattr(rs.sd, "load_embeddings", lambda: store)
    uid = _user_with_goal_vector("text-embedding-004", fake.dim)
    with SessionLocal() as db:
        out = rs.recommend_for_user(db, db.get(User, uid), embedder=fake)
    assert fake.calls == [(["đệm hát pop"], "RETRIEVAL_QUERY")]  # chỉ văn bản mục tiêu (03 Bảng 3)
    n = len(fake.calls)
    assert out["content_source"] == "embedding"
    with SessionLocal() as db:
        assert db.get(User, uid).goal_embedding_model == fake.model
    with SessionLocal() as db:  # lần sau dùng lại, không gọi thêm
        rs.recommend_for_user(db, db.get(User, uid), embedder=fake)
    assert len(fake.calls) == n


def test_r2_dimension_mismatch_does_not_break_recommend(monkeypatch):
    # Cùng tên mô hình nhưng khác số chiều (đổi EMBEDDING_DIM mà chưa tính lại file): trước đây lỗi 500.
    fake = FakeEmbedder()
    monkeypatch.setattr(rs.sd, "load_embeddings", lambda: _fake_store(fake))
    uid = _user_with_goal_vector(fake.model, fake.dim * 2)
    body = get(uid)
    assert body["content_source"] == "none"
    assert all(x["components"]["content"] == 0 for x in body["next"])


def test_r2_embedder_with_other_dim_is_not_called_every_request(monkeypatch):
    # Embedder hiện tại cho số chiều khác file kỹ năng: tính lại cũng vô ích, nên không gọi Gemini mỗi lượt.
    store_fake, other = FakeEmbedder(), FakeEmbedder(dim=128)
    store = _fake_store(store_fake)
    monkeypatch.setattr(rs.sd, "load_embeddings", lambda: store)
    uid = _user_with_goal_vector(store_fake.model, 128)
    with SessionLocal() as db:
        out = rs.recommend_for_user(db, db.get(User, uid), embedder=other)
    assert other.calls == [] and out["content_source"] == "none"


def test_r2_skill_vector_of_wrong_length_is_skipped(monkeypatch):
    fake = FakeEmbedder()
    store = _fake_store(fake)
    broken = next(iter(store["skills"]))
    store["skills"][broken]["vector"] = store["skills"][broken]["vector"][:10]
    monkeypatch.setattr(rs.sd, "load_embeddings", lambda: store)
    uid = make_user()
    with SessionLocal() as db:
        user = db.get(User, uid)
        user.goal_text = "đệm hát pop"
        rs.embed_goal(db, user, fake)
        db.commit()
        content, source, _ = rs.content_scores(user)
    assert source == "embedding" and broken not in content and content


def test_startup_warns_when_embedding_config_differs_from_skill_file(monkeypatch):
    store = rs.sd.load_embeddings()
    on = replace(rs.settings, ai_enabled=True)
    assert rs.embedding_config_mismatch(replace(on, gemini_embed_model=store["model"], gemini_embed_dim=store["dim"])) is None
    msg = rs.embedding_config_mismatch(replace(on, gemini_embed_model=store["model"], gemini_embed_dim=1536))
    assert msg and "1536" in msg and "build_skill_embeddings" in msg
    assert rs.embedding_config_mismatch(replace(rs.settings, ai_enabled=False, gemini_embed_dim=1536)) is None
