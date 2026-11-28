"""PR 4 hoàn thiện Admin (Phúc 7A, 8A, 24/11/2026): nâng/hạ vai trò qua web, công tắc AI lưu CSDL (ADR-036)."""

from __future__ import annotations

from dataclasses import replace as dc_replace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.api import ai_tutor
from app.admin import router as admin_router
from app.core import ai_switch
from app.db.models import AppSetting
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import auth
from tests.test_admin_quan_tri import make_user

A = "/api/v1/admin"


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
    with SessionLocal() as db:
        db.execute(delete(AppSetting))
        db.commit()
    ai_switch.reset_cache()


def test_doi_vai_tro_qua_web_da_go(client):
    """ADR-036 bổ sung (27/11/2026, Phúc 1A): không còn nâng/hạ Quản trị viên qua web; khóa/mở khóa vẫn dùng được."""
    admin_id = make_user("admin")
    h = auth(admin_id, "admin")
    target = make_user()
    t = auth(target)
    for body in ({"role": "admin"}, {"role": "learner", "is_active": True}):
        assert client.patch(f"{A}/users/{target}", headers=h, json=body).status_code == 400
    assert client.get(f"{A}/stats", headers=t).status_code == 403   # vẫn là người học
    assert not [a for a in client.get(f"{A}/audit", headers=h).json() if a["action"] == "user.role"]
    assert client.patch(f"{A}/users/{admin_id}", headers=h, json={"role": "learner"}).status_code == 400
    assert client.patch(f"{A}/users/{target}", headers=h, json={}).status_code == 400
    r = client.patch(f"{A}/users/{target}", headers=h, json={"is_active": False})
    assert r.status_code == 200 and r.json()["role"] == "learner" and r.json()["is_active"] is False
    learner = auth(make_user())
    assert client.patch(f"{A}/users/{admin_id}", headers=learner, json={"is_active": False}).status_code == 403


def test_cong_tac_ai_tat_thi_khong_tra_provider_va_ghi_nhat_ky(client, monkeypatch):
    h = auth(make_user("admin"), "admin")
    sentinel = object()
    # Giả như .env đã bật AI và có khóa: provider đã nằm trong bộ nhớ đệm.
    fake = dc_replace(ai_tutor.settings, ai_enabled=True, gemini_api_key="x")
    monkeypatch.setattr(ai_tutor, "settings", fake)
    monkeypatch.setattr(admin_router, "settings", fake)
    key = (True, True, fake.gemini_model, fake.gemini_fallback_model)
    monkeypatch.setitem(ai_tutor._provider_cache, key, sentinel)
    dkey = (True, True, admin_router.settings.gemini_model)
    monkeypatch.setitem(admin_router._draft_provider_cache, dkey, sentinel)
    assert ai_tutor.provider_dep() is sentinel and admin_router.draft_provider_dep() is sentinel
    r = client.put(f"{A}/ai/switch", headers=h, json={"on": False})
    assert r.status_code == 200 and r.json() == {"switch_on": False, "env_ready": True}
    assert ai_tutor.provider_dep() is None and admin_router.draft_provider_dep() is None
    with SessionLocal() as db:
        assert db.get(AppSetting, "ai_enabled").value == {"on": False}
    client.put(f"{A}/ai/switch", headers=h, json={"on": True})
    assert ai_tutor.provider_dep() is sentinel
    actions = [a["action"] for a in client.get(f"{A}/audit", headers=h).json()]
    assert "ai.switch.off" in actions and "ai.switch.on" in actions


def test_khong_co_khoa_thi_bat_cong_tac_van_khong_co_ai(client):
    h = auth(make_user("admin"), "admin")
    client.put(f"{A}/ai/switch", headers=h, json={"on": True})
    status = client.get(f"{A}/ai/status", headers=h).json()
    assert status["switch_on"] is True and status["env_ready"] is False and status["enabled"] is False


def test_nguoi_hoc_khong_doi_duoc_cong_tac(client):
    assert client.put(f"{A}/ai/switch", headers=auth(make_user()), json={"on": False}).status_code == 403
