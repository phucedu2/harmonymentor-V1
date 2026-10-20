"""Phase 2.3: multi-key Lesson 1 pedagogy and UI contract regression tests."""
from pathlib import Path

from app.content.curriculum_specs import lesson_by_id

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "src"


def test_interval_quality_explanation_has_two_families_spectrums_and_concrete_aug_dim_examples():
    lesson = lesson_by_id("L01")
    block = next(b for b in lesson["blocks"] if b[0] == "L01-B05")
    payload = block[2]
    intro = payload["intro"]
    assert "1–4–5–8" in intro
    assert "2–3–6–7" in intro
    assert "Minor (m)" in intro and "Major (M)" in intro
    assert len(payload["spectrums"]) == 2
    spectrum_text = " ".join(x["text"] for x in payload["spectrums"])
    for token in ["d (Giảm", "P (Đúng", "m (Thứ)", "M (Trưởng)", "A (Tăng"]:
        assert token in spectrum_text
    terms = {x["symbol"]: x for x in payload["terms"]}
    assert "C→G#" in terms["A"]["example"]
    assert "A5" in terms["A"]["example"]
    assert "C→Gb" in terms["d"]["example"]
    assert "d5" in terms["d"]["example"]


def test_counting_rule_is_taught_before_interval_spelling_example():
    lesson = lesson_by_id("L01")
    section2 = next(b[2] for b in lesson["blocks"] if b[0] == "L01-B04")
    paragraphs = section2["paragraphs"]
    assert "nốt đầu được tính là 1" in paragraphs[0]
    assert "phím xuất phát = 0" in paragraphs[1]
    joined = " ".join(paragraphs)
    assert joined.index("nốt đầu được tính là 1") < joined.index("quãng 3 từ C")


def test_lesson1_has_shared_root_explorer_blocks_and_24_key_overview():
    lesson = lesson_by_id("L01")
    block_types = [b[1] for b in lesson["blocks"]]
    for kind in ["interval_explorer", "triad_explorer", "triad_notation_explorer", "triad_audio_explorer", "key_overview"]:
        assert kind in block_types
    overview = next(b[2] for b in lesson["blocks"] if b[1] == "key_overview")
    assert overview["tiers"] == ["tier-1", "tier-2", "tier-3"]


def test_checkpoint_and_quiz_are_not_reusing_c_examples_or_leaking_minor_formula():
    lesson = lesson_by_id("L01")
    by_id = {q["id"]: q for q in lesson["exercises"]}
    assert by_id["L01-Q01"]["prompt"] == "Quãng từ F lên A là gì?"
    assert "G major" in by_id["L01-Q02"]["prompt"]
    assert "D minor" in by_id["L01-Q04"]["prompt"]
    assert "1-b3-5" not in by_id["L01-Q03"]["prompt"]
    assert "1-3-5" in by_id["L01-Q03"]["prompt"]
    checkpoints = [b[2] for b in lesson["blocks"] if b[1] == "checkpoint"]
    assert {x["random_practice"] for x in checkpoints} == {"interval", "triad"}


def test_review_bank_uses_multiple_roots():
    lesson = lesson_by_id("L01")
    text = " ".join(x["front"] for x in lesson["review_items"])
    for root in ["F", "D", "G", "B", "A"]:
        assert root in text
    assert "Build C major" not in text


def test_frontend_root_selector_declares_all_12_pitch_positions_and_24_major_minor_cards():
    source = (FRONTEND / "content" / "lessons.ts").read_text(encoding="utf-8")
    for label in ["C#/Db", "D#/Eb", "F#/Gb", "G#/Ab", "A#/Bb"]:
        assert label in source
    assert source.count('label: "') >= 24
    for symbol in ["C", "Dm", "Em", "F", "G", "Am", "D", "E", "A", "Cm", "Fm", "Gm", "Bb", "Eb", "Db", "F#", "Ab", "B", "C#m", "Ebm", "F#m", "G#m", "Bbm", "Bm"]:
        assert f'symbol: "{symbol}"' in source


def test_lesson_runner_uses_shared_root_state_and_random_practice_widgets():
    source = (FRONTEND / "components" / "learning" / "LessonRunner.tsx").read_text(encoding="utf-8")
    assert 'useState("C")' in source
    assert "IntervalExplorer" in source
    assert "TriadExplorer" in source
    assert "TriadNotationExplorer" in source
    assert "TriadAudioExplorer" in source
    assert "KeyOverview24" in source
    assert "RandomPracticePanel" in source
    assert 'placeholder: "Ví dụ định dạng: 1-3-5"' in source
    assert 'placeholder: "Ví dụ: 1-b3-5"' not in source


def test_chord_inspector_refreshes_when_dynamic_symbol_changes():
    source = (FRONTEND / "components" / "learning" / "ChordInspector.tsx").read_text(encoding="utf-8")
    assert "queryKey" in source
    assert "if (eager || open) void load()" in source
    assert "displayLabel" in source


def test_music_util_and_notation_support_enharmonic_and_double_accidental_paths():
    theory = (FRONTEND / "theory" / "lesson1Theory.ts").read_text(encoding="utf-8")
    notation = (FRONTEND / "components" / "music" / "NotationStaff.tsx").read_text(encoding="utf-8")
    music_utils = (FRONTEND / "audio" / "musicUtils.ts").read_text(encoding="utf-8")
    assert "spellInterval" in theory and "buildTriad" in theory
    assert "#{1,2}" in notation and "b{1,2}" in notation
    assert "accidentalOffset" in music_utils


def test_audio_preview_normalizes_spelled_scientific_notes_to_sounding_pitch():
    source = (FRONTEND / "components" / "music" / "AudioControls.tsx").read_text(encoding="utf-8")
    assert "scientificToMidi" in source
    assert "midiToScientific" in source
    engine = (FRONTEND / "audio" / "AudioEngine.ts").read_text(encoding="utf-8")
    assert "piano.releaseAll()" in engine
