"""GĐ5 (09/11/2026): trả lời Luyện tập bằng cách bấm piano ảo.

Phím đen có hai tên (C#/Db) nên bấm phím không thể hiện cách viết: máy chủ chấm lớp cao độ bằng Music Engine
(pitch_class_only), nhắc cách viết chuẩn, và ghi "input": "piano" vào lịch sử. Gõ chữ vẫn chấm chính tả như cũ.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.models import User
from app.db.session import SessionLocal
from app.main import app
from app.services.practice_service import PracticeInputInvalid, grade_practice
from tests.auth_helpers import auth

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def _schema():
    with TestClient(app):
        yield


def make_user() -> str:
    user_id = "gd5-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=user_id, display_name="Bấm piano", role="learner"))
        db.commit()
    return user_id


def test_piano_cham_theo_lop_cao_do_va_nhac_cach_viet():
    res = grade_practice("chord", {"symbol": "Ebm7b5"}, ["D#4", "F#4", "A4", "C#5"], "piano")
    assert res["correct"] is True
    assert res["expected"] == ["Eb", "Gb", "Bbb", "Db"]  # Engine vẫn trả cách viết chuẩn
    assert "Eb Gb Bbb Db" in res["message_vi"]


def test_go_chu_van_cham_chinh_ta():
    assert grade_practice("chord", {"symbol": "Ebm7b5"}, ["D#", "F#", "A", "C#"])["correct"] is False


def test_piano_sai_phim_van_sai():
    assert grade_practice("chord", {"symbol": "C"}, ["C4", "E4", "G4", "B4"], "piano")["correct"] is False
    assert grade_practice("chord", {"symbol": "Am"}, ["A3", "C#4", "E4"], "piano")["correct"] is False


def test_am_giai_bam_piano_can_dung_thu_tu():
    ok = ["F4", "G4", "A4", "A#4", "C5", "D5", "E5"]
    assert grade_practice("scale", {"tonic": "F", "scale_type": "major"}, ok, "piano")["correct"] is True
    swapped = ["F4", "G4", "A4", "C5", "A#4", "D5", "E5"]
    assert grade_practice("scale", {"tonic": "F", "scale_type": "major"}, swapped, "piano")["correct"] is False


def test_quang_va_so_la_ma_khong_nhan_piano():
    with pytest.raises(PracticeInputInvalid):
        grade_practice("interval", {"lower": "C", "upper": "E"}, "M3", "piano")


def test_api_ghi_input_piano_vao_lich_su():
    uid = make_user()
    h = auth(uid, "learner")
    res = client.post("/api/v1/practice/attempts", headers=h, json={
        "kind": "chord", "level": "de", "question": {"symbol": "D"}, "answer": ["D4", "F#4", "A4"], "input": "piano"})
    assert res.status_code == 200, res.text
    assert res.json()["correct"] is True
    hist = client.get("/api/v1/practice/history", headers=h).json()
    assert hist["items"][0]["question"] == {"symbol": "D", "input": "piano"}
    bad = client.post("/api/v1/practice/attempts", headers=h, json={
        "kind": "roman", "level": "de", "question": {"key": "C", "chord": "G"}, "answer": "V", "input": "piano"})
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "PRACTICE_INPUT_INVALID"
