"""Tên chất lượng hợp âm viết bằng chữ (phiếu Phúc 09/11): "hợp âm B diminished" từng ra B trưởng (B D# F#)."""

import pytest

from app.ai.tutor.engine_query import engine_answer


def _chords(q):
    return {f["args"]["symbol"]: f["result"] for f in engine_answer(q).facts if f["tool"] == "get_chord_tones"}


@pytest.mark.parametrize("q, sym, notes", [
    ("hợp âm B diminished bấm như thế nào", "Bdim", "B D F"),
    ("hop am F# giam gom not nao", "F#dim", "F# A C"),
    ("hợp âm C augmented", "Caug", "C E G#"),
    ("hợp âm C tăng", "Caug", "C E G#"),
    ("hop am C tang gom not nao", "Caug", "C E G#"),
    ("hop am A minor", "Am", "A C E"),
    ("hợp âm Rê trưởng gồm nốt nào", "D", "D F# A"),
])
def test_chat_luong_bang_chu(q, sym, notes):
    assert _chords(q) == {sym: notes}


@pytest.mark.parametrize("q", ["hợp âm D sus4", "hợp âm B half-diminished", "hợp âm G bảy", "hợp âm C maj7"])
def test_chat_luong_khac_khong_doan_la_truong(q):
    """Chất lượng không đọc được thì không đưa nốt hợp âm trưởng (đưa sai còn tệ hơn không đưa)."""
    assert _chords(q) == {}


@pytest.mark.parametrize("q", ["hop am C tang dan am luong", "hợp âm C tăng dần"])
def test_tang_dan_khong_phai_hop_am_tang(q):
    """"tăng dần" là nghĩa khác: giữ hợp âm trưởng như khi không có chữ chất lượng."""
    assert _chords(q) == {"C": "C E G"}
