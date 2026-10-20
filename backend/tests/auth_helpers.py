"""Tiện ích test: tạo người dùng trực tiếp trong CSDL và cấp access token, bỏ qua bước đăng nhập."""

from __future__ import annotations

from app.auth.security import create_access_token


def auth(user_id: str, role: str = "learner") -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id, role)}"}
