"""Băm mật khẩu, access token JWT và refresh token ngẫu nhiên."""

from __future__ import annotations

import hashlib
import logging
import re
import secrets
from pathlib import Path
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


def _load_common_passwords() -> frozenset[str]:
    path = Path(__file__).with_name("data") / "common_passwords.txt"
    lines = path.read_text(encoding="utf-8").splitlines()
    return frozenset(line.strip() for line in lines if line.strip() and not line.startswith("#"))


# B3/4A: chặn 1.000 mật khẩu phổ biến (danh sách cục bộ, không gọi dịch vụ ngoài như HIBP).
COMMON_PASSWORDS = _load_common_passwords()
# Mật khẩu chứa tên sản phẩm là thứ kẻ dò thử đầu tiên.
PRODUCT_WORDS = ("harmonymentor",)


def password_problem(password: str, email: str | None = None) -> str | None:
    """Trả câu lỗi đầu tiên (tiếng Việt) hoặc None. `email` để chặn mật khẩu chứa phần trước @ (4A)."""
    if len(password) < 8:
        return "Mật khẩu cần ít nhất 8 ký tự."
    if not re.search(r"[^\W\d_]", password):
        return "Mật khẩu cần ít nhất một chữ cái."
    if not re.search(r"\d", password):
        return "Mật khẩu cần ít nhất một chữ số."
    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        return "Mật khẩu quá dài (tối đa 72 byte)."
    lowered = password.lower()
    if lowered in COMMON_PASSWORDS:
        return "Mật khẩu này quá phổ biến, rất dễ bị đoán. Hãy chọn mật khẩu khác."
    if any(word in lowered for word in PRODUCT_WORDS):
        return "Mật khẩu không nên chứa tên HarmonyMentor. Hãy chọn mật khẩu khác."
    local = (email or "").split("@", 1)[0].strip().lower()
    if len(local) >= 4 and local in lowered:
        return "Mật khẩu không nên chứa email của bạn. Hãy chọn mật khẩu khác."
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


def new_one_time_token() -> str:
    """Token 32 byte ngẫu nhiên cho liên kết trong email (A1)."""
    return secrets.token_urlsafe(32)


def password_stamp(changed_at: datetime | None) -> int:
    """Mốc đổi mật khẩu tính bằng mili giây, gắn vào access token (claim "pwd", ADR-040 A2).
    So bằng nhau thay vì so iat (chỉ chính xác tới giây) để token cấp trong cùng giây với lần đổi vẫn bị chặn."""
    if changed_at is None:
        return 0
    aware = changed_at if changed_at.tzinfo else changed_at.replace(tzinfo=timezone.utc)
    return int(aware.timestamp() * 1000)


def create_access_token(user_id: str, role: str, now: datetime | None = None, pwd: int = 0) -> str:
    now = now or datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "pwd": pwd,
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
