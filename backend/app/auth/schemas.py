from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .avatars import AvatarKey

Instrument = Literal["piano", "guitar", "drums"]


class RegisterIn(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(max_length=200)
    display_name: str = Field(min_length=1, max_length=160)


class LoginIn(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(max_length=200)
    # A8: true → phiên 30 ngày trượt; false → cookie phiên (mất khi đóng trình duyệt) + refresh 1 ngày.
    # Mặc định true để client cũ chưa gửi trường này giữ hành vi cookie lâu dài như trước.
    remember: bool = True


class UserOut(BaseModel):
    id: str
    email: str | None
    display_name: str
    role: Literal["learner", "admin"]
    preferred_instrument: Instrument | None
    goal_text: str | None
    avatar: AvatarKey
    # ADR-040: banner nhắc xác minh (mức mềm) và dòng "Đổi lần cuối" ở Hồ sơ.
    email_verified: bool = True
    password_changed_at: datetime | None = None


class AuthOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserOut


class ProfilePatchIn(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=160)
    preferred_instrument: Instrument | None = None
    avatar: AvatarKey | None = None


class EmailIn(BaseModel):
    email: str = Field(max_length=320)


class TokenIn(BaseModel):
    token: str = Field(min_length=1, max_length=200)


class ResetPasswordIn(BaseModel):
    token: str = Field(min_length=1, max_length=200)
    new_password: str = Field(max_length=200)


class ChangePasswordIn(BaseModel):
    current_password: str = Field(max_length=200)
    new_password: str = Field(max_length=200)
    sign_out_others: bool = True


class MessageOut(BaseModel):
    message: str


class ResetCheckOut(BaseModel):
    email_masked: str


class RegisterPendingOut(BaseModel):
    """1A: email đã có tài khoản. Không có token; giao diện hiện màn "Kiểm tra hộp thư"."""
    status: Literal["check_email"] = "check_email"
    message: str
