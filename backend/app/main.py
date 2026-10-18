"""HarmonyMentor Phase 0.3/0.4 application skeleton.

The legacy deterministic Music Engine routes stay available under /api/v1/engine while new
learning/content/review contracts are introduced incrementally.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .api.router import api_router
from .core.config import settings
from .db.seed import seed_database
from .db.session import SessionLocal, create_schema
from .music_engine.errors import MusicEngineError


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_schema:
        create_schema()
    if settings.seed_demo_content:
        with SessionLocal() as db:
            seed_database(db)
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.include_router(api_router)


@app.exception_handler(MusicEngineError)
async def engine_error_handler(_: Request, exc: MusicEngineError):
    return JSONResponse(status_code=422, content={"error": exc.to_dict()})


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "version": settings.app_version}
