"""ADR-019: hợp âm mở rộng (maj9, m9, 9, 13) và mixolydian, cho L07. Engine tất định, không đụng DB."""

import pytest

from app.music_engine.chord import CHORD_TYPES, chord_member, chord_tones, identify_chord, parse_chord_symbol
from app.music_engine.claims import CLAIMS
from app.music_engine.scale import SCALE_TYPES, build_scale, scale_degree_of, scale_step_pattern


def names(notes):
    return [n.name for n in notes]


@pytest.mark.parametrize("symbol,expected", [
    ("Cmaj9", ["C", "E", "G", "B", "D"]),
    ("G13", ["G", "B", "D", "F", "A", "E"]),
    ("G9", ["G", "B", "D", "F", "A"]),
    ("Dm9", ["D", "F", "A", "C", "E"]),
    ("Dbmaj9", ["Db", "F", "Ab", "C", "Eb"]),
    ("F#13", ["F#", "A#", "C#", "E", "G#", "D#"]),
    ("Ebm9", ["Eb", "Gb", "Bb", "Db", "F"]),
])
def test_extended_chord_tones(symbol, expected):
    assert names(chord_tones(symbol)) == expected


def test_extended_aliases():
    assert parse_chord_symbol("CΔ9").type.id == "maj9"
    assert parse_chord_symbol("C-9").type.id == "m9"
    assert parse_chord_symbol("Cmin9").type.id == "m9"


def test_extended_symbol_roundtrip_and_no_inversion_for_tensions():
    cs = parse_chord_symbol("G13/A")  # bass = 9: tension, không phải thể đảo
    assert cs.symbol == "G13/A"
    assert cs.inversion is None
    assert parse_chord_symbol("Cmaj9/E").inversion == 1


def test_chord_member_for_tensions():
    g13 = parse_chord_symbol("G13")
    assert chord_member(g13, "A") == "ninth"
    assert chord_member(g13, "E") == "thirteenth"
    assert chord_member(g13, "F") == "seventh"


def test_identify_extended_chord():
    best = identify_chord(["C", "E", "G", "B", "D"])[0]
    assert best.chord.symbol == "Cmaj9"
    assert identify_chord(["G", "B", "D", "F", "A", "E"])[0].chord.symbol == "G13"


def test_old_chord_identification_unchanged():
    assert identify_chord(["C", "E", "G", "Bb"])[0].chord.symbol == "C7"
    assert identify_chord(["B", "D", "F", "A"])[0].chord.symbol == "Bm7b5"


def test_mixolydian():
    assert names(build_scale("G", "mixolydian")) == ["G", "A", "B", "C", "D", "E", "F"]
    assert names(build_scale("Eb", "mixolydian")) == ["Eb", "F", "G", "Ab", "Bb", "C", "Db"]
    assert scale_step_pattern("C", "mixolydian") == [2, 2, 1, 2, 2, 1, 2]
    assert scale_degree_of("F", "G", "mixolydian") == 7


def test_new_items_are_flagged_unverified_until_reviewed():
    for cid in ("maj9", "m9", "9", "13"):
        assert CHORD_TYPES[cid].verified is False
        assert set(CHORD_TYPES[cid].claim_ids) <= set(CLAIMS)
    assert not SCALE_TYPES["mixolydian"].mvp
    assert not CLAIMS["MUS-EXT-001"].meets_engine_threshold
