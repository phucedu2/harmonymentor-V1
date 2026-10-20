"""Phase 2: beginner-safe lesson exposition and interactive music block contracts."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.content.curriculum_specs import lesson_by_id
from app.main import app
from app.services.grading_service import grade_payload


def blocks(lesson_id: str, block_type: str):
    return [b for b in lesson_by_id(lesson_id)["blocks"] if b[1] == block_type]


def test_lesson1_defines_interval_abbreviations_before_quiz_without_tritone_overload():
    lesson = lesson_by_id("L01")
    glossary_indices = [i for i, block in enumerate(lesson["blocks"]) if block[1] == "glossary"]
    checkpoint_index = next(i for i, block in enumerate(lesson["blocks"]) if block[0] == "L01-BCP1")
    assert glossary_indices
    assert max(glossary_indices[:2]) < checkpoint_index

    terms = [term for block in blocks("L01", "glossary") for term in block[2].get("terms", [])]
    by_symbol = {term.get("symbol"): term for term in terms}
    for symbol in ["M", "m", "P", "A", "d"]:
        assert symbol in by_symbol, symbol
        assert by_symbol[symbol]["definition"].strip()

    lesson_text = " ".join(str(block[2]) for block in lesson["blocks"])
    interval_block = next(block for block in lesson["blocks"] if block[1] == "interval_explorer")
    assert interval_block[2]["intervals"] == ["M3", "m3", "P5", "d5"]
    assert "Tritone" not in lesson_text
    assert "A4" not in lesson_text
    assert "P5" in lesson_text
    assert "d5" in lesson_text
    assert "A5" in lesson_text


def test_lesson1_objectives_do_not_frontload_specialist_jargon():
    lesson = lesson_by_id("L01")
    objective_text = " ".join(lesson["objectives"]).casefold()
    for jargon in ["enharmonic", "spelling", "triad", "quãng tám"]:
        assert jargon not in objective_text
    block_text = " ".join(str(block[2]) for block in lesson["blocks"])
    assert "một số giáo trình" not in block_text.casefold()
    assert "Open Music Theory" not in block_text


def test_lesson1_teaches_keyboard_half_steps_before_intervals():
    lesson = lesson_by_id("L01")
    text = " ".join(str(block[2]) for block in lesson["blocks"][:4])
    for token in ["E–F", "B–C", "không có phím đen", "1 nửa cung", "2 nửa cung", "1 cung nguyên"]:
        assert token in text
    piano_index = next(i for i, block in enumerate(lesson["blocks"]) if block[0] == "L01-B03")
    checkpoint_index = next(i for i, block in enumerate(lesson["blocks"]) if block[0] == "L01-BCP1")
    assert lesson["blocks"][piano_index][1] == "piano"
    assert lesson["blocks"][piano_index][2]["show_octave_numbers"] is False
    assert piano_index < checkpoint_index


def test_lesson1_spelling_rule_is_taught_before_triad_construction():
    lesson = lesson_by_id("L01")
    spelling_index = next(i for i, block in enumerate(lesson["blocks"]) if block[0] == "L01-B04")
    triad_index = next(i for i, block in enumerate(lesson["blocks"]) if block[0] == "L01-B08")
    checkpoint_index = next(i for i, block in enumerate(lesson["blocks"]) if block[0] == "L01-BCP2")
    assert spelling_index < triad_index < checkpoint_index
    text = str(lesson["blocks"][spelling_index][2])
    assert "họ E" in text
    assert "D#" in text
    assert "Eb" in text
    assert "C–E–G" in text


def test_lesson1_triad_construction_uses_interval_method_and_complete_formulas():
    lesson = lesson_by_id("L01")
    triad_text = str(next(block[2] for block in lesson["blocks"] if block[0] == "L01-B08"))
    assert "Bước 1" in triad_text
    assert "Bước 2" in triad_text
    assert "M3" in triad_text and "P5" in triad_text
    assert "m3" in triad_text and "d5" in triad_text
    assert "chưa cần biết âm giai" in triad_text

    triad_explorer = next(block[2] for block in lesson["blocks"] if block[0] == "L01-B09")
    text = str(triad_explorer)
    assert "major" in text and "minor" in text and "diminished" in text and "augmented" in text
    assert "1–♭3–♭5" in text and "1–3–#5" in text


def test_lesson1_dynamic_triad_notation_explorer_keeps_shared_root_contract():
    lesson = lesson_by_id("L01")
    block = next(block for block in lesson["blocks"] if block[0] == "L01-B10")
    assert block[1] == "triad_notation_explorer"
    assert block[2]["default_root"] == "C"

def test_lesson1_section_numbers_are_continuous():
    lesson = lesson_by_id("L01")
    numbered_titles = []
    for block in lesson["blocks"]:
        title = block[2].get("title", "")
        head = title.split(".", 1)[0]
        if head.isdigit():
            numbered_titles.append(int(head))
    assert numbered_titles == list(range(1, 11))

def test_lesson1_free_response_prompts_explain_input_format_without_leaking_answers():
    lesson = lesson_by_id("L01")
    by_id = {exercise["id"]: exercise for exercise in lesson["exercises"]}
    assert "Nốt-Nốt-Nốt" in by_id["L01-Q02"]["prompt"]
    assert "1-3-5" in by_id["L01-Q03"]["prompt"]
    assert "1-b3-5" not in by_id["L01-Q03"]["prompt"]
    assert "D minor" in by_id["L01-Q04"]["prompt"]
    assert "Có hoặc Không" in by_id["L01-Q05"]["prompt"]
    assert "B diminished" in by_id["L01-Q06"]["prompt"]

def test_formula_grader_accepts_ascii_and_unicode_flat_symbols():
    config = {"normalize_dashes": True, "normalize_accidentals": True}
    for answer in ["1-b3-5", "1-♭3-5", "1–♭3–5"]:
        assert grade_payload("exact", {"expected": "1-b3-5"}, config, answer).correct


def test_lessons_1_to_4_have_explanation_before_assessment_and_music_interaction():
    for lesson_id in ["L01", "L02", "L03", "L04"]:
        lesson = lesson_by_id(lesson_id)
        block_types = [block[1] for block in lesson["blocks"]]
        assert "theory" in block_types or "glossary" in block_types
        assert "checkpoint" in block_types
        assert any(kind in block_types for kind in ["piano", "audio", "notation", "progression"])


def test_lesson2_explains_seventh_and_roman_symbol_vocabulary():
    terms = [term for block in blocks("L02", "glossary") for term in block[2].get("terms", [])]
    symbols = {term.get("symbol") for term in terms}
    assert {"maj7", "m7", "7", "ø7 / m7♭5", "I, ii, V"}.issubset(symbols)


def test_lesson3_and_lesson4_define_function_and_voice_leading_language():
    l3_text = " ".join(str(block[2]) for block in lesson_by_id("L03")["blocks"])
    for token in ["Tonic", "Predominant", "Dominant", "Tiến trình hợp âm"]:
        assert token in l3_text

    l4_text = " ".join(str(block[2]) for block in lesson_by_id("L04")["blocks"])
    for token in ["ii–V–I", "Guide tones", "Voice leading", "Common tone"]:
        assert token in l4_text


def test_runtime_lessons_expose_phase2_block_types():
    with TestClient(app) as client:
        l01 = client.get("/api/v1/lessons/L01").json()
        l04 = client.get("/api/v1/lessons/L04").json()
        assert {"glossary", "piano", "interval_explorer", "triad_explorer", "triad_notation_explorer", "triad_audio_explorer", "key_overview"}.issubset({block["block_type"] for block in l01["blocks"]})
        assert {"glossary", "notation", "piano", "audio", "progression"}.issubset({block["block_type"] for block in l04["blocks"]})


def test_lesson2_to_4_beginner_vocabulary_gaps_are_closed():
    l02_text = " ".join(str(block[2]) for block in lesson_by_id("L02")["blocks"])
    for token in ["Whole step", "2 nửa cung", "half step", "Key", "Giọng / trung tâm điệu tính"]:
        assert token in l02_text

    l04_text = " ".join(str(block[2]) for block in lesson_by_id("L04")["blocks"])
    assert "Voicing" in l04_text
    assert "Cách xếp nốt của hợp âm" in l04_text


def test_lesson4_piano_block_can_submit_deterministic_keyboard_evidence():
    piano_blocks = blocks("L04", "piano")
    assert len(piano_blocks) == 1
    payload = piano_blocks[0][2]
    assert payload["exercise_id"] == "L04-Q03"
    assert payload["evidence_mode"] == "pitch_class"
