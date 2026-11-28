"""phuc-music Bước 2: phần khám phá Bài 1 lấy quãng/hợp âm từ API Music Engine, không tự tính ở frontend.

So API với bảng vàng của HM-001 (frontend/tests/fixtures/l01_engine_scientific.json, sinh từ Engine),
nên đổi từ tính ở frontend sang gọi API không làm sai một nốt nào trong 17 cách viết nốt gốc.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = json.loads((ROOT / "frontend" / "tests" / "fixtures" / "l01_engine_scientific.json").read_text(encoding="utf-8"))
client = TestClient(app)


def _get(root: str) -> dict:
    res = client.get(f"/api/v1/music/lesson1/{root.replace('#', '%23')}")
    assert res.status_code == 200, res.text
    return res.json()


@pytest.mark.parametrize("root", GOLDEN["roots"])
def test_quang_va_hop_am_khop_bang_vang(root):
    data = _get(root)
    got_intervals = {i["code"]: i["pitches"] for i in data["intervals"]}
    for row in (r for r in GOLDEN["intervals"] if r["root"] == root):
        assert got_intervals[row["code"]] == row["notes"]
    got_triads = {t["quality"]: t["pitches"] for t in data["triads"]}
    for row in (r for r in GOLDEN["triads"] if r["root"] == root):
        assert got_triads[row["quality"]] == row["notes"]


@pytest.mark.parametrize(("root", "code", "upper", "midi"), [
    ("G#", "M3", "B#4", 72), ("E", "A5", "B#4", 72), ("Ab", "m3", "Cb5", 71), ("F", "d5", "Cb5", 71),
])
def test_ca_bien_hm001(root, code, upper, midi):
    interval = next(i for i in _get(root)["intervals"] if i["code"] == code)
    assert interval["pitches"][1] == {"name": upper, "midi": midi}


def test_thong_tin_hien_thi_lay_tu_engine():
    data = _get("F")
    assert data["letter_frame"] == ["F", "A", "C"]
    dim = next(t for t in data["triads"] if t["quality"] == "diminished")
    assert dim["symbol"] == "Fdim"
    assert dim["notes"] == ["F", "Ab", "Cb"]
    assert dim["formula"] == ["1", "b3", "b5"]
    assert dim["interval_formula"] == ["m3", "d5"]
    semis = {i["code"]: i["semitones"] for i in data["intervals"]}
    assert semis == {"M3": 4, "m3": 3, "P5": 7, "d5": 6, "A5": 8}


@pytest.mark.parametrize("bad", ["H", "C4", "Xb"])
def test_not_goc_sai_tra_loi_engine(bad):
    res = client.get(f"/api/v1/music/lesson1/{bad}")
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "INVALID_PITCH"
