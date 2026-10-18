"""Công cụ cho AI Tutor gọi qua function calling (SRS FR-AI-13).

AI không tự suy ra nốt/hợp âm; nó gọi các hàm này. Mỗi hàm trả JSON thuần.
`analyze_progression` (K09) và `get_lesson` chưa làm: K09 chưa đủ nguồn, get_lesson cần kho bài học.
"""

from __future__ import annotations

from .chord import chord_tones, parse_chord_symbol
from .errors import MusicEngineError
from .interval import interval_between
from .scale import build_scale


def _safe(fn):
    def wrapper(**kwargs):
        try:
            return {"ok": True, **fn(**kwargs)}
        except MusicEngineError as e:
            return {"ok": False, "error": e.to_dict()}
    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper


@_safe
def get_chord_tones(symbol: str) -> dict:
    """Các nốt của một hợp âm, ví dụ 'Ebm7b5' → Eb Gb Bbb Db."""
    cs = parse_chord_symbol(symbol)
    return {"symbol": cs.symbol, "notes": [str(n) for n in chord_tones(symbol)],
            "bass": cs.bass.name if cs.bass else None, "source_claims": list(cs.type.claim_ids),
            "verified": cs.type.verified}


@_safe
def get_scale(tonic: str, scale_type: str = "major") -> dict:
    """Các nốt của âm giai, ví dụ ('E', 'major') → E F# G# A B C# D#."""
    return {"tonic": tonic, "scale_type": scale_type, "notes": [str(n) for n in build_scale(tonic, scale_type)]}


@_safe
def identify_interval(lower: str, upper: str) -> dict:
    """Tên quãng đi lên giữa hai nốt, ví dụ ('A#', 'E#') → P5."""
    iv = interval_between(lower, upper)
    return {"interval": iv.name, "semitones": iv.semitones}


TOOL_DECLARATIONS = [
    {"name": "get_chord_tones", "description": get_chord_tones.__doc__,
     "parameters": {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]}},
    {"name": "get_scale", "description": get_scale.__doc__,
     "parameters": {"type": "object", "properties": {
         "tonic": {"type": "string"},
         "scale_type": {"type": "string", "enum": ["major", "natural_minor", "harmonic_minor",
                                                   "melodic_minor", "dorian"]}},
         "required": ["tonic"]}},
    {"name": "identify_interval", "description": identify_interval.__doc__,
     "parameters": {"type": "object", "properties": {"lower": {"type": "string"}, "upper": {"type": "string"}},
                    "required": ["lower", "upper"]}},
]
TOOLS = {"get_chord_tones": get_chord_tones, "get_scale": get_scale, "identify_interval": identify_interval}
