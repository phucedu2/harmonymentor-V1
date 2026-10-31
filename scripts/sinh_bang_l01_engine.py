"""Sinh bảng đáp án scientific pitch + MIDI cho phần khám phá L01 từ Music Engine (HM-001).

Vì sao cần: frontend L01 tự dựng quãng/hợp âm để vẽ khuông và phát âm thanh ngay, không chờ API.
Bảng này để test frontend so với Music Engine (nguồn sự thật duy nhất) ở mọi nốt gốc L01 hỗ trợ.

Chạy lại sau khi đổi Engine hoặc danh sách nốt gốc:
    python scripts/sinh_bang_l01_engine.py
`backend/tests/test_hm001_l01_engine_golden.py` báo đỏ nếu file JSON đã cũ.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.music_engine.interval import transpose  # noqa: E402
from app.music_engine.pitch import parse_note  # noqa: E402

LESSONS_TS = ROOT / "frontend" / "src" / "content" / "lessons.ts"
OUTPUT = ROOT / "frontend" / "tests" / "fixtures" / "l01_engine_scientific.json"

ROOT_OCTAVE = 4
# Khớp INTERVALS/TRIADS trong frontend/src/theory/lesson1Theory.ts.
INTERVAL_CODES = ["M3", "m3", "P5", "d5", "A5"]
TRIADS = {
    "major": ("M3", "P5"),
    "minor": ("m3", "P5"),
    "diminished": ("m3", "d5"),
    "augmented": ("M3", "A5"),
}
# Ca biên của ticket HM-001: dấu hóa vượt qua ranh giới B/C và dấu hóa kép.
MIDI_CASES = ["C4", "E4", "D4", "F4", "G4", "D5", "B#3", "B#4", "Cb4", "Cb5", "B##4", "Cbb5", "E#4", "Fb4"]


def root_spellings() -> list[str]:
    """Đọc mọi cách viết nốt gốc mà RootKeySelector cho chọn, để bảng không bỏ sót nốt nào."""
    text = LESSONS_TS.read_text(encoding="utf-8")
    block = text.split("export const ROOT_KEY_OPTIONS", 1)[1].split("];", 1)[0]
    spellings: list[str] = []
    for group in re.findall(r"spellings:\s*\[([^\]]*)\]", block):
        spellings.extend(re.findall(r'"([^"]+)"', group))
    if not spellings:
        raise RuntimeError("Không đọc được ROOT_KEY_OPTIONS trong lessons.ts")
    return spellings


def scientific(note) -> dict:
    return {"name": str(note), "midi": note.midi}


def build_table() -> dict:
    roots = root_spellings()
    intervals = []
    triads = []
    for root in roots:
        base = parse_note(f"{root}{ROOT_OCTAVE}")
        for code in INTERVAL_CODES:
            upper = transpose(base, code)
            intervals.append({"root": root, "code": code, "notes": [scientific(base), scientific(upper)]})
        for quality, (third, fifth) in TRIADS.items():
            notes = [base, transpose(base, third), transpose(base, fifth)]
            triads.append({"root": root, "quality": quality, "notes": [scientific(n) for n in notes]})
    return {
        "_nguon": "Sinh bởi scripts/sinh_bang_l01_engine.py từ backend/app/music_engine; không sửa tay.",
        "root_octave": ROOT_OCTAVE,
        "roots": roots,
        "intervals": intervals,
        "triads": triads,
        "midi": [{"name": name, "midi": parse_note(name).midi} for name in MIDI_CASES],
    }


def render() -> str:
    return json.dumps(build_table(), ensure_ascii=False, indent=2) + "\n"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(), encoding="utf-8")
    table = build_table()
    print(f"Đã ghi {OUTPUT.relative_to(ROOT)}: {len(table['roots'])} nốt gốc, "
          f"{len(table['intervals'])} quãng, {len(table['triads'])} hợp âm, {len(table['midi'])} ca MIDI")


if __name__ == "__main__":
    main()
