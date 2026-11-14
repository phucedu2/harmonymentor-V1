from __future__ import annotations

from pydantic import BaseModel


class ChordContextOut(BaseModel):
    key: str
    roman: str | None = None
    function: str | None = None


class ChordInspectOut(BaseModel):
    symbol: str
    quality: str
    formula: list[str]
    notes: list[str]
    bass: str | None = None
    inversion: int | None = None
    verified: bool
    context: ChordContextOut | None = None


class PitchOut(BaseModel):
    """Một cao độ có quãng tám: tên ASPN (vd B#4) và số MIDI, cùng do Music Engine tính."""

    name: str
    midi: int


class Lesson1IntervalOut(BaseModel):
    code: str
    semitones: int
    upper: str
    pitches: list[PitchOut]


class Lesson1TriadOut(BaseModel):
    quality: str
    symbol: str
    formula: list[str]
    interval_formula: list[str]
    notes: list[str]
    pitches: list[PitchOut]


class Lesson1TheoryOut(BaseModel):
    root: str
    root_octave: int
    letter_frame: list[str]
    intervals: list[Lesson1IntervalOut]
    triads: list[Lesson1TriadOut]
