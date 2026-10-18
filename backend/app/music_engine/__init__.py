"""Music Theory Engine của HarmonyMentor AI (Python thuần, không phụ thuộc cơ sở dữ liệu).

Bản phát triển 0.2.0-dev. Xem README.md ở thư mục gốc để biết phạm vi và các quyết định đang áp dụng.
"""

from .chord import ChordSymbol, build_chord, chord_tones, identify_chord, parse_chord_symbol
from .errors import MusicEngineError
from .interval import Interval, interval_between, invert, parse_interval, transpose
from .key import key_from_signature, key_signature, relative_major, relative_minor
from .pitch import Note, note_from_midi, parse_note
from .roman import diatonic_chords, roman_numeral
from .scale import build_scale

__version__ = "0.2.0-dev"
__all__ = [
    "ChordSymbol", "Interval", "MusicEngineError", "Note",
    "build_chord", "build_scale", "chord_tones", "diatonic_chords", "identify_chord",
    "interval_between", "invert", "key_from_signature", "key_signature", "note_from_midi",
    "parse_chord_symbol", "parse_interval", "parse_note", "relative_major", "relative_minor",
    "roman_numeral", "transpose",
]
