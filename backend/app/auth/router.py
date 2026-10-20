"""Endpoint xác thực và hồ sơ theo ADR-004 (FR-AUTH-01..07, 10)."""

from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, Request, Response
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.errors import AppError, error_response
from ..db.models import User
from ..db.session import get_db
from .deps import client_ip, get_current_user
from .schemas import AuthOut, LoginIn, ProfilePatchIn, RegisterIn, UserOut
from .service import (
    access_token_for,
    authenticate,
    issue_refresh_token,
    register_user,
    revoke_refresh_token,
    rotate_refresh_token,
)

REFRESH_COOKIE = "hm_refresh"
# Cookie chỉ gửi kèm các request /api/v1/auth/*, không đi theo mọi request API.
REFRESH_COOKIE_PATH = "/api/v1/auth"

router = APIRouter(prefix="/api/v1", tags=["auth"])


def user_out(user: User) -> UserOut:
    return UserOut(id=user.id, email=user.email, display_name=user.display_name, role=user.role,
                   preferred_instrument=user.preferred_instrument, goal_text=user.goal_text)


def _clear_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH, httponly=True, samesite="lax",
                           secure=settings.cookie_secure)


def _session_response(response: Response, user: User, refresh_token: str) -> AuthOut:
    response.set_cookie(
        REFRESH_COOKIE, refresh_token, max_age=settings.refresh_token_days * 86400, path=REFRESH_COOKIE_PATH,
        httponly=True, samesite="lax", secure=settings.cookie_secure,
    )
    response.headers["Cache-Control"] = "no-store"
    return AuthOut(access_token=access_token_for(user), expires_in=settings.access_token_minutes * 60,
                   user=user_out(user))


@router.post("/auth/register", response_model=AuthOut, status_code=201)
def register(body: RegisterIn, response: Response, db: Session = Depends(get_db)):
    user = register_user(db, body.email, body.password, body.display_name)
    return _session_response(response, user, issue_refresh_token(db, user))


@router.post("/auth/login", response_model=AuthOut)
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    user = authenticate(db, body.email, body.password, client_ip(request, settings.trust_proxy))
    return _session_response(response, user, issue_refresh_token(db, user))


@router.post("/auth/refresh", response_model=AuthOut)
def refresh(response: Response, hm_refresh: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    try:
        user, new_token = rotate_refresh_token(db, hm_refresh)
    except AppError as exc:
        # Token hỏng/hết hạn: xóa cookie để trình duyệt không gửi lại mãi.
        failed = error_response(exc.status, exc.code, exc.message)
        _clear_cookie(failed)
        return failed
    return _session_response(response, user, new_token)


@router.post("/auth/logout", status_code=204)
def logout(hm_refresh: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    revoke_refresh_token(db, hm_refresh)
    response = Response(status_code=204)
    _clear_cookie(response)
    return response


@router.get("/me", response_model=UserOut)
def read_me(user: User = Depends(get_current_user)):
    return user_out(user)


@router.patch("/me", response_model=UserOut)
def update_me(body: ProfilePatchIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sent = body.model_fields_set
    if "display_name" in sent:
        name = (body.display_name or "").strip()
        if not name:
            raise AppError(400, "VALIDATION_ERROR", "Tên hiển thị không được để trống.",
                           fields={"display_name": "Hãy nhập tên hiển thị."})
        user.display_name = name
    if "preferred_instrument" in sent:
        user.preferred_instrument = body.preferred_instrument
    db.commit()
    return user_out(user)
