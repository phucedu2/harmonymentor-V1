"""Ví dụ lấy trực tiếp từ nguồn đã đọc. Mỗi test ghi claim_id và vị trí.

Nếu một test ở đây hỏng, hoặc code sai, hoặc nguồn bị hiểu sai: KHÔNG sửa test cho khớp code
khi chưa đối chiếu lại nguồn.
"""

import pytest

from app.music_engine import (build_scale, chord_tones, diatonic_chords, interval_between, invert,
                              key_from_signature, key_signature, parse_note, relative_minor, transpose)
from app.music_engine.errors import InvalidInterval, UnsupportedKey
from app.music_engine.key import ORDER_OF_FLATS, ORDER_OF_SHARPS
from app.music_engine.rhythm import duration_beats


def names(notes):
    return [str(n) for n in notes]


# MUS-PITCH-002 — Fankhauser Ch. 1, tr. 10; OMT ASPN tr. 55
def test_middle_c_is_c4_and_b_below_is_b3():
    assert parse_note("C4").midi == 60
    assert parse_note("B3").midi == 59
    assert parse_note("A4").midi == 69  # A4 = 440 Hz (MUS-PITCH-003)


# MUS-ACC-004 — OMT tr. 50–53: E#=F, Fb=E, B#=C, Cb=B (cùng cao độ, khác tên)
@pytest.mark.parametrize("a,b", [("E#4", "F4"), ("Fb4", "E4"), ("B#3", "C4"), ("Cb4", "B3")])
def test_enharmonic_pairs(a, b):
    na, nb = parse_note(a), parse_note(b)
    assert na.midi == nb.midi
    assert not na.same_spelling(nb)


# MUS-SCALE-003 — Fankhauser tr. 16: bậc 3 của E trưởng là G#, không phải Ab
def test_e_major_third_degree_is_g_sharp():
    assert names(build_scale("E"))[2] == "G#"


# MUS-SCALE-009 — Fankhauser tr. 18: D# thứ hòa âm = D# E# F# G# A# B C##
def test_d_sharp_harmonic_minor():
    assert names(build_scale("D#", "harmonic_minor")) == ["D#", "E#", "F#", "G#", "A#", "B", "C##"]


# MUS-SCALE-002/005/006/007/008 — công thức nửa cung (F tr. 16–18; OMT Major/Minor Scales)
@pytest.mark.parametrize("scale_type,pattern", [
    ("major", [2, 2, 1, 2, 2, 2, 1]),
    ("natural_minor", [2, 1, 2, 2, 1, 2, 2]),
    ("harmonic_minor", [2, 1, 2, 2, 1, 3, 1]),
    ("melodic_minor", [2, 1, 2, 2, 2, 2, 1]),
    ("dorian", [2, 1, 2, 2, 2, 1, 2]),
])
def test_scale_step_patterns(scale_type, pattern):
    from app.music_engine.scale import scale_step_pattern
    for tonic in ["C", "F#", "Bb", "Eb", "A"]:
        assert scale_step_pattern(tonic, scale_type) == pattern


# MUS-SCALE-007 — melodic minor đi xuống = thứ tự nhiên (F tr. 17; OMT)
def test_melodic_minor_descending_is_natural_minor():
    assert names(build_scale("A", "melodic_minor", descending=True)) == list(
        reversed(names(build_scale("A", "natural_minor"))))


# MUS-INT-007 — Fankhauser tr. 44: A#–E# là quãng 5 đúng
def test_a_sharp_to_e_sharp_is_p5():
    assert interval_between("A#", "E#").name == "P5"


# MUS-INT-006 — Fankhauser tr. 44: B–F là cặp phím trắng duy nhất không phải M/m/P
def test_only_b_f_is_not_major_minor_perfect():
    white = "CDEFGAB"
    odd = [(a, b) for a in white for b in white if a != b
           and interval_between(a, b).quality not in ("M", "m", "P")]
    assert set(odd) == {("B", "F"), ("F", "B")}  # B–F = d5, và đảo của nó F–B = A4


# MUS-INT-004 — Fankhauser tr. 44: 6 nửa cung = A4 hoặc d5; MUS-INT-005: khác nhau
def test_tritone_two_names():
    assert interval_between("C4", "F#4").name == "A4"
    assert interval_between("C4", "Gb4").name == "d5"
    assert interval_between("C4", "F#4").semitones == interval_between("C4", "Gb4").semitones == 6


# MUS-INT-008 — Fankhauser bài tập 9, 20: có A1 và d8, không có d1
def test_augmented_unison_and_diminished_octave_exist_but_not_d1():
    assert transpose("G4", "A1") == parse_note("G#4")
    assert interval_between("F##4", "F#5").name == "d8"
    with pytest.raises(InvalidInterval):
        transpose("C4", "d1")


# MUS-INT-009 — Fankhauser tr. 55; OMT Intervals: cộng 9, M↔m, P↔P, A↔d
@pytest.mark.parametrize("iv,inv", [("M3", "m6"), ("m2", "M7"), ("P4", "P5"), ("A4", "d5"), ("P1", "P8")])
def test_inversion(iv, inv):
    assert invert(iv).name == inv
    assert invert(iv).number + int(iv[1:]) == 9


# MUS-INT-010 — Fankhauser tr. 55: M9, m10, +11, P12, P15
@pytest.mark.parametrize("upper,name", [("D5", "M9"), ("Eb5", "m10"), ("F#5", "A11"), ("G5", "P12"), ("C6", "P15")])
def test_compound_intervals(upper, name):
    assert interval_between("C4", upper).name == name


# MUS-KEY-002 — thứ tự dấu hóa (F tr. 35; OMT Major Scales). File Fankhauser in lỗi "FCGBDAEB".
def test_order_of_accidentals():
    assert "".join(ORDER_OF_SHARPS) == "FCGDAEB"
    assert "".join(ORDER_OF_FLATS) == "BEADGCF"


# MUS-KEY-003 — dấu thăng cuối thấp hơn chủ âm nửa cung; dấu giáng áp cuối là chủ âm
@pytest.mark.parametrize("count", range(1, 8))
def test_identify_major_key_from_signature(count):
    sharp_key = key_signature(key_from_signature(count, "sharp"))
    assert transpose(sharp_key.accidentals[-1], "m2").same_spelling(sharp_key.tonic)
    if count >= 2:
        flat_key = key_signature(key_from_signature(count, "flat"))
        assert flat_key.accidentals[-2].same_spelling(flat_key.tonic)


# MUS-KEY-004 — giọng thứ tương quan thấp hơn quãng 3 thứ (A thứ ↔ C trưởng)
def test_relative_minor():
    assert relative_minor("C").name == "A"
    assert relative_minor("Eb").name == "C"


# MUS-KEY-005 — tối đa 7 dấu; Gb thứ → dùng F# thứ (Fankhauser tr. 36)
def test_more_than_seven_accidentals_rejected_with_enharmonic_suggestion():
    with pytest.raises(UnsupportedKey) as e:
        key_signature("Gb", "minor")
    assert e.value.details["suggestion"] == "F# minor"


# MUS-TRIAD-002 — Fankhauser tr. 120 (C: I ii iii IV V vi vii°); OMT Triads
def test_major_key_triad_qualities():
    assert [r.numeral for r in diatonic_chords("C")] == ["I", "ii", "iii", "IV", "V", "vi", "vii°"]
    assert [r.chord.symbol for r in diatonic_chords("C")] == ["C", "Dm", "Em", "F", "G", "Am", "Bdim"]


# MUS-7TH-001 — Fankhauser tr. 152 ví dụ: g: V7 = D, F#, A, C (V7 của Sol thứ dựng trên D)
def test_dominant_seventh_example():
    assert names(chord_tones("D7")) == ["D", "F#", "A", "C"]


# MUS-7TH-004 — OMT Seventh Chords: 5 loại theo ba + bảy
@pytest.mark.parametrize("symbol,notes", [
    ("Cmaj7", ["C", "E", "G", "B"]), ("C7", ["C", "E", "G", "Bb"]), ("Cm7", ["C", "Eb", "G", "Bb"]),
    ("Cm7b5", ["C", "Eb", "Gb", "Bb"]), ("Cdim7", ["C", "Eb", "Gb", "Bbb"]),
])
def test_seventh_chord_qualities(symbol, notes):
    assert names(chord_tones(symbol)) == notes


# MUS-RHY-001 — OMT Notating Rhythm: quan hệ 2:1, chấm dôi thêm một nửa
def test_note_values():
    assert duration_beats("whole") == 2 * duration_beats("half") == 4 * duration_beats("quarter")
    assert duration_beats("eighth") == 2 * duration_beats("sixteenth")
    assert duration_beats("quarter", dots=1) == duration_beats("quarter") * 3 / 2
