"""ADR-030 bước 2: YIN và đặc trưng cho model nhận diện nốt. Bản TypeScript giống hệt:
frontend/src/audio/pitch/yin.ts và features.ts (test Vitest so khớp số với file mẫu do script này xuất).

Đặc trưng = 2 "bức ảnh" nhỏ của một khung âm thanh 2048 mẫu:
  1. Đường YIN d'(τ) đọc tại 181 cao độ cách nhau 1/3 nửa cung (MIDI 36 → 96). Có cao độ f thì d'(sr/f) gần 0.
     YIN chỉ lấy "đáy đầu tiên dưới ngưỡng", hay chọn nhầm đáy ở quãng tám; model nhìn CẢ đường cong để chọn.
  2. Phổ biên độ (FFT) gom theo nửa cung MIDI 36 → 108 (73 ô), log rồi chuẩn hóa: cho biết họa âm nào mạnh.
"""

from __future__ import annotations

import numpy as np

FRAME = 2048
GRID_LO, GRID_HI, GRID_STEP = 36.0, 96.0, 1 / 3  # lưới cao độ cho đường YIN
SPEC_LO, SPEC_HI = 36, 108                       # ô phổ theo nửa cung
N_GRID = int(round((GRID_HI - GRID_LO) / GRID_STEP)) + 1  # 181
N_SPEC = SPEC_HI - SPEC_LO + 1                            # 73
N_FEATURES = N_GRID + N_SPEC                              # 254
YIN_MIN_HZ, YIN_MAX_HZ, YIN_THRESHOLD, YIN_MIN_CLARITY = 70.0, 1500.0, 0.15, 0.8
SILENCE_RMS = 0.005


def midi_to_hz(m):
    return 440.0 * 2.0 ** ((np.asarray(m, dtype=np.float64) - 69.0) / 12.0)


def rms(frame: np.ndarray) -> float:
    return float(np.sqrt(np.mean(frame.astype(np.float64) ** 2)))


def cmnd(frame: np.ndarray, tau_max: int) -> np.ndarray:
    """d'(τ) cho τ = 0..tau_max+1, cửa sổ w = FRAME/2 (giống yin.ts)."""
    x = frame.astype(np.float64)
    w = len(x) // 2
    head = x[:w]
    d = np.empty(tau_max + 2)
    d[0] = 0.0
    for tau in range(1, tau_max + 2):
        diff = head - x[tau:tau + w]
        d[tau] = diff @ diff
    out = np.ones_like(d)
    run = np.cumsum(d[1:])
    with np.errstate(divide="ignore", invalid="ignore"):
        out[1:] = np.where(run > 0, d[1:] * np.arange(1, tau_max + 2) / run, 1.0)
    return out


def yin(frame: np.ndarray, sr: float) -> tuple[float, float] | None:
    """Đúng thuật toán của yin.ts: trả (hz, clarity) hoặc None."""
    w = len(frame) // 2
    tau_min = max(2, int(np.floor(sr / YIN_MAX_HZ)))
    tau_max = min(w - 1, int(np.ceil(sr / YIN_MIN_HZ)))
    c = cmnd(frame, tau_max)
    below = np.nonzero(c[tau_min:tau_max + 1] < YIN_THRESHOLD)[0]
    if len(below) == 0:
        return None
    t = tau_min + int(below[0])
    while t + 1 <= tau_max and c[t + 1] < c[t]:
        t += 1
    a, b, cc = c[t - 1], c[t], c[t + 1]
    den = a - 2 * b + cc
    shift = (a - cc) / (2 * den) if den > 0 else 0.0
    better = t + max(-1.0, min(1.0, shift))
    return sr / better, max(0.0, min(1.0, 1 - b))


def yin_hz(frame: np.ndarray, sr: float) -> float | None:
    """Bộ nhận diện YIN như trên trình duyệt: im lặng hoặc độ rõ < 0,8 thì không trả lời."""
    if rms(frame) < SILENCE_RMS:
        return None
    r = yin(frame, sr)
    return r[0] if r and r[1] >= YIN_MIN_CLARITY else None


def grid_midis() -> np.ndarray:
    return GRID_LO + GRID_STEP * np.arange(N_GRID)


def features(frame: np.ndarray, sr: float) -> tuple[np.ndarray, np.ndarray]:
    """Trả (vector 254 đặc trưng, đường d' đầy đủ để tinh chỉnh Hz sau khi model chọn nốt)."""
    x = frame.astype(np.float64)
    taus = sr / midi_to_hz(grid_midis())
    tau_max = int(np.ceil(taus.max())) + 1
    c = cmnd(x, tau_max)
    lo = np.floor(taus).astype(int)
    frac = taus - lo
    curve = c[lo] * (1 - frac) + c[lo + 1] * frac
    # Phổ: cửa sổ Hann, |FFT|, mỗi ô nửa cung lấy giá trị lớn nhất trong khoảng ±0,5 nửa cung.
    n = len(x)
    hann = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(n) / n)
    mag = np.abs(np.fft.rfft(x * hann))
    bin_hz = sr / n
    spec = np.empty(N_SPEC)
    for i, m in enumerate(range(SPEC_LO, SPEC_HI + 1)):
        lo_b = int(np.floor(midi_to_hz(m - 0.5) / bin_hz))
        hi_b = int(np.ceil(midi_to_hz(m + 0.5) / bin_hz))
        spec[i] = mag[lo_b:hi_b + 1].max()
    spec = np.log1p(spec)
    spec = spec / (spec.max() + 1e-9)
    return np.concatenate([np.clip(curve, 0, 2), spec]), c


def refine_hz(c: np.ndarray, sr: float, midi: int) -> float:
    """Model chọn nốt (nửa cung); Hz chính xác lấy ở đáy d' trong khoảng ±0,5 nửa cung quanh nốt đó."""
    t_lo = int(np.floor(sr / midi_to_hz(midi + 0.5)))
    t_hi = min(len(c) - 2, int(np.ceil(sr / midi_to_hz(midi - 0.5))))
    t = t_lo + int(np.argmin(c[t_lo:t_hi + 1]))
    t = max(1, t)
    a, b, cc = c[t - 1], c[t], c[t + 1]
    den = a - 2 * b + cc
    shift = (a - cc) / (2 * den) if den > 0 else 0.0
    hz = sr / (t + max(-1.0, min(1.0, shift)))
    # Ở nốt cao τ nhỏ nên đáy có thể rơi sát biên; giữ Hz trong nốt model đã chọn để Engine đặt đúng tên đó.
    return float(np.clip(hz, midi_to_hz(midi - 0.49), midi_to_hz(midi + 0.49)))
