"""Mẫu nền (FR-17): trống, bass và nhịp đánh hợp âm cho 4 phong cách, tính theo phách trong ô nhịp 4/4.

Vì sao để ở backend: dự án lưu `drum_events` (tài liệu 04 Bảng 8), nên máy chủ phải biết mẫu để trải ra sự kiện.
Frontend chỉ đọc mẫu qua API rồi phát bằng Tone.js; không tự bịa mẫu.
Bass chỉ nói "nốt gốc"/"nốt năm" của hợp âm; tên nốt thật lấy từ Music Engine lúc phát.
Mẫu do Claude soạn theo cách chơi phổ biến, chưa có nguồn đối chiếu; nhóm nghe thử rồi chỉnh (ADR-010).
"""

from __future__ import annotations

BEATS_PER_BAR = 4
DRUMS = ("kick", "snare", "hat")


def _hats(velocity: int, step: float = 0.5) -> list[dict]:
    count = int(BEATS_PER_BAR / step)
    return [{"drum": "hat", "beat": i * step, "velocity": velocity if i % 2 == 0 else velocity - 15} for i in range(count)]


STYLES: dict[str, dict] = {
    "pop": {
        "label": "Pop",
        "description": "Trống chắc, hợp âm đánh hai lần mỗi ô. Hợp vòng quen tai.",
        "default_bpm": 100,
        "swing": 0.0,
        "drums": [{"drum": "kick", "beat": 0, "velocity": 110}, {"drum": "kick", "beat": 2.5, "velocity": 100},
                  {"drum": "snare", "beat": 1, "velocity": 95}, {"drum": "snare", "beat": 3, "velocity": 95},
                  *_hats(70)],
        "bass": [{"beat": 0, "beats": 1.5, "tone": "root"}, {"beat": 1.5, "beats": 0.5, "tone": "root"},
                 {"beat": 2, "beats": 2, "tone": "fifth"}],
        "chords": [{"beat": 0, "beats": 2}, {"beat": 2, "beats": 2}],
    },
    "ballad": {
        "label": "Ballad",
        "description": "Chậm, hợp âm ngân cả ô, trống nhẹ nửa nhịp.",
        "default_bpm": 72,
        "swing": 0.0,
        "drums": [{"drum": "kick", "beat": 0, "velocity": 95}, {"drum": "snare", "beat": 2, "velocity": 80},
                  *_hats(55, step=1.0)],
        "bass": [{"beat": 0, "beats": 2, "tone": "root"}, {"beat": 2, "beats": 2, "tone": "fifth"}],
        "chords": [{"beat": 0, "beats": 4}],
    },
    "bossa": {
        "label": "Bossa nova",
        "description": "Bass gốc–năm đều, hợp âm nảy lệch phách kiểu Brazil.",
        "default_bpm": 130,
        "swing": 0.0,
        "drums": [{"drum": "kick", "beat": 0, "velocity": 90}, {"drum": "kick", "beat": 1.5, "velocity": 80},
                  {"drum": "kick", "beat": 2, "velocity": 90}, {"drum": "kick", "beat": 3.5, "velocity": 80},
                  {"drum": "snare", "beat": 1, "velocity": 70}, {"drum": "snare", "beat": 2.5, "velocity": 70},
                  *_hats(60)],
        "bass": [{"beat": 0, "beats": 1.5, "tone": "root"}, {"beat": 1.5, "beats": 0.5, "tone": "fifth"},
                 {"beat": 2, "beats": 1.5, "tone": "fifth"}, {"beat": 3.5, "beats": 0.5, "tone": "root"}],
        "chords": [{"beat": 0, "beats": 1.5}, {"beat": 1.5, "beats": 2.5}],
    },
    "lofi": {
        "label": "Lo-fi",
        "description": "Nhịp lắc (swing), trống mềm, hợp âm ngân dài.",
        "default_bpm": 80,
        "swing": 0.35,
        "drums": [{"drum": "kick", "beat": 0, "velocity": 100}, {"drum": "kick", "beat": 2.5, "velocity": 90},
                  {"drum": "snare", "beat": 1, "velocity": 75}, {"drum": "snare", "beat": 3, "velocity": 75},
                  *_hats(50)],
        "bass": [{"beat": 0, "beats": 3, "tone": "root"}, {"beat": 3, "beats": 1, "tone": "fifth"}],
        "chords": [{"beat": 0, "beats": 4}],
    },
}


def drum_events(style: str, bars: int) -> list[dict]:
    """Trải mẫu trống ra cả dự án: start_beat tính từ đầu bài (ô 1 phách 0)."""
    pattern = STYLES[style]["drums"]
    return [{"drum": hit["drum"], "start_beat": bar * BEATS_PER_BAR + hit["beat"], "velocity": hit["velocity"]}
            for bar in range(bars) for hit in pattern]
