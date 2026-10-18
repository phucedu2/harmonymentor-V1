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
