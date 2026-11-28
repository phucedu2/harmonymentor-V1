"""ADR-040: quên mật khẩu, đặt lại, đổi mật khẩu, xác minh email, "Ghi nhớ đăng nhập" (C1).

Mỗi test có hộp thư ConsoleSender riêng (fixture `_hop_thu_va_gioi_han_sach` trong conftest.py),
nên đọc lại được đúng thư đã gửi, đúng người nhận và đúng liên kết.
"""

from __future__ import annotations

import logging
import re
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth.login_limiter import attempt_key, login_attempts
from app.auth.security import COMMON_PASSWORDS, hash_refresh_token, password_problem
from app.core.config import Settings, check_runtime_settings
from app.db.models import EmailVerificationToken, PasswordResetToken, RefreshToken, User
from app.db.session import SessionLocal
from app.email import render
from app.email.sender import ConsoleSender, build_message, mask_email
from app.main import app

PASSWORD = "nhacly2026"
NEW_PASSWORD = "giaiDieu2027"
CHECK_MSG = "Nếu email này có tài khoản"
TOKEN_RE = re.compile(r"#token=([A-Za-z0-9_\-]+)")
ROOT = Path(__file__).resolve().parents[2]


def new_email(prefix: str = "u") -> str:
    return f"{prefix}-{uuid4().hex[:10]}@example.com"


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def outbox(_hop_thu_va_gioi_han_sach) -> ConsoleSender:
    return _hop_thu_va_gioi_han_sach


def register(client: TestClient, email: str, password: str = PASSWORD):
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password, "display_name": "Phúc"})
    assert r.status_code == 201, r.text
    return r


def bearer(resp) -> dict[str, str]:
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def mails_to(outbox: ConsoleSender, email: str, subject: str | None = None):
    return [m for m in outbox.outbox if m.to == email and (subject is None or m.subject == subject)]


def reset_token_from(outbox: ConsoleSender, email: str) -> str:
    mail = mails_to(outbox, email, "Reset your HarmonyMentor password")[-1]
    match = TOKEN_RE.search(mail.text)
    assert match, mail.text
    assert match.group(0) in mail.html
    return match.group(1)


def forgot(client: TestClient, email: str):
    return client.post("/api/v1/auth/forgot-password", json={"email": email})


# ---------- Quên mật khẩu: không lộ email ----------

def test_forgot_same_answer_for_existing_and_unknown_email(client, outbox):
    email = new_email()
    register(client, email)
    known = forgot(client, email)
    unknown = forgot(client, new_email("lạ"))
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json() and CHECK_MSG in known.json()["message"]
    assert set(known.headers) - {"x-request-id", "date", "content-length"} == \
        set(unknown.headers) - {"x-request-id", "date", "content-length"}
    # Chỉ email có tài khoản mới nhận thư, và thư đi đúng người.
    assert len(mails_to(outbox, email, "Reset your HarmonyMentor password")) == 1
    assert all(m.subject != "Reset your HarmonyMentor password" or m.to == email for m in outbox.outbox)


def test_forgot_skips_synthetic_inactive_and_passwordless_users(client, outbox):
    emails = [new_email("sim"), new_email("khoa")]
    with SessionLocal() as db:
        db.add(User(id=str(uuid4()), display_name="Mô phỏng", email=emails[0], is_synthetic=True))
        db.add(User(id=str(uuid4()), display_name="Bị khóa", email=emails[1], is_active=False))
        db.commit()
    for email in emails:
        r = forgot(client, email)
        assert r.status_code == 202 and CHECK_MSG in r.json()["message"]
        assert mails_to(outbox, email) == []


def test_forgot_rate_limits_per_email_and_per_ip(client, outbox):
    email = new_email()
    register(client, email)
    assert [forgot(client, email).status_code for _ in range(3)] == [202, 202, 202]
    fourth = forgot(client, email)
    assert fourth.status_code == 429 and fourth.json()["error"]["code"] == "RATE_LIMITED"
    assert int(fourth.headers["Retry-After"]) > 0
    assert len(mails_to(outbox, email)) == 1 + 3  # thư xác minh + 3 thư đặt lại
    # Theo IP: 10 / giờ (3 lượt ở trên đã tính, lượt thứ 4 bị chặn ở tầng email sau khi đã qua tầng IP).
    codes = [forgot(client, new_email("ip")).status_code for _ in range(7)]
    assert codes == [202] * 6 + [429]


def test_new_reset_link_invalidates_old_one(client, outbox):
    email = new_email()
    register(client, email)
    forgot(client, email)
    old = reset_token_from(outbox, email)
    forgot(client, email)
    new = reset_token_from(outbox, email)
    assert old != new
    assert client.post("/api/v1/auth/reset-password/check", json={"token": old}).status_code == 400
    assert client.post("/api/v1/auth/reset-password/check", json={"token": new}).status_code == 200


def test_only_hash_is_stored(client, outbox):
    email = new_email()
    register(client, email)
    forgot(client, email)
    token = reset_token_from(outbox, email)
    with SessionLocal() as db:
        row = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_refresh_token(token)))
        assert row is not None and token not in row.token_hash
        assert _minutes(row.expires_at - row.created_at) == 30


def _minutes(delta: timedelta) -> int:
    return round(delta.total_seconds() / 60)


# ---------- Đặt lại mật khẩu ----------

def test_check_returns_masked_email(client, outbox):
    email = new_email("phuc")
    register(client, email)
    forgot(client, email)
    r = client.post("/api/v1/auth/reset-password/check", json={"token": reset_token_from(outbox, email)})
    assert r.status_code == 200 and r.json() == {"email_masked": mask_email(email)}
    assert r.json()["email_masked"].startswith("p***@")


@pytest.mark.parametrize("token", ["", "sai-token", "x" * 43])
def test_check_and_reset_reject_wrong_token(client, token):
    check = client.post("/api/v1/auth/reset-password/check", json={"token": token})
    reset = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": NEW_PASSWORD})
    assert check.status_code == reset.status_code == 400 if token else check.status_code in (400, 422)
    if token:
        assert check.json()["error"]["code"] == reset.json()["error"]["code"] == "RESET_TOKEN_INVALID"


def test_expired_token_is_rejected(client, outbox):
    email = new_email()
    register(client, email)
    forgot(client, email)
    token = reset_token_from(outbox, email)
    with SessionLocal() as db:
        row = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_refresh_token(token)))
        row.expires_at = row.created_at - timedelta(seconds=1)
        db.commit()
    r = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": NEW_PASSWORD})
    assert r.status_code == 400 and r.json()["error"]["code"] == "RESET_TOKEN_INVALID"


def test_reset_full_flow_revokes_everything(client, outbox):
    email = new_email()
    first = register(client, email)
    old_access = bearer(first)
    second = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert second.status_code == 200
    # Khóa đăng nhập đang có ở một IP khác cũng phải được xóa sau khi đặt lại.
    for _ in range(5):
        login_attempts.record_failure(attempt_key("10.0.0.9", email))
    assert login_attempts.locked_for(attempt_key("10.0.0.9", email)) > 0

    forgot(client, email)
    token = reset_token_from(outbox, email)
    weak = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "password1"})
    assert weak.status_code == 400 and "phổ biến" in weak.json()["error"]["fields"]["new_password"]
    same = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": PASSWORD})
    assert same.status_code == 400 and "khác mật khẩu cũ" in same.json()["error"]["fields"]["new_password"]

    ok = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": NEW_PASSWORD})
    assert ok.status_code == 200 and "set-cookie" not in ok.headers  # không tự đăng nhập
    # Dùng lại cùng liên kết: hỏng.
    again = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "khacNua2028"})
    assert again.status_code == 400

    # Access token cũ chết ngay (không đợi 30 phút); mọi refresh token bị thu hồi.
    assert client.get("/api/v1/me", headers=old_access).status_code == 401
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        live = db.scalars(select(RefreshToken).where(RefreshToken.user_id == user.id,
                                                     RefreshToken.revoked_at.is_(None))).all()
        assert live == [] and user.password_changed_at is not None and user.email_verified_at is not None
    assert client.post("/api/v1/auth/refresh").status_code == 401
    assert login_attempts.locked_for(attempt_key("10.0.0.9", email)) == 0

    # Mật khẩu cũ hỏng, mật khẩu mới vào được; token mới dùng được /me.
    assert client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD}).status_code == 401
    fresh = client.post("/api/v1/auth/login", json={"email": email, "password": NEW_PASSWORD})
    assert fresh.status_code == 200
    assert client.get("/api/v1/me", headers=bearer(fresh)).status_code == 200

    notice = mails_to(outbox, email, "Your password was changed")
    assert len(notice) == 1 and "(GMT+7)" in notice[0].text and "/quen-mat-khau" in notice[0].text


def test_two_parallel_resets_only_one_wins_sequential_guard(client, outbox):
    """Bản SQLite: hai lần nộp cùng token liền nhau, lần sau thua. Bản song song thật nằm ở test PostgreSQL."""
    email = new_email()
    register(client, email)
    forgot(client, email)
    token = reset_token_from(outbox, email)
    results = [client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": pw}).status_code
               for pw in (NEW_PASSWORD, "khacNua2028")]
    assert results == [200, 400]


# ---------- Đổi mật khẩu khi đang đăng nhập ----------

def change(client, headers, current=PASSWORD, new=NEW_PASSWORD, sign_out_others=True):
    return client.post("/api/v1/auth/change-password", headers=headers,
                       json={"current_password": current, "new_password": new, "sign_out_others": sign_out_others})


def test_change_password_wrong_current_counts_toward_lock(client, outbox):
    email = new_email()
    headers = bearer(register(client, email))
    for _ in range(5):
        r = change(client, headers, current="saiMatKhau1")
        assert r.status_code == 400 and "current_password" in r.json()["error"]["fields"]
    locked = change(client, headers)  # đúng mật khẩu nhưng đã bị khóa
    assert locked.status_code == 429 and locked.json()["error"]["code"] == "LOGIN_LOCKED"
    login = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 429  # 10A: chung bộ đếm với đăng nhập
    assert mails_to(outbox, email, "Your password was changed") == []


def test_change_password_requires_login(client):
    r = client.post("/api/v1/auth/change-password",
                    json={"current_password": PASSWORD, "new_password": NEW_PASSWORD})
    assert r.status_code == 401


def test_change_password_signs_out_others_and_keeps_current(client, outbox):
    email = new_email()
    device_a = TestClient(app)
    device_b = TestClient(app)
    a = register(device_a, email)
    b = device_b.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    r = change(device_a, bearer(a))
    assert r.status_code == 200 and "hm_refresh=" in r.headers["set-cookie"]
    assert device_a.get("/api/v1/me", headers=bearer(r)).status_code == 200
    assert device_a.get("/api/v1/me", headers=bearer(a)).status_code == 401   # access cũ của chính máy A
    assert device_b.get("/api/v1/me", headers=bearer(b)).status_code == 401
    assert device_b.post("/api/v1/auth/refresh").status_code == 401           # máy B bị đăng xuất
    assert device_a.post("/api/v1/auth/refresh").status_code == 200           # máy A vẫn giữ phiên
    notice = mails_to(outbox, email, "Your password was changed")
    assert len(notice) == 1 and "other devices have been signed out" in notice[0].text


def test_change_password_without_sign_out_keeps_other_refresh(client, outbox):
    email = new_email()
    device_a = TestClient(app)
    device_b = TestClient(app)
    a = register(device_a, email)
    b = device_b.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert change(device_a, bearer(a), sign_out_others=False).status_code == 200
    # Access token cũ của B vẫn chết (A2), nhưng B tự lấy phiên mới bằng refresh token còn hạn.
    assert device_b.get("/api/v1/me", headers=bearer(b)).status_code == 401
    assert device_b.post("/api/v1/auth/refresh").status_code == 200
    assert "signed out" not in mails_to(outbox, email, "Your password was changed")[0].text


def test_change_password_rejects_same_or_weak(client):
    email = f"namhoc{uuid4().hex[:4]}@example.com"
    headers = bearer(register(client, email))
    assert "khác mật khẩu cũ" in change(client, headers, new=PASSWORD).json()["error"]["fields"]["new_password"]
    assert "email" in change(client, headers, new=email.split("@")[0] + "9").json()["error"]["fields"]["new_password"]


# ---------- Đăng ký: không lộ email, xác minh email ----------

def test_register_existing_email_sends_notice_not_error(client, outbox):
    email = new_email()
    register(client, email)
    dup = client.post("/api/v1/auth/register", json={"email": email, "password": "khacHan2026",
                                                      "display_name": "Kẻ lạ"})
    assert dup.status_code == 202 and "hm_refresh" not in dup.headers.get("set-cookie", "")
    notice = mails_to(outbox, email, "You already have a HarmonyMentor account")
    assert len(notice) == 1 and "/quen-mat-khau" in notice[0].text
    # Mật khẩu cũ không bị đổi bởi lần đăng ký thứ hai.
    assert client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200


def test_register_rate_limited_per_ip(client):
    codes = [client.post("/api/v1/auth/register", json={"email": new_email(), "password": PASSWORD,
                                                         "display_name": "A"}).status_code for _ in range(11)]
    assert codes == [201] * 10 + [429]


def test_verify_email_flow(client, outbox):
    email = new_email()
    r = register(client, email)
    assert r.json()["user"]["email_verified"] is False
    mail = mails_to(outbox, email, "Verify your email")
    assert len(mail) == 1 and "/xac-minh-email#token=" in mail[0].text
    token = TOKEN_RE.search(mail[0].text).group(1)
    assert client.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 200
    assert client.get("/api/v1/me", headers=bearer(r)).json()["email_verified"] is True
    again = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert again.status_code == 400 and again.json()["error"]["code"] == "VERIFY_TOKEN_INVALID"
    # Đã xác minh rồi thì gửi lại chỉ báo đã xác minh, không gửi thư.
    resend = client.post("/api/v1/auth/resend-verification", headers=bearer(r))
    assert resend.status_code == 200 and len(mails_to(outbox, email, "Verify your email")) == 1


def test_resend_verification_invalidates_old_and_is_limited(client, outbox):
    email = new_email()
    headers = bearer(register(client, email))
    first = TOKEN_RE.search(mails_to(outbox, email, "Verify your email")[0].text).group(1)
    codes = [client.post("/api/v1/auth/resend-verification", headers=headers).status_code for _ in range(4)]
    assert codes == [202, 202, 202, 429]
    assert client.post("/api/v1/auth/verify-email", json={"token": first}).status_code == 400
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        live = db.scalars(select(EmailVerificationToken).where(EmailVerificationToken.user_id == user.id,
                                                               EmailVerificationToken.used_at.is_(None))).all()
        assert len(live) == 1


# ---------- Ghi nhớ đăng nhập ----------

def test_remember_false_gives_session_cookie_and_one_day(client):
    email = new_email()
    register(client, email)
    r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD, "remember": False})
    cookie = r.headers["set-cookie"]
    assert "Max-Age" not in cookie and "expires" not in cookie.lower()
    with SessionLocal() as db:
        row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(
            r.cookies.get("hm_refresh") or client.cookies.get("hm_refresh"))))
        assert row.remember is False and round((row.expires_at - row.created_at).total_seconds() / 3600) == 24
    rotated = client.post("/api/v1/auth/refresh")
    assert rotated.status_code == 200 and "Max-Age" not in rotated.headers["set-cookie"]


def test_remember_true_gives_30_days_and_absolute_cap(client):
    email = new_email()
    register(client, email)
    r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD, "remember": True})
    assert f"Max-Age={30 * 86400}" in r.headers["set-cookie"]
    token = client.cookies.get("hm_refresh")
    with SessionLocal() as db:
        row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(token)))
        # Giả lập phiên đã bắt đầu 89 ngày trước: xoay vòng không được kéo quá trần 90 ngày.
        row.session_started_at = row.created_at - timedelta(days=89)
        db.commit()
    assert client.post("/api/v1/auth/refresh").status_code == 200
    with SessionLocal() as db:
        new = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(
            client.cookies.get("hm_refresh"))))
        assert new.remember is True
        assert (new.expires_at - new.session_started_at) <= timedelta(days=90, seconds=1)


# ---------- Bí mật không lọt vào log ----------

def test_no_token_or_password_in_logs(client, outbox, caplog):
    caplog.set_level(logging.DEBUG)
    email = new_email()
    first = register(client, email)
    forgot(client, email)
    token = reset_token_from(outbox, email)
    client.post("/api/v1/auth/reset-password/check", json={"token": token})
    client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": NEW_PASSWORD})
    fresh = client.post("/api/v1/auth/login", json={"email": email, "password": NEW_PASSWORD})
    change(client, bearer(fresh), current=NEW_PASSWORD, new="lanThuBa2029")
    verify_token = TOKEN_RE.search(mails_to(outbox, email, "Verify your email")[0].text).group(1)
    text = caplog.text
    for secret in (token, verify_token, PASSWORD, NEW_PASSWORD, "lanThuBa2029", first.json()["access_token"]):
        assert secret not in text
    assert "#token=" not in text and email not in text  # log chỉ có email đã che
    assert "password_reset_requested user_id=" in text and "password_changed user_id=" in text


# ---------- Cấu hình, mẫu thư, danh sách mật khẩu ----------

def test_production_refuses_console_email():
    with pytest.raises(RuntimeError, match="EMAIL_BACKEND=console"):
        check_runtime_settings(Settings(app_env="production", email_backend="console"))
    check_runtime_settings(Settings(app_env="production", email_backend="smtp"))


def test_smtp_password_hidden_from_repr():
    assert "bi-mat-16-ky-tu" not in repr(Settings(smtp_password="bi-mat-16-ky-tu"))


def test_email_has_html_text_and_inline_logo():
    mail = render.reset_password_email("a@example.com", "<b>Phúc</b>", "http://localhost:5173/dat-lai-mat-khau#token=abc", 30)
    assert "&lt;b&gt;Phúc&lt;/b&gt;" in mail.html        # tên người dùng không chèn được HTML
    assert "cid:hm-logo" in mail.html and "expires in 30 minutes" in mail.text
    msg = build_message(mail, "HarmonyMentor <no-reply@example.com>")
    types = [part.get_content_type() for part in msg.walk()]
    assert {"text/plain", "text/html", "image/png"} <= set(types)


def test_vietnam_time_format():
    from datetime import datetime, timezone

    assert render.format_vn_time(datetime(2026, 11, 25, 10, 39, tzinfo=timezone.utc)) == "25 Nov 2026, 5:39 PM (GMT+7)"
    assert render.format_vn_time(datetime(2026, 11, 25, 17, 5, tzinfo=timezone.utc)) == "26 Nov 2026, 12:05 AM (GMT+7)"


def test_email_palette_matches_brand():
    css = (ROOT / "frontend/src/theme/brands.css").read_text(encoding="utf-8")
    block = css.split(':root[data-brand="san-khau"],', 1)[1].split("}", 1)[0]
    tokens = dict(re.findall(r"--color-([a-z-]+):\s*(#[0-9a-fA-F]{6})", block))
    for key, value in render.PALETTE.items():
        assert tokens[key.replace("_", "-")].lower() == value, key


def test_common_passwords_in_sync_and_enforced():
    backend = (ROOT / "backend/app/auth/data/common_passwords.txt").read_text(encoding="utf-8")
    frontend = (ROOT / "frontend/src/auth/common-passwords.txt").read_text(encoding="utf-8")
    assert backend == frontend and len(COMMON_PASSWORDS) == 1000
    assert password_problem("Password1") and password_problem("abcd1234")
    assert password_problem("toiHocHarmonyMentor1")
    assert password_problem("nhacly2026") is None
