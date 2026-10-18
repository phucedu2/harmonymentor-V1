"""Ví dụ và yêu cầu nêu trực tiếp trong SRS v1.3 (mục 4.4, 4.4.1, 4.5, 4.9, FR-AI-13)."""

import pytest

from app.music_engine import chord_tones, parse_chord_symbol, parse_note, roman_numeral
from app.music_engine.errors import (ConventionNotVerified, NotDiatonic, NotSupportedInMvp, UnknownQuality,
                                     UnsupportedSpelling)
from app.music_engine.grading import (grade_build_chord, grade_build_interval, grade_build_scale,
                                      grade_identify_chord, grade_identify_interval, grade_roman_numeral)


def names(notes):
    return [str(n) for n in notes]


# SRS 4.4: G#4 và Ab4 cùng MIDI 68 nhưng là hai tên nốt khác nhau
def test_same_midi_different_names():
    assert parse_note("G#4").midi == parse_note("Ab4").midi == 68
    assert str(parse_note("Ab4")) == "Ab4"


# SRS 4.4.1: midi = 12 × (octave + 1) + pc(letter) + accidental; hiển thị "Eb4", "F##3"
@pytest.mark.parametrize("text,midi", [("Eb4", 63), ("F##3", 55), ("Cb4", 59), ("B#3", 60)])
def test_midi_formula(text, midi):
    assert parse_note(text).midi == midi


def test_accidental_range_is_plus_minus_two():
    with pytest.raises(UnsupportedSpelling):
        chord_tones("Fbdim7")  # Fb dim7 cần Ebbb (giáng ba) → từ chối, không đoán


# SRS 4.4.1: Bm7b5 = B D F A; Ebm7b5 = Eb Gb Bbb Db (FR-AI-13 cũng dùng ví dụ này)
def test_srs_spelling_examples():
    assert names(chord_tones("Bm7b5")) == ["B", "D", "F", "A"]
    assert names(chord_tones("Ebm7b5")) == ["Eb", "Gb", "Bbb", "Db"]


# SRS 4.4.1 bí danh: maj7 = M7 = Δ7; m7b5 = ø7; min = m = -; dim = °
@pytest.mark.parametrize("a,b", [("CM7", "Cmaj7"), ("CΔ7", "Cmaj7"), ("Bø7", "Bm7b5"),
                                 ("Amin", "Am"), ("A-", "Am"), ("A-7", "Am7"), ("B°", "Bdim")])
def test_srs_aliases(a, b):
    assert parse_chord_symbol(a, "srs").notes == parse_chord_symbol(b, "srs").notes


def test_unknown_quality_is_rejected_not_guessed():
    with pytest.raises(UnknownQuality):
        parse_chord_symbol("Cmaj13")


# SRS 4.4.1: C/E được phân tích; chỉ kiểm tra nốt bass
def test_slash_chord():
    cs = parse_chord_symbol("C/E")
    assert cs.bass.name == "E" and cs.inversion == 1 and names(cs.notes) == ["C", "E", "G"]


# SRS 4.5: bảng mã lỗi, đúng các ví dụ trong bảng
@pytest.mark.parametrize("symbol,answer,code", [
    ("G7", ["G", "B", "D", "F#"], "SEVENTH_QUALITY"),
    ("Am", ["A", "C#", "E"], "THIRD_QUALITY"),
    ("Bdim", ["B", "D", "F#"], "FIFTH_QUALITY"),
    ("G7", ["G", "B", "F"], "MISSING_TONE"),
    ("C", ["C", "E", "G", "A"], "EXTRA_TONE"),
    ("Dm7", ["E", "G", "B", "D"], "WRONG_ROOT"),
    ("Ab", ["G#", "C", "D#"], "ENHARMONIC_SPELLING"),
])
def test_error_codes_from_srs_table(symbol, answer, code):
    r = grade_build_chord(symbol, answer)
    assert not r["correct"]
    assert r["primary_error"] == code
    assert r["message_vi"]


# SRS 4.5 ví dụ chính: G7 → G B D F# → "quãng 7 trưởng thay vì quãng 7 thứ", đáp án G B D F
def test_g7_diagnosis_message():
    r = grade_build_chord("G7", ["G", "B", "D", "F#"])
    assert "quãng 7 trưởng thay vì quãng 7 thứ" in r["message_vi"]
    assert r["expected"] == ["G", "B", "D", "F"]


# SRS 4.4: "G# C D#" cho bài "dựng Ab" sai ở strict, đúng ở pitch_class_only
def test_grading_modes():
    assert not grade_build_chord("Ab", ["G#", "C", "D#"], "strict_spelling")["correct"]
    assert grade_build_chord("Ab", ["G#", "C", "D#"], "pitch_class_only")["correct"]


# SRS 4.4.1: thể đảo được chấp nhận trừ khi root_position_only
def test_inversions_accepted_unless_root_position_only():
    assert grade_build_chord("C", ["E4", "G4", "C5"])["correct"]
    r = grade_build_chord("C", ["E4", "G4", "C5"], root_position_only=True)
    assert r["primary_error"] == "NOT_ROOT_POSITION"


# SRS 4.9 build_interval: {root: "C4", interval: "M3"} → ["C4","E4"]
def test_build_interval():
    assert grade_build_interval("C4", "M3", "E4")["correct"]
    assert grade_build_interval("C4", "M3", "Fb4")["primary_error"] == "ENHARMONIC_SPELLING"
    assert grade_build_interval("C4", "M3", "F4")["primary_error"] == "WRONG_INTERVAL_SIZE"


# SRS 4.9 identify_interval: A4 ≠ d5
def test_identify_interval_a4_not_d5():
    assert grade_identify_interval("C4", "F#4", "A4")["correct"]
    assert grade_identify_interval("C4", "F#4", "+4")["correct"]  # QĐ-2.1: nhận bí danh +4
    assert not grade_identify_interval("C4", "F#4", "d5")["correct"]


# SRS 4.9 build_scale: {tonic: "D", type: "major"} → 7 tên nốt
def test_build_scale():
    assert grade_build_scale("D", "major", ["D", "E", "F#", "G", "A", "B", "C#"])["correct"]
    r = grade_build_scale("D", "major", ["D", "E", "Gb", "G", "A", "B", "C#"])
    assert r["primary_error"] == "ENHARMONIC_SPELLING" and r["wrong_degrees"] == [3]


# SRS 4.9 identify_chord: chấp nhận bí danh (Am7 = A-7)
def test_identify_chord_aliases():
    assert grade_identify_chord(["A", "C", "E", "G"], "Am7")["correct"]
    assert grade_identify_chord(["A", "C", "E", "G"], "A-7")["correct"]
    assert not grade_identify_chord(["A", "C", "E", "G"], "A7")["correct"]


# SRS 4.9 roman_numeral: {key: "C", chord: "Dm7"} → "ii7"; hoa/thường phải khớp
def test_roman_numeral():
    assert roman_numeral("C", "Dm7").numeral == "ii7"
    assert grade_roman_numeral("C", "Dm7", "ii7")["correct"]
    assert grade_roman_numeral("C", "Dm7", "II7")["primary_error"] == "ROMAN_QUALITY_MARK"
    assert grade_roman_numeral("C", "Bdim", "viio")["correct"]


# Quyết định đã chốt: giọng thứ, thể đảo, hồ sơ jazz-pop, hợp âm ngoài giọng
def test_mvp_guards():
    with pytest.raises(NotSupportedInMvp):
        roman_numeral("A", "Am", mode="minor")   # QĐ-2.2
    with pytest.raises(NotSupportedInMvp):
        roman_numeral("C", "C/E")                # QĐ-2.3 (khuyến nghị)
    with pytest.raises(ConventionNotVerified):
        roman_numeral("C", "Dm7", profile="jazzpop")
    with pytest.raises(NotDiatonic):
        roman_numeral("C", "D7")
