"""HarmonyMentor Phase 0.3/0.4 application skeleton.

The legacy deterministic Music Engine routes stay available under /api/v1/engine while new
learning/content/review contracts are introduced incrementally.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .api.router import api_router
from .content.versioning import SeedConflictError
from .core.config import check_runtime_settings, settings
from .core.errors import install_error_handlers
from .core.health import check_db, check_redis
from .core.middleware import install_middleware
from .db.seed import seed_database
from .db.session import SessionLocal, create_schema
from .music_engine.errors import MusicEngineError

logger = logging.getLogger("harmonymentor.seed")


@asynccontextmanager
async def lifespan(_: FastAPI):
    check_runtime_settings(settings)
    if settings.auto_create_schema:
        create_schema()
    if settings.seed_demo_content:
        with SessionLocal() as db:
            try:
                seed_database(db)
            except SeedConflictError as exc:
                # Dừng khởi động có chủ ý (ADR-006): chạy tiếp với nội dung lệch phiên bản là âm thầm đổi nghĩa lượt làm cũ.
                logger.error("%s", exc)
                raise
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.include_router(api_router)
install_error_handlers(app)
install_middleware(app, settings.cors_origins)


@app.exception_handler(MusicEngineError)
async def engine_error_handler(_: Request, exc: MusicEngineError):
    return JSONResponse(status_code=422, content={"error": exc.to_dict()})


@app.get("/health", tags=["system"])
def health():
    """Trạng thái CSDL và Redis cho healthcheck của Docker: 200 khi mọi phần sống, 503 kèm phần lỗi."""
    checks = {"db": check_db(), "redis": check_redis(settings.redis_url)}
    ok = all(v in ("ok", "not_configured") for v in checks.values())
    body = {"status": "ok" if ok else "degraded", "version": settings.app_version, "checks": checks}
    return JSONResponse(status_code=200 if ok else 503, content=body)
