"""G1 (T4): ví dụ hợp âm trong bài phải đổi theo giọng, không cố định C/Cmaj7.

Nguồn sự thật là Music Engine: số La Mã + giọng -> ký hiệu hợp âm, frontend không tự tính."""

import pytest
from fastapi.testclient import TestClient

from app.content.curriculum_specs import LESSON_SPECS
from app.content.draft_specs import DRAFT_LESSON_SPECS, blocks_with_drafts
from app.content.progression import KEYS, resolve_progression
from app.main import app

client = TestClient(app)
URL = "/api/v1/music/progression"


@pytest.mark.parametrize("key, numerals, expected", [
    ("C", "Imaj7,ii7,V7,Imaj7", ["Cmaj7", "Dm7", "G7", "Cmaj7"]),
    ("G", "Imaj7,ii7,V7,Imaj7", ["Gmaj7", "Am7", "D7", "Gmaj7"]),
    ("F", "ii7,V7,Imaj7", ["Gm7", "C7", "Fmaj7"]),
    ("Eb", "I,V,vi,IV", ["Eb", "Bb", "Cm", "Ab"]),
    ("C", "I,V7/ii,ii7,V7,I", ["C", "A7", "Dm7", "G7", "C"]),
    ("D", "I,V7/ii,ii7,V7,I", ["D", "B7", "Em7", "A7", "D"]),
    ("C", "I,IV,iv,I", ["C", "F", "Fm", "C"]),
    ("A", "I,IV,iv,I", ["A", "D", "Dm", "A"]),
])
def test_endpoint_resolves_by_engine(key, numerals, expected):
    r = client.get(URL, params={"key": key, "numerals": numerals})
    assert r.status_code == 200, r.text
    assert r.json()["symbols"] == expected


def test_bad_input_is_422_not_silent_c():
    assert client.get(URL, params={"key": "H", "numerals": "I"}).status_code == 422
    assert client.get(URL, params={"key": "C", "numerals": "I,XX"}).status_code == 422
    assert client.get(URL, params={"key": "C", "numerals": ""}).status_code == 422


def _example_blocks():
    for spec in LESSON_SPECS + DRAFT_LESSON_SPECS:
        for bid, btype, payload in blocks_with_drafts(spec):
            symbols = payload.get("progression") if btype == "audio" else payload.get("chords") if btype == "audio" else None
            if btype in ("audio", "progression") and (payload.get("progression") or payload.get("chords") or btype == "progression"):
                yield bid, btype, payload


def test_every_chord_example_declares_numerals_and_matches_default_key():
    """Mỗi khối ví dụ hợp âm có `numerals`; ở giọng mặc định phải ra đúng ký hiệu đang hiển thị (không đổi nội dung cũ)."""
    blocks = list(_example_blocks())
    assert len(blocks) >= 12
    for bid, btype, payload in blocks:
        assert payload.get("numerals"), f"{bid} thiếu numerals"
        key = payload.get("key", "C")
        shown = payload.get("progression") or payload.get("chords")
        if btype == "progression":
            shown = [p.strip() for p in payload["prompt"].split("=")[0].split("→")]
        assert resolve_progression(key, payload["numerals"]) == shown, bid


def test_all_example_blocks_work_in_all_12_keys_and_differ_from_c():
    blocks = list(_example_blocks())
    for bid, _, payload in blocks:
        in_c = resolve_progression("C", payload["numerals"])
        for key in KEYS:
            out = resolve_progression(key, payload["numerals"])
            assert len(out) == len(in_c)
            if key != "C":
                assert out != in_c, f"{bid} vẫn ra giống C ở giọng {key}"
