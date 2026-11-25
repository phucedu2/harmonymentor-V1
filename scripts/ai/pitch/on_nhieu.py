"""Tạo tạp âm tổng hợp để train và đo khả năng nghe nốt khi phòng ồn (Phúc 1D 2B, 25/11/2026).

Không có bản thu tạp âm thật CC0 trong repo, nên 5 loại tạp âm thường gặp ở phòng học được SINH ra bằng công thức:
  quat        quạt/điều hòa: tiếng ù trầm (nhiễu nâu) + tiếng gió (nhiễu hồng) + họa âm điện 50/60 Hz
  giong_noi   nhiều người nói chuyện/TV: nguyên âm có formant, cao độ trượt 90–250 Hz (trùng dải nốt trầm, khó nhất)
  nhac_nen    nhạc nền: nốt và hợp âm của nhạc cụ khác phát liên tục
  tieng_dong  gõ bàn, đóng cửa, ho: xung ngắn, tắt nhanh
  loa_laptop  piano ảo phát qua loa laptop rồi vào micro: mất trầm, vang phòng (không phải tạp âm cộng thêm mà là đường truyền)
Mọi hàm nhận `rng` để tái lập được, và trả mảng float64 độ dài n (chưa chuẩn hóa mức to nhỏ).
**Giới hạn:** đây là mô phỏng, chưa thay được bản thu phòng thật.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import lfilter

SR = 48000
HPF_HZ, HPF_STAGES = 70.0, 2   # phải khớp frontend/src/audio/pitch/pipeline.ts
NOISE_TYPES = ["quat", "giong_noi", "nhac_nen", "tieng_dong"]
VOWELS = {"a": (800, 1150, 2900), "e": (530, 1840, 2480), "i": (270, 2140, 2950), "o": (450, 800, 2830), "u": (325, 700, 2530)}


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64) ** 2)) + 1e-12)


def scale_to(x: np.ndarray, target_rms: float) -> np.ndarray:
    return x * (target_rms / rms(x))


def _filtered(x: np.ndarray, lo: float | None, hi: float | None) -> np.ndarray:
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    if lo:
        spec *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-6)) ** 4)
    if hi:
        spec *= 1 / np.sqrt(1 + (f / hi) ** 4)
    return np.fft.irfft(spec, len(x))


def pink(n: int, rng: np.random.Generator) -> np.ndarray:
    spec = np.fft.rfft(rng.normal(size=n))
    spec[1:] /= np.sqrt(np.arange(1, len(spec)))
    return np.fft.irfft(spec, n)


def brown(n: int, rng: np.random.Generator) -> np.ndarray:
    spec = np.fft.rfft(rng.normal(size=n))
    spec[1:] /= np.arange(1, len(spec))
    return np.fft.irfft(spec, n)


def hum(n: int, rng: np.random.Generator) -> np.ndarray:
    t = np.arange(n) / SR
    base = rng.choice([50.0, 60.0])
    return sum(np.sin(2 * np.pi * base * k * t + rng.uniform(0, 6)) / k for k in range(1, 13))


def quat(n: int, rng: np.random.Generator) -> np.ndarray:
    """Quạt/điều hòa: ù trầm + gió + (đôi khi) tiếng ù điện; mức của từng phần ngẫu nhiên nên mỗi phòng một khác."""
    x = scale_to(brown(n, rng), 1.0) * rng.uniform(0.5, 1.5) + scale_to(pink(n, rng), 1.0) * rng.uniform(0.2, 1.0)
    if rng.random() < 0.6:
        x = x + scale_to(hum(n, rng), 1.0) * rng.uniform(0.2, 1.2)
    if rng.random() < 0.4:   # quạt có cánh: một âm thuần hơi dao động quanh 100–300 Hz
        t = np.arange(n) / SR
        f = rng.uniform(100, 300)
        x = x + 0.3 * np.sin(2 * np.pi * f * t + 0.5 * np.sin(2 * np.pi * rng.uniform(0.2, 1.5) * t)) * rng.uniform(0.3, 1.0)
    return x


def _talker(n: int, rng: np.random.Generator) -> np.ndarray:
    out = np.zeros(n)
    pos = int(rng.uniform(0, 0.3) * SR)
    f0 = rng.uniform(90, 250)
    while pos < n:
        seg = int(rng.uniform(0.1, 0.32) * SR)
        seg = min(seg, n - pos)
        t = np.arange(seg) / SR
        if rng.random() < 0.8:   # âm hữu thanh: răng cưa có cao độ trượt, lọc qua 3 formant của nguyên âm
            f_end = f0 * rng.uniform(0.8, 1.25)
            f = np.linspace(f0, f_end, seg)
            f0 = float(np.clip(f_end, 85, 260))
            phase = 2 * np.pi * np.cumsum(f) / SR
            formants = VOWELS[rng.choice(list(VOWELS))]
            sig = np.zeros(seg)
            for k in range(1, int(5000 / f.mean()) + 1):
                fk = k * f.mean()
                sig += sum(1 / (1 + ((fk - fm) / 110) ** 2) for fm in formants) / k * np.sin(k * phase)
            env = np.sin(np.pi * np.arange(seg) / seg) ** 0.7
            out[pos:pos + seg] += scale_to(sig, 1.0) * env
        else:                    # âm xát (s, sh): nhiễu cao tần
            out[pos:pos + seg] += _filtered(rng.normal(size=seg), 2500, 9000) * np.sin(np.pi * np.arange(seg) / seg) * 0.3
        pos += seg + int(rng.uniform(0.04, 0.35) * SR)
    return out


def giong_noi(n: int, rng: np.random.Generator) -> np.ndarray:
    """2–4 người nói cùng lúc (tiếng người nói chuyện, TV)."""
    return sum(_talker(n, rng) for _ in range(int(rng.integers(2, 5))))


def nhac_nen(n: int, rng: np.random.Generator, pool: list[np.ndarray]) -> np.ndarray:
    """Nhạc nền: nốt/hợp âm của các nhạc cụ trong `pool` (mỗi mảng là một nốt đã thu) rải liên tục."""
    out = np.zeros(n)
    pos = 0
    while pos < n:
        for _ in range(int(rng.integers(1, 4))):
            note = pool[int(rng.integers(0, len(pool)))]
            seg = note[: int(rng.uniform(0.8, 2.5) * SR)]
            end = min(n, pos + len(seg))
            out[pos:end] += seg[: end - pos] * rng.uniform(0.5, 1.0)
        pos += int(rng.uniform(0.4, 1.6) * SR)
    return out


def tieng_dong(n: int, rng: np.random.Generator) -> np.ndarray:
    """Xung ngắn (gõ bàn, bấm chuột, đóng cửa): nhiễu băng rộng tắt nhanh + tiếng thịch trầm, khoảng 0,3–1,5 giây một lần."""
    out = np.zeros(n)
    pos = int(rng.uniform(0, 0.5) * SR)
    while pos < n:
        ln = min(int(rng.uniform(0.05, 0.35) * SR), n - pos)
        t = np.arange(ln) / SR
        decay = np.exp(-t / rng.uniform(0.01, 0.07))
        burst = _filtered(rng.normal(size=ln), rng.uniform(100, 600), rng.uniform(3000, 12000)) * decay
        thump = np.sin(2 * np.pi * rng.uniform(55, 220) * t) * np.exp(-t / rng.uniform(0.03, 0.12)) * rng.uniform(0, 2)
        out[pos:pos + ln] += (burst + thump * rms(burst)) * rng.uniform(0.4, 1.0)
        pos += ln + int(rng.uniform(0.3, 1.5) * SR)
    return out


def make_noise(kind: str, n: int, rng: np.random.Generator, pool: list[np.ndarray] | None = None) -> np.ndarray:
    if kind == "quat":
        return quat(n, rng)
    if kind == "giong_noi":
        return giong_noi(n, rng)
    if kind == "nhac_nen":
        return nhac_nen(n, rng, pool or [])
    if kind == "tieng_dong":
        return tieng_dong(n, rng)
    raise ValueError(kind)


def loa_laptop(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Âm đi qua loa laptop nhỏ và vang phòng: mất trầm dưới ~200 Hz, hơi gắt, đuôi vang RT60 0,2–0,6 giây."""
    y = _filtered(x, rng.uniform(150, 260), rng.uniform(6000, 11000))
    rt60 = rng.uniform(0.2, 0.6)
    t = np.arange(int(rt60 * SR)) / SR
    ir = rng.normal(size=len(t)) * np.exp(-6.9 * t / rt60)
    ir[0] = 0
    ir = ir / np.abs(ir).sum() * rng.uniform(0.6, 1.4)
    wet = np.convolve(y, ir)[: len(y)]
    return y + wet


def hpf(x: np.ndarray, hz: float = HPF_HZ, stages: int = HPF_STAGES) -> np.ndarray:
    """Lọc trầm Butterworth bậc 2 xếp tầng, cùng công thức RBJ với pipeline.ts (BiquadFilterNode highpass)."""
    w0 = 2 * np.pi * hz / SR
    c, alpha = np.cos(w0), np.sin(w0) / (2 * np.sqrt(0.5))
    a0 = 1 + alpha
    b = np.array([(1 + c) / 2, -(1 + c), (1 + c) / 2]) / a0
    a = np.array([1.0, -2 * c / a0, (1 - alpha) / a0])
    for _ in range(stages):
        x = lfilter(b, a, x)
    return x
