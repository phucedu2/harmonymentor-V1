"""RS-07: hỏi đáp cơ bản khi AI tắt. Nội dung là bản nháp (nguyên tắc 17), mọi nốt/hợp âm được Engine soát lại."""

from __future__ import annotations

import json
from dataclasses import replace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.ai.tutor import faq
from app.ai.tutor.guardrail import scan_reply
from app.api import ai_tutor
from app.core.config import settings
from app.db.models import User
from app.db.session import SessionLocal
from app.main import app
from app.services import ai_tutor_service as ts
from tests.auth_helpers import auth

client = TestClient(app)
DATA = json.loads(faq._PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module", autouse=True)
def _schema_and_seed():
    with TestClient(app):
        yield


@pytest.fixture(autouse=True)
def _no_ai():
    app.dependency_overrides[ai_tutor.embedder_dep] = lambda: None
    app.dependency_overrides[ai_tutor.provider_dep] = lambda: None
    yield
    app.dependency_overrides.pop(ai_tutor.embedder_dep, None)
    app.dependency_overrides.pop(ai_tutor.provider_dep, None)


@pytest.mark.parametrize("item", DATA["muc"], ids=lambda m: m["id"])
def test_noi_dung_dung_nhac_ly_va_co_nguon(item):
    claims = scan_reply(item["tra_loi"])
    assert all(c.status == "verified" for c in claims), [c for c in claims if c.status != "verified"]
    assert item["nguon"] and item["bai"].startswith("L")
    assert item["status"] in ("draft", "approved")


@pytest.mark.parametrize("q, fid", [("hợp âm là gì vậy bạn?", "FAQ-01"), ("hop am la gi", "FAQ-01"),
                                    ("C la not gi vay", "FAQ-02"), ("nua cung la gi a", "FAQ-03"),
                                    ("cho mình hỏi quãng là gì", "FAQ-05")])
def test_khop_ca_co_dau_va_khong_dau(q, fid):
    assert faq.match(q, show_draft=True).id == fid


@pytest.mark.parametrize("q", ["hợp âm mượn là gì", "hợp âm C gồm nốt nào", "quãng 3 trưởng là gì"])
def test_khong_khop_cau_cu_the_hon(q):
    assert faq.match(q, show_draft=True) is None


def test_ban_nhap_an_khi_tat_show_draft():
    assert faq.match("hop am la gi", show_draft=False) is None


def _ask(q):
    uid = "rs07-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="RS-07", email=f"{uid}@example.test"))
        db.commit()
    r = client.post("/api/v1/chat/message", json={"message": q}, headers=auth(uid))
    assert r.status_code == 200, r.text
    return r.json()


def test_ai_tat_tra_loi_tu_kho_hoi_dap(monkeypatch):
    monkeypatch.setattr(ts, "settings", replace(settings, show_draft_content=True))
    j = _ask("hop am la gi")
    assert j["source_label"] == "Hỏi đáp cơ bản" and "C E G" in j["reply"]
    assert j["suggested_lesson"]["lesson_id"] == "L01"
    assert j["verified"] is False  # không gắn "Engine xác nhận" cho câu không gọi công cụ


def test_tat_show_draft_giu_cau_du_phong_cu(monkeypatch):
    monkeypatch.setattr(ts, "settings", replace(settings, show_draft_content=False))
    j = _ask("hop am la gi")
    assert j["source_label"] != "Hỏi đáp cơ bản"
