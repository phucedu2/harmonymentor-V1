"""Giai đoạn B: xác thực, phân quyền và cô lập dữ liệu theo người dùng (FR-AUTH, NFR-18, NFR-19, N3)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.auth.security import create_access_token
from app.db.models import User
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import auth

PASSWORD = "nhacly2026"


def new_email(prefix: str = "u") -> str:
    return f"{prefix}-{uuid4().hex[:10]}@example.com"


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def register(client: TestClient, email: str | None = None, password: str = PASSWORD, name: str = "Phúc"):
    return client.post("/api/v1/auth/register", json={"email": email or new_email(), "password": password,
                                                      "display_name": name})


def bearer(resp) -> dict[str, str]:
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_register_returns_session_and_secure_cookie(client):
    email = new_email("Reg").upper()
    r = register(client, email=email)
    assert r.status_code == 201
    body = r.json()
    assert body["token_type"] == "bearer" and body["expires_in"] == 1800
    assert body["user"]["email"] == email.lower()
    assert body["user"]["role"] == "learner"
    cookie = r.headers["set-cookie"]
    assert "hm_refresh=" in cookie and "HttpOnly" in cookie and "Path=/api/v1/auth" in cookie
    assert "samesite=lax" in cookie.lower()
    with SessionLocal() as db:
        user = db.get(User, body["user"]["id"])
        assert user.hashed_password.startswith("$2")  # bcrypt, không lưu mật khẩu thô
        assert PASSWORD not in user.hashed_password


@pytest.mark.parametrize("password,field_msg", [
    ("abc123", "8 ký tự"),
    ("12345678", "chữ cái"),
    ("abcdefgh", "chữ số"),
])
def test_weak_password_is_rejected_with_400(client, password, field_msg):
    r = register(client, password=password)
    assert r.status_code == 400
    err = r.json()["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert field_msg in err["fields"]["password"]


def test_invalid_email_and_duplicate_email(client):
    bad = register(client, email="khong-phai-email")
    assert bad.status_code == 400 and "email" in bad.json()["error"]["fields"]

    email = new_email()
    assert register(client, email=email).status_code == 201
    dup = register(client, email=email.upper())
    assert dup.status_code == 409 and dup.json()["error"]["code"] == "EMAIL_TAKEN"


def test_login_me_and_wrong_password(client):
    email = new_email()
    register(client, email=email)
    wrong = client.post("/api/v1/auth/login", json={"email": email, "password": "sai12345"})
    assert wrong.status_code == 401 and wrong.json()["error"]["code"] == "INVALID_CREDENTIALS"
    unknown = client.post("/api/v1/auth/login", json={"email": new_email(), "password": PASSWORD})
    # Không lộ việc email có tồn tại hay không.
    assert unknown.status_code == 401 and unknown.json()["error"]["code"] == "INVALID_CREDENTIALS"

    ok = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert ok.status_code == 200
    me = client.get("/api/v1/me", headers=bearer(ok))
    assert me.status_code == 200 and me.json()["email"] == email


def test_sixth_failed_login_is_locked_with_429(client):
    email = new_email("lock")
    register(client, email=email)
    for _ in range(5):
        r = client.post("/api/v1/auth/login", json={"email": email, "password": "sai12345"})
        assert r.status_code == 401
    sixth = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert sixth.status_code == 429
    assert sixth.json()["error"]["code"] == "LOGIN_LOCKED"
    assert 0 < int(sixth.headers["Retry-After"]) <= 900


def test_successful_login_resets_failure_counter(client):
    email = new_email("reset")
    register(client, email=email)
    for _ in range(4):
        client.post("/api/v1/auth/login", json={"email": email, "password": "sai12345"})
    assert client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200
    for _ in range(4):
        client.post("/api/v1/auth/login", json={"email": email, "password": "sai12345"})
    assert client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200


def test_refresh_rotates_and_old_token_is_rejected(client):
    register(client)
    old = client.cookies.get("hm_refresh")
    first = client.post("/api/v1/auth/refresh")
    assert first.status_code == 200
    new = client.cookies.get("hm_refresh")
    assert new and new != old

    # Dùng lại refresh token cũ (đã xoay) → 401.
    replay = TestClient(app)
    replay.cookies.set("hm_refresh", old, path="/api/v1/auth")
    assert replay.post("/api/v1/auth/refresh").status_code == 401

    # Token mới vẫn dùng được.
    assert client.post("/api/v1/auth/refresh").status_code == 200


def test_logout_revokes_refresh_token(client):
    register(client)
    token = client.cookies.get("hm_refresh")
    out = client.post("/api/v1/auth/logout")
    assert out.status_code == 204
    assert 'hm_refresh=""' in out.headers["set-cookie"] or "Max-Age=0" in out.headers["set-cookie"]
    replay = TestClient(app)
    replay.cookies.set("hm_refresh", token, path="/api/v1/auth")
    assert replay.post("/api/v1/auth/refresh").status_code == 401


def test_refresh_without_cookie_is_401(client):
    r = client.post("/api/v1/auth/refresh")
    assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHORIZED"


def test_expired_or_forged_access_token_is_401(client):
    user_id = register(client).json()["user"]["id"]
    expired = create_access_token(user_id, "learner", now=datetime.now(timezone.utc) - timedelta(minutes=31))
    r = client.get("/api/v1/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHORIZED"
    assert client.get("/api/v1/me", headers={"Authorization": "Bearer abc.def.ghi"}).status_code == 401


def test_patch_me_updates_profile(client):
    reg = register(client)
    r = client.patch("/api/v1/me", json={"display_name": "  Phúc Trần ", "preferred_instrument": "guitar"},
                     headers=bearer(reg))
    assert r.status_code == 200
    assert r.json()["display_name"] == "Phúc Trần" and r.json()["preferred_instrument"] == "guitar"
    bad = client.patch("/api/v1/me", json={"preferred_instrument": "violin"}, headers=bearer(reg))
    assert bad.status_code == 400
    # Không gửi trường nào thì không đổi gì.
    same = client.patch("/api/v1/me", json={}, headers=bearer(reg))
    assert same.json()["preferred_instrument"] == "guitar"


def test_learner_gets_403_on_admin_and_admin_gets_200(client):
    learner = register(client)
    r = client.get("/api/v1/admin/ping", headers=bearer(learner))
    assert r.status_code == 403 and r.json()["error"]["code"] == "FORBIDDEN"
    assert client.get("/api/v1/admin/ping").status_code == 401

    admin_id = learner.json()["user"]["id"]
    with SessionLocal() as db:
        db.get(User, admin_id).role = "admin"
        db.commit()
    assert client.get("/api/v1/admin/ping", headers=auth(admin_id, "admin")).status_code == 200


def test_personal_routes_require_login_and_public_routes_do_not(client):
    for method, path in [("get", "/api/v1/learning/overview"), ("get", "/api/v1/review/due"),
                         ("post", "/api/v1/lessons/L01/start"), ("post", "/api/v1/lessons/L01/complete"),
                         ("get", "/api/v1/me")]:
        r = getattr(client, method)(path)
        assert r.status_code == 401, path
    assert client.post("/api/v1/attempts", json={"exercise_version_id": "L01-Q01-v4", "answer": "M3"}).status_code == 401

    assert client.get("/api/v1/lessons").status_code == 200
    assert client.get("/api/v1/lessons/L01").status_code == 200
    assert client.get("/api/v1/music/chords/inspect", params={"symbol": "Ebm7b5"}).json()["notes"] == ["Eb", "Gb", "Bbb", "Db"]
    assert client.get("/api/v1/engine/chord/G7").status_code == 200


def test_user_cannot_touch_another_users_data(client):
    a = register(client, name="A")
    b = TestClient(app)
    b_reg = register(b, name="B")
    a_id = a.json()["user"]["id"]

    assert client.post("/api/v1/lessons/L01/complete", headers=bearer(a)).status_code == 200
    a_due = client.get("/api/v1/review/due", params={"include_future": "true"}, headers=bearer(a)).json()
    assert a_due
    item_id = a_due[0]["review_item_id"]

    # B không thấy lịch ôn của A. Thẻ là nội dung bài học công khai, nên B trả lời thẻ đó chỉ nhận
    # "thẻ chưa kích hoạt với bạn" (409) và lịch ôn của A không đổi.
    assert b.get("/api/v1/review/due", params={"include_future": "true"}, headers=bearer(b_reg)).json() == []
    answer = b.post(f"/api/v1/review/{item_id}/answer", json={"answer": "M3"}, headers=bearer(b_reg))
    assert answer.status_code == 409 and answer.json()["error"]["code"] == "REVIEW_STATE_NOT_ACTIVE"
    a_after = client.get("/api/v1/review/due", params={"include_future": "true"}, headers=bearer(a)).json()
    assert a_after == a_due

    # Gửi user_id của A trong body bị bỏ qua: lượt làm vẫn ghi cho B.
    attempt = b.post("/api/v1/attempts", json={"user_id": a_id, "exercise_version_id": "L01-Q01-v4", "answer": "M3"},
                     headers=bearer(b_reg))
    assert attempt.status_code == 200 and attempt.json()["user_id"] == b_reg.json()["user"]["id"]
    overview_a = client.get("/api/v1/learning/overview", headers=bearer(a)).json()
    l01 = next(x for x in overview_a["lessons"] if x["lesson_id"] == "L01")
    assert l01["attempt_count"] == 0


def test_synthetic_and_inactive_users_cannot_use_tokens(client):
    synthetic_id = "sim-" + uuid4().hex[:10]
    with SessionLocal() as db:
        db.add(User(id=synthetic_id, display_name="Mô phỏng", is_synthetic=True))
        db.commit()
    assert client.get("/api/v1/me", headers=auth(synthetic_id)).status_code == 401

    reg = register(client)
    with SessionLocal() as db:
        db.get(User, reg.json()["user"]["id"]).is_active = False
        db.commit()
    assert client.get("/api/v1/me", headers=bearer(reg)).status_code == 401
    assert client.post("/api/v1/auth/refresh").status_code == 401


def test_validation_errors_use_srs_7_4_format(client):
    r = client.post("/api/v1/auth/login", json={"email": "x@example.com"})
    assert r.status_code == 400
    err = r.json()["error"]
    assert err["code"] == "VALIDATION_ERROR" and "password" in err["fields"] and err["retryable"] is False
    missing = client.get("/api/v1/lessons/KHONG-CO")
    assert missing.status_code == 404 and "code" in missing.json()["error"]
