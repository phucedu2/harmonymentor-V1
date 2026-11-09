"""GĐ5 (09/11/2026): liên kết học thêm bên ngoài theo bài.

Khẳng định: chỉ tài liệu miễn phí của nguồn mở đã ghi trong source_registry; mục nháp ẩn với người học cho tới
khi Đạt duyệt; bật SHOW_DRAFT_CONTENT thì hiện kèm dấu nháp; API bài học trả đúng danh sách.
"""

from __future__ import annotations

from dataclasses import replace
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient

from app.content import external_resources as er
from app.content import versioning
from app.core.config import settings
from app.main import app

client = TestClient(app)


def draft(monkeypatch, on: bool) -> None:
    # Settings là dataclass đóng băng: thay cả đối tượng mà versioning đang dùng.
    monkeypatch.setattr(versioning, "settings", replace(settings, show_draft_content=on))


ALLOWED_HOSTS = {"viva.pressbooks.pub", "musictheory.pugetsound.edu"}


@pytest.fixture(autouse=True, scope="module")
def _schema():
    with TestClient(app):
        yield


def test_moi_bai_l01_l05_co_it_nhat_hai_lien_ket_mien_phi_tu_nguon_mo():
    for lesson_id in ("L01", "L02", "L03", "L04", "L05"):
        items = er.EXTERNAL_RESOURCES[lesson_id]
        assert len(items) >= 2
        for item in items:
            url = urlparse(item["url"])
            assert url.scheme == "https" and url.hostname in ALLOWED_HOSTS, item["url"]
            assert item["free"] is True and item["why_vi"]


def test_muc_nhap_an_voi_nguoi_hoc(monkeypatch):
    draft(monkeypatch, False)
    assert er.resources_for("L01") == []
    assert er.resources_for("L99") == []


def test_bat_xem_nhap_thi_hien_kem_dau_nhap(monkeypatch):
    draft(monkeypatch, True)
    items = er.resources_for("L05")
    assert items and all(item["draft"] is True and "status" not in item for item in items)


def test_api_bai_hoc_tra_lien_ket(monkeypatch):
    draft(monkeypatch, True)
    body = client.get("/api/v1/lessons/L01").json()
    assert [r["url"] for r in body["external_resources"]] == [r["url"] for r in er.EXTERNAL_RESOURCES["L01"]]
    draft(monkeypatch, False)
    assert client.get("/api/v1/lessons/L01").json()["external_resources"] == []
