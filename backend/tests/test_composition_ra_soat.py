"""RS-13: lời giải thích của Harmony Lab không gán nhãn sai và nhắc cách viết đúng tên nốt."""

from app.composition.rules import analyze


def bar(chords, index):
    return analyze("C", chords)["bars"][index]


def test_rs13_a7_khong_phai_chromatic_mediant():
    result = bar(["C", "A7", "F", "G"], 1)
    assert result["rule"] != "chromatic_mediant"
    assert "cùng loại hợp âm" not in result["reason_vi"]


def test_rs13_a_thang_duoc_nhac_viet_la_bb():
    result = bar(["C", "A#", "F", "G"], 1)
    assert "nên viết là Bb" in result["reason_vi"]
    assert "nên viết" not in bar(["C", "Bb", "F", "G"], 1)["reason_vi"]
