"""Bộ phối khí Harmony Lab (ADR-012 đề xuất): từ vòng hợp âm + phong cách + seed → nốt cho từng nhạc cụ.

Vì sao ở backend: nguyên tắc "cao độ do Music Engine tính" và dự án lưu `drum_events` (tài liệu 04 Bảng 8).
Mọi tên nốt, nốt màu (7, 9, 13) và nốt đi của bass đều dựng bằng `transpose`/`parse_chord_symbol` của Engine;
file này chỉ chọn quãng tám, nhịp và lực đánh. Frontend thêm lệch phách người (humanize) rồi phát.

Bản phối gồm 4 vòng (QĐ 10A): vòng 1 mộc, vòng 2–3 đủ, vòng 4 có fill lớn; khi lặp lại thì quay về vòng 2.
Cùng (vòng hợp âm, phong cách, seed, năng lượng, ARRANGEMENT_VERSION) luôn ra cùng một bản phối.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from itertools import product
from typing import Optional

from ..music_engine import MusicEngineError, Note, build_chord, build_scale, parse_chord_symbol, parse_note, transpose
from .styles import ARRANGEMENT_VERSION, PACKS, char_velocity, pattern_for

BEATS_PER_BAR = 4
CYCLES = 4
LOOP_FROM_CYCLE = 1


class ArrangementError(ValueError):
    def __init__(self, code: str, message_vi: str):
        super().__init__(message_vi)
        self.code = code
        self.message_vi = message_vi


# --- hòa âm: nốt hợp âm + nốt màu, tất cả qua Engine ----------------------------------------------

@dataclass
class Harmony:
    symbol: str                 # ký hiệu gốc trên lưới (không đổi)
    root: Note                  # không có quãng tám
    family: str                 # maj/min/dim/7/maj7/...
    roles: dict[str, Note]      # "1","3","5","7","9","13" → nốt (không quãng tám), đánh vần theo Engine
    color_label: Optional[str]  # "Cmaj7", "G7 + 13", "C + 9"; None nếu phát đúng ký hiệu gốc


_ROLE_OF_INTERVAL = {"P1": "1", "m3": "3", "M3": "3", "P4": "4", "M2": "2", "d5": "5", "P5": "5", "A5": "5",
                     "m7": "7", "M7": "7", "d7": "7"}


def _roles(root: Note, intervals: tuple[str, ...]) -> dict[str, Note]:
    return {_ROLE_OF_INTERVAL[iv]: transpose(root, iv) for iv in intervals}


def _scale_pcs(key: Note) -> set[int]:
    return {n.pitch_class for n in build_scale(key, "major")}


def harmonize(symbol: str, key: Note, color: str, rng: random.Random) -> Harmony:
    """Tô màu theo phong cách (QĐ 7A): chỉ thêm nốt ở lớp phát; ký hiệu trên lưới giữ nguyên.

    Hợp âm 7 dựng bằng `build_chord` của Engine (loại maj7/m7/7/m7b5 Engine đã có); nốt 9, 13 dựng bằng
    `transpose(gốc, "M9"/"M13")`, không thêm loại hợp âm mới vào Engine.
    """
    chord = parse_chord_symbol(symbol)
    root, family = chord.root.with_octave(None), chord.type.id
    roles = _roles(root, chord.type.intervals)
    label: Optional[str] = None
    if color == "none" or family in ("aug", "sus2", "sus4"):
        return Harmony(chord.symbol, root, family, roles, None)

    scale = _scale_pcs(key)
    # Hợp âm trưởng là "át" khi gốc ở bậc V hoặc nốt 3 nằm ngoài giọng (át phụ V/x): tô 7 thay vì maj7.
    dominant = family == "maj" and (root.pitch_class == transpose(key, "P5").pitch_class
                                    or roles["3"].pitch_class not in scale)
    seventh_type = {"maj": "7" if dominant else "maj7", "min": "m7", "dim": "m7b5"}.get(family)

    if color in ("seventh", "ninth", "rich") and seventh_type:
        seventh = build_chord(root, seventh_type)
        roles = _roles(root, seventh.type.intervals)
        label = seventh.symbol
    elif color in ("seventh", "ninth", "rich"):
        label = None  # đã là hợp âm 7 trên lưới

    add9 = False
    if color in ("ninth", "rich") and family != "dim" and roles.get("5") and family != "m7b5":
        add9 = True
    elif color == "add9" and family == "maj" and not dominant and rng.random() < 0.5:
        add9 = True
    if add9:
        roles["9"] = transpose(root, "M9").with_octave(None)
        base = label or chord.symbol
        label = f"{base} + 9"
    if color == "rich" and ("7" in roles) and dominant and rng.random() < 0.5:
        roles["13"] = transpose(root, "M13").with_octave(None)
        label = f"{label or chord.symbol} + 13" if "+ 9" not in (label or "") else f"{label}, 13"
    return Harmony(chord.symbol, root, family, roles, label)


def realize(note: Note, octave: int) -> int:
    return note.with_octave(octave).midi


def nearest_midi(note: Note, target: float, lo: int, hi: int) -> int:
    """Quãng tám của `note` gần `target` nhất trong [lo, hi]."""
    options = [realize(note, o) for o in range(0, 9) if lo <= realize(note, o) <= hi]
    if not options:
        options = [realize(note, o) for o in range(0, 9)]
    return min(options, key=lambda m: (abs(m - target), m))


# --- thế bấm có dẫn giọng --------------------------------------------------------------------------

def _candidates(tones: list[Note], lo: int, hi: int, max_span: int, min_low_gap: int) -> list[list[int]]:
    per_tone = [[realize(t, o) for o in range(1, 8) if lo <= realize(t, o) <= hi] for t in tones]
    out = []
    for combo in product(*per_tone):
        v = sorted(combo)
        if len(set(v)) != len(v) or v[-1] - v[0] > max_span:
            continue
        # Quãng hẹp ở tầm thấp nghe đục: dưới E3 thì hai nốt dưới cùng phải cách nhau ≥ quãng 4.
        if v[0] < 52 and len(v) > 1 and v[1] - v[0] < min_low_gap:
            continue
        out.append(v)
    return out


def movement(prev: list[int], cand: list[int]) -> int:
    """Tổng quãng di chuyển (nửa cung) giữa hai thế bấm.

    Cùng số nốt: ghép bè theo thứ tự trầm → cao rồi cộng |chênh lệch| (bè 1 đi tới bè 1...).
    Khác số nốt: mỗi nốt tới nốt gần nhất của thế bấm kia, lấy chiều lớn hơn.
    """
    if not prev:
        return 0
    if len(prev) == len(cand):
        return sum(abs(a - b) for a, b in zip(sorted(prev), sorted(cand)))
    a = sum(min(abs(c - p) for p in prev) for c in cand)
    b = sum(min(abs(p - c) for c in cand) for p in prev)
    return max(a, b)


def lead(tones: list[Note], prev: list[int], lo: int, hi: int, rng: random.Random, max_span: int = 12,
         target_top: int = 67, min_low_gap: int = 5) -> list[int]:
    cands = _candidates(tones, lo, hi, max_span, min_low_gap)
    if not cands:
        cands = _candidates(tones, lo - 5, hi + 5, max_span + 7, 3)
    if not cands:
        raise ArrangementError("VOICING_FAILED", "Không dựng được thế bấm cho hợp âm này.")

    def cost(v: list[int]) -> float:
        if prev:
            return movement(prev, v) + 0.3 * abs(v[-1] - prev[-1])
        return abs(v[-1] - target_top) + 0.2 * (v[-1] - v[0])

    scored = sorted(cands, key=lambda v: (cost(v), v))
    best = cost(scored[0])
    near = [v for v in scored if cost(v) <= best + 1.5][:3]  # biến tấu nhỏ theo seed, vẫn gần tối ưu
    return rng.choice(near)


def keys_tones(h: Harmony, voicing: str) -> list[Note]:
    r = h.roles
    if voicing == "rootless" and "7" in r:
        tones = [r["3"], r.get("5"), r["7"], r.get("9") or r.get("13")]
        tones = [t for t in tones if t is not None]
        if "9" in r and "5" in r and len(tones) > 4:
            tones.remove(r["5"])
        return tones
    if voicing == "shell" and "7" in r:
        return [r["1"], r["3"], r["7"]]
    order = ["1", "3", "5", "7", "9", "13"]
    tones = [r[k] for k in order if k in r]
    if len(tones) >= 5:  # 5 nốt trở lên: bỏ nốt 5 cho gọn (nốt ít "màu" nhất)
        tones = [t for t in tones if t is not r.get("5")]
    return tones


def guitar_voicing(h: Harmony, style_voicing: str, prev: list[int], rng: random.Random) -> list[int]:
    r = h.roles
    if style_voicing == "power":
        root = nearest_midi(r["1"], 45, 40, 52)
        fifth = transpose(r["1"].with_octave(4), "P5").pitch_class
        return [root, root + ((fifth - root) % 12), root + 12]
    if style_voicing == "shell":
        tones = [r["1"], r["3"], r.get("7") or r["5"]]
        return lead(tones, prev, 43, 62, rng, max_span=14, target_top=58, min_low_gap=3)
    if style_voicing == "high":
        tones = [r["3"], r["5"], r.get("7") or r.get("9") or r["1"]]
        return lead(tones, prev, 60, 79, rng, max_span=9, target_top=74)
    # "open": gốc ở dưới (dây Mi/La), các nốt còn lại xếp lên như hợp âm guitar mở, 4–5 nốt.
    root = nearest_midi(r["1"], 47 if not prev else prev[0], 40, 52)
    upper_tones = [r["5"], r["1"], r["3"]] + ([r["7"]] if "7" in r else []) + ([r["9"]] if "9" in r else [])
    upper = lead(upper_tones[:4], prev[1:] if prev else [], root + 5, root + 24, rng, max_span=16, target_top=64,
                 min_low_gap=3)
    return [root] + [m for m in upper if m > root]


# --- bass ------------------------------------------------------------------------------------------

def approach(next_root: Note, prev_midi: int, key: Note, kind: str, lo: int, hi: int) -> int:
    """Nốt đi vào gốc ô sau: nửa cung dưới/trên (chromatic), bậc trong giọng, hoặc nốt 5 (át)."""
    target = nearest_midi(next_root, prev_midi, lo, hi)
    if kind == "below":
        return nearest_midi(transpose(next_root, "M7").with_octave(None), target - 1, lo, hi)
    if kind == "above":
        return nearest_midi(transpose(next_root, "m2").with_octave(None), target + 1, lo, hi)
    if kind == "fifth":
        return nearest_midi(transpose(next_root, "P5").with_octave(None), target + 7 if target + 7 <= hi else target - 5,
                            lo, hi)
    # bậc trong giọng gần gốc ô sau nhất (không trùng)
    scale = build_scale(key, "major")
    options = [nearest_midi(n, target, lo, hi) for n in scale]
    options = [m for m in options if 0 < abs(m - target) <= 2] or [target - 1]
    return min(options, key=lambda m: abs(m - prev_midi))


def bass_note(role: str, h: Harmony, nxt: Optional[Harmony], prev: int, key: Note, lo: int, hi: int,
              rng: random.Random, approach_kinds: list[str]) -> int:
    r = h.roles
    # Gốc gần nốt trước nhưng kéo nhẹ về giữa tầm, để bass không trôi dần xuống tầm đục (dưới F1).
    root = nearest_midi(r["1"], 0.65 * prev + 0.35 * (lo + hi) / 2, lo, hi)
    if role in ("R", "r"):
        return root
    if role == "5":
        five = r.get("5") or r["1"]
        cand = [m for m in (nearest_midi(five, root + 7, lo, hi), nearest_midi(five, root - 5, lo, hi))]
        return min(cand, key=lambda m: abs(m - prev))
    if role == "8":
        return root + 12 if root + 12 <= hi + 5 else root
    if role == "3":
        return nearest_midi(r["3"], root + 4, lo, hi)
    if role == "7":
        return nearest_midi(r.get("7") or r["5"], root + 10, lo, hi + 5)
    if role == "A":
        target = nxt or h
        return approach(target.roles["1"], prev, key, rng.choice(approach_kinds), lo, hi)
    return root


def walking_bar(h: Harmony, nxt: Harmony, prev: int, key: Note, lo: int, hi: int, rng: random.Random) -> list[int]:
    """Walking bass 4 nốt/ô: gốc · 2 nốt nối (ưu tiên nốt hợp âm ở phách 3) · nốt đi vào gốc ô sau.

    Chọn cặp nốt nối có tổng bước nhảy nhỏ, đi một hướng, không lặp nốt: nghe như người chơi "đi" tới hợp âm sau.
    """
    root = nearest_midi(h.roles["1"], 0.65 * prev + 0.35 * (lo + hi) / 2, lo, hi)
    target = nearest_midi(nxt.roles["1"], root, lo, hi)
    last = approach(nxt.roles["1"], target, key, rng.choice(["below", "above", "fifth", "below"]), lo, hi)
    chord_pcs = {h.roles[k].pitch_class for k in ("1", "3", "5", "7") if k in h.roles}
    pool = sorted({m for n in build_scale(key, "major") + [h.roles[k] for k in ("3", "5", "7") if k in h.roles]
                   for m in (realize(n, o) for o in range(1, 5)) if lo <= m <= hi + 3})
    best, best_cost = None, 1e9
    for n2 in pool:
        for n3 in pool:
            seq = [root, n2, n3, last]
            if len(set(seq[:3])) < 3 or n3 == last:
                continue
            steps = [seq[i + 1] - seq[i] for i in range(3)]
            cost = sum(abs(x) for x in steps)
            cost += sum(3 for x in steps if abs(x) > 5)
            cost += 2 * sum(1 for i in range(2) if steps[i] * steps[i + 1] < 0)
            cost += 0 if n3 % 12 in chord_pcs else 1.5
            cost += 0 if n2 % 12 in chord_pcs else 0.5
            cost += rng.random() * 1.2  # biến tấu theo seed giữa các đường đi gần tối ưu
            if cost < best_cost:
                best, best_cost = [root, n2, n3, last], cost
    return best or [root, root + 7, root + 4, last]


# --- dựng bản phối ---------------------------------------------------------------------------------

def _seed_int(*parts: object) -> int:
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:12], 16)


def cycle_levels(energy: int) -> list[int]:
    return [max(1, energy - 1), energy, energy, energy]


def _hits(pattern: str, grid: int, bar_start: float):
    """Duyệt chuỗi mẫu: ký tự đánh + '=' kéo dài. Trả (vị trí phách, độ dài phách, ký tự)."""
    step = BEATS_PER_BAR / grid
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch in ".=":
            i += 1
            continue
        j = i + 1
        while j < len(pattern) and pattern[j] == "=":
            j += 1
        yield bar_start + i * step, (j - i) * step, ch
        i += 1


def arrange(key: str, style: str, chords: list[Optional[str]], seed: int = 1, energy: int = 2,
            bpm: Optional[int] = None) -> dict:
    if style not in PACKS:
        raise ArrangementError("UNKNOWN_STYLE", f"Phong cách {style!r} không có.")
    if energy not in (1, 2, 3):
        raise ArrangementError("BAD_ENERGY", "Năng lượng chỉ nhận 1, 2 hoặc 3.")
    pack = PACKS[style]
    try:
        tonic = parse_note(key).with_octave(None)
    except MusicEngineError as exc:
        raise ArrangementError("BAD_KEY", f"Không đọc được giọng {key!r}.") from exc
    grid = pack["grid"]
    bars = len(chords)
    rng_h = random.Random(_seed_int("harmony", seed, style, *chords))
    harmonies: list[Optional[Harmony]] = []
    for symbol in chords:
        if not symbol:
            harmonies.append(None)
            continue
        try:
            harmonies.append(harmonize(symbol, tonic, pack["color"], rng_h))
        except MusicEngineError as exc:
            raise ArrangementError("BAD_CHORD", f"Không đọc được hợp âm {symbol!r}.") from exc

    tracks: dict[str, dict] = {
        "keys": {"instrument": pack["keys"]["instrument"], "events": []},
        "bass": {"instrument": pack["bass"]["instrument"], "events": []},
        "guitar": {"instrument": pack["guitar"]["instrument"], "events": []},
        "drums": {"kit": pack["drums"].get("kit", "acoustic"), "events": []},
    }
    prev_keys: list[int] = []
    prev_lh: int = 0
    prev_gtr: list[int] = []
    b_lo, b_hi = pack["bass"]["range"]
    prev_bass = nearest_midi(harmonies[0].roles["1"], 38, b_lo, b_hi) if harmonies[0] else 38

    for cycle in range(CYCLES):
        level = cycle_levels(energy)[cycle]
        rng = random.Random(_seed_int(seed, style, energy, cycle, *chords))
        variant = {part: rng.randrange(1_000_000) for part in ("keys", "bass", "guitar", "drums", "lh", "perc")}
        for bar in range(bars):
            gbar = cycle * bars + bar
            start = gbar * BEATS_PER_BAR
            h = harmonies[bar]
            nxt = harmonies[(bar + 1) % bars] or h
            last_bar = bar == bars - 1
            fill = None
            if last_bar and level >= 2:
                fill = "big" if cycle == CYCLES - 1 else "small"

            # trống + bộ gõ (trống vẫn chạy ở ô trống để giữ nhịp)
            dpat = pattern_for(pack["drums"]["patterns"], level, variant["drums"], bar, grid)
            if fill and pack["drums"].get("fills", {}).get(fill):
                fills = pack["drums"]["fills"][fill]
                dpat = {**dpat, **fills[(variant["drums"] + cycle) % len(fills)]}
            crash_here = pack["drums"].get("crash", True) and bar == 0 and cycle > 0 and level >= 2
            for piece_name, pat in dpat.items():
                for beat, _, ch in _hits(pat, grid, start):
                    if crash_here and beat == start and piece_name in ("hh_c", "hh_o", "ride", "br_hh", "br_ride"):
                        continue  # nhát crash thay cho hat/ride ở phách 1
                    tracks["drums"]["events"].append({"beat": beat, "drum": piece_name, "vel": char_velocity(ch)})
            if crash_here:
                tracks["drums"]["events"].append({"beat": start, "drum": "crash", "vel": 100 if level == 3 else 84})
            perc = pack["drums"].get("perc")
            if perc:
                ppat = pattern_for(perc, level, variant["perc"], bar, grid)
                for piece_name, pat in ppat.items():
                    for beat, _, ch in _hits(pat, grid, start):
                        tracks["drums"]["events"].append({"beat": beat, "drum": piece_name, "vel": char_velocity(ch)})
            if h is None:
                continue

            # phím (kênh "Hợp âm")
            kp = pack["keys"]
            k_lo, k_hi = kp["range"]
            voicing = lead(keys_tones(h, kp["voicing"]), prev_keys, k_lo, k_hi, rng,
                           max_span=kp.get("max_span", 12), target_top=kp.get("top", 67))
            prev_keys = voicing
            kpat = pattern_for(kp["patterns"], level, variant["keys"], bar, grid)
            for beat, dur, ch in _hits(kpat, grid, start):
                notes = voicing if ch not in "tT" else voicing[-2:]
                tracks["keys"]["events"].append({"beat": beat, "dur": dur, "midi": notes, "vel": char_velocity(ch),
                                                 "art": "roll" if ch in "rR" else "block"})
            if kp.get("lh"):
                lh_pat = pattern_for(kp["lh"], level, variant["lh"], bar, grid)
                lh_root = nearest_midi(h.roles["1"], prev_lh or 43, 36, 50)
                prev_lh = lh_root
                role_midi = {"1": lh_root, "5": nearest_midi(h.roles["5"] if "5" in h.roles else h.roles["1"], lh_root + 7, lh_root, lh_root + 11),
                             "8": lh_root + 12, "3": nearest_midi(h.roles["3"], lh_root + 16, lh_root + 12, lh_root + 23),
                             "7": nearest_midi(h.roles.get("7", h.roles["1"]), lh_root + 10, lh_root + 1, lh_root + 12)}
                for beat, dur, ch in _hits(lh_pat, grid, start):
                    if ch in role_midi:
                        tracks["keys"]["events"].append({"beat": beat, "dur": dur, "midi": [role_midi[ch]],
                                                         "vel": 62 if beat % 1 else 70, "art": "lh"})

            # bass
            bp = pack["bass"]
            if bp.get("walk") and level >= 2:
                notes = walking_bar(h, nxt, prev_bass, tonic, b_lo, b_hi, rng)
                for i, m in enumerate(notes):
                    tracks["bass"]["events"].append({"beat": start + i, "dur": 0.92, "midi": [m],
                                                     "vel": 92 if i % 2 == 0 else 84, "art": "sustain"})
                prev_bass = notes[-1]
            else:
                bpat = pattern_for(bp["patterns"], level, variant["bass"], bar, grid)
                for beat, dur, ch in _hits(bpat, grid, start):
                    if ch == "x":  # nốt chết (dead note): tiếng gõ dây, không rõ cao độ
                        tracks["bass"]["events"].append({"beat": beat, "dur": 0.12, "midi": [prev_bass],
                                                         "vel": 55, "art": "dead"})
                        continue
                    m = bass_note(ch.upper() if ch != "r" else "R", h, nxt, prev_bass, tonic, b_lo, b_hi, rng,
                                  bp.get("approach", ["below", "scale"]))
                    if ch == "A" and dur > 1:
                        dur = 1
                    tracks["bass"]["events"].append({"beat": beat, "dur": dur, "midi": [m],
                                                     "vel": 62 if ch == "r" else 100 if beat % BEATS_PER_BAR == 0
                                                     else 88 if beat % 1 == 0 else 76,
                                                     "art": bp.get("art", "sustain")})
                    prev_bass = m

            # guitar
            gp = pack["guitar"]
            if level >= gp.get("min_energy", 2):
                gv = guitar_voicing(h, gp["voicing"], prev_gtr, rng)
                prev_gtr = gv
                gpat = pattern_for(gp["patterns"], level, variant["guitar"], bar, grid)
                for beat, dur, ch in _hits(gpat, grid, start):
                    if ch.isdigit():
                        idx = min(int(ch) - 1, len(gv) - 1)
                        tracks["guitar"]["events"].append({"beat": beat, "dur": dur, "midi": [gv[idx]], "vel": 78,
                                                           "art": "pick"})
                        continue
                    art = {"D": "down", "d": "down", "U": "up", "u": "up", "M": "mute", "P": "palm", "O": "down",
                           "S": "stab", "s": "stab"}.get(ch, "down")
                    vel = {"D": 96, "d": 72, "U": 80, "u": 60, "M": 70, "P": 88, "O": 104, "S": 90, "s": 70}.get(ch, 80)
                    notes = gv if art not in ("stab",) else gv[-3:]
                    tracks["guitar"]["events"].append({"beat": beat, "dur": dur, "midi": notes, "vel": vel, "art": art})

    for track in tracks.values():
        track["events"].sort(key=lambda e: (e["beat"], e.get("drum", "")))
    colors = [{"bar": i, "symbol": h.symbol, "played": h.color_label} if h else {"bar": i, "symbol": None, "played": None}
              for i, h in enumerate(harmonies)]
    return {
        "version": ARRANGEMENT_VERSION, "style": style, "seed": seed, "energy": energy,
        "bpm": bpm or pack["default_bpm"], "grid": grid, "bars_per_cycle": bars, "cycles": CYCLES,
        "loop_from_cycle": LOOP_FROM_CYCLE, "total_beats": CYCLES * bars * BEATS_PER_BAR,
        "feel": pack["feel"], "fx": pack["fx"], "colors": colors, "tracks": tracks,
    }


def drum_events_for(key: str, style: str, chords: list[Optional[str]], seed: int, energy: int) -> list[dict]:
    """`drum_events` để lưu dự án (tài liệu 04 Bảng 8): trải đủ 4 vòng, đúng như lúc phát."""
    events = arrange(key, style, chords, seed, energy)["tracks"]["drums"]["events"]
    return [{"drum": e["drum"], "start_beat": e["beat"], "velocity": e["vel"]} for e in events]
