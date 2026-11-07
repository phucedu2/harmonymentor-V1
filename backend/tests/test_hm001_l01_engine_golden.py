"""HM-001: bảng đáp án L01 cho frontend phải trùng với Music Engine hiện tại.

Frontend test (frontend/tests/lesson1Scientific.test.ts) so code TypeScript với bảng JSON;
test này giữ bảng JSON không bị cũ so với Engine, nên hai phía luôn cùng một nguồn sự thật.
"""

import importlib.util
import json
from pathlib import Path

import pytest

from app.music_engine.interval import transpose
from app.music_engine.pitch import parse_note

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "sinh_bang_l01_engine.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("sinh_bang_l01_engine", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bang_l01_trong_frontend_khop_engine():
    gen = _load_generator()
    on_disk = gen.OUTPUT.read_text(encoding="utf-8")
    assert on_disk == gen.render(), "Bảng đã cũ: chạy python scripts/sinh_bang_l01_engine.py"
    data = json.loads(on_disk)
    # 12 vị trí cao độ, 17 cách viết; mỗi nốt gốc 5 quãng + 4 hợp âm.
    assert len(data["roots"]) == 17
    assert len(data["intervals"]) == 17 * 5
    assert len(data["triads"]) == 17 * 4


@pytest.mark.parametrize(
    ("root", "code", "upper", "midi"),
    [("G#4", "M3", "B#4", 72), ("E4", "A5", "B#4", 72), ("Ab4", "m3", "Cb5", 71), ("F4", "d5", "Cb5", 71)],
)
def test_engine_dung_cac_ca_ticket(root, code, upper, midi):
    note = transpose(parse_note(root), code)
    assert str(note) == upper
    assert note.midi == midi
