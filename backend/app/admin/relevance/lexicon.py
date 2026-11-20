"""Từ vựng nhạc lý và hòa âm (Việt + Anh, không dấu, chữ thường) cho điểm liên quan v1.

Chọn từ ĐẶC TRƯNG của nhạc lý. Cố ý bỏ các từ chung như "nhạc", "bài hát", "nốt" riêng lẻ, "note", "key": chúng xuất hiện cả
trong tin tức, lời bài hát, công thức nấu ăn ("ghi chú", "nốt hương")."""

from __future__ import annotations

import re

from ...ai.tutor.bm25 import strip_accents

VI_TERMS = [
    "nhac ly", "hoa am", "hop am", "am giai", "nua cung", "cung nguyen", "giong truong", "giong thu", "chu am", "bac am",
    "khoa nhac", "khuong nhac", "dau thang", "dau giang", "dau hoa", "tiet tau", "quang ba", "quang nam", "quang bay",
    "quang tam", "chuyen giong", "dao hop am", "cao do", "hop am bay", "hop am ba", "vong hop am", "tien trinh hop am",
    "ky hieu hop am", "so la ma", "chuc nang hoa am", "bac chu", "bac thuong", "dieu tinh", "voicing", "quang truong",
    "quang thu", "quang giam", "quang tang", "quang dung", "phach manh", "nhip phach",
]
EN_TERMS = [
    "music theory", "harmony", "chord", "chords", "interval", "intervals", "scale", "scales", "semitone", "whole step",
    "half step", "tonic", "dominant", "subdominant", "supertonic", "mediant", "submediant", "leading tone", "key signature",
    "triad", "triads", "seventh chord", "arpeggio", "cadence", "progression", "voicing", "voice leading", "melody",
    "pitch", "octave", "accidental", "sharp", "flat", "major", "minor", "diminished", "augmented", "mode", "modal",
    "secondary dominant", "roman numeral", "time signature", "rhythm", "tempo", "staff", "clef", "tonality", "modulation",
    "transposition", "enharmonic", "counterpoint", "chord progression", "guide tone", "ii-v-i", "tritone",
]
# Hợp âm viết bằng ký hiệu: Cmaj7, Dm7, G7, F#m7b5, Bb, Am...
_CHORD = re.compile(r"\b[A-G][#b]?(?:maj7|maj9|maj|m7b5|m7|m9|m6|m|dim7|dim|aug|sus[24]|add9|13|11|9|7|6)\b")
_ROMAN_PROG = re.compile(r"\b(?:i{1,3}|iv|v|vi{1,2}|vii)(?:7|maj7)?(?:\s*[-–→>]\s*(?:i{1,3}|iv|v|vi{1,2}|vii)(?:7|maj7)?){1,}\b", re.I)

_ALL_TERMS = sorted(set(VI_TERMS + EN_TERMS), key=len, reverse=True)
_ALL_TERMS_RE = re.compile(r"\b(?:" + "|".join(re.escape(t) for t in _ALL_TERMS) + r")\b")
_WORD = re.compile(r"\w+", re.UNICODE)


def count_hits(text: str) -> tuple[int, int]:
    """Trả (số lần gặp từ khóa nhạc lý, số từ). Ký hiệu hợp âm và vòng số La Mã tính là từ khóa."""
    plain = strip_accents(text.lower())
    words = len(_WORD.findall(plain))
    hits = len(_ALL_TERMS_RE.findall(plain))
    hits += len(_CHORD.findall(text))            # giữ nguyên hoa/thường: "Am7" khác "am"
    hits += len(_ROMAN_PROG.findall(text)) * 2
    return hits, words
