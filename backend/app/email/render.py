"""Dựng thư từ mẫu Jinja2 (A10): HTML dạng bảng + CSS inline cho Gmail/Outlook, kèm bản chữ thuần.

Thư viết bằng tiếng Anh (yêu cầu của nhóm); giao diện web vẫn tiếng Việt.
Ứng dụng email không đọc được biến CSS nên màu lấy từ token "Sân khấu" sáng trong
frontend/src/theme/brands.css; test_email_palette_matches_brand kiểm hai nơi luôn khớp.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .sender import OutgoingEmail

HERE = Path(__file__).parent
LOGO_CID = "hm-logo"

# Token brand "Sân khấu" (sáng) dùng trong thư. Đổi ở brands.css thì đổi ở đây (test bắt lệch).
PALETTE = {
    "bg": "#f4f2f8",
    "surface": "#ffffff",
    "ink": "#17142b",
    "muted": "#57536e",
    "line": "#dcd8e8",
    "primary": "#4b33b8",
    "on_primary": "#ffffff",
    "signature": "#f2b33d",
}

# Việt Nam không có giờ mùa hè nên dùng độ lệch cố định, không phụ thuộc gói tzdata trong image.
VN_TZ = timezone(timedelta(hours=7), "GMT+7")


@lru_cache(maxsize=1)
def _env() -> Environment:
    return Environment(loader=FileSystemLoader(HERE / "templates"), autoescape=select_autoescape(["html"]),
                       trim_blocks=True, lstrip_blocks=True)


@lru_cache(maxsize=1)
def _logo() -> bytes:
    return (HERE / "assets" / "logo.png").read_bytes()


def format_vn_time(moment: datetime) -> str:
    """25 Nov 2026, 5:39 PM (GMT+7). Tự viết thay vì %-I để chạy cả trên Windows."""
    local = (moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)).astimezone(VN_TZ)
    hour = local.hour % 12 or 12
    ampm = "AM" if local.hour < 12 else "PM"
    return f"{local.day} {local.strftime('%b %Y')}, {hour}:{local.minute:02d} {ampm} (GMT+7)"


def _build(template: str, to: str, subject: str, **ctx) -> OutgoingEmail:
    env = _env()
    ctx = {"subject": subject, "c": PALETTE, "logo_cid": LOGO_CID, **ctx}
    html = env.get_template(f"{template}.html").render(**ctx)
    text = env.get_template(f"{template}.txt").render(**ctx)
    return OutgoingEmail(to=to, subject=subject, html=html, text=text, inline_images={LOGO_CID: (_logo(), "png")})


def reset_password_email(to: str, name: str, link: str, minutes: int) -> OutgoingEmail:
    return _build("reset_password", to, "Reset your HarmonyMentor password", name=name, link=link, minutes=minutes)


def password_changed_email(to: str, name: str, when: datetime, reset_link: str, signed_out: bool) -> OutgoingEmail:
    return _build("password_changed", to, "Your password was changed", name=name, when=format_vn_time(when),
                  reset_link=reset_link, signed_out=signed_out)


def verify_email(to: str, name: str, link: str, hours: int) -> OutgoingEmail:
    return _build("verify_email", to, "Verify your email", name=name, link=link, hours=hours)


def account_exists_email(to: str, name: str, login_link: str, reset_link: str) -> OutgoingEmail:
    """Ai đó đăng ký bằng email đã có tài khoản (1A): báo chủ email thay vì báo người đăng ký."""
    return _build("account_exists", to, "You already have a HarmonyMentor account", name=name,
                  login_link=login_link, reset_link=reset_link)
