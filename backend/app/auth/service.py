"""Nghiệp vụ đăng ký, đăng nhập, xoay vòng và thu hồi refresh token."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.errors import AppError
from ..db.models import RefreshToken, User
from .login_limiter import attempt_key, login_attempts
from .security import (
    DUMMY_HASH,
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    password_problem,
    verify_password,
)

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    # SQLite trả datetime không có múi giờ; coi như UTC.
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register_user(db: Session, email: str, password: str, display_name: str) -> User:
    email = normalize_email(email)
    fields: dict[str, str] = {}
    if not EMAIL_RE.match(email):
        fields["email"] = "Email chưa đúng định dạng."
    problem = password_problem(password)
    if problem:
        fields["password"] = problem
    if not display_name.strip():
        fields["display_name"] = "Hãy nhập tên hiển thị."
    if fields:
        raise AppError(400, "VALIDATION_ERROR", "Thông tin đăng ký chưa hợp lệ.", fields=fields)
    if db.scalar(select(User.id).where(User.email == email)):
        raise AppError(409, "EMAIL_TAKEN", "Email này đã có tài khoản.")
    user = User(id=str(uuid.uuid4()), email=email, hashed_password=hash_password(password),
                display_name=display_name.strip(), role="learner")
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:  # hai yêu cầu đăng ký cùng email chạy song song
        db.rollback()
        raise AppError(409, "EMAIL_TAKEN", "Email này đã có tài khoản.") from exc
    return user


def authenticate(db: Session, email: str, password: str, ip: str) -> User:
    email = normalize_email(email)
    key = attempt_key(ip, email)
    wait = login_attempts.locked_for(key)
    if wait:
        raise AppError(429, "LOGIN_LOCKED", "Bạn đã nhập sai quá nhiều lần. Hãy thử lại sau.",
                       retryable=True, headers={"Retry-After": str(wait)})
    user = db.scalar(select(User).where(User.email == email))
    ok = verify_password(password, user.hashed_password if user else DUMMY_HASH)
    if not ok or user is None or not user.is_active or user.is_synthetic:
        login_attempts.record_failure(key)
        raise AppError(401, "INVALID_CREDENTIALS", "Email hoặc mật khẩu chưa đúng.")
    login_attempts.reset(key)
    return user


def issue_refresh_token(db: Session, user: User) -> str:
    token = new_refresh_token()
    db.add(RefreshToken(id=str(uuid.uuid4()), user_id=user.id, token_hash=hash_refresh_token(token),
                        expires_at=utcnow() + timedelta(days=settings.refresh_token_days)))
    db.commit()
    return token


def rotate_refresh_token(db: Session, token: str | None) -> tuple[User, str]:
    """Đổi refresh token cũ lấy token mới; token cũ bị thu hồi ngay (NFR-18)."""
    invalid = AppError(401, "UNAUTHORIZED", "Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại.")
    if not token:
        raise invalid
    now = utcnow()
    # Thu hồi có điều kiện trong một câu UPDATE: hai request dùng cùng token thì chỉ một cái thắng.
    result = db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == hash_refresh_token(token), RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
        .returning(RefreshToken.user_id, RefreshToken.expires_at)
    ).first()
    if result is None or _aware(result.expires_at) <= now:
        db.commit()
        raise invalid
    user = db.get(User, result.user_id)
    if user is None or not user.is_active or user.is_synthetic:
        db.commit()
        raise invalid
    new_token = issue_refresh_token(db, user)  # commit cả hai thay đổi
    return user, new_token


def revoke_refresh_token(db: Session, token: str | None) -> None:
    if not token:
        return
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == hash_refresh_token(token), RefreshToken.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )
    db.commit()


def access_token_for(user: User) -> str:
    return create_access_token(user.id, user.role)
