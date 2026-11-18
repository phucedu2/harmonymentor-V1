"""Ảnh đại diện con vật (ADR-029, 10A). Không cho tải ảnh lên: chỉ chọn trong bộ con vật vẽ sẵn ở frontend,
nên không phải lưu file hay kiểm duyệt ảnh. Người chưa chọn nhận một con cố định suy từ id (đổi máy vẫn giống nhau)."""

from __future__ import annotations

import hashlib
from typing import Literal, get_args

AvatarKey = Literal["meo", "cao", "gau", "cu", "chim_canh_cut", "tho", "gau_truc", "ech", "ho", "koala", "su_tu", "ca_voi"]
AVATARS: tuple[str, ...] = get_args(AvatarKey)


def default_avatar(user_id: str) -> str:
    # SHA-256 thay vì hash(): hash() của Python đổi theo mỗi lần chạy nên con vật sẽ nhảy sau khi khởi động lại.
    return AVATARS[int(hashlib.sha256(user_id.encode("utf-8")).hexdigest(), 16) % len(AVATARS)]


def avatar_of(user_id: str, stored: str | None) -> str:
    return stored if stored in AVATARS else default_avatar(user_id)
