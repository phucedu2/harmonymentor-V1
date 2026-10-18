from __future__ import annotations

from fastapi import APIRouter, Query

from ..contracts.music import ChordContextOut, ChordInspectOut
from ..music_engine import parse_chord_symbol, roman_numeral
from ..music_engine.errors import MusicEngineError

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
