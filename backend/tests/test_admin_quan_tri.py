"""Quản trị (điểm lệch 3, ADR-023): sửa bài học có bản nháp/xuất bản/khôi phục, ẩn bài, người dùng, thống kê.

Chạy trên CSDL dùng chung của bộ test, nên mỗi test dọn bản sửa của mình để không làm đổi nội dung các test khác.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db.models import AdminAuditLog, Attempt, ContentRevision, User
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import answer_lesson_correctly, auth


def make_user(role="learner", active=True, synthetic=False):
    uid = f"adm-{uuid4().hex[:12]}"
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="Thử quản trị", email=None if synthetic else f"{uid}@example.test", role=role,
                    is_active=active, is_synthetic=synthetic))
        db.commit()
    return uid


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
    with SessionLocal() as db:  # trả nội dung về như seed
        db.execute(delete(ContentRevision))
        db.commit()


@pytest.fixture()
def admin():
    uid = make_user("admin")
    return uid, auth(uid, "admin")


def first_theory(client, headers, lesson="L11"):
    detail = client.get(f"/api/v1/admin/lessons/{lesson}", headers=headers).json()
    return next(b for b in detail["blocks"] if b["block_type"] == "theory")


def learner_block(client, lesson, block_id):
    body = client.get(f"/api/v1/lessons/{lesson}").json()
    return next(b for b in body["blocks"] if b["id"] == block_id)


@pytest.mark.parametrize("path", ["/lessons", "/users", "/stats", "/audit", "/lessons/L01"])
def test_nguoi_hoc_bi_chan_khoi_quan_tri(client, path):
    learner = auth(make_user())
    assert client.get(f"/api/v1/admin{path}", headers=learner).status_code == 403
    assert client.get(f"/api/v1/admin{path}").status_code == 401


def test_sua_bai_ban_nhap_chua_hien_cho_nguoi_hoc_den_khi_xuat_ban(client, admin):
    _, headers = admin
    block = first_theory(client, headers)
    payload = dict(block["payload"])
    payload["title"] = "1. Vòng hợp âm là gì (đã sửa)"
    saved = client.put(f"/api/v1/admin/lessons/L11/blocks/{block['id']}", headers=headers, json={"payload": payload, "note": "thử"})
    assert saved.status_code == 200, saved.text
    assert learner_block(client, "L11", block["id"])["payload"]["title"] == block["base_payload"]["title"]
    assert first_theory(client, headers)["payload"]["title"].endswith("(đã sửa)")  # Admin xem trước bản nháp
    published = client.post(f"/api/v1/admin/revisions/{saved.json()['revision_id']}/publish", headers=headers, json={})
    assert published.status_code == 200, published.text
    assert learner_block(client, "L11", block["id"])["payload"]["title"].endswith("(đã sửa)")


def test_lich_su_va_khoi_phuc_ve_noi_dung_goc(client, admin):
    _, headers = admin
    block = first_theory(client, headers)
    for suffix in (" A", " B"):
        payload = dict(block["payload"], title=block["base_payload"]["title"] + suffix)
        rev = client.put(f"/api/v1/admin/lessons/L11/blocks/{block['id']}", headers=headers, json={"payload": payload}).json()["revision_id"]
        assert client.post(f"/api/v1/admin/revisions/{rev}/publish", headers=headers, json={}).status_code == 200
    history = client.get(f"/api/v1/admin/lessons/L11/blocks/{block['id']}/history", headers=headers).json()
    assert [h["status"] for h in history].count("published") == 2
    old = next(h for h in history if h["payload"]["title"].endswith(" A"))
    assert client.post(f"/api/v1/admin/lessons/L11/blocks/{block['id']}/restore", headers=headers, json={"revision_id": old["id"]}).status_code == 200
    assert learner_block(client, "L11", block["id"])["payload"]["title"].endswith(" A")
    assert client.post(f"/api/v1/admin/lessons/L11/blocks/{block['id']}/restore", headers=headers, json={}).status_code == 200
    assert learner_block(client, "L11", block["id"])["payload"]["title"] == block["base_payload"]["title"]
    # lịch sử không bị xóa khi khôi phục
    assert len(client.get(f"/api/v1/admin/lessons/L11/blocks/{block['id']}/history", headers=headers).json()) == 4


def test_khong_sua_duoc_truong_khoa_hay_them_truong(client, admin):
    _, headers = admin
    detail = client.get("/api/v1/admin/lessons/L11", headers=headers).json()
    checkpoint = next(b for b in detail["blocks"] if b["block_type"] == "checkpoint")
    locked = dict(checkpoint["payload"], exercise_id="L11-Q02")
    res = client.put(f"/api/v1/admin/lessons/L11/blocks/{checkpoint['id']}", headers=headers, json={"payload": locked})
    assert res.status_code == 422 and "FIELD_LOCKED" in res.text
    extra = dict(checkpoint["payload"], script="<script>")
    assert client.put(f"/api/v1/admin/lessons/L11/blocks/{checkpoint['id']}", headers=headers, json={"payload": extra}).status_code == 422
    assert client.put("/api/v1/admin/lessons/L11/blocks/khong-co", headers=headers, json={"payload": {}}).status_code == 404


def test_engine_bao_cho_sai_nhac_ly_truoc_khi_xuat_ban(client, admin):
    _, headers = admin
    block = first_theory(client, headers)
    payload = dict(block["payload"], paragraphs=["Hợp âm Cmaj7 gồm C E G A."])
    saved = client.put(f"/api/v1/admin/lessons/L11/blocks/{block['id']}", headers=headers, json={"payload": payload}).json()
    assert saved["engine"]["contradicted"] and saved["engine"]["contradicted"][0]["engine"] == "C E G B"
    refused = client.post(f"/api/v1/admin/revisions/{saved['revision_id']}/publish", headers=headers, json={})
    assert refused.status_code == 409 and "ENGINE_FLAGS" in refused.text
    assert learner_block(client, "L11", block["id"])["payload"] == block["base_payload"]
    ok = client.post(f"/api/v1/admin/revisions/{saved['revision_id']}/publish", headers=headers, json={"acknowledge_engine_flags": True})
    assert ok.status_code == 200


def test_an_va_hien_lai_bai_hoc(client, admin):
    _, headers = admin
    assert "L11" in [x["id"] for x in client.get("/api/v1/lessons").json()]
    assert client.post("/api/v1/admin/lessons/L11/visibility", headers=headers, json={"hidden": True}).status_code == 200
    assert "L11" not in [x["id"] for x in client.get("/api/v1/lessons").json()]
    assert client.get("/api/v1/lessons/L11").status_code == 404
    learner = auth(make_user())
    assert client.post("/api/v1/lessons/L11/start", headers=learner).status_code == 404
    assert client.get("/api/v1/learning/overview", headers=learner).json()["total_lessons"] == 8
    listed = {x["id"]: x for x in client.get("/api/v1/admin/lessons", headers=headers).json()}
    assert listed["L11"]["hidden"] is True
    assert client.post("/api/v1/admin/lessons/L11/visibility", headers=headers, json={"hidden": False}).status_code == 200
    assert client.get("/api/v1/lessons/L11").status_code == 200


def test_quan_ly_nguoi_dung_khoa_mo_va_khong_lo_bi_mat(client, admin):
    admin_id, headers = admin
    target = make_user()
    listing = client.get("/api/v1/admin/users", headers=headers, params={"q": target[:10]}).json()
    row = next(u for u in listing["items"] if u["id"] == target)
    assert set(row) == {"id", "email", "display_name", "role", "is_active", "created_at", "lessons_completed", "attempts", "last_activity"}
    assert client.patch(f"/api/v1/admin/users/{admin_id}", headers=headers, json={"is_active": False}).status_code == 409
    assert client.patch(f"/api/v1/admin/users/{target}", headers=headers, json={"is_active": False}).status_code == 200
    assert client.get("/api/v1/me/mastery", headers=auth(target)).status_code == 401  # tài khoản khóa không dùng được token cũ
    assert client.patch(f"/api/v1/admin/users/{target}", headers=headers, json={"is_active": True}).status_code == 200
    assert client.get("/api/v1/me/mastery", headers=auth(target)).status_code == 200
    synthetic = make_user(synthetic=True)
    assert client.patch(f"/api/v1/admin/users/{synthetic}", headers=headers, json={"is_active": False}).status_code == 404
    actions = [a["action"] for a in client.get("/api/v1/admin/audit", headers=headers).json()]
    assert "user.lock" in actions and "user.unlock" in actions


def test_thong_ke_chi_tinh_nguoi_hoc_that_va_bo_luot_thu_cua_admin(client, admin):
    _, headers = admin
    before = client.get("/api/v1/admin/stats", headers=headers).json()
    answer_lesson_correctly(client, "L01", headers)  # lượt của Admin là is_test
    after_admin = client.get("/api/v1/admin/stats", headers=headers).json()
    assert after_admin["totals"]["attempts"] == before["totals"]["attempts"]
    learner = make_user()
    answer_lesson_correctly(client, "L01", auth(learner))
    after = client.get("/api/v1/admin/stats", headers=headers).json()
    assert after["totals"]["attempts"] > before["totals"]["attempts"]
    assert after["totals"]["learners"] == before["totals"]["learners"] + 1
    assert len(after["timeline"]) == 30 and after["timeline"][-1]["attempts"] > 0
    assert {"label", "count"} <= set(after["mastery"][0]) and after["funnel"] and after["skills"]
    assert all(0 <= s["first_try_correct_rate"] <= 1 for s in after["skills"])


def test_sua_noi_dung_ghi_nhat_ky(client, admin):
    _, headers = admin
    block = first_theory(client, headers)
    payload = dict(block["payload"], title="Tiêu đề thử nhật ký")
    rev = client.put(f"/api/v1/admin/lessons/L11/blocks/{block['id']}", headers=headers, json={"payload": payload}).json()["revision_id"]
    client.post(f"/api/v1/admin/revisions/{rev}/publish", headers=headers, json={})
    log = client.get("/api/v1/admin/audit", headers=headers).json()
    assert {"content.save_draft", "content.publish"} <= {a["action"] for a in log}
    assert "Tiêu đề thử nhật ký" not in str(log)  # nhật ký không chép nội dung
