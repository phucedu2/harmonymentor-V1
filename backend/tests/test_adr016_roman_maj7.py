"""ADR-016: số La Mã của hợp âm maj7 nhận cả "Imaj7" (bài L02 dạy) và "IM7" (Engine, MT21C §8.3)."""

import pytest

from app.music_engine.grading import grade_roman_numeral
from app.music_engine.roman import roman_numeral


@pytest.mark.parametrize("key,chord,answers", [
    ("C", "Cmaj7", ["Imaj7", "IM7", " Imaj7 "]),
    ("C", "Fmaj7", ["IVmaj7", "IVM7"]),
    ("G", "Gmaj7", ["Imaj7", "IM7"]),
])
def test_maj7_and_M7_are_both_accepted(key, chord, answers):
    for answer in answers:
        assert grade_roman_numeral(key, chord, answer)["correct"], (chord, answer)


@pytest.mark.parametrize("key,chord,answer,error", [
    ("C", "Cmaj7", "I7", "ROMAN_QUALITY_MARK"),     # I7 là hợp âm bảy át trên I, khác Cmaj7
    ("C", "Cmaj7", "imaj7", "ROMAN_QUALITY_MARK"),
    ("C", "Cmaj7", "IVmaj7", "ROMAN_DEGREE"),
    ("C", "G7", "Vmaj7", "ROMAN_QUALITY_MARK"),    # G7 có quãng 7 thứ
])
def test_other_marks_still_wrong(key, chord, answer, error):
    out = grade_roman_numeral(key, chord, answer)
    assert not out["correct"] and out["primary_error"] == error


def test_engine_canonical_output_unchanged():
    # Engine vẫn trả IM7; chỉ phần chấm chấp nhận thêm cách viết maj7.
    assert roman_numeral("C", "Cmaj7").numeral == "IM7"
    assert roman_numeral("C", "Fmaj7").numeral == "IVM7"
