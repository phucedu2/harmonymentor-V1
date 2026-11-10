"""Mở khóa L05–L08 (10/11/2026): lý thuyết hiện cho người học; câu hỏi ở dạng nháp chờ Đạt duyệt; chưa nạp thẻ ôn.

Khẳng định: bài không còn "trống" (có khối lý thuyết), người học không thấy câu nháp và khối checkpoint trỏ tới câu
nháp, chưa hoàn thành được bài khi chưa có câu; bật SHOW_DRAFT_CONTENT thì thấy đủ 6 câu mỗi bài để duyệt.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app.content import versioning
from app.content.curriculum_specs import MIGRATED_LESSON_IDS, PENDING_REVIEW_LESSON_IDS
from app.main import app
from tests.auth_helpers import auth

PENDING = sorted(PENDING_REVIEW_LESSON_IDS)


@pytest.fixture()
def drafts_on(monkeypatch):
    monkeypatch.setattr(versioning, "settings", replace(versioning.settings, show_draft_content=True))


def test_danh_sach_cho_duyet_tach_khoi_bai_da_phat_hanh():
    assert PENDING == ["L05", "L06", "L07", "L08"]
    assert not PENDING_REVIEW_LESSON_IDS & MIGRATED_LESSON_IDS


@pytest.mark.parametrize("lesson_id", PENDING)
def test_nguoi_hoc_thay_ly_thuyet_nhung_chua_thay_cau_nhap(lesson_id):
    with TestClient(app) as client:
        summary = next(x for x in client.get("/api/v1/lessons").json() if x["id"] == lesson_id)
        assert summary["block_count"] > 0          # hết "Sắp có"
        assert summary["exercise_count"] == 0       # câu chưa duyệt không lộ ra
        assert summary["review_item_count"] == 0    # thẻ ôn chưa nạp
        detail = client.get(f"/api/v1/lessons/{lesson_id}").json()
        assert detail["exercises"] == []
        assert all(b["block_type"] != "checkpoint" for b in detail["blocks"])
        done = client.post(f"/api/v1/lessons/{lesson_id}/complete", headers=auth("demo-user"))
        assert done.status_code == 409 and done.json()["error"]["code"] == "LESSON_HAS_NO_EXERCISES"


@pytest.mark.parametrize("lesson_id", PENDING)
def test_che_do_nhap_thay_du_cau_de_duyet(lesson_id, drafts_on):
    with TestClient(app) as client:
        detail = client.get(f"/api/v1/lessons/{lesson_id}").json()
        assert len(detail["exercises"]) == 6
        ids = {e["id"] for e in detail["exercises"]}
        checkpoints = [b for b in detail["blocks"] if b["block_type"] == "checkpoint"]
        assert all(b["payload"]["exercise_id"] in ids for b in checkpoints)


def test_bai_da_phat_hanh_khong_doi():
    with TestClient(app) as client:
        lessons = {x["id"]: x for x in client.get("/api/v1/lessons").json()}
        assert [lessons[x]["exercise_count"] for x in ("L01", "L02", "L03", "L04")] == [8, 10, 6, 6]
        assert all(lessons[x]["review_item_count"] == 8 for x in ("L01", "L02", "L03", "L04"))
