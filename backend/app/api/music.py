from __future__ import annotations

from fastapi import APIRouter, Query

from ..contracts.music import (
    ChordContextOut,
    ChordInspectOut,
    Lesson1IntervalOut,
    Lesson1TheoryOut,
    Lesson1TriadOut,
    PitchOut,
)
from ..music_engine import parse_chord_symbol, parse_interval, parse_note, roman_numeral, transpose
from ..music_engine.errors import InvalidPitch, MusicEngineError

router = APIRouter(prefix="/api/v1/music", tags=["music"])

_INTERVAL_TO_DEGREE = {
    "P1": "1", "m2": "b2", "M2": "2", "A2": "#2",
    "m3": "b3", "M3": "3", "P4": "4", "A4": "#4", "d5": "b5", "P5": "5", "A5": "#5",
    "m6": "b6", "M6": "6", "d7": "bb7", "m7": "b7", "M7": "7",
}


def _function_for_degree(degree: int) -> str | None:
    if degree in {1, 3, 6}:
        return "tonic"
    if degree in {2, 4}:
        return "subdominant"
    if degree == 5:
        return "dominant"
    return None


def _inspect(symbol: str, key: str | None) -> ChordInspectOut:
    chord = parse_chord_symbol(symbol)
    context = None
    if key:
        try:
            roman = roman_numeral(key, chord.symbol)
            context = ChordContextOut(key=key, roman=roman.numeral, function=_function_for_degree(roman.degree))
        except MusicEngineError:
            context = ChordContextOut(key=key, roman=None, function=None)
    return ChordInspectOut(
        symbol=chord.symbol, quality=chord.type.id,
        formula=[_INTERVAL_TO_DEGREE.get(iv, iv) for iv in chord.type.intervals],
        notes=[str(n) for n in chord.notes], bass=chord.bass.name if chord.bass else None,
        inversion=chord.inversion, verified=chord.type.verified, context=context,
    )


@router.get("/chords/inspect", response_model=ChordInspectOut)
def inspect_chord_query(
    symbol: str = Query(..., description="Chord symbol; query form supports slash chords such as C/E."),
    key: str | None = Query(default=None, description="Optional major-key context for MVP."),
):
    return _inspect(symbol, key)


@router.get("/chords/{symbol}", response_model=ChordInspectOut)
def inspect_chord_path(symbol: str, key: str | None = Query(default=None, description="Optional major-key context for MVP.")):
    """Convenience route for symbols without '/'. Prefer /chords/inspect for slash chords."""
    return _inspect(symbol, key)


# Phần khám phá Bài 1 (quãng và hợp âm ba nốt trên 12 nốt gốc). Trước đây frontend tự tính trong
# lesson1Theory.ts; nay mọi tên nốt, quãng tám và MIDI do Engine sinh (nguyên tắc bất biến số 1).
LESSON1_INTERVALS = ("M3", "m3", "P5", "d5", "A5")
LESSON1_TRIADS = (("major", ""), ("minor", "m"), ("diminished", "dim"), ("augmented", "aug"))
LESSON1_ROOT_OCTAVE = 4


def _pitch(note) -> PitchOut:
    return PitchOut(name=str(note), midi=note.midi)


@router.get("/lesson1/{root}", response_model=Lesson1TheoryOut)
def lesson1_theory(root: str):
    """Quãng M3/m3/P5/d5/A5 và 4 loại hợp âm ba nốt dựng trên `root` ở quãng tám 4."""
    # Đọc nốt gốc không kèm quãng tám rồi mới gắn quãng tám 4, để lỗi báo đúng chữ người dùng gửi.
    parsed = parse_note(root)
    if parsed.octave is not None:
        raise InvalidPitch("Nốt gốc chỉ gồm tên nốt, không kèm quãng tám (vd G#, không phải G#4)", value=root)
    base = parsed.with_octave(LESSON1_ROOT_OCTAVE)
    spelled_root = base.name
    intervals = []
    for code in LESSON1_INTERVALS:
        upper = transpose(base, code)
        intervals.append(Lesson1IntervalOut(
            code=code, semitones=parse_interval(code).semitones, upper=upper.name,
            pitches=[_pitch(base), _pitch(upper)],
        ))
    triads = []
    for quality, suffix in LESSON1_TRIADS:
        chord = parse_chord_symbol(f"{spelled_root}{suffix}")
        pitches = [transpose(base, iv) for iv in chord.type.intervals]
        # Hai đường tính (ký hiệu hợp âm và dựng quãng từ nốt gốc) phải ra cùng tên nốt.
        assert [p.name for p in pitches] == [n.name for n in chord.notes], chord.symbol
        triads.append(Lesson1TriadOut(
            quality=quality, symbol=chord.symbol,
            formula=[_INTERVAL_TO_DEGREE.get(iv, iv) for iv in chord.type.intervals],
            interval_formula=[iv for iv in chord.type.intervals if iv != "P1"],
            notes=[n.name for n in chord.notes], pitches=[_pitch(p) for p in pitches],
        ))
    frame = [transpose(base, iv).letter for iv in ("P1", "M3", "P5")]
    frame[0] = spelled_root
    return Lesson1TheoryOut(
        root=spelled_root, root_octave=LESSON1_ROOT_OCTAVE, letter_frame=frame,
        intervals=intervals, triads=triads,
    )
