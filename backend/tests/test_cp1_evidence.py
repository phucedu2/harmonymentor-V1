"""Test bổ sung cho minh chứng CP1: các hành vi SRS 4.4.1/4.5/4.9 đã chạy đúng nhưng trước đó chưa có test riêng.

Không đổi hành vi Engine; chỉ khóa lại hành vi hiện tại.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.music_engine import interval_between
from app.music_engine.grading import grade_build_chord, grade_build_interval
from app.music_engine.rhythm import grade_taps

client = TestClient(app)
P = "/api/v1/engine"


# SRS 4.4.1: bài hợp âm so lớp cao độ, bỏ qua quãng tám
def test_build_chord_ignores_octave():
    assert grade_build_chord("C", ["E3", "G5", "C2"])["correct"]


# SRS 4.4.1: bài quãng so cao độ chính xác (có quãng tám)
def test_build_interval_wrong_octave():
    assert grade_build_interval("C4", "M3", "E5")["primary_error"] == "WRONG_OCTAVE"


# SRS 4.4.1: A4 và d5 cùng 6 nửa cung nhưng là hai quãng khác nhau
def test_a4_and_d5_same_semitones_different_names():
    a4, d5 = interval_between("C4", "F#4"), interval_between("C4", "Gb4")
    assert (a4.name, d5.name) == ("A4", "d5")
    assert a4.semitones == d5.semitones == 6


# SRS 4.5: EARLY_ONSET; SRS 4.9: dung sai ±80 ms (79 ms đạt, 81 ms không đạt)
def test_tap_early_onset_and_80ms_boundary():
    def codes(taps):
        return [e["code"] for e in grade_taps([0, 1], taps, 120)["events"]]

    assert codes([0.0, 0.5 - 0.09]) == ["OK", "EARLY_ONSET"]
    assert codes([0.079, 0.5 - 0.079]) == ["OK", "OK"]
    assert codes([0.081, 0.5]) == ["LATE_ONSET", "OK"]


# SRS 4.9: API chấm bài (các endpoint chưa có test trong test_api.py)
@pytest.mark.parametrize("path,body,expected", [
    ("build-scale", {"tonic": "D", "answer": ["D", "E", "F#", "G", "A", "B", "C#"]}, True),
    ("build-interval", {"root": "C4", "interval": "M3", "answer": "E4"}, True),
    ("identify-interval", {"lower": "C4", "upper": "F#4", "answer": "d5"}, False),
    ("identify-chord", {"notes": ["A", "C", "E", "G"], "answer": "A-7"}, True),
    ("tap-rhythm", {"expected_beats": [0, 1], "taps_seconds": [0.0, 0.5], "bpm": 120}, True),
])
def test_grade_endpoints(path, body, expected):
    r = client.post(f"{P}/grade/{path}", json=body)
    assert r.status_code == 200 and r.json()["correct"] is expected
