"""Style pack của bộ phối khí (ADR-012 đề xuất): dữ liệu, không phải code, để nhóm đọc và chỉnh như bản nhạc.

Mỗi phong cách một file. Mẫu nhịp viết bằng chuỗi, mỗi ký tự là một ô lưới (16 ô/ô nhịp = nốt móc kép,
12 ô/ô nhịp = móc đơn chia ba cho cảm giác swing hoặc 12/8). Chuỗi dài gấp đôi = mẫu 2 ô nhịp (vd clave bossa).

  Trống/bộ gõ   X mạnh · x thường · o nhẹ · g ghost note · . nghỉ
  Phím          X/x/o đánh khối · R/r rải (arpeggiate) · T/t chỉ 2 nốt trên · = ngân tiếp · . nghỉ
  Tay trái      1 gốc · 5 nốt năm · 8 quãng tám · 3 nốt ba (quãng 10) · 7 nốt bảy · = ngân
  Bass          R gốc · r gốc nhẹ · 5 · 8 · 3 · 7 · A nốt đi vào gốc ô sau · x nốt chết · = ngân
  Guitar        D/d quạt xuống · U/u quạt lên · M quạt tắt tiếng (chicken scratch) · P power chord chặn tiếng ·
                O power chord mở · S/s nhát chặn (3 nốt trên) · 1–5 gảy từng nốt (1 = nốt thấp nhất)

`patterns` theo mức năng lượng {1: [...], 2: [...], 3: [...]}; mỗi mức có 1–4 biến thể, seed chọn biến thể.
Nguồn tham khảo cách chơi của từng phong cách: docs/backing-track/PHONG_CACH.md.
"""
from __future__ import annotations

from importlib import import_module

# Tăng khi đổi luật phối hoặc style pack: dự án lưu số này để biết bản phối đã cập nhật (QĐ 5A).
ARRANGEMENT_VERSION = 1

ORDER = ("pop", "ballad", "bossa", "lofi", "jazz", "rock", "indie", "funk", "rnb")
PACKS: dict[str, dict] = {sid: import_module(f".{sid}", __name__).PACK for sid in ORDER}

DRUM_CODES = {"kick", "snare", "rim", "xstick", "br_snare", "hh_c", "hh_o", "hh_p", "br_hh", "ride", "ride_b",
              "br_ride", "crash", "tom_h", "tom_m", "tom_f", "conga_h", "conga_l", "shaker", "tamb", "tri", "clap"}
INSTRUMENTS = {"keys": {"piano", "epiano", "clav"}, "bass": {"bass", "upright"}, "guitar": {"guitar"}}

_VEL = {"X": 112, "x": 90, "o": 66, "g": 34, "R": 96, "r": 76, "T": 92, "t": 70}


def char_velocity(ch: str) -> int:
    return _VEL.get(ch, 84)


def pattern_for(patterns: dict, level: int, pick: int, bar: int, grid: int):
    """Mẫu cho mức năng lượng (lấy mức gần nhất ≤ level, không có thì mức nhỏ nhất), biến thể theo seed,
    cắt đúng đoạn của ô nhịp `bar` nếu mẫu dài nhiều ô."""
    levels = sorted(patterns)
    usable = [lv for lv in levels if lv <= level] or levels[:1]
    variants = patterns[usable[-1]]
    chosen = variants[pick % len(variants)]
    if isinstance(chosen, str):
        return _segment(chosen, bar, grid)
    return {k: _segment(v, bar, grid) for k, v in chosen.items()}


def _segment(pattern: str, bar: int, grid: int) -> str:
    if not pattern:
        return ""
    n = len(pattern) // grid
    i = bar % n
    return pattern[i * grid:(i + 1) * grid]


def validate(pack: dict) -> list[str]:
    """Kiểm style pack: độ dài mẫu đúng lưới, mã trống ≤ 8 ký tự và có mẫu âm thanh, nhạc cụ hợp lệ."""
    errors: list[str] = []
    grid = pack["grid"]
    lo, hi = pack["bpm_range"]
    if not lo <= pack["default_bpm"] <= hi:
        errors.append("default_bpm ngoài bpm_range")

    def check(name: str, value) -> None:
        if isinstance(value, dict):
            for k, v in value.items():
                if name.startswith("drums") and k not in DRUM_CODES:
                    errors.append(f"{name}: mã trống lạ {k!r}")
                if len(k) > 8:
                    errors.append(f"{name}: mã {k!r} dài quá 8 ký tự (cột drum_events.drum)")
                check(f"{name}.{k}", v)
        elif isinstance(value, str) and value and len(value) % grid:
            errors.append(f"{name}: dài {len(value)} không chia hết cho lưới {grid}")

    for part in ("keys", "bass", "guitar"):
        if pack[part]["instrument"] not in INSTRUMENTS[part]:
            errors.append(f"{part}: nhạc cụ {pack[part]['instrument']!r} không có")
        for lv, variants in pack[part].get("patterns", {}).items():
            for v in variants:
                check(f"{part}[{lv}]", v)
        for lv, variants in pack[part].get("lh", {}).items():
            for v in variants:
                check(f"{part}.lh[{lv}]", v)
    for lv, variants in pack["drums"]["patterns"].items():
        for v in variants:
            check(f"drums[{lv}]", v)
    for kind, variants in pack["drums"].get("fills", {}).items():
        for v in variants:
            check(f"drums.fill.{kind}", v)
    for lv, variants in pack["drums"].get("perc", {}).items():
        for v in variants:
            check(f"drums.perc[{lv}]", v)
    return errors


def public(pack_id: str) -> dict:
    """Phần style pack gửi cho /composition/options (giao diện chỉ cần tên, mô tả, tempo, swing)."""
    p = PACKS[pack_id]
    return {"id": pack_id, "label": p["label"], "description": p["description"], "default_bpm": p["default_bpm"],
            "bpm_range": p["bpm_range"], "swing": p["feel"]["swing"], "instruments": {
                "keys": p["keys"]["instrument"], "bass": p["bass"]["instrument"], "guitar": p["guitar"]["instrument"]}}
