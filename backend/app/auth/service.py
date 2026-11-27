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
    password_stamp,
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


def register_user(db: Session, email: str, password: str, display_name: str) -> tuple[User, bool]:
    """Trả (người dùng, đã_tạo_mới). Email đã có tài khoản thì KHÔNG báo lỗi 409 (lộ email, ADR-040 mục 1A):
    trả người dùng cũ với cờ False để router hiện "kiểm tra hộp thư" và gửi thư báo cho chủ email."""
    email = normalize_email(email)
    fields: dict[str, str] = {}
    if not EMAIL_RE.match(email):
        fields["email"] = "Email chưa đúng định dạng."
    problem = password_problem(password, email)
    if problem:
        fields["password"] = problem
    if not display_name.strip():
        fields["display_name"] = "Hãy nhập tên hiển thị."
    if fields:
        raise AppError(400, "VALIDATION_ERROR", "Thông tin đăng ký chưa hợp lệ.", fields=fields)
    # Băm mật khẩu ở cả hai nhánh để thời gian phản hồi email cũ/mới như nhau (bcrypt chiếm gần hết thời gian).
    hashed = hash_password(password)
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        return existing, False
    user = User(id=str(uuid.uuid4()), email=email, hashed_password=hashed,
                display_name=display_name.strip(), role="learner")
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # hai yêu cầu đăng ký cùng email chạy song song: coi như email đã có
        db.rollback()
        existing = db.scalar(select(User).where(User.email == email))
        if existing is None:
            raise
        return existing, False
    return user, True


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


def refresh_expiry(remember: bool, started_at: datetime, now: datetime) -> datetime:
    """3A: trượt 30 ngày (ghi nhớ) hoặc 1 ngày (phiên), nhưng không quá trần tuyệt đối 90 ngày từ lúc đăng nhập."""
    days = settings.remember_refresh_days if remember else settings.session_refresh_days
    return min(now + timedelta(days=days), _aware(started_at) + timedelta(days=settings.session_absolute_days))


def issue_refresh_token(db: Session, user: User, remember: bool = True,
                        session_started_at: datetime | None = None) -> str:
    token = new_refresh_token()
    now = utcnow()
    started = session_started_at or now
    db.add(RefreshToken(id=str(uuid.uuid4()), user_id=user.id, token_hash=hash_refresh_token(token),
                        expires_at=refresh_expiry(remember, started, now), remember=remember,
                        session_started_at=started))
    db.commit()
    return token


def revoke_all_refresh_tokens(db: Session, user_id: str, keep_hash: str | None = None) -> None:
    """Thu hồi mọi phiên của người dùng (đặt lại/đổi mật khẩu). keep_hash: giữ lại đúng một phiên."""
    stmt = update(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
    if keep_hash:
        stmt = stmt.where(RefreshToken.token_hash != keep_hash)
    db.execute(stmt.values(revoked_at=utcnow()))


def rotate_refresh_token(db: Session, token: str | None) -> tuple[User, str, bool]:
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
        .returning(RefreshToken.user_id, RefreshToken.expires_at, RefreshToken.remember,
                   RefreshToken.session_started_at, RefreshToken.created_at)
    ).first()
    if result is None or _aware(result.expires_at) <= now:
        db.commit()
        raise invalid
    user = db.get(User, result.user_id)
    if user is None or not user.is_active or user.is_synthetic:
        db.commit()
        raise invalid
    # Token mới giữ kiểu phiên và mốc bắt đầu của token cũ (trần 90 ngày không bị kéo dài bởi xoay vòng).
    remember = bool(result.remember)
    started = result.session_started_at or result.created_at
    new_token = issue_refresh_token(db, user, remember, started)  # commit cả hai thay đổi
    return user, new_token, remember


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
    return create_access_token(user.id, user.role, pwd=password_stamp(user.password_changed_at))
