from __future__ import annotations

import logging

from sqlalchemy import text

from ..db.session import engine

log = logging.getLogger(__name__)


def check_db() -> str:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:  # noqa: BLE001 — mọi lỗi kết nối đều là "error"
        log.exception("Health check: CSDL lỗi")
        return "error"


def check_redis(url: str) -> str:
    if not url:
        return "not_configured"
    try:
        import redis

        client = redis.Redis.from_url(url, socket_timeout=1, socket_connect_timeout=1)
        return "ok" if client.ping() else "error"
    except Exception:  # noqa: BLE001
        log.exception("Health check: Redis lỗi")
        return "error"
