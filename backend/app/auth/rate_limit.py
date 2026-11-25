"""Giới hạn tần suất kiểu cửa sổ cố định cho quên mật khẩu, gửi lại thư xác minh, đăng ký (ADR-040).

Dùng chung hạ tầng với khóa đăng nhập: Redis khi có REDIS_URL (nhiều tiến trình chia sẻ bộ đếm),
không có thì bộ nhớ trong. Redis lỗi thì cho qua (fail open) và ghi log, giống login_limiter.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Protocol

from ..core.config import settings

log = logging.getLogger(__name__)


class RateLimitStore(Protocol):
    def hit(self, key: str, limit: int, window_seconds: int) -> int:
        """Ghi một lượt. Trả số giây phải chờ nếu đã vượt giới hạn (lượt này bị từ chối), 0 nếu được phép."""

    def clear(self) -> None: ...


class MemoryRateLimitStore:
    def __init__(self) -> None:
        self._data: dict[str, tuple[int, float, int]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window_seconds: int) -> int:
        now = time.monotonic()
        with self._lock:
            count, start, window = self._data.get(key, (0, now, window_seconds))
            if now - start >= window:
                count, start = 0, now
            if count >= limit:
                return max(1, int(window - (now - start)))
            self._data[key] = (count + 1, start, window_seconds)
            return 0

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


class RedisRateLimitStore:
    def __init__(self, url: str) -> None:
        import redis

        self._redis = redis.Redis.from_url(url, socket_timeout=1, socket_connect_timeout=1)

    def hit(self, key: str, limit: int, window_seconds: int) -> int:
        name = f"rl:{key}"
        try:
            pipe = self._redis.pipeline()
            pipe.incr(name)
            pipe.expire(name, window_seconds, nx=True)
            pipe.ttl(name)
            count, _, ttl = pipe.execute()
            if int(count) > limit:
                return max(1, int(ttl)) if ttl and ttl > 0 else window_seconds
            return 0
        except Exception:  # noqa: BLE001 — mọi lỗi kết nối Redis
            log.exception("Redis không ghi được bộ đếm giới hạn tần suất")
            return 0

    def clear(self) -> None:  # chỉ dùng trong test với bộ nhớ trong
        pass


def build_store() -> RateLimitStore:
    return RedisRateLimitStore(settings.redis_url) if settings.redis_url else MemoryRateLimitStore()


rate_limits: RateLimitStore = build_store()

HOUR = 3600
# A3: 3 yêu cầu / email / giờ và 10 / IP / giờ. Đăng ký 10 / IP / giờ (quyết định A của Phúc, 25/11).
FORGOT_PER_EMAIL = 3
FORGOT_PER_IP = 10
RESEND_VERIFY_PER_USER = 3
REGISTER_PER_IP = 10
