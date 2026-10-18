"""Kiểm chéo toàn bộ với music21 (SRS 4.4.1: chỉ chạy trong test, không chạy lúc vận hành).

Mục đích: bắt lỗi code. music21 không phải "nguồn" kiến thức; nếu hai bên lệch nhau,
phải đối chiếu lại giáo trình trước khi kết luận bên nào sai.
"""

import itertools

import pytest

music21 = pytest.importorskip("music21")
from music21 import harmony, interval as m21interval, key as m21key, pitch as m21pitch, scale as m21scale

from app.music_engine import build_scale, chord_tones, interval_between, key_signature, transpose
from app.music_engine.errors import MusicEngineError
from app.music_engine.key import all_supported_keys
from app.music_engine.pitch import LETTERS, Note

ALL_SPELLINGS = [Note(l, a) for l in LETTERS for a in (-2, -1, 0, 1, 2)]
COMMON_ROOTS = [Note(l, a) for l in LETTERS for a in (-1, 0, 1)]


def m21name(n: Note) -> str:
    acc = "#" * n.accidental if n.accidental > 0 else "-" * -n.accidental
    return f"{n.letter}{acc}" + ("" if n.octave is None else str(n.octave))


def ours(n: Note) -> str:
    return m21name(n)


def test_intervals_all_spelling_pairs():
    """35 × 35 cặp tên nốt, nốt trên ở quãng tám 4 hoặc 5 (gồm cả quãng kép)."""
    checked = 0
    for a in ALL_SPELLINGS:
        lo = a.with_octave(4)
        for b in ALL_SPELLINGS:
            for octv in (4, 5):
                hi = b.with_octave(octv)
                if hi.diatonic_index < lo.diatonic_index:
                    continue
                try:
                    theirs = m21interval.Interval(noteStart=m21pitch.Pitch(m21name(lo)),
                                                  noteEnd=m21pitch.Pitch(m21name(hi)))
                    their_name = theirs.name
                except music21.interval.IntervalException:
                    their_name = None  # music21 cũng không gọi tên được
                try:
                    mine = interval_between(lo, hi)
                except MusicEngineError:
                    # Engine chỉ được từ chối khi quãng vượt tăng kép/giảm kép, hoặc là "quãng 1 giảm".
                    assert their_name is None or their_name.startswith(("AAA", "ddd")) \
                        or (lo.diatonic_index == hi.diatonic_index and hi.midi < lo.midi), (str(lo), str(hi), their_name)
                    continue
                assert mine.name == theirs.name, (str(lo), str(hi), mine.name, theirs.name)
                assert mine.semitones == theirs.semitones
                checked += 1
    assert checked > 1400  # 1495 cặp so được khi viết test


@pytest.mark.parametrize("iv", ["P1", "A1", "m2", "M2", "A2", "d3", "m3", "M3", "A3", "d4", "P4", "A4",
                                "d5", "P5", "A5", "m6", "M6", "A6", "d7", "m7", "M7", "d8", "P8", "M9", "m10"])
def test_transpose_matches_music21(iv):
    for root in COMMON_ROOTS:
        r = root.with_octave(4)
        try:
            mine = transpose(r, iv)
        except MusicEngineError:
            continue  # cần dấu hóa vượt ±2
        theirs = m21pitch.Pitch(m21name(r)).transpose(iv)
        assert ours(mine) == theirs.nameWithOctave, (str(r), iv)


M21_SCALES = {
    "major": m21scale.MajorScale,
    "natural_minor": m21scale.MinorScale,
    "harmonic_minor": m21scale.HarmonicMinorScale,
    "melodic_minor": m21scale.MelodicMinorScale,
    "dorian": m21scale.DorianScale,
}


@pytest.mark.parametrize("scale_type", list(M21_SCALES))
def test_scales_match_music21(scale_type):
    for tonic in COMMON_ROOTS:
        try:
            mine = [ours(n) for n in build_scale(tonic, scale_type)]
        except MusicEngineError:
            continue
        theirs = [p.name for p in M21_SCALES[scale_type](m21name(tonic)).getPitches()[:7]]
        assert mine == theirs, (tonic.name, scale_type)


@pytest.mark.parametrize("mode", ["major", "minor"])
def test_key_signatures_match_music21(mode):
    keys = all_supported_keys(mode)
    assert len(keys) == 15
    for ks in keys:
        tonic = m21name(ks.tonic) if mode == "major" else m21name(ks.tonic).lower()
        k = m21key.Key(tonic)
        sign = 1 if ks.kind == "sharp" else -1
        assert ks.count * (sign if ks.count else 1) == k.sharps, ks.label
        assert [ours(n) for n in ks.accidentals] == [p.name for p in k.alteredPitches], ks.label


M21_CHORD_FIGURES = {"maj": "", "min": "m", "dim": "dim", "aug": "+", "7": "7", "maj7": "maj7",
                     "m7": "m7", "m7b5": "m7b5", "dim7": "dim7", "sus2": "sus2", "sus4": "sus4"}


@pytest.mark.parametrize("chord_type", list(M21_CHORD_FIGURES))
def test_chords_match_music21(chord_type):
    from app.music_engine.chord import CHORD_TYPES
    for root in COMMON_ROOTS:
        symbol = f"{root.name}{CHORD_TYPES[chord_type].display}"
        try:
            mine = [ours(n) for n in chord_tones(symbol)]
        except MusicEngineError:
            continue
        cs = harmony.ChordSymbol(m21name(root) + M21_CHORD_FIGURES[chord_type])
        theirs = [p.name for p in cs.pitches]
        # music21 có thể xếp nốt theo voicing khác; so tập tên nốt (đúng chính tả), không so thứ tự.
        assert sorted(mine) == sorted(theirs), (symbol, mine, theirs)


def test_roman_numerals_match_music21():
    """Số La Mã giọng trưởng (thể gốc). music21 viết 'o' cho giảm và 'M7' hiếm khi dùng nên so sau khi chuẩn hóa."""
    from music21 import chord as m21chord, roman as m21roman
    from app.music_engine import diatonic_chords
    for ks in all_supported_keys("major"):
        for sevenths in (False, True):
            for rn in diatonic_chords(ks.tonic, sevenths):
                root = rn.chord.root.with_octave(3)
                notes = [transpose(root, iv) for iv in rn.chord.type.intervals]
                c = m21chord.Chord([m21name(n) for n in notes])
                fig = m21roman.romanNumeralFromChord(c, m21key.Key(m21name(ks.tonic))).figure
                fig = fig.replace("o", "°").replace("/o", "ø")
                if rn.numeral.endswith("M7"):
                    # music21 ghi hợp âm bảy trưởng là "I7"; ký hiệu IM7 của mình chưa có nguồn (claims.UNSOURCED).
                    assert fig == rn.numeral.replace("M7", "7"), (ks.label, rn.numeral, fig)
                else:
                    assert fig == rn.numeral, (ks.label, rn.numeral, fig)
