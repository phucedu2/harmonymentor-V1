"""GĐ3 góp ý thầy G2: nháp lý thuyết L06, L07, L08, Claude soạn 08/11/2026, chờ Đạt/Astra duyệt.

Mọi nốt và quãng ghi trong bài phải khớp Music Engine (nguyên tắc 1). Hợp âm mở rộng (9, 13) và mixolydian chưa có
trong Engine nên tension kiểm bằng quãng, mode kiểm bằng cách xoay major scale."""

from __future__ import annotations

import re

import pytest

from app.ai.tutor.chunker import lesson_chunks
from app.ai.tutor.guardrail import run_tool
from app.content.curriculum_specs import LESSON_SPECS
from app.content.draft_l06_l08 import DRAFT, L06_DRAFT_BLOCKS, L07_DRAFT_BLOCKS, L08_DRAFT_BLOCKS
from app.content.draft_specs import blocks_with_drafts
from app.content.versioning import block_visible

LESSONS = {"L06": L06_DRAFT_BLOCKS, "L07": L07_DRAFT_BLOCKS, "L08": L08_DRAFT_BLOCKS}


def spec(lesson):
    return next(s for s in LESSON_SPECS if s["id"] == lesson)


def tones(symbol):
    value, raw = run_tool("get_chord_tones", {"symbol": symbol})
    assert value is not None, raw
    return value.split()


def scale(tonic, kind):
    value, raw = run_tool("get_scale", {"tonic": tonic, "scale_type": kind})
    assert value is not None, raw
    return value.split()


def interval(lower, upper):
    value, raw = run_tool("identify_interval", {"lower": lower, "upper": upper})
    assert value is not None, raw
    return value


def text(lesson):
    return " ".join(str(p) for _, _, p in LESSONS[lesson])


@pytest.mark.parametrize("lesson, blocks", LESSONS.items())
def test_blocks_are_draft_hidden_and_not_in_tutor_kb(lesson, blocks):
    assert spec(lesson)["blocks"] == []
    ids = [b[0] for b in blocks_with_drafts(spec(lesson))]
    assert len(ids) == len(set(ids)) and all(i.startswith(f"{lesson}-") for i in ids)
    assert all(p.get("status") == DRAFT and not block_visible(p) for _, _, p in blocks)
    assert not [c for c in lesson_chunks() if c.lesson_id == lesson]


@pytest.mark.parametrize("lesson, blocks", LESSONS.items())
def test_checkpoints_point_to_existing_exercises(lesson, blocks):
    ex = {e["id"] for e in spec(lesson)["exercises"]}
    cps = [p["exercise_id"] for _, t, p in blocks if t == "checkpoint"]
    assert cps and set(cps) <= ex


# ───────── L06: hợp âm mượn ─────────
def test_l06_parallel_minor_notes():
    assert "C–D–Eb–F–G–Ab–Bb" in text("L06")
    assert scale("C", "natural_minor") == "C D Eb F G Ab Bb".split()


@pytest.mark.parametrize("symbol, root_interval", [("Fm", None), ("Ab", "m6"), ("Bb", "m7")])
def test_l06_borrowed_chords_come_from_c_minor_and_have_non_key_notes(symbol, root_interval):
    m = re.search(rf"= {symbol} \(([^)]*)\)", text("L06"))
    assert m and m[1].split("–") == tones(symbol)
    minor, major = set(scale("C", "natural_minor")), set(scale("C", "major"))
    assert set(tones(symbol)) <= minor            # mượn đúng từ C minor
    assert set(tones(symbol)) - major             # có nốt ngoài C major
    if root_interval:
        assert interval("C", symbol) == root_interval


def test_l06_fm_differs_from_f_by_one_note():
    assert [n for n in tones("Fm") if n not in tones("F")] == ["Ab"]
    assert [n for n in tones("F") if n not in tones("Fm")] == ["A"]


def test_l06_example_progression():
    assert next(p for b, _, p in L06_DRAFT_BLOCKS if b == "L06-B06")["progression"] == ["C", "F", "Fm", "C"]


# ───────── L07: tension và chord-scale ─────────
@pytest.mark.parametrize("chord, nine, eleven, thirteen", [
    ("Dm7", "E", "G", "B"), ("G7", "A", "C", "E"), ("Cmaj7", "D", "F", "A")])
def test_l07_tensions_by_interval(chord, nine, eleven, thirteen):
    root = tones(chord)[0]
    assert (interval(root, nine), interval(root, eleven), interval(root, thirteen)) == ("M2", "P4", "M6")
    assert f"{chord} (" in text("L07") and f"9 = {nine}, 11 = {eleven}, 13 = {thirteen}" in text("L07")


def test_l07_chord_tones_listed_match_engine():
    for chord in ("Dm7", "G7", "Cmaj7"):
        m = re.search(rf"{chord} \(([A-G][#b]?(?:–[A-G][#b]?)+)\)", text("L07"))
        assert m and m[1].split("–") == tones(chord)


def test_l07_modes_are_rotations_of_c_major():
    c_major = scale("C", "major")
    rot = lambda k: c_major[k:] + c_major[:k]       # noqa: E731
    assert scale("D", "dorian") == rot(1)           # D Dorian, Engine tính
    for name, k in (("D Dorian", 1), ("G Mixolydian", 4), ("C Ionian", 0)):
        assert f"{name}: {'–'.join(rot(k))}" in text("L07") or name == "C Ionian"
    assert "C Ionian (chính là C major): C–D–E–F–G–A–B" in text("L07")


def test_l07_eleven_clash_claim_is_a_half_step():
    assert interval("B", "C") == "m2"            # 11 của G7 (C) cách quãng 3 (B) nửa cung


# ───────── L08: shell voicing ─────────
@pytest.mark.parametrize("chord", ["Dm7", "G7", "Cmaj7"])
def test_l08_shell_is_root_third_seventh(chord):
    t = tones(chord)
    shell = f"{t[0]}–{t[1]}–{t[3]}"
    assert f"{chord}: {shell}" in text("L08") or f"{chord} = {shell}" in text("L08")


def test_l08_guide_tone_connections():
    dm7, g7, cmaj7 = tones("Dm7"), tones("G7"), tones("Cmaj7")
    assert dm7[1] == g7[3] == "F"                 # quãng 3 của Dm7 giữ, thành quãng 7 của G7
    assert (dm7[3], g7[1]) == ("C", "B") and interval("B", "C") == "m2"
    assert g7[1] == cmaj7[3] == "B"               # quãng 3 của G7 giữ, thành quãng 7 của Cmaj7
    assert (g7[3], cmaj7[1]) == ("F", "E") and interval("E", "F") == "m2"
