"""Giao diện EmailSender và hai bản cài đặt (A9).

- ConsoleSender: giữ thư trong bộ nhớ (test đọc lại được) và chỉ ghi log người nhận đã che + tiêu đề.
  KHÔNG ghi nội dung thư vào log vì thư chứa liên kết một lần (A11).
- SmtpSender: smtplib, STARTTLS khi cần. Cùng một lớp cho Mailpit (dev, cổng 1025, không TLS, không đăng nhập)
  và Gmail SMTP (smtp.gmail.com:587, STARTTLS, Mật khẩu ứng dụng 16 ký tự).
"""

from __future__ import annotations

import logging
import smtplib
import ssl
import threading
from dataclasses import dataclass, field
from email.message import EmailMessage
from email.utils import make_msgid
from typing import Protocol

from ..core.config import Settings, settings

log = logging.getLogger(__name__)


@dataclass
class OutgoingEmail:
    to: str
    subject: str
    html: str
    text: str
    # cid -> (bytes, kiểu con của image/*). Logo nhúng CID chạy trên Gmail/Outlook kể cả khi web ở localhost (6A).
    inline_images: dict[str, tuple[bytes, str]] = field(default_factory=dict)


class EmailSender(Protocol):
    def send(self, email: OutgoingEmail) -> None: ...


def mask_email(email: str) -> str:
    """p***@gmail.com: đủ để người dùng nhận ra, không lộ trọn địa chỉ trên màn hình hay trong log."""
    local, _, domain = email.partition("@")
    if not domain:
        return "***"
    return f"{local[:1]}***@{domain}"


class ConsoleSender:
    def __init__(self) -> None:
        self.outbox: list[OutgoingEmail] = []
        self._lock = threading.Lock()

    def send(self, email: OutgoingEmail) -> None:
        with self._lock:
            self.outbox.append(email)
        log.info("Email (console) tới %s: %s", mask_email(email.to), email.subject)


def build_message(email: OutgoingEmail, sender: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = email.to
    msg["Subject"] = email.subject
    msg["Message-ID"] = make_msgid(domain=sender.rsplit("@", 1)[-1].strip(">") or "harmonymentor.local")
    # Thư giao dịch: không để trình đọc thư tự trả lời vắng mặt vào hộp thư gửi.
    msg["Auto-Submitted"] = "auto-generated"
    msg.set_content(email.text)
    msg.add_alternative(email.html, subtype="html")
    html_part = msg.get_payload()[1]
    for cid, (data, subtype) in email.inline_images.items():
        html_part.add_related(data, maintype="image", subtype=subtype, cid=f"<{cid}>", filename=f"{cid}.{subtype}")
    return msg


class SmtpSender:
    def __init__(self, cfg: Settings) -> None:
        self._cfg = cfg

    def _use_starttls(self) -> bool:
        flag = self._cfg.smtp_starttls
        return self._cfg.smtp_port == 587 if flag == "auto" else flag in {"1", "true"}

    def send(self, email: OutgoingEmail) -> None:
        cfg = self._cfg
        msg = build_message(email, cfg.email_from)
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=cfg.smtp_timeout_seconds) as smtp:
            if self._use_starttls():
                smtp.starttls(context=ssl.create_default_context())
            if cfg.smtp_user:
                smtp.login(cfg.smtp_user, cfg.smtp_password)
            smtp.send_message(msg)
        log.info("Email (smtp) tới %s: %s", mask_email(email.to), email.subject)


_sender: EmailSender | None = None


def get_sender() -> EmailSender:
    global _sender
    if _sender is None:
        _sender = SmtpSender(settings) if settings.email_backend == "smtp" else ConsoleSender()
    return _sender


def set_sender(sender: EmailSender | None) -> None:
    """Test thay bộ gửi (ví dụ ConsoleSender mới để đọc hộp thư sạch)."""
    global _sender
    _sender = sender


def deliver(email: OutgoingEmail) -> None:
    """Gửi trong BackgroundTasks: lỗi SMTP chỉ ghi log (không có nội dung thư), không làm hỏng request đã trả."""
    try:
        get_sender().send(email)
    except Exception:  # noqa: BLE001 — mọi lỗi mạng/SMTP
        log.exception("Không gửi được email tới %s (%s)", mask_email(email.to), email.subject)
