"""ADR-031: nhận diện nốt từ micro. Trình duyệt đo tần số, Music Engine đặt tên nốt và chấm.

Khẳng định: công thức Hz → MIDI đúng ở các nốt mốc, cent lệch đúng dấu, từ chối tần số ngoài phím piano,
và lượt "micro" ở Luyện tập chấm theo lớp cao độ giống bấm phím, ghi riêng trong lịch sử.
"""

from __future__ import annotations

import math
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.models import User
from app.db.session import SessionLocal
from app.main import app
from app.music_engine import note_from_frequency
from app.music_engine.errors import InvalidPitch
from tests.auth_helpers import auth

client = TestClient(app)


def hz_of(midi: int, cents: float = 0.0) -> float:
    return 440.0 * 2 ** ((midi - 69 + cents / 100) / 12)


@pytest.mark.parametrize(("hz", "note", "midi"), [
    (440.0, "A4", 69), (261.63, "C4", 60), (329.63, "E4", 64), (82.41, "E2", 40),  # dây Mi trầm guitar
    (27.5, "A0", 21), (4186.01, "C8", 108), (466.16, "A#4", 70),
])
def test_not_moc(hz, note, midi):
    r = note_from_frequency(hz)
    assert (str(r.note), r.midi) == (note, midi)
    assert abs(r.cents) < 1


def test_cent_lech_dung_dau_va_lam_tron_ve_not_gan_nhat():
    assert note_from_frequency(hz_of(64, 30)).cents == pytest.approx(30, abs=0.1)
    assert note_from_frequency(hz_of(64, -30)).cents == pytest.approx(-30, abs=0.1)
    # Lệch quá nửa cung thì sang nốt bên cạnh: E4 + 60 cent gần F4 hơn (F4 - 40 cent).
    r = note_from_frequency(hz_of(64, 60))
    assert (str(r.note), r.cents) == ("F4", pytest.approx(-40, abs=0.1))


def test_ten_giang_khi_yeu_cau_va_chuan_a4_khac():
    assert str(note_from_frequency(466.16, prefer="flat").note) == "Bb4"
    # Dàn nhạc chỉnh A4 = 442 Hz: 442 Hz vẫn là A4 lệch 0 cent.
    assert note_from_frequency(442.0, a4_hz=442.0).cents == 0


@pytest.mark.parametrize("bad", [0, -5, 20.0, 5000.0, math.nan, math.inf])
def test_tu_choi_tan_so_ngoai_dai(bad):
    with pytest.raises(InvalidPitch):
        note_from_frequency(bad)


def test_api_doi_tan_so():
    ok = client.get("/api/v1/engine/note-from-frequency", params={"hz": 329.63})
    assert ok.status_code == 200 and ok.json()["note"] == "E4" and ok.json()["midi"] == 64
    bad = client.get("/api/v1/engine/note-from-frequency", params={"hz": 10})
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "INVALID_PITCH"


@pytest.fixture(scope="module")
def _schema():
    with TestClient(app):
        yield


def make_user() -> str:
    uid = "mic-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="Đàn thử", role="learner"))
        db.commit()
    return uid


def practice(uid: str, kind: str, question: dict, answer, input_mode: str):
    return client.post("/api/v1/practice/attempts", headers=auth(uid),
                       json={"kind": kind, "level": "de", "question": question, "answer": answer, "input": input_mode})


def test_luot_micro_cham_theo_cao_do_va_ghi_rieng(_schema):
    uid = make_user()
    # Micro trả tên thăng (D#4) cho nốt Eb của Cm: đúng cao độ, máy nhắc cách viết chuẩn.
    ok = practice(uid, "chord", {"symbol": "Cm"}, ["C4", "D#4", "G4"], "micro")
    assert ok.status_code == 200 and ok.json()["correct"] is True
    assert ok.json()["message_vi"].startswith("Đúng cao độ") and "C Eb G" in ok.json()["message_vi"]
    bad = practice(uid, "chord", {"symbol": "Cm"}, ["C4", "E4", "G4"], "micro")
    assert bad.json()["correct"] is False
    items = client.get("/api/v1/practice/history", headers=auth(uid)).json()["items"]
    assert all(item["question"].get("input") == "micro" for item in items)


def test_micro_khong_dung_cho_quang(_schema):
    uid = make_user()
    r = practice(uid, "interval", {"lower": "C4", "upper": "E4"}, ["E4"], "micro")
    assert r.status_code == 422 and r.json()["error"]["code"] == "PRACTICE_INPUT_INVALID"
