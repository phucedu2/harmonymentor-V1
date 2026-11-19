"""ADR-030 bước 2: dựng bộ dữ liệu khung âm thanh có nhãn nốt (MIDI).

Nguồn (đều có sẵn trong repo, ghi công ở frontend/public/samples/CREDITS.md):
  - Mẫu THU THẬT: piano Salamander (CC BY 3.0), epiano, clav, guitar, guitar_mute, bass, upright, cello (CC0).
    Nhãn = số MIDI ghi trong manifest (cao độ đã đo lại khi dựng mẫu).
  - Khung KHÔNG CÓ NỐT (nhãn 0): ù điện, nhiễu trắng/hồng, để model biết im lặng thay vì đoán bừa.
  - Giọng hát TỔNG HỢP (không có bản thu giọng CC0 trong repo): xung thanh môn + 3 formant nguyên âm a/o/i + rung giọng.
Tăng cường dữ liệu (data augmentation): dịch cao độ ±1 nửa cung bằng lấy mẫu lại, đổi âm lượng, và 5 điều kiện
thu (CONDITIONS) mô phỏng micro thật. Mỗi khung mang "nhóm" = bản thu gốc, để lúc chia train/test mọi bản biến đổi
của cùng một bản thu nằm cùng một phía (nếu không, model được "xem trước đề").

    python scripts/ai/pitch/du_lieu.py --out /tmp/pitch_data.npz
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dac_trung import FRAME, SILENCE_RMS, features, rms  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SAMPLES = ROOT / "frontend" / "public" / "samples"
SR = 48000
MIDI_LO, MIDI_HI = 40, 88  # E2 (dây trầm guitar) → E6
INSTRUMENTS = ["piano", "epiano", "clav", "guitar", "guitar_mute", "bass", "upright", "cello"]
OFFSETS_S = [0.06, 0.15, 0.3, 0.5, 0.8]  # vị trí lấy khung sau lúc bấm nốt
# Điều kiện thu: sạch, nhiễu trắng 15/5 dB, "micro laptop" (cắt trầm dưới 250 Hz + nhiễu hồng 15 dB),
# "ồn điện" (tiếng ù 50 Hz và họa âm). YIN dễ sai nhất khi mất âm gốc hoặc nhiễu mạnh.
CONDITIONS = ["sach", "nhieu15", "nhieu5", "micro_laptop", "u_dien"]


def decode(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def shift(audio: np.ndarray, semis: int) -> np.ndarray:
    """Dịch cao độ bằng lấy mẫu lại (phát nhanh hơn 2^(s/12) lần), như đổi tốc độ băng."""
    if semis == 0:
        return audio
    rate = 2 ** (semis / 12)
    idx = np.arange(0, len(audio) - 1, rate)
    return np.interp(idx, np.arange(len(audio)), audio)


def voice(midi: int, vowel: str, rng: np.random.Generator, seconds: float = 1.0) -> np.ndarray:
    """Giọng hát tổng hợp: răng cưa có rung giọng 5,5 Hz ±20 cent, lọc qua 3 formant của nguyên âm."""
    formants = {"a": (800, 1150, 2900), "o": (450, 800, 2830), "i": (270, 2140, 2950)}[vowel]
    n = int(SR * seconds)
    t = np.arange(n) / SR
    f0 = 440 * 2 ** ((midi - 69) / 12) * 2 ** (0.2 / 12 * np.sin(2 * np.pi * 5.5 * t + rng.uniform(0, 6)))
    phase = 2 * np.pi * np.cumsum(f0) / SR
    k_max = int(8000 / f0.max())
    sig = np.zeros(n)
    for k in range(1, k_max + 1):
        fk = k * f0.mean()
        gain = sum(1 / (1 + ((fk - f) / 90) ** 2) for f in formants) / k
        sig += gain * np.sin(k * phase)
    env = np.minimum(1, t / 0.05)
    return 0.3 * sig / np.abs(sig).max() * env


def pink(n: int, rng: np.random.Generator) -> np.ndarray:
    spec = np.fft.rfft(rng.normal(size=n))
    spec[1:] /= np.sqrt(np.arange(1, len(spec)))
    x = np.fft.irfft(spec, n)
    return x / (rms(x) + 1e-12)


def highpass(x: np.ndarray, hz: float) -> np.ndarray:
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    spec *= 1 / np.sqrt(1 + (hz / np.maximum(f, 1e-6)) ** 8)  # bậc 4, giống loa/micro nhỏ không thu được trầm
    return np.fft.irfft(spec, len(x))


def degrade(fr: np.ndarray, cond: str, rng: np.random.Generator) -> np.ndarray:
    x = fr * rng.uniform(0.3, 1.5)
    if cond == "nhieu15":
        x = x + rng.normal(0, rms(x) / 10 ** (15 / 20), FRAME)
    elif cond == "nhieu5":
        x = x + rng.normal(0, rms(x) / 10 ** (5 / 20), FRAME)
    elif cond == "micro_laptop":
        x = highpass(x, 250)
        x = x + pink(FRAME, rng) * rms(x) / 10 ** (15 / 20)
    elif cond == "u_dien":
        t = np.arange(FRAME) / SR
        ph = rng.uniform(0, 6)
        hum = sum(np.sin(2 * np.pi * 50 * k * t + ph * k) / k for k in range(1, 13))
        x = x + hum / rms(hum) * rms(x) * rng.uniform(0.3, 2.0)
    return x


def frames_of(audio: np.ndarray, rng: np.random.Generator):
    for off in OFFSETS_S:
        start = int(off * SR)
        if start + FRAME > len(audio):
            break
        fr = audio[start:start + FRAME]
        if rms(fr) < SILENCE_RMS * 2:
            continue
        for cond in CONDITIONS:
            yield degrade(fr, cond, rng).astype(np.float32), cond


NONE = 0  # nhãn "không có nốt": tiếng ù, tiếng ồn phòng. Model phải học im lặng, không đoán bừa.


def background(rng: np.random.Generator) -> np.ndarray:
    """Khung không có nốt nào: ù điện 50/60 Hz, nhiễu trắng/hồng, hoặc trộn, ở nhiều mức to nhỏ."""
    t = np.arange(FRAME) / SR
    kind = rng.integers(0, 4)
    base = rng.choice([50.0, 60.0])
    hum = sum(np.sin(2 * np.pi * base * k * t + rng.uniform(0, 6)) / k for k in range(1, 13))
    hum = hum / rms(hum)
    if kind == 0:
        x = hum
    elif kind == 1:
        x = rng.normal(size=FRAME)
    elif kind == 2:
        x = pink(FRAME, rng)
    else:
        x = hum + pink(FRAME, rng) * rng.uniform(0.3, 1.5)
    return x / rms(x) * 10 ** rng.uniform(-2.2, -0.7)  # RMS ≈ 0,006 → 0,2


def build(seed: int = 7):
    rng = np.random.default_rng(seed)
    manifest = json.loads((SAMPLES / "manifest.json").read_text())
    X, y, groups, inst, raw, conds = [], [], [], [], [], []
    for name in INSTRUMENTS:
        zones = [z for z in manifest["instruments"][name]["pieces"]["notes"] if z["midi"] is not None]
        for z in zones:
            audio = decode(SAMPLES / z["file"])
            for s in (-1, 0, 1):
                midi = z["midi"] + s
                if not MIDI_LO <= midi <= MIDI_HI:
                    continue
                for fr, cond in frames_of(shift(audio, s), rng):
                    X.append(features(fr, SR)[0]); y.append(midi); groups.append(f"{name}/{z['file']}"); inst.append(name)
                    raw.append(fr); conds.append(cond)
    for midi in range(MIDI_LO, 80):  # giọng người thường không lên quá ~G5
        for vowel in "aoi":
            audio = voice(midi, vowel, rng)
            for fr, cond in frames_of(audio, rng):
                X.append(features(fr, SR)[0]); y.append(midi); groups.append(f"voice/{midi}-{vowel}"); inst.append("voice")
                raw.append(fr); conds.append(cond)
    for i in range(3000):
        fr = background(rng).astype(np.float32)
        X.append(features(fr, SR)[0]); y.append(NONE); groups.append(f"nen/{i // 10}"); inst.append("nen")
        raw.append(fr); conds.append("khong_not")
    return (np.array(X, dtype=np.float32), np.array(y), np.array(groups), np.array(inst), np.array(raw, dtype=np.float32),
            np.array(conds))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/pitch_data.npz")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    X, y, g, inst, raw, cond = build(a.seed)
    np.savez_compressed(a.out, X=X, y=y, groups=g, inst=inst, raw=raw, cond=cond)
    print(f"{len(y)} khung, {len(set(g))} bản thu, nhạc cụ: " + ", ".join(f"{k}={int((inst == k).sum())}" for k in sorted(set(inst))))
