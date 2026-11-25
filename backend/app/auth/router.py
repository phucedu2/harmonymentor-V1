"""Endpoint xác thực và hồ sơ theo ADR-004 (FR-AUTH-01..07, 10) và ADR-040 (quên/đổi mật khẩu, xác minh email)."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.errors import AppError, error_response
from ..db.models import User
from ..db.session import get_db
from .avatars import avatar_of
from .deps import client_ip, get_current_user
from ..db.models import RefreshToken
from ..email.sender import deliver
from . import account
from .rate_limit import (
    FORGOT_PER_EMAIL,
    FORGOT_PER_IP,
    HOUR,
    REGISTER_PER_IP,
    RESEND_VERIFY_PER_USER,
    rate_limits,
)
from .schemas import (
    AuthOut,
    ChangePasswordIn,
    EmailIn,
    LoginIn,
    MessageOut,
    ProfilePatchIn,
    RegisterIn,
    RegisterPendingOut,
    ResetCheckOut,
    ResetPasswordIn,
    TokenIn,
    UserOut,
)
from .security import hash_refresh_token
from .service import (
    _aware,
    access_token_for,
    authenticate,
    issue_refresh_token,
    normalize_email,
    register_user,
    revoke_all_refresh_tokens,
    revoke_refresh_token,
    rotate_refresh_token,
    utcnow,
)

REFRESH_COOKIE = "hm_refresh"
# Cookie chỉ gửi kèm các request /api/v1/auth/*, không đi theo mọi request API.
REFRESH_COOKIE_PATH = "/api/v1/auth"

router = APIRouter(prefix="/api/v1", tags=["auth"])


def user_out(user: User) -> UserOut:
    return UserOut(id=user.id, email=user.email, display_name=user.display_name, role=user.role,
                   preferred_instrument=user.preferred_instrument, goal_text=user.goal_text,
                   avatar=avatar_of(user.id, user.avatar_key), email_verified=user.email_verified_at is not None,
                   password_changed_at=_aware(user.password_changed_at) if user.password_changed_at else None)


def _clear_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH, httponly=True, samesite="lax",
                           secure=settings.cookie_secure)


def _session_response(response: Response, user: User, refresh_token: str, remember: bool = True) -> AuthOut:
    # A8: không ghi nhớ thì cookie phiên (không max_age), trình duyệt xóa khi đóng.
    max_age = settings.remember_refresh_days * 86400 if remember else None
    response.set_cookie(
        REFRESH_COOKIE, refresh_token, max_age=max_age, path=REFRESH_COOKIE_PATH,
        httponly=True, samesite="lax", secure=settings.cookie_secure,
    )
    response.headers["Cache-Control"] = "no-store"
    return AuthOut(access_token=access_token_for(user), expires_in=settings.access_token_minutes * 60,
                   user=user_out(user))


def _ip(request: Request) -> str:
    return client_ip(request, settings.trust_proxy)


def _limit(key: str, limit: int, window: int = HOUR) -> None:
    wait = rate_limits.hit(key, limit, window)
    if wait:
        raise AppError(429, "RATE_LIMITED", "Bạn gửi yêu cầu hơi nhiều. Hãy thử lại sau ít phút.",
                       retryable=True, headers={"Retry-After": str(wait)})


CHECK_EMAIL_MESSAGE = ("Nếu email này có tài khoản, chúng tôi đã gửi liên kết đặt lại mật khẩu. "
                       "Hãy kiểm tra hộp thư (cả mục Thư rác).")


@router.post("/auth/register", response_model=AuthOut, status_code=201,
             responses={202: {"model": RegisterPendingOut}})
def register(body: RegisterIn, request: Request, response: Response, background: BackgroundTasks,
             db: Session = Depends(get_db)):
    ip = _ip(request)
    _limit(f"register:ip:{ip}", REGISTER_PER_IP)
    user, created = register_user(db, body.email, body.password, body.display_name)
    if not created:
        # 1A: không nói "email đã có tài khoản"; chủ email nhận thư báo (nếu tài khoản còn nhận được thư).
        if account._can_receive_mail(user):
            background.add_task(deliver, account.account_exists_notice(user))
        return JSONResponse(status_code=202, headers={"Cache-Control": "no-store"}, content=RegisterPendingOut(
            message="Hãy kiểm tra hộp thư của bạn để tiếp tục.").model_dump())
    background.add_task(deliver, account.create_verification(db, user, ip))
    return _session_response(response, user, issue_refresh_token(db, user))


@router.post("/auth/login", response_model=AuthOut)
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    user = authenticate(db, body.email, body.password, _ip(request))
    return _session_response(response, user, issue_refresh_token(db, user, body.remember), body.remember)


@router.post("/auth/refresh", response_model=AuthOut)
def refresh(response: Response, hm_refresh: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    try:
        user, new_token, remember = rotate_refresh_token(db, hm_refresh)
    except AppError as exc:
        # Token hỏng/hết hạn: xóa cookie để trình duyệt không gửi lại mãi.
        failed = error_response(exc.status, exc.code, exc.message)
        _clear_cookie(failed)
        return failed
    return _session_response(response, user, new_token, remember)


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
    if "avatar" in sent:
        user.avatar_key = body.avatar  # None = quay về con vật mặc định suy từ id
    db.commit()
    return user_out(user)


# ---------- ADR-040: quên / đặt lại / đổi mật khẩu, xác minh email ----------

@router.post("/auth/forgot-password", response_model=MessageOut, status_code=202)
def forgot_password(body: EmailIn, request: Request, background: BackgroundTasks):
    """A3: luôn 202 cùng một câu; tra người dùng và gửi thư sau khi đã trả lời (thời gian phản hồi đều nhau)."""
    ip = _ip(request)
    email = normalize_email(body.email)
    _limit(f"forgot:ip:{ip}", FORGOT_PER_IP)
    _limit(f"forgot:email:{email}", FORGOT_PER_EMAIL)
    background.add_task(account.process_forgot_password, email, ip)
    return MessageOut(message=CHECK_EMAIL_MESSAGE)


@router.post("/auth/reset-password/check", response_model=ResetCheckOut)
def reset_password_check(body: TokenIn, request: Request, db: Session = Depends(get_db)):
    # Giới hạn theo IP để không ai dò token hàng loạt (token 256 bit nên chỉ là lớp phòng thêm).
    _limit(f"reset-check:ip:{_ip(request)}", 30)
    return ResetCheckOut(email_masked=account.check_reset_token(db, body.token))


@router.post("/auth/reset-password", response_model=MessageOut)
def reset_password(body: ResetPasswordIn, request: Request, background: BackgroundTasks,
                   db: Session = Depends(get_db)):
    ip = _ip(request)
    _limit(f"reset:ip:{ip}", 30)
    user = account.reset_password(db, body.token, body.new_password, ip)
    background.add_task(deliver, account.password_changed_notice(user, utcnow(), signed_out=True))
    # A5: không tự đăng nhập; frontend chuyển tới /dang-nhap?da-dat-lai=1.
    return MessageOut(message="Đã đặt lại mật khẩu. Hãy đăng nhập bằng mật khẩu mới.")


@router.post("/auth/change-password", response_model=AuthOut)
def change_password(body: ChangePasswordIn, request: Request, response: Response, background: BackgroundTasks,
                    hm_refresh: str | None = Cookie(default=None), user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """A6. Đặt dưới /auth (không phải /me/password) vì cookie refresh chỉ gửi kèm /api/v1/auth/*:
    cần nó để biết phiên nào là phiên hiện tại mà giữ lại (ADR-040 mục "Lệch so với đề bài")."""
    ip = _ip(request)
    account.change_password(db, user, body.current_password, body.new_password, ip)
    current = None
    if hm_refresh:
        current = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(hm_refresh),
                                                       RefreshToken.revoked_at.is_(None), RefreshToken.user_id == user.id))
    if body.sign_out_others:
        revoke_all_refresh_tokens(db, user.id)
    elif current is not None:
        current.revoked_at = utcnow()
    remember = bool(current.remember) if current is not None else False
    started = (current.session_started_at or current.created_at) if current is not None else None
    db.commit()
    background.add_task(deliver, account.password_changed_notice(user, utcnow(), signed_out=body.sign_out_others))
    # Access token cũ đã chết theo password_changed_at; cấp phiên mới cho thiết bị đang dùng.
    return _session_response(response, user, issue_refresh_token(db, user, remember, started), remember)


@router.post("/auth/verify-email", response_model=MessageOut)
def verify_email(body: TokenIn, request: Request, db: Session = Depends(get_db)):
    _limit(f"verify:ip:{_ip(request)}", 30)
    account.verify_email(db, body.token)
    return MessageOut(message="Đã xác minh email. Cảm ơn bạn!")


@router.post("/auth/resend-verification", response_model=MessageOut, status_code=202)
def resend_verification(request: Request, background: BackgroundTasks, user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    if user.email_verified_at is not None or not user.email:
        return JSONResponse(status_code=200, content={"message": "Email của bạn đã được xác minh."})
    _limit(f"resend-verify:user:{user.id}", RESEND_VERIFY_PER_USER)
    background.add_task(deliver, account.create_verification(db, user, _ip(request)))
    return MessageOut(message="Đã gửi lại thư xác minh. Hãy kiểm tra hộp thư của bạn.")
