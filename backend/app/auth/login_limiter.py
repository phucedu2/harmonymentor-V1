"""Khóa đăng nhập: 5 lần sai trong 15 phút theo cặp IP + email (NFR-19).

Dùng Redis khi có REDIS_URL để nhiều tiến trình API chia sẻ bộ đếm; không có thì dùng bộ nhớ trong.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Protocol

from ..core.config import settings

log = logging.getLogger(__name__)

MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60


class LoginAttemptStore(Protocol):
    def locked_for(self, key: str) -> int:
        """Số giây còn bị khóa; 0 nếu được thử."""

    def record_failure(self, key: str) -> None: ...

    def reset(self, key: str) -> None: ...


class MemoryLoginAttemptStore:
    def __init__(self) -> None:
        self._data: dict[str, tuple[int, float]] = {}
        self._lock = threading.Lock()

    def _current(self, key: str) -> tuple[int, float] | None:
        entry = self._data.get(key)
        if entry and time.monotonic() - entry[1] >= WINDOW_SECONDS:
            self._data.pop(key, None)
            return None
        return entry

    def locked_for(self, key: str) -> int:
        with self._lock:
            entry = self._current(key)
            if not entry or entry[0] < MAX_FAILURES:
                return 0
            return max(1, int(WINDOW_SECONDS - (time.monotonic() - entry[1])))

    def record_failure(self, key: str) -> None:
        with self._lock:
            entry = self._current(key)
            self._data[key] = (entry[0] + 1, entry[1]) if entry else (1, time.monotonic())

    def reset(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)


class RedisLoginAttemptStore:
    """Cửa sổ cố định: lần sai đầu tiên đặt TTL 15 phút. Redis lỗi thì cho đăng nhập tiếp (fail open)
    và ghi log, để sự cố Redis không khóa toàn bộ người dùng; mật khẩu vẫn được kiểm tra bình thường."""

    def __init__(self, url: str) -> None:
        import redis

        self._redis = redis.Redis.from_url(url, socket_timeout=1, socket_connect_timeout=1)

    @staticmethod
    def _key(key: str) -> str:
        return f"login_fail:{key}"

    def locked_for(self, key: str) -> int:
        try:
            count = self._redis.get(self._key(key))
            if count is None or int(count) < MAX_FAILURES:
                return 0
            ttl = self._redis.ttl(self._key(key))
            return max(1, int(ttl)) if ttl and ttl > 0 else WINDOW_SECONDS
        except Exception:  # noqa: BLE001 — mọi lỗi kết nối Redis
            log.exception("Redis không đọc được bộ đếm đăng nhập")
            return 0

    def record_failure(self, key: str) -> None:
        try:
            pipe = self._redis.pipeline()
            pipe.incr(self._key(key))
            pipe.expire(self._key(key), WINDOW_SECONDS, nx=True)
            pipe.execute()
        except Exception:  # noqa: BLE001
            log.exception("Redis không ghi được bộ đếm đăng nhập")

    def reset(self, key: str) -> None:
        try:
            self._redis.delete(self._key(key))
        except Exception:  # noqa: BLE001
            log.exception("Redis không xóa được bộ đếm đăng nhập")


def build_store() -> LoginAttemptStore:
    return RedisLoginAttemptStore(settings.redis_url) if settings.redis_url else MemoryLoginAttemptStore()


login_attempts: LoginAttemptStore = build_store()


def attempt_key(ip: str, email: str) -> str:
    return f"{ip}|{email}"
