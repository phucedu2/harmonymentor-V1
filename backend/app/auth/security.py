"""Băm mật khẩu, access token JWT và refresh token ngẫu nhiên."""

from __future__ import annotations

import hashlib
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from ..core.config import settings

log = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"


def _resolve_secret() -> str:
    if settings.jwt_secret:
        return settings.jwt_secret
    if settings.app_env == "production":
        raise RuntimeError("Thiếu JWT_SECRET: môi trường production không được chạy với khóa tạm.")
    # Dev/test: khóa ngẫu nhiên theo tiến trình, không viết cứng trong code. Khởi động lại thì
    # access token cũ hết hiệu lực, nhưng refresh token (lưu trong CSDL) vẫn lấy lại phiên được.
    log.warning("JWT_SECRET chưa đặt; dùng khóa tạm cho môi trường %s.", settings.app_env)
    return secrets.token_urlsafe(48)


JWT_SECRET = _resolve_secret()

# NFR-19: ≥ 8 ký tự, có chữ cái và chữ số. bcrypt chỉ dùng 72 byte đầu nên chặn mật khẩu dài hơn
# thay vì âm thầm cắt (hai mật khẩu khác nhau ở byte 73 sẽ trùng nhau).
BCRYPT_MAX_BYTES = 72


def password_problem(password: str) -> str | None:
    if len(password) < 8:
        return "Mật khẩu cần ít nhất 8 ký tự."
    if not re.search(r"[^\W\d_]", password):
        return "Mật khẩu cần ít nhất một chữ cái."
    if not re.search(r"\d", password):
        return "Mật khẩu cần ít nhất một chữ số."
    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        return "Mật khẩu quá dài (tối đa 72 byte)."
    return None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("ascii"))
    except ValueError:
        return False


# Băm sẵn một mật khẩu giả để khi email không tồn tại vẫn tốn thời gian như khi sai mật khẩu,
# tránh dò email qua thời gian phản hồi.
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def create_access_token(user_id: str, role: str, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_minutes)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"require": ["exp", "sub"]})
    except jwt.PyJWTError:
        return None
    return payload if payload.get("type") == "access" else None


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
