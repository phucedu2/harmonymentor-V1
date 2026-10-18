"""Trường độ, nhịp 4/4 và chấm bài gõ nhịp.

Claim:
- MUS-RHY-001     Tròn = 2 trắng, trắng = 2 đen, đen = 2 móc đơn, móc đơn = 2 móc kép;
                  chấm dôi thêm một nửa giá trị; dấu nối cộng trường độ (OMT Notating Rhythm). 1 nguồn.
- MUS-METER-002   Số trên = số phách, số dưới = giá trị một phách (F tr. 68–69).
- SRS 4.4.1/4.9   MVP chỉ nhịp 4/4; gõ nhịp lệch tối đa ±80 ms.

Đơn vị thời gian nội bộ là PHÁCH (nốt đen = 1 phách trong 4/4), không phải giây.
Giây chỉ tính khi biết tempo (BPM).
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

from .errors import InvalidRhythm, NotSupportedInMvp

NOTE_VALUES: dict[str, Fraction] = {
    "whole": Fraction(4),
    "half": Fraction(2),
    "quarter": Fraction(1),
    "eighth": Fraction(1, 2),
    "sixteenth": Fraction(1, 4),
}
SUPPORTED_METERS = {"4/4": 4}
DEFAULT_TOLERANCE_MS = 80


def duration_beats(value: str, dots: int = 0) -> Fraction:
    """Trường độ tính bằng phách (nốt đen = 1). Chỉ hỗ trợ 0 hoặc 1 chấm dôi (nguồn chỉ nói chấm đơn)."""
    if value not in NOTE_VALUES:
        raise InvalidRhythm(f"Giá trị nốt không hỗ trợ: {value!r}", supported=list(NOTE_VALUES))
    if dots not in (0, 1):
        raise InvalidRhythm("Chỉ hỗ trợ một chấm dôi", dots=dots)
    base = NOTE_VALUES[value]
    return base * Fraction(3, 2) if dots else base


def tied_beats(*durations: tuple[str, int]) -> Fraction:
    """Dấu nối: cộng trường độ các nốt cùng cao độ, chỉ đánh nốt đầu."""
    return sum((duration_beats(v, d) for v, d in durations), Fraction(0))


def measure_capacity(meter: str = "4/4") -> int:
    if meter not in SUPPORTED_METERS:
        raise NotSupportedInMvp("MVP chỉ hỗ trợ nhịp 4/4 (SRS)", meter=meter)
    return SUPPORTED_METERS[meter]


def check_measure(durations: list[tuple[str, int]], meter: str = "4/4") -> dict:
    """Tổng trường độ một ô nhịp so với số phách cho phép."""
    total = sum((duration_beats(v, d) for v, d in durations), Fraction(0))
    capacity = measure_capacity(meter)
    return {"total_beats": float(total), "capacity": capacity,
            "status": "ok" if total == capacity else ("under" if total < capacity else "over")}


def beats_to_seconds(beats: float | Fraction, bpm: float) -> float:
    beats_value = float(beats)
    if not math.isfinite(bpm) or bpm <= 0:
        raise InvalidRhythm("Tempo phải là số hữu hạn > 0", bpm=bpm)
    if not math.isfinite(beats_value):
        raise InvalidRhythm("Số phách phải là số hữu hạn", beats=beats_value)
    return beats_value * 60.0 / bpm


@dataclass
class TapResult:
    code: str                 # "OK" | "EARLY_ONSET" | "LATE_ONSET" | "MISSED_BEAT" | "EXTRA_TAP"
    expected_beat: float | None
    tap_seconds: float | None
    deviation_ms: float | None


def grade_taps(expected_beats: list[float], taps_seconds: list[float], bpm: float,
               tolerance_ms: float = DEFAULT_TOLERANCE_MS, start_seconds: float = 0.0) -> dict:
    """Chấm bài tap_rhythm (SRS 4.9): mỗi lần gõ lệch trong ±tolerance; không thiếu, không thừa.

    Ghép mỗi phách cần gõ với lần gõ gần nhất chưa dùng, trong cửa sổ bằng một nửa khoảng cách
    ngắn nhất giữa hai phách liền nhau (tối đa 250 ms).
    `EXTRA_TAP` là mã đề xuất thêm, chưa có trong bảng mã lỗi SRS 4.5.
    """
    if not expected_beats:
        raise InvalidRhythm("Mẫu nhịp cần ít nhất một phách để chấm")
    if not math.isfinite(bpm) or bpm <= 0:
        raise InvalidRhythm("Tempo phải là số hữu hạn > 0", bpm=bpm)
    if not math.isfinite(tolerance_ms) or tolerance_ms <= 0:
        raise InvalidRhythm("Dung sai phải là số hữu hạn > 0 ms", tolerance_ms=tolerance_ms)
    if not math.isfinite(start_seconds):
        raise InvalidRhythm("Thời điểm bắt đầu phải là số hữu hạn", start_seconds=start_seconds)
    if any(not math.isfinite(float(b)) or float(b) < 0 for b in expected_beats):
        raise InvalidRhythm("Các phách kỳ vọng phải là số hữu hạn >= 0", expected_beats=expected_beats)
    if any(b <= a for a, b in zip(expected_beats, expected_beats[1:])):
        raise InvalidRhythm("Các phách kỳ vọng phải tăng nghiêm ngặt", expected_beats=expected_beats)
    if any(not math.isfinite(float(t)) for t in taps_seconds):
        raise InvalidRhythm("Thời điểm gõ phải là số hữu hạn", taps_seconds=taps_seconds)

    expected_s = [start_seconds + beats_to_seconds(b, bpm) for b in expected_beats]
    gaps = [b - a for a, b in zip(expected_s, expected_s[1:]) if b > a]
    window = min([0.25] + [g / 2 for g in gaps])
    used = [False] * len(taps_seconds)
    results: list[TapResult] = []
    for beat, t_exp in zip(expected_beats, expected_s):
        best, best_dev = None, None
        for i, t in enumerate(taps_seconds):
            if used[i]:
                continue
            dev = t - t_exp
            if abs(dev) <= window and (best_dev is None or abs(dev) < abs(best_dev)):
                best, best_dev = i, dev
        if best is None:
            results.append(TapResult("MISSED_BEAT", beat, None, None))
            continue
        used[best] = True
        dev_ms = best_dev * 1000
        code = "OK" if abs(dev_ms) <= tolerance_ms else ("EARLY_ONSET" if dev_ms < 0 else "LATE_ONSET")
        results.append(TapResult(code, beat, taps_seconds[best], round(dev_ms, 1)))
    for i, t in enumerate(taps_seconds):
        if not used[i]:
            results.append(TapResult("EXTRA_TAP", None, t, None))
    correct = all(r.code == "OK" for r in results)
    return {"correct": correct, "tolerance_ms": tolerance_ms, "events": [r.__dict__ for r in results]}
