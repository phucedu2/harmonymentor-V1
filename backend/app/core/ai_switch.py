"""Công tắc AI do Quản trị viên bật/tắt qua web (ADR-036, Phúc 8A).

AI chạy khi CẢ HAI cùng bật: .env (AI_ENABLED + khóa Gemini) và công tắc này. Công tắc chỉ tắt được, không bật được AI
khi .env chưa có khóa: khóa API không bao giờ đi qua web hay CSDL. Đọc CSDL có bộ nhớ đệm vài giây để mỗi yêu cầu
không tốn thêm một truy vấn; đổi công tắc thì xóa bộ nhớ đệm ngay.
"""

from __future__ import annotations

import time
from typing import Any

SETTING_KEY = "ai_enabled"
_TTL = 5.0
_cache: dict[str, Any] = {"at": 0.0, "on": True}


def switch_on() -> bool:
    now = time.monotonic()
    if now - _cache["at"] < _TTL:
        return bool(_cache["on"])
    from ..db.models import AppSetting
    from ..db.session import SessionLocal
    try:
        with SessionLocal() as db:
            row = db.get(AppSetting, SETTING_KEY)
            on = True if row is None else bool((row.value or {}).get("on", True))
    except Exception:  # noqa: BLE001 - CSDL cũ chưa có bảng: giữ hành vi trước đây (theo .env)
        on = True
    _cache.update(at=now, on=on)
    return on


def reset_cache() -> None:
    _cache.update(at=0.0, on=True)
