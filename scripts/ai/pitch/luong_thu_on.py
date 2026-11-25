"""Dựng các "luồng thu thử" có tạp âm để đo ĐÚNG đường xử lý chạy trên trình duyệt (Phúc 1D 2B 4A, 25/11/2026).

Mỗi luồng = 10 nốt đàn (piano/epiano/guitar/upright) cách nhau khoảng lặng, trộn tạp âm ở mức SNR cho trước.
SNR tính theo RMS của đoạn đang ngân nốt so với RMS tạp âm. Nốt lấy từ các bản thu "giữ riêng" (crc32(file) % 5 == 0):
cả lần train cũ lẫn mới đều KHÔNG được thấy các bản này (train.py --giu-rieng), nên so trước/sau là công bằng.
Còn có luồng "loa": piano ảo phát qua loa laptop rồi vào micro, và luồng chỉ có tạp âm để đếm nốt ma.

    python scripts/ai/pitch/luong_thu_on.py --out /tmp/luong_on
Đầu ra: <out>/chi_muc.json + các file .f32 (float32 little-endian, 48 kHz, 1 kênh).
"""

from __future__ import annotations

import argparse
import json
import sys
import zlib
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from du_lieu import MIDI_HI, MIDI_LO, SAMPLES, decode  # noqa: E402
from on_nhieu import NOISE_TYPES, SR, loa_laptop, make_noise, rms, scale_to  # noqa: E402

PLAY = ["piano", "epiano", "guitar", "upright"]
SNRS = [20, 12, 6, 0]
SIGNAL_RMS = 0.05            # ≈ −26 dBFS: mức thường gặp khi đàn cách micro laptop vài chục cm
N_NOTES, NOTE_S, GAP_S = 10, 1.0, 0.5
SEEDS = 3


def giu_rieng(file: str) -> bool:
    return zlib.crc32(file.encode()) % 5 == 0


def zones(manifest, name: str, held: bool):
    return [z for z in manifest["instruments"][name]["pieces"]["notes"]
            if z["midi"] is not None and MIDI_LO <= z["midi"] <= MIDI_HI and giu_rieng(z["file"]) == held]


def note_stream(rng, manifest, cache):
    """Trả (tín hiệu, mặt nạ đang ngân, danh sách nốt thật)."""
    pool = [(n, z) for n in PLAY for z in zones(manifest, n, True)]
    total = int(SR * (0.4 + N_NOTES * (NOTE_S + GAP_S)))
    sig = np.zeros(total)
    mask = np.zeros(total, dtype=bool)
    truth, pos = [], int(0.4 * SR)
    for _ in range(N_NOTES):
        name, z = pool[int(rng.integers(0, len(pool)))]
        if z["file"] not in cache:
            cache[z["file"]] = decode(SAMPLES / z["file"])
        a = cache[z["file"]][: int(NOTE_S * SR)].copy()
        fade = int(0.08 * SR)
        a[-fade:] *= np.linspace(1, 0, fade)
        sig[pos:pos + len(a)] += a
        mask[pos:pos + len(a)] = True
        truth.append({"t0": pos / SR, "t1": (pos + len(a)) / SR, "midi": int(z["midi"]), "inst": name})
        pos += int((NOTE_S + GAP_S) * SR)
    return sig * (SIGNAL_RMS / rms(sig[mask])), mask, truth


def background_pool(manifest, cache):
    pool = []
    for n in ["piano", "guitar", "epiano", "clav", "cello"]:
        for z in zones(manifest, n, False)[:12]:
            if z["file"] not in cache:
                cache[z["file"]] = decode(SAMPLES / z["file"])
            pool.append(cache[z["file"]])
    return pool


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/luong_on")
    ap.add_argument("--seed", type=int, default=2026)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((SAMPLES / "manifest.json").read_text())
    cache: dict = {}
    pool = background_pool(manifest, cache)
    rng = np.random.default_rng(a.seed)
    index = []

    def save(name, x, meta):
        (out / f"{name}.f32").write_bytes(np.asarray(x, dtype="<f4").tobytes())
        index.append({"name": name, "file": f"{name}.f32", "sr": SR, **meta})

    for seed in range(SEEDS):
        sig, mask, truth = note_stream(rng, manifest, cache)
        n = len(sig)
        save(f"sach_{seed}", sig, {"kind": "sach", "snr": None, "notes": truth})
        for kind in NOISE_TYPES:
            for snr in SNRS:
                noise = scale_to(make_noise(kind, n, rng, pool), SIGNAL_RMS / 10 ** (snr / 20))
                save(f"{kind}_{snr}_{seed}", sig + noise, {"kind": kind, "snr": snr, "notes": truth})
        # Piano ảo phát qua loa laptop: tín hiệu đổi màu + vang phòng, đo lại mức sau khi qua loa.
        via = loa_laptop(sig, rng)
        via *= SIGNAL_RMS / rms(via[mask])
        save(f"loa_sach_{seed}", via, {"kind": "loa", "snr": None, "notes": truth})
        noise = scale_to(make_noise("quat", n, rng, pool), SIGNAL_RMS / 10 ** (12 / 20))
        save(f"loa_quat12_{seed}", via + noise, {"kind": "loa+quat", "snr": 12, "notes": truth})
    # Chỉ có tạp âm (không ai đàn): mọi nốt máy báo ra là "nốt ma".
    for kind in NOISE_TYPES:
        for snr in (6, 0):   # mức tạp âm bằng 1/2 và 1/1 mức đàn bình thường
            noise = scale_to(make_noise(kind, int(30 * SR), rng, pool), SIGNAL_RMS / 10 ** (snr / 20))
            save(f"chi_on_{kind}_{snr}", noise, {"kind": kind, "snr": snr, "notes": []})
    (out / "chi_muc.json").write_text(json.dumps(index))
    print(f"{len(index)} luồng ghi vào {out}")


if __name__ == "__main__":
    main()
