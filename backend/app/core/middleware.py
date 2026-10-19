"""Middleware vận hành (NFR-01, NFR-24): X-Response-Time, X-Request-ID, log truy cập JSON và CORS.

Log chỉ ghi method, đường dẫn (không có query string), mẫu route, mã trạng thái và thời gian;
không bao giờ ghi body, header Authorization hay cookie, nên mật khẩu và token không lọt vào log.
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

access_log = logging.getLogger("harmonymentor.access")
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _configure_access_log() -> None:
    if access_log.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    access_log.addHandler(handler)
    access_log.setLevel(logging.INFO)
    access_log.propagate = False


def parse_origins(raw: str) -> list[str]:
    return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]


def install_middleware(app: FastAPI, cors_origins: str) -> None:
    _configure_access_log()

    origins = parse_origins(cors_origins)
    if origins:
        # Mặc định rỗng vì frontend gọi cùng origin (Vite proxy / nginx). Chỉ mở khi cần, không dùng "*"
        # vì có cookie refresh (allow_credentials).
        app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                           allow_methods=["*"], allow_headers=["*"], expose_headers=["X-Response-Time", "X-Request-ID"])

    @app.middleware("http")
    async def timing_and_access_log(request: Request, call_next):
        incoming = request.headers.get("X-Request-ID", "")
        request_id = incoming if _REQUEST_ID_RE.match(incoming) else uuid.uuid4().hex
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            route = request.scope.get("route")
            access_log.info(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "route": getattr(route, "path", None),
                "status": status,
                "duration_ms": round(duration_ms, 2),
            }, ensure_ascii=False))
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        response.headers["X-Request-ID"] = request_id
        return response
