"""Giai đoạn B (DevOps): header thời gian xử lý, request id, log không lộ bí mật, /health, CORS, p95."""

from __future__ import annotations

import importlib.util
import io
import json
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.main as main_module
from app.core.middleware import install_middleware, parse_origins
from app.main import app

ROOT = Path(__file__).resolve().parents[2]


def _load_p95():
    spec = importlib.util.spec_from_file_location("p95", ROOT / "scripts" / "p95.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines: list[str] = []

    def emit(self, record):
        self.lines.append(record.getMessage())


def test_every_response_has_response_time_and_request_id():
    with TestClient(app) as client:
        for path in ["/health", "/api/v1/lessons", "/api/v1/khong-co", "/api/v1/me"]:
            r = client.get(path)
            assert r.headers["X-Response-Time"].endswith("ms"), path
            assert float(r.headers["X-Response-Time"][:-2]) >= 0
            assert len(r.headers["X-Request-ID"]) == 32


def test_request_id_is_echoed_only_when_safe():
    with TestClient(app) as client:
        assert client.get("/health", headers={"X-Request-ID": "abc-123"}).headers["X-Request-ID"] == "abc-123"
        unsafe = client.get("/health", headers={"X-Request-ID": "x\" injected"}).headers["X-Request-ID"]
        assert unsafe != "x\" injected" and len(unsafe) == 32


def test_access_log_is_json_with_route_and_never_contains_secrets():
    capture = _Capture()
    logger = logging.getLogger("harmonymentor.access")
    logger.addHandler(capture)
    secret = "MatKhau" + uuid4().hex[:6] + "9"
    try:
        with TestClient(app) as client:
            email = f"log-{uuid4().hex[:8]}@example.com"
            reg = client.post("/api/v1/auth/register", json={"email": email, "password": secret, "display_name": "Log"})
            token = reg.json()["access_token"]
            client.post("/api/v1/auth/login", json={"email": email, "password": secret})
            client.get("/api/v1/lessons/L01")
            client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    finally:
        logger.removeHandler(capture)
    entries = [json.loads(line) for line in capture.lines]
    lesson = next(e for e in entries if e["path"] == "/api/v1/lessons/L01")
    assert lesson["route"] == "/api/v1/lessons/{lesson_id}" and lesson["status"] == 200
    assert {"ts", "request_id", "method", "duration_ms"} <= set(lesson)
    joined = "\n".join(capture.lines)
    assert secret not in joined and token not in joined and "hm_refresh" not in joined


def test_health_ok_without_redis_and_503_when_a_dependency_fails(monkeypatch):
    with TestClient(app) as client:
        ok = client.get("/health")
        assert ok.status_code == 200
        assert ok.json()["checks"] == {"db": "ok", "redis": "not_configured"}

        monkeypatch.setattr(main_module, "check_redis", lambda url: "error")
        down = client.get("/health")
        assert down.status_code == 503
        assert down.json()["status"] == "degraded" and down.json()["checks"]["redis"] == "error"


def test_cors_only_allows_configured_origins():
    assert parse_origins(" http://a.test/ , ,http://b.test") == ["http://a.test", "http://b.test"]
    assert parse_origins("") == []

    demo = FastAPI()
    install_middleware(demo, "http://localhost:3000")

    @demo.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(demo)
    allowed = client.get("/ping", headers={"Origin": "http://localhost:3000"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert allowed.headers["access-control-allow-credentials"] == "true"
    other = client.get("/ping", headers={"Origin": "http://evil.test"})
    assert "access-control-allow-origin" not in other.headers


def test_p95_script_groups_by_route_and_uses_nearest_rank():
    p95 = _load_p95()
    assert p95.percentile(list(range(1, 21)), 95) == 19
    assert p95.percentile([5.0], 95) == 5.0
    log = "\n".join(
        [f'api-1  | {json.dumps({"method": "GET", "route": "/api/v1/lessons/{lesson_id}", "path": f"/api/v1/lessons/L0{i % 4}", "duration_ms": float(i)})}'
         for i in range(1, 21)]
        + ["INFO:     Uvicorn running", "{không phải json"]
    )
    groups = p95.parse_lines(io.StringIO(log))
    assert list(groups) == ["GET /api/v1/lessons/{lesson_id}"]
    table = p95.render(groups, min_count=1)
    assert "| `GET /api/v1/lessons/{lesson_id}` | 20 | 10.0 | 19.0 | 20.0 |" in table
