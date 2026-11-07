"""GĐ3 góp ý thầy G2: nháp lý thuyết L05 (Secondary Dominants), Claude soạn 07/11/2026.

Mọi hợp âm và nốt ghi trong nháp phải khớp Music Engine (nguyên tắc 1). Nháp không được lộ ra người học hay vào kho
AI Tutor trước khi Astra/Đạt duyệt."""

from __future__ import annotations

import re

import pytest

from app.ai.tutor.chunker import lesson_chunks
from app.ai.tutor.guardrail import run_tool
from app.ai.tutor.router import later_lesson
from app.content.curriculum_specs import LESSON_SPECS
from app.content.draft_specs import DRAFT, L05_DRAFT_BLOCKS, blocks_with_drafts

SPEC = next(s for s in LESSON_SPECS if s["id"] == "L05")
TEXT = " ".join(str(p) for _, _, p in L05_DRAFT_BLOCKS)
# Bậc → hợp âm bảy thuận giọng của C major (đích), lấy từ Engine trong test, không ghi tay.
TARGETS = {"ii": "D", "iii": "E", "IV": "F", "V": "G", "vi": "A"}


def tones(symbol: str) -> list[str]:
    value, raw = run_tool("get_chord_tones", {"symbol": symbol})
    assert value is not None, raw
    return value.split()


def test_all_l05_blocks_are_draft_and_ids_unique():
    assert SPEC["blocks"] == []      # chưa có bản phát hành: dùng nháp
    ids = [b[0] for b in blocks_with_drafts(SPEC)]
    assert len(ids) == len(set(ids)) and all(i.startswith("L05-") for i in ids)
    assert all(p.get("status") == DRAFT for _, _, p in L05_DRAFT_BLOCKS)


def test_draft_not_in_tutor_knowledge_base_and_later_lesson_rule_still_on():
    assert not any(c.lesson_id == "L05" for c in lesson_chunks())
    assert later_lesson("át phụ là gì") == "L05"


def test_checkpoints_point_to_existing_l05_exercises():
    ex = {e["id"] for e in SPEC["exercises"]}
    cps = [p["exercise_id"] for _, t, p in L05_DRAFT_BLOCKS if t == "checkpoint"]
    assert cps and set(cps) <= ex


@pytest.mark.parametrize("numeral, target_root", TARGETS.items())
def test_secondary_dominant_table_matches_engine(numeral, target_root):
    """Dòng "V7/x = R7 (n1–n2–n3–n4)": root cách root chord đích quãng 5 đúng, các nốt đúng như Engine tính."""
    m = re.search(rf"V7/{numeral} = ([A-G][#b]?7) \(([^)]*)\)", TEXT)
    assert m, numeral
    symbol, notes = m[1], m[2].split("–")
    value, raw = run_tool("identify_interval", {"lower": target_root, "upper": symbol[:-1]})
    assert value == "P5", raw
    assert notes == tones(symbol)


@pytest.mark.parametrize("symbol", sorted(set(re.findall(r"\b([A-G][#b]?(?:maj7|m7|7))\s*=\s*[A-G]", TEXT))))
def test_every_spelled_chord_matches_engine(symbol):
    m = re.search(rf"\b{re.escape(symbol)}\s*=\s*([A-G][#b]?(?:–[A-G][#b]?)+)", TEXT)
    assert m and m[1].split("–") == tones(symbol)


def test_non_key_notes_claims_match_engine():
    """"Nốt ngoài key" ghi cho mỗi át phụ đúng bằng các nốt của hợp âm không thuộc âm giai C major."""
    value, _ = run_tool("get_scale", {"tonic": "C", "scale_type": "major"})
    scale = set(value.split())
    for line in next(p["items"] for b, _, p in L05_DRAFT_BLOCKS if b == "L05-B05")[:5]:
        symbol = re.search(r"= ([A-G][#b]?7)", line)[1]
        outside = [n for n in tones(symbol) if n not in scale]
        claimed = re.findall(r"\b([A-G][#b])(?![A-Za-z0-9#])", line.split("Nốt ngoài key:")[1])
        assert sorted(claimed) == sorted(outside), line


def test_example_progression_is_i_v7ii_ii_v_i_in_c():
    prog = next(p for b, _, p in L05_DRAFT_BLOCKS if b == "L05-B07")["progression"]
    assert prog == ["Cmaj7", "A7", "Dm7", "G7", "Cmaj7"]
    for chord, numeral in (("Dm7", "ii7"), ("G7", "V7"), ("Cmaj7", "IM7")):
        value, raw = run_tool("get_roman_numeral", {"key": "C", "chord": chord})
        assert value == numeral, raw
