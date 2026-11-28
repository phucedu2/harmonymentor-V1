"""Quên mật khẩu, đặt lại, đổi mật khẩu, xác minh email (ADR-040, OWASP Forgot Password Cheat Sheet).

Nguyên tắc chung:
- Token gốc chỉ nằm trong email; CSDL lưu SHA-256. Dùng token bằng một câu UPDATE có điều kiện,
  nên hai request song song với cùng liên kết chỉ một cái thắng (giống rotate_refresh_token).
- Không endpoint nào cho biết email có tài khoản hay không: quên mật khẩu tra người dùng trong
  BackgroundTasks, sau khi đã trả 202 cùng một câu.
- Không ghi token, mật khẩu hay URL có token vào log. Log sự kiện bảo mật chỉ gồm user_id + IP.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.errors import AppError
from ..db.models import EmailVerificationToken, PasswordResetToken, User
from ..db.session import SessionLocal
from ..email import render
from ..email.sender import deliver, mask_email
from .login_limiter import attempt_key, login_attempts
from .security import hash_password, hash_refresh_token, new_one_time_token, password_problem, verify_password
from .service import _aware, normalize_email, revoke_all_refresh_tokens, utcnow

security_log = logging.getLogger("app.security")

# Phiên CSDL cho việc chạy nền; test PostgreSQL thay bằng sessionmaker của schema tạm.
session_factory = SessionLocal

RESET_PATH = "/dat-lai-mat-khau"
VERIFY_PATH = "/xac-minh-email"


def _link(path: str, token: str) -> str:
    # 2A: token sau dấu # không bao giờ được trình duyệt gửi lên máy chủ, nên không lọt vào log nginx/Vite hay Referer.
    return f"{settings.frontend_base_url.rstrip('/')}{path}#token={token}"


def _plain_link(path: str) -> str:
    return f"{settings.frontend_base_url.rstrip('/')}{path}"


def _can_receive_mail(user: User | None) -> bool:
    return bool(user and user.email and user.is_active and not user.is_synthetic)


def reset_invalid() -> AppError:
    return AppError(400, "RESET_TOKEN_INVALID", "Liên kết đặt lại mật khẩu đã hết hạn hoặc đã được dùng.")


def verify_invalid() -> AppError:
    return AppError(400, "VERIFY_TOKEN_INVALID", "Liên kết xác minh đã hết hạn hoặc đã được dùng.")


# ---------- Quên mật khẩu ----------

def process_forgot_password(email: str, ip: str) -> None:
    """Chạy trong BackgroundTasks với phiên CSDL riêng (phiên của request đã đóng)."""
    email = normalize_email(email)
    with session_factory() as db:
        user = db.scalar(select(User).where(User.email == email))
        if not _can_receive_mail(user):
            return  # A3: bỏ qua email lạ, người học mô phỏng, tài khoản bị khóa; người gọi vẫn thấy cùng câu
        now = utcnow()
        # A1: liên kết mới làm mọi liên kết cũ chưa dùng hết hiệu lực.
        db.execute(update(PasswordResetToken)
                   .where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
                   .values(used_at=now))
        token = new_one_time_token()
        db.add(PasswordResetToken(id=str(uuid.uuid4()), user_id=user.id, token_hash=hash_refresh_token(token),
                                  created_at=now, expires_at=now + timedelta(minutes=settings.password_reset_minutes),
                                  requested_ip=ip[:64]))
        db.commit()
        security_log.info("password_reset_requested user_id=%s ip=%s", user.id, ip)
        deliver(render.reset_password_email(user.email, user.display_name, _link(RESET_PATH, token),
                                            settings.password_reset_minutes))


def _valid_reset_row(db: Session, token: str) -> PasswordResetToken | None:
    if not token:
        return None
    row = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_refresh_token(token)))
    if row is None or row.used_at is not None or _aware(row.expires_at) <= utcnow():
        return None
    return row


def check_reset_token(db: Session, token: str) -> str:
    """A4: trả email đã che để trang đặt lại báo sớm liên kết hỏng, trước khi người dùng gõ mật khẩu."""
    row = _valid_reset_row(db, token)
    user = db.get(User, row.user_id) if row else None
    if not _can_receive_mail(user):
        raise reset_invalid()
    return mask_email(user.email)


def reset_password(db: Session, token: str, new_password: str, ip: str) -> User:
    row = _valid_reset_row(db, token)
    user = db.get(User, row.user_id) if row else None
    if not _can_receive_mail(user):
        raise reset_invalid()
    # Kiểm tra mật khẩu TRƯỚC khi đốt token, để gõ mật khẩu yếu không làm hỏng liên kết.
    _check_new_password(user, new_password, field="new_password")
    now = utcnow()
    used = db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.id == row.id, PasswordResetToken.used_at.is_(None))
        .values(used_at=now)
        .returning(PasswordResetToken.id)
    ).first()
    if used is None:  # request song song đã dùng liên kết này
        db.rollback()
        raise reset_invalid()
    _apply_new_password(db, user, new_password, now)
    revoke_all_refresh_tokens(db, user.id)
    if user.email_verified_at is None:  # 11A: mở được thư tức là sở hữu email
        user.email_verified_at = now
    db.commit()
    login_attempts.reset_email(user.email)
    security_log.info("password_reset_completed user_id=%s ip=%s", user.id, ip)
    return user


# ---------- Đổi mật khẩu khi đang đăng nhập ----------

def change_password(db: Session, user: User, current: str, new_password: str, ip: str) -> None:
    key = attempt_key(ip, user.email or user.id)
    wait = login_attempts.locked_for(key)
    if wait:  # 10A: dùng chung bộ đếm với đăng nhập
        raise AppError(429, "LOGIN_LOCKED", "Bạn đã nhập sai quá nhiều lần. Hãy thử lại sau.",
                       retryable=True, headers={"Retry-After": str(wait)})
    if not verify_password(current, user.hashed_password):
        login_attempts.record_failure(key)
        security_log.info("password_change_wrong_current user_id=%s ip=%s", user.id, ip)
        raise AppError(400, "VALIDATION_ERROR", "Mật khẩu hiện tại chưa đúng.",
                       fields={"current_password": "Mật khẩu hiện tại chưa đúng."})
    login_attempts.reset(key)
    _check_new_password(user, new_password, field="new_password")
    _apply_new_password(db, user, new_password, utcnow())
    security_log.info("password_changed user_id=%s ip=%s", user.id, ip)


def _check_new_password(user: User, new_password: str, field: str) -> None:
    problem = password_problem(new_password, user.email)
    if problem is None and verify_password(new_password, user.hashed_password):
        problem = "Mật khẩu mới cần khác mật khẩu cũ."
    if problem:
        raise AppError(400, "VALIDATION_ERROR", "Mật khẩu mới chưa hợp lệ.", fields={field: problem})


def _apply_new_password(db: Session, user: User, new_password: str, now: datetime) -> None:
    user.hashed_password = hash_password(new_password)
    # Làm tròn tới mili giây cho khớp claim "pwd" của access token (password_stamp) trên cả SQLite lẫn PostgreSQL.
    user.password_changed_at = now.replace(microsecond=now.microsecond // 1000 * 1000)
    # Liên kết đặt lại còn treo cũng hết hiệu lực khi mật khẩu đã đổi.
    db.execute(update(PasswordResetToken)
               .where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
               .values(used_at=now))


def password_changed_notice(user: User, when: datetime, signed_out: bool):
    return render.password_changed_email(user.email, user.display_name, when, _plain_link("/quen-mat-khau"), signed_out)


# ---------- Xác minh email ----------

def create_verification(db: Session, user: User, ip: str):
    """Tạo liên kết xác minh mới (vô hiệu liên kết cũ) và trả thư cần gửi."""
    now = utcnow()
    db.execute(update(EmailVerificationToken)
               .where(EmailVerificationToken.user_id == user.id, EmailVerificationToken.used_at.is_(None))
               .values(used_at=now))
    token = new_one_time_token()
    db.add(EmailVerificationToken(id=str(uuid.uuid4()), user_id=user.id, token_hash=hash_refresh_token(token),
                                  created_at=now, expires_at=now + timedelta(hours=settings.email_verify_hours),
                                  requested_ip=ip[:64]))
    db.commit()
    return render.verify_email(user.email, user.display_name, _link(VERIFY_PATH, token), settings.email_verify_hours)


def verify_email(db: Session, token: str) -> User:
    if not token:
        raise verify_invalid()
    now = utcnow()
    row = db.execute(
        update(EmailVerificationToken)
        .where(EmailVerificationToken.token_hash == hash_refresh_token(token), EmailVerificationToken.used_at.is_(None))
        .values(used_at=now)
        .returning(EmailVerificationToken.user_id, EmailVerificationToken.expires_at)
    ).first()
    if row is None or _aware(row.expires_at) <= now:
        db.rollback()
        raise verify_invalid()
    user = db.get(User, row.user_id)
    if not _can_receive_mail(user):
        db.rollback()
        raise verify_invalid()
    if user.email_verified_at is None:
        user.email_verified_at = now
    db.commit()
    security_log.info("email_verified user_id=%s", user.id)
    return user


def account_exists_notice(user: User):
    return render.account_exists_email(user.email, user.display_name, _plain_link("/dang-nhap"),
                                       _plain_link("/quen-mat-khau"))
