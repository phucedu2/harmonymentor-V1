"""Phụ thuộc FastAPI: lấy người dùng từ Bearer token, chặn người không phải admin."""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from ..core.errors import AppError
from ..db.models import User
from ..db.session import get_db
from .security import decode_access_token


def _unauthorized() -> AppError:
    return AppError(401, "UNAUTHORIZED", "Bạn cần đăng nhập.", headers={"WWW-Authenticate": "Bearer"})


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise _unauthorized()
    payload = decode_access_token(token.strip())
    if payload is None:
        raise _unauthorized()
    user = db.get(User, payload["sub"])
    # Người dùng bị khóa hoặc người học mô phỏng (không đăng nhập được, nguyên tắc 9) đều bị chặn.
    if user is None or not user.is_active or user.is_synthetic:
        raise _unauthorized()
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise AppError(403, "FORBIDDEN", "Chức năng này chỉ dành cho Quản trị viên.")
    return user


def client_ip(request: Request, trust_proxy: bool) -> str:
    if trust_proxy:
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
