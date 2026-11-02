"""Bộ dựng bài hát Harmony Lab (ADR-013 đề xuất): từ 1–3 vòng hợp âm → backing track có cấu trúc đoạn.

Vì sao tách khỏi `arranger.arrange`: chế độ Vòng lặp phải giữ y nguyên từng nốt của bản v1 (QĐ 2A), nên file này
chỉ DÙNG LẠI các hàm của bộ phối (tô màu, dẫn giọng, bass, guitar, mẫu nhịp) mà không sửa chúng.

Luồng dựng (sổ tay: docs/backing-track/CAU_TRUC_BAI_HAT.md):
1. Đọc form (các đoạn + vòng A/B/C) → trải thành danh sách ô nhịp, mỗi ô biết đoạn, hợp âm, năng lượng 1–5.
2. Chọn kiểu chuyển đoạn ("auto" → luật theo loại đoạn) và 1–3 "đột biến" theo seed.
3. Dựng từng ô bằng công thức năng lượng (ENERGY_RECIPE). Dẫn giọng và bass nối liền qua ranh giới đoạn vì
   thế bấm trước (prev) được mang sang đoạn sau.
4. Chèn chuyển đoạn (fill, snare build, drop, stop-time, riser...), kết bài (nhỏ dần, ngân, một nhát, tag ii–V).
5. Hook nhạc cụ ở đúng chỗ (mục E), automation âm lượng/bộ lọc/reverb, ghi chú producer từng đoạn.

Mọi cao độ (kể cả hook, hợp âm lên giọng, tag ii–V, hợp âm I kết bài) dựng bằng Music Engine.
Cùng (form, giọng, phong cách, seed, năng lượng tổng, SONG_VERSION) luôn ra cùng một bài.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from ..music_engine import MusicEngineError, Note, build_chord, build_scale, parse_chord_symbol, parse_note, transpose
from .arranger import (
    BEATS_PER_BAR, ArrangementError, Harmony, _hits, _seed_int, bass_note, guitar_voicing, harmonize, keys_tones, lead,
    nearest_midi, walking_bar,
)
from .styles import PACKS, char_velocity, pattern_for

SONG_VERSION = 2
MAX_BARS = 160          # giới hạn cứng: thời gian dựng + số dòng drum_events (ADR-013)
MAX_SECTIONS = 32

SECTION_TYPES = ("intro", "verse", "pre", "chorus", "post", "bridge", "breakdown", "solo", "outro")
SECTION_LABELS = {"intro": "Intro", "verse": "Verse", "pre": "Pre-Chorus", "chorus": "Chorus", "post": "Post-Chorus",
                  "bridge": "Bridge", "breakdown": "Breakdown", "solo": "Solo", "outro": "Outro"}
TRANSITIONS = ("auto", "none", "fill_small", "fill_big", "snare_build", "drop_bar", "stop_time", "pickup", "riser",
               "reverse_cymbal")
ENDINGS = ("auto", "fade", "ritardando_fermata", "big_hit", "tag_x3")
FEELS = ("auto", "normal", "half", "double")
LENGTHS = ("short", "medium", "full")
PARTS = ("keys", "bass", "guitar", "drums", "perc", "hook")

TRANSITION_LABELS = {
    "none": "nối thẳng", "fill_small": "fill nhỏ", "fill_big": "fill tom lớn", "snare_build": "snare dồn",
    "drop_bar": "drop (im 2 phách)", "stop_time": "stop-time", "pickup": "nhát mồi", "riser": "riser",
    "reverse_cymbal": "cymbal ngược",
}
ENDING_LABELS = {"fade": "nhỏ dần", "ritardando_fermata": "chậm dần + ngân", "big_hit": "một nhát đồng loạt",
                 "tag_x3": "tag ii–V × 3"}

# Công thức năng lượng 1–5 (mục D của sổ tay). `level` = mức mẫu nhịp sẵn có 1–3 của style pack (không xóa mẫu cũ).
#   bass: mức mẫu bass · guitar: mức để so với `min_energy` của guitar · notes: số nốt tối đa của phím (None = đủ)
#   top: dời đỉnh thế bấm phím (nửa cung) · lh: tay trái quãng tám (piano) · db: âm lượng tổng của đoạn (automation)
# db hiệu chỉnh theo số đo 02/11/2026: chỉ riêng mật độ lớp đã làm Chorus to hơn Verse ~3 LU, bản đầu (-4 → 0 dB)
# đo được +7,2 LU và đỉnh -0,2 dBTP; nên chênh dB giữa các mức để nhỏ và hạ cả đường 2 dB cho limiter dư chỗ.
ENERGY_RECIPE = {
    1: {"level": 1, "bass": 1, "guitar": 1, "notes": 3, "top": -3, "lh": False, "db": -4.5},
    2: {"level": 2, "bass": 1, "guitar": 1, "notes": 3, "top": -3, "lh": False, "db": -2.5},
    3: {"level": 2, "bass": 2, "guitar": 2, "notes": None, "top": 0, "lh": False, "db": -2.5},
    4: {"level": 3, "bass": 3, "guitar": 3, "notes": None, "top": 3, "lh": True, "db": -2.0},
    5: {"level": 3, "bass": 3, "guitar": 3, "notes": None, "top": 5, "lh": True, "db": -1.5},
}
HOOK_RANGE = (72, 88)    # C5–E6: trên tầm giọng hát (nguyên tắc 4)
HOOK_CONTOURS = ([0, 1, 2, -1], [0, -1, -2, 1], [0, 2, 1, 0], [0, 1, 0, -1], [0, -2, -1, 1], [0, 1, 1, -2])


class SongError(ArrangementError):
    pass


# --- form: dựng mặc định từ khuôn, chuẩn hóa form người dùng gửi ------------------------------------

def _prog_len(progressions: dict, ref: str) -> int:
    chords = progressions.get(ref) or progressions.get("A") or []
    return max(1, len(chords))


def round_bars(bars: int, cycle: int, section_type: str) -> int:
    """QĐ 7A: số ô của đoạn làm tròn về bội số độ dài vòng. Đoạn ngắn (Intro, Pre, Tag...) ngắn hơn một vòng thì giữ."""
    if bars % cycle == 0:
        return bars
    if bars < cycle and section_type in ("intro", "pre", "post", "breakdown", "outro"):
        return bars
    return max(1, round(bars / cycle)) * cycle


def section_labels(sections: list[dict]) -> list[str]:
    """Nhãn hiển thị: "Verse 1", "Verse 2", "Chorus cuối"... khi khuôn không đặt nhãn riêng."""
    counts: dict[str, int] = {}
    totals = {t: sum(1 for s in sections if s["type"] == t) for t in SECTION_TYPES}
    last_chorus = max((i for i, s in enumerate(sections) if s["type"] == "chorus"), default=-1)
    custom_totals: dict[str, int] = {}
    for s in sections:
        if s.get("label"):
            custom_totals[s["label"]] = custom_totals.get(s["label"], 0) + 1
    custom_counts: dict[str, int] = {}
    out = []
    for i, s in enumerate(sections):
        counts[s["type"]] = counts.get(s["type"], 0) + 1
        if s.get("label"):
            lab = s["label"]
            custom_counts[lab] = custom_counts.get(lab, 0) + 1
            out.append(f"{lab} · {custom_counts[lab]}" if custom_totals[lab] > 1 else lab)
            continue
        base = SECTION_LABELS[s["type"]]
        if s["type"] == "chorus" and i == last_chorus and totals["chorus"] > 1:
            out.append("Chorus cuối")
        elif totals[s["type"]] > 1 and s["type"] in ("verse", "chorus", "pre", "post", "solo"):
            out.append(f"{base} {counts[s['type']]}")
        else:
            out.append(base)
    return out


def default_form(style: str, length: str, progressions: dict) -> dict:
    """Form mặc định của phong cách ở độ dài đã chọn; đổi độ dài không đụng tới vòng A/B/C (mục F)."""
    if style not in PACKS:
        raise SongError("UNKNOWN_STYLE", f"Phong cách {style!r} không có.")
    if length not in LENGTHS:
        raise SongError("BAD_LENGTH", "Độ dài chỉ nhận short, medium hoặc full.")
    sections = []
    for i, entry in enumerate(PACKS[style]["song"]["forms"][length]):
        stype, bars, ref, energy = entry[:4]
        label = entry[4] if len(entry) > 4 else None
        sections.append({"id": f"s{i + 1}", "type": stype, "label": label,
                         "bars": round_bars(bars, _prog_len(progressions, ref), stype), "progression": ref,
                         "energy": energy, "feel": "auto", "hook": True, "transition": "auto", "seed": None})
    return {"length": length, "hook": True, "modulate": {"enabled": False, "semitones": 1}, "ending": "auto",
            "progressions": {k: progressions.get(k) for k in ("A", "B", "C")}, "sections": sections}


def normalize_form(style: str, form: dict) -> dict:
    """Kiểm form người dùng gửi (đã qua Pydantic ở router) theo luật nghiệp vụ: tổng ô, loại đoạn, vòng A."""
    progressions = form.get("progressions") or {}
    a = progressions.get("A") or []
    if not a or not any(a):
        raise SongError("EMPTY_PROGRESSION", "Vòng A cần ít nhất một hợp âm.")
    sections = form.get("sections")
    if not sections:
        sections = default_form(style, form.get("length") or "medium", progressions)["sections"]
    if len(sections) > MAX_SECTIONS:
        raise SongError("TOO_MANY_SECTIONS", f"Tối đa {MAX_SECTIONS} đoạn.")
    total = sum(int(s["bars"]) for s in sections)
    if total > MAX_BARS:
        raise SongError("SONG_TOO_LONG", f"Bài dài {total} ô, quá giới hạn {MAX_BARS} ô.")
    for s in sections:
        if s["type"] not in SECTION_TYPES:
            raise SongError("BAD_SECTION", f"Loại đoạn {s['type']!r} không có.")
    out = dict(form)
    out["sections"] = [dict(s) for s in sections]
    out["progressions"] = {k: progressions.get(k) for k in ("A", "B", "C")}
    out.setdefault("hook", True)
    out.setdefault("modulate", {"enabled": False, "semitones": 1})
    out.setdefault("ending", "auto")
    return out


# --- gợi ý vòng B/C cho ô trống (QĐ 3A: chỉ gợi ý, người dùng nghe thử rồi mới chấp nhận) -------------

_DEGREE = {"I": ("P1", "maj"), "ii": ("M2", "min"), "iii": ("M3", "min"), "IV": ("P4", "maj"), "V": ("P5", "maj"),
           "vi": ("M6", "min"), "bVII": ("m7", "maj")}
BORROW_OK = {"pop", "rock", "indie", "funk", "rnb"}


def _degree_chord(tonic: Note, numeral: str) -> str:
    iv, kind = _DEGREE[numeral]
    return build_chord(transpose(tonic, iv), kind).symbol


def suggest_progression(key: str, style: str, slot: str, a: list[Optional[str]], seed: int) -> dict:
    """Vòng gợi ý theo luật chức năng (sổ tay mục C, nguồn [3]):
    B (Chorus) bắt đầu ở IV hoặc I và đi về V để quay vòng; C (Bridge) bắt đầu ở vi hoặc IV, mượn bVII nếu phong cách cho phép.
    """
    tonic = parse_note(key).with_octave(None)
    rng = random.Random(_seed_int("suggest", key, style, slot, seed, *a))
    first = next((c for c in a if c), None)
    starts_on_i = bool(first) and parse_chord_symbol(first).root.pitch_class == tonic.pitch_class
    if slot == "B":
        options = [["IV", "I", "V", "vi"], ["IV", "V", "I", "vi"], ["I", "V", "vi", "IV"], ["vi", "IV", "I", "V"]]
        if starts_on_i:
            options = options[:2] + options[3:]
        why = "Vòng Chorus bắt đầu ở hợp âm khác Verse để nghe \"mở ra\", và có V để kéo về đầu vòng."
    else:
        options = [["vi", "IV", "I", "V"], ["IV", "V", "vi", "vi"], ["vi", "V", "IV", "V"]]
        if style in BORROW_OK:
            options.append(["IV", "bVII", "I", "V"])
        why = "Bridge cần tương phản: bắt đầu ở vi hoặc IV (không phải I)" + (
            ", có thể mượn bVII từ giọng thứ cùng tên." if style in BORROW_OK else ".")
    numerals = rng.choice(options)
    chords = [_degree_chord(tonic, n) for n in numerals]
    if chords == [c for c in a if c][:4]:
        numerals = options[(options.index(numerals) + 1) % len(options)]
        chords = [_degree_chord(tonic, n) for n in numerals]
    return {"slot": slot, "chords": chords, "numerals": numerals, "reason_vi": why}


# --- kế hoạch ô nhịp --------------------------------------------------------------------------------

@dataclass
class Sec:
    idx: int
    type: str
    label: str
    bars: int
    start_bar: int
    ref: str
    energy: int            # năng lượng thật đã cộng "Năng lượng tổng"
    design_energy: int     # năng lượng trong form
    feel: str
    hook: bool
    transition: str        # kiểu chuyển đoạn ở CUỐI đoạn này (sang đoạn sau)
    occurrence: int        # lần thứ mấy của loại đoạn này
    seed: int
    parts: set
    add_layer: bool
    tonic: Note
    notes: list[str] = field(default_factory=list)

    @property
    def start_beat(self) -> float:
        return self.start_bar * BEATS_PER_BAR

    @property
    def end_beat(self) -> float:
        return (self.start_bar + self.bars) * BEATS_PER_BAR


def _default_transition(style: str, cur: str, nxt: Optional[str]) -> str:
    """Luật chuyển đoạn khi form để "auto" (sổ tay mục C)."""
    rules = PACKS[style]["song"].get("transitions", {})
    if nxt is None:
        return "none"
    if nxt == "chorus":
        key = f"chorus_from_{cur}"
        if key in rules:
            return rules[key]
        if cur in ("pre", "breakdown"):
            return "snare_build"
        return rules.get("chorus", "fill_big")
    if cur == "intro":
        return "pickup"
    if nxt in ("bridge", "solo", "breakdown"):
        return "fill_big"
    return "fill_small"


def _pick_surprises(style: str, secs: list[Sec], explicit: set[int], seed: int) -> list[dict]:
    """1–3 "đột biến" ở ranh giới đoạn, theo seed, trong danh sách cho phép của phong cách (nguyên tắc 5)."""
    allowed = PACKS[style]["song"]["surprises"]
    rng = random.Random(_seed_int("surprise", seed, style, *[s.type for s in secs]))
    last_chorus = max((s.idx for s in secs if s.type == "chorus"), default=-1)
    candidates = []
    for kind, where in allowed:
        if kind in ("half", "double"):
            targets = [s for s in secs if (where == "last_chorus" and s.idx == last_chorus)
                       or (where == s.type and where != "last_chorus")]
            targets = [s for s in targets if s.feel == "auto"]
            if kind == "double" and PACKS[style]["grid"] != 16:
                targets = []
            for s in targets:
                candidates.append((kind, s.idx))
        else:
            # đặt ở cuối đoạn ngay trước đoạn `where` (chuyển đoạn của đoạn trước đó)
            for s in secs[:-1]:
                nxt = secs[s.idx + 1]
                # Không đặt ở Intro: Intro → đoạn đầu cần nối mềm (nhát mồi), chưa có gì để "tương phản".
                if nxt.type == where and s.idx not in explicit and s.bars >= 2 and s.type != "intro":
                    candidates.append((kind, s.idx))
    rng.shuffle(candidates)
    want = 1 + rng.randrange(3)
    chosen, used = [], set()
    for kind, idx in candidates:
        if len(chosen) >= want:
            break
        slot = (idx, kind in ("half", "double"))
        if slot in used:
            continue
        used.add(slot)
        chosen.append({"kind": kind, "section": idx})
    if not chosen:
        # Bảo đảm luôn có ít nhất 1 điểm bất ngờ: drop trước đoạn cao trào đầu tiên (hoặc trước Outro).
        for s in secs[:-1]:
            nxt = secs[s.idx + 1]
            if nxt.type in ("chorus", "solo", "outro") and s.bars >= 2 and s.idx not in explicit:
                chosen.append({"kind": "drop_bar", "section": s.idx})
                break
    return chosen


# --- dựng từng phần ---------------------------------------------------------------------------------

def _thin(h: Harmony, tones: list[Note], limit: Optional[int]) -> list[Note]:
    """Verse: phím tối đa 3 nốt (chừa chỗ cho giọng).

    Thế bấm có gốc (close): bỏ 13, 9 trước rồi mới tới 5, để không thành chùm C–D–E sát nhau.
    Thế bấm không gốc (rootless, jazz/lo-fi): bỏ 5 trước, giữ 3–7–9 là phần "màu" của hợp âm.
    """
    if limit is None or len(tones) <= limit:
        return tones
    keep = list(tones)
    order = ("13", "9", "5", "1", "7") if h.roles["1"] in tones else ("5", "13", "1", "9", "7")
    for role in order:
        if len(keep) <= limit:
            break
        note = h.roles.get(role)
        if note is not None and note in keep and len(keep) > limit:
            keep.remove(note)
    return keep[:limit] if len(keep) > limit else keep


def _half_time(dpat: dict, grid: int) -> dict:
    """Half-time: kick phách 1, snare chỉ phách 3, hat/ride nốt đen; giữ bộ gõ. Nghe chậm một nửa mà tempo không đổi."""
    q = grid // 4
    out = {}
    hat = next((p for p in ("ride", "hh_c", "br_ride", "br_hh", "hh_o") if p in dpat), None)
    for piece, pat in dpat.items():
        if piece in ("kick", "snare", "xstick", "rim", "br_snare") or piece == hat:
            continue
        if piece.startswith("tom") or piece in ("hh_o", "ride_b", "hh_p"):
            continue
        out[piece] = pat
    cells = ["."] * grid
    cells[0] = "X"
    out["kick"] = "".join(cells)
    cells = ["."] * grid
    cells[2 * q] = "X"
    out["snare"] = "".join(cells)
    if hat:
        cells = ["."] * grid
        for i in range(0, grid, q):
            cells[i] = "x"
        out[hat] = "".join(cells)
    return out


def _double_time(dpat: dict, grid: int) -> dict:
    """Double-time (chỉ lưới 16): kick móc đơn xuôi, snare móc đơn ngược, hat móc đơn: "chạy" gấp đôi."""
    keep = {p: v for p, v in dpat.items() if p in ("tamb", "shaker", "crash")}
    keep["kick"] = "X...x...X...x..."
    keep["snare"] = "..X...X...X...X."
    keep["hh_o" if "hh_o" in dpat else "hh_c"] = "x.x.x.x.x.x.x.x."
    return keep


def _stickify(dpat: dict) -> dict:
    """Verse năng lượng 2: snare thật → side-stick, cymbal mở → hat đóng (chừa chỗ cho giọng)."""
    out = {}
    for piece, pat in dpat.items():
        if piece == "snare":
            out["xstick"] = pat.replace("g", ".")
        elif piece in ("hh_o", "ride", "ride_b"):
            out.setdefault("hh_c", pat.replace("X", "x"))
        else:
            out[piece] = pat
    return out


@dataclass
class Ctx:
    style: str
    pack: dict
    grid: int
    tracks: dict
    prev_keys: list = field(default_factory=list)
    prev_lh: int = 0
    prev_gtr: list = field(default_factory=list)
    prev_bass: int = 38


def _drums_bar(ctx: Ctx, sec: Sec, e: int, bar_in: int, start: float, variant: int, fill: Optional[str],
               crash: bool, out: list) -> None:
    pack, grid = ctx.pack, ctx.grid
    rec = ENERGY_RECIPE[e]
    if "drums" in sec.parts:
        dpat = pattern_for(pack["drums"]["patterns"], rec["level"], variant, bar_in, grid)
        if e <= 2 and pack["song"].get("verse_stick"):
            dpat = _stickify(dpat)
        feel = sec.feel
        if feel == "half":
            dpat = _half_time(dpat, grid)
        elif feel == "double" and grid == 16:
            dpat = _double_time(dpat, grid)
        if fill and pack["drums"].get("fills", {}).get(fill):
            fills = pack["drums"]["fills"][fill]
            dpat = {**dpat, **fills[(variant + sec.occurrence) % len(fills)]}
        for piece, pat in dpat.items():
            for beat, _, ch in _hits(pat, grid, start):
                if crash and beat == start and piece in ("hh_c", "hh_o", "ride", "br_hh", "br_ride"):
                    continue
                out.append({"beat": beat, "drum": piece, "vel": char_velocity(ch)})
        if crash:
            out.append({"beat": start, "drum": "crash", "vel": 104 if e >= 4 else 86})
    explicit_perc = "perc" in (pack["song"].get("parts", {}).get(sec.type) or [])
    if "perc" in sec.parts:
        perc = pack["drums"].get("perc")
        plevel = rec["level"] + (1 if sec.add_layer else 0)
        if perc and (e >= 2 or explicit_perc):
            ppat = pattern_for(perc, min(plevel, 3), variant, bar_in, grid)
            for piece, pat in ppat.items():
                for beat, _, ch in _hits(pat, grid, start):
                    out.append({"beat": beat, "drum": piece, "vel": char_velocity(ch)})
        has_tamb = bool(perc) and any("tamb" in v for lv in perc.values() for v in lv)
        # Lớp thêm khi guitar đã có sẵn: tambourine phách 2–4 (trừ jazz chổi: không hợp kit).
        extra = sec.add_layer and _guitar_base(pack, sec, e)
        if extra and pack["drums"].get("kit") == "brush" and "drums" in sec.parts:
            # Jazz: tambourine không hợp; tay ride gõ chuông (ride bell) phách 2–4 làm lớp thêm.
            for k in (1, 3):
                out.append({"beat": start + k, "drum": "ride_b", "vel": 70})
        elif (e >= 5 or extra) and not has_tamb and "drums" in sec.parts:
            # Mức 5: thêm tambourine phách 2–4 (một lớp "lấp lánh" cho Chorus cuối).
            q = BEATS_PER_BAR / 4
            for k in (1, 3):
                out.append({"beat": start + k * q, "drum": "tamb", "vel": 84})


def _keys_bar(ctx: Ctx, sec: Sec, e: int, h: Harmony, bar_in: int, start: float, variant: int, lh_variant: int,
              rng: random.Random) -> None:
    kp, grid = ctx.pack["keys"], ctx.grid
    rec = ENERGY_RECIPE[e]
    k_lo, k_hi = kp["range"]
    shift, limit = rec["top"], rec["notes"]
    if sec.type == "verse":
        # Nguyên tắc 4: Verse luôn chừa chỗ cho giọng hát (tối đa 3 nốt, không đẩy đỉnh lên), dù năng lượng cao.
        shift, limit = min(shift, 0), min(limit or 3, 3)
    top = kp.get("top", 67) + shift
    # Đoạn thưa: chặn trần tầm phím ngay trên đích, để dẫn giọng (lead) tự tìm thế bấm thấp mà vẫn đi gần.
    hi = min(k_hi, top + 4) if shift < 0 else k_hi + shift
    if shift < 0 and ctx.prev_keys:
        # Từ Chorus về Verse: hạ tầm dần (đỉnh xuống tối đa 4 nửa cung mỗi ô) thay vì nhảy cả quãng tám ở ranh giới.
        hi = max(hi, ctx.prev_keys[-1] - 4)
    tones = _thin(h, keys_tones(h, kp["voicing"]), limit)
    voicing = lead(tones, ctx.prev_keys, k_lo, hi, rng, max_span=kp.get("max_span", 12), target_top=top)
    ctx.prev_keys = voicing
    level = rec["level"] + (1 if sec.add_layer and rec["level"] < 3 and e >= 3 else 0)
    kpat = pattern_for(kp["patterns"], level, variant, bar_in, grid)
    for beat, dur, ch in _hits(kpat, grid, start):
        notes = voicing if ch not in "tT" else voicing[-2:]
        ctx.tracks["keys"]["events"].append({"beat": beat, "dur": dur, "midi": notes, "vel": char_velocity(ch),
                                             "art": "roll" if ch in "rR" else "block"})
    lh_root = nearest_midi(h.roles["1"], ctx.prev_lh or 43, 36, 50)
    if kp.get("lh"):
        lh_pat = pattern_for(kp["lh"], rec["level"], lh_variant, bar_in, grid)
        ctx.prev_lh = lh_root
        five = h.roles.get("5") or h.roles["1"]
        role_midi = {"1": lh_root, "5": nearest_midi(five, lh_root + 7, lh_root, lh_root + 11), "8": lh_root + 12,
                     "3": nearest_midi(h.roles["3"], lh_root + 16, lh_root + 12, lh_root + 23),
                     "7": nearest_midi(h.roles.get("7", h.roles["1"]), lh_root + 10, lh_root + 1, lh_root + 12)}
        for beat, dur, ch in _hits(lh_pat, grid, start):
            if ch in role_midi:
                ctx.tracks["keys"]["events"].append({"beat": beat, "dur": dur, "midi": [role_midi[ch]],
                                                     "vel": 62 if beat % 1 else 70, "art": "lh"})
    elif rec["lh"] and kp["instrument"] == "piano":
        # Cao trào: tay trái quãng tám ở phách 1 và 3 (mở rộng tầm xuống dưới, nguồn [7]).
        ctx.prev_lh = lh_root
        for k in (0, 2):
            ctx.tracks["keys"]["events"].append({"beat": start + k, "dur": 2.0, "midi": [lh_root, lh_root + 12],
                                                 "vel": 72, "art": "lh"})


def _bass_bar(ctx: Ctx, sec: Sec, e: int, h: Harmony, nxt: Harmony, bar_in: int, start: float, variant: int,
              rng: random.Random, pedal: Optional[Note]) -> None:
    bp, grid = ctx.pack["bass"], ctx.grid
    b_lo, b_hi = bp["range"]
    tonic = sec.tonic
    level = min(3, ENERGY_RECIPE[e]["bass"] + (1 if sec.add_layer else 0))
    out = ctx.tracks["bass"]["events"]
    if pedal is not None:
        # Pedal point: bass giữ một nốt (bậc V) trong khi hợp âm đổi → căng, "đòi" về Chorus (nguồn [3]).
        m = nearest_midi(pedal, ctx.prev_bass, b_lo, b_hi)
        bpat = pattern_for(bp["patterns"], max(2, level), variant, bar_in, grid)
        for beat, dur, ch in _hits(bpat, grid, start):
            if ch == "x":
                continue
            out.append({"beat": beat, "dur": min(dur, 1.0), "midi": [m], "vel": 92 if beat % 1 == 0 else 80,
                        "art": bp.get("art", "sustain")})
        ctx.prev_bass = m
        return
    if bp.get("walk") and level >= 2:
        notes = walking_bar(h, nxt, ctx.prev_bass, tonic, b_lo, b_hi, rng)
        for i, m in enumerate(notes):
            out.append({"beat": start + i, "dur": 0.92, "midi": [m], "vel": 92 if i % 2 == 0 else 84, "art": "sustain"})
        ctx.prev_bass = notes[-1]
        return
    bpat = pattern_for(bp["patterns"], level, variant, bar_in, grid)
    for beat, dur, ch in _hits(bpat, grid, start):
        if ch == "x":
            out.append({"beat": beat, "dur": 0.12, "midi": [ctx.prev_bass], "vel": 55, "art": "dead"})
            continue
        m = bass_note(ch.upper() if ch != "r" else "R", h, nxt, ctx.prev_bass, tonic, b_lo, b_hi, rng,
                      bp.get("approach", ["below", "scale"]))
        if ch == "A" and dur > 1:
            dur = 1
        out.append({"beat": beat, "dur": dur, "midi": [m],
                    "vel": 62 if ch == "r" else 100 if beat % BEATS_PER_BAR == 0 else 88 if beat % 1 == 0 else 76,
                    "art": bp.get("art", "sustain")})
        ctx.prev_bass = m


_GTR_ART = {"D": "down", "d": "down", "U": "up", "u": "up", "M": "mute", "P": "palm", "O": "down", "S": "stab",
            "s": "stab"}
_GTR_VEL = {"D": 96, "d": 72, "U": 80, "u": 60, "M": 70, "P": 88, "O": 104, "S": 90, "s": 70}


def _guitar_base(pack: dict, sec: Sec, e: int) -> bool:
    return "guitar" in sec.parts and ENERGY_RECIPE[e]["guitar"] >= pack["guitar"].get("min_energy", 2)


def _guitar_on(pack: dict, sec: Sec, e: int) -> bool:
    """Guitar chơi khi công thức năng lượng cho phép; "thêm một lớp" (Verse 2...) thì guitar vào nếu đang tắt."""
    if "guitar" not in sec.parts:
        return False
    return _guitar_base(pack, sec, e) or (sec.add_layer and e >= 2)


def _guitar_bar(ctx: Ctx, sec: Sec, e: int, h: Harmony, bar_in: int, start: float, variant: int,
                rng: random.Random) -> None:
    gp, grid = ctx.pack["guitar"], ctx.grid
    gv = guitar_voicing(h, gp["voicing"], ctx.prev_gtr, rng)
    ctx.prev_gtr = gv
    glevel = min(3, ENERGY_RECIPE[e]["guitar"] + (1 if sec.add_layer else 0))
    gpat = pattern_for(gp["patterns"], glevel, variant, bar_in, grid)
    for beat, dur, ch in _hits(gpat, grid, start):
        if ch.isdigit():
            idx = min(int(ch) - 1, len(gv) - 1)
            ctx.tracks["guitar"]["events"].append({"beat": beat, "dur": dur, "midi": [gv[idx]], "vel": 78, "art": "pick"})
            continue
        art = _GTR_ART.get(ch, "down")
        notes = gv if art != "stab" else gv[-3:]
        ctx.tracks["guitar"]["events"].append({"beat": beat, "dur": dur, "midi": notes, "vel": _GTR_VEL.get(ch, 80),
                                               "art": art})


def _snare_build(start_bar_beat: float, bars: int, out: list) -> None:
    """Snare dồn (nguồn [2]): ô áp chót móc đơn, ô cuối móc kép rồi móc ba ở 2 phách cuối, lực tăng dần, kick nốt đen."""
    hits: list[tuple[float, int]] = []
    if bars >= 2:
        b0 = start_bar_beat
        hits += [(b0 + i * 0.5, 50 + i * 3) for i in range(8)]
        start_bar_beat += BEATS_PER_BAR
    b1 = start_bar_beat
    hits += [(b1 + i * 0.25, 78 + i * 3) for i in range(8)]
    hits += [(b1 + 2 + i * 0.125, min(124, 100 + i * 2)) for i in range(16)]
    for beat, vel in hits:
        out.append({"beat": beat, "drum": "snare", "vel": vel})
    for k in range(4):
        out.append({"beat": b1 + k, "drum": "kick", "vel": 92})


# --- hook nhạc cụ -----------------------------------------------------------------------------------

def _hook_bars(sec: Sec, blocked: set[int]) -> list[tuple[int, bool]]:
    """(ô trong đoạn, chỉ_mảnh_ngắn). Luật mục E: nơi nên/hạn chế/không."""
    if not sec.hook or "hook" not in sec.parts:
        return []
    t, n = sec.type, sec.bars
    out: list[tuple[int, bool]] = []
    if t in ("intro", "chorus", "post", "outro"):
        out = [(b, False) for b in range(n) if b % 2 == 1]
        if t == "outro":
            out = out[:2]  # nhắc lại lần cuối, rồi để Outro lắng
    elif t == "solo":
        out = [(b, False) for b in (0, 1, n - 2, n - 1) if 0 <= b < n]
        out = sorted(set(out))
    elif t == "verse":
        out = [(b, True) for b in range(n) if b % 4 == 3][:2]
    return [(b, short) for b, short in out if (sec.start_bar + b) not in blocked]


def _scale_midis(tonic: Note, lo: int, hi: int) -> list[int]:
    pcs = {n.pitch_class for n in build_scale(tonic, "major")}
    return [m for m in range(lo - 2, hi + 3) if m % 12 in pcs]


def _hook_bar(rhythm: str, contour: list[int], h: Harmony, tonic: Note, start: float, grid: int, prev: int,
              short: bool) -> tuple[list[dict], int]:
    """Một lượt hook: phách mạnh rơi vào nốt hợp âm gần nhất, phách yếu là nốt trong gam (đi bậc theo đường nét)."""
    lo, hi = HOOK_RANGE
    scale = _scale_midis(tonic, lo, hi)
    chord_pcs = {h.roles[k].pitch_class for k in h.roles}
    chord = [m for m in range(lo, hi + 1) if m % 12 in chord_pcs]
    hits = list(_hits(rhythm, grid, start))
    if short:
        hits = hits[:2]
    events = []
    cur = prev
    strong_step = grid // 4
    for i, (beat, dur, _ch) in enumerate(hits):
        step = contour[i % len(contour)]
        cell = round((beat - start) * grid / BEATS_PER_BAR)
        if i == 0:
            target = min(chord, key=lambda m: (abs(m - cur), m))
        else:
            idx = min(range(len(scale)), key=lambda j: abs(scale[j] - cur))
            cand = scale[max(0, min(len(scale) - 1, idx + step))]
            if cell % strong_step == 0:
                target = min(chord, key=lambda m: (abs(m - cand), m))
            else:
                target = cand
        target = max(lo, min(hi, target))
        events.append({"beat": beat, "dur": min(dur, 2.0), "midi": [target], "vel": 84 if i == 0 else 76,
                       "art": "block"})
        cur = target
    return events, cur


# --- dựng bài ---------------------------------------------------------------------------------------

def _transpose_symbol(symbol: str, interval: str) -> str:
    chord = parse_chord_symbol(symbol)
    root = transpose(chord.root.with_octave(None), interval)
    out = build_chord(root, chord.type.id)
    if chord.bass is not None:
        return f"{out.symbol}/{transpose(chord.bass.with_octave(None), interval).name}"
    return out.symbol


def arrange_song(key: str, style: str, form: dict, seed: int = 1, energy: int = 2, bpm: Optional[int] = None) -> dict:
    if style not in PACKS:
        raise SongError("UNKNOWN_STYLE", f"Phong cách {style!r} không có.")
    if energy not in (1, 2, 3):
        raise SongError("BAD_ENERGY", "Năng lượng tổng chỉ nhận 1, 2 hoặc 3.")
    pack = PACKS[style]
    song_rules = pack["song"]
    grid = pack["grid"]
    try:
        tonic0 = parse_note(key).with_octave(None)
    except MusicEngineError as exc:
        raise SongError("BAD_KEY", f"Không đọc được giọng {key!r}.") from exc
    form = normalize_form(style, form)
    progs = form["progressions"]
    offset = energy - 2
    raw = form["sections"]
    labels = section_labels(raw)

    # 1. đoạn → Sec
    secs: list[Sec] = []
    occ: dict[str, int] = {}
    bar = 0
    explicit: set[int] = set()
    for i, s in enumerate(raw):
        occ[s["type"]] = occ.get(s["type"], 0) + 1
        ref = s.get("progression") or "A"
        ref = ref if progs.get(ref) and any(progs[ref]) else "A"   # QĐ 3A: vòng trống → tạm dùng A
        parts_rule = song_rules.get("parts", {}).get(s["type"])
        parts = set(parts_rule) if parts_rule else set(PARTS)
        if not form.get("hook", True):
            parts.discard("hook")
        e_design = int(s["energy"])
        sec_seed = int(s["seed"]) if s.get("seed") else _seed_int(seed, style, i, s["type"], occ[s["type"]])
        if (s.get("transition") or "auto") != "auto":
            explicit.add(i)
        secs.append(Sec(idx=i, type=s["type"], label=labels[i], bars=int(s["bars"]), start_bar=bar, ref=ref,
                        energy=max(1, min(5, e_design + offset)), design_energy=e_design,
                        feel=s.get("feel") or "auto", hook=bool(s.get("hook", True)),
                        transition=s.get("transition") or "auto", occurrence=occ[s["type"]], seed=sec_seed,
                        parts=parts, add_layer=False, tonic=tonic0))
        bar += int(s["bars"])
    total_bars = bar

    # 2. không lặp y hệt: lần lặp thứ 2+ của một loại đoạn (cùng hoặc thấp hơn năng lượng lần trước) thêm một lớp.
    last_e: dict[str, int] = {}
    for s in secs:
        if s.type in last_e and s.energy <= last_e[s.type] and s.type in ("verse", "chorus", "pre", "solo", "post"):
            s.add_layer = True
        last_e[s.type] = s.energy

    # 3. chuyển đoạn + đột biến
    for s in secs:
        nxt = secs[s.idx + 1].type if s.idx + 1 < len(secs) else None
        if s.transition == "auto":
            s.transition = _default_transition(style, s.type, nxt)
    surprises = _pick_surprises(style, secs, explicit, seed)
    for sp in surprises:
        s = secs[sp["section"]]
        if sp["kind"] in ("half", "double"):
            s.feel = sp["kind"]
        else:
            s.transition = sp["kind"]
    for s in secs:
        if s.feel == "auto":
            s.feel = "normal"
        if s.feel == "double" and grid != 16:
            s.feel = "normal"

    # 4. kết bài
    ending = form.get("ending") or "auto"
    if ending == "auto":
        ending = song_rules["ending"]
    last = secs[-1]

    # 5. hợp âm từng ô (+ lên giọng ở Chorus cuối nếu bật, QĐ 5A)
    mod = form.get("modulate") or {}
    mod_from: Optional[int] = None
    mod_interval = "m2" if int(mod.get("semitones", 1)) == 1 else "M2"
    last_chorus = max((s.idx for s in secs if s.type == "chorus"), default=-1)
    if mod.get("enabled") and last_chorus > 0:
        mod_from = last_chorus
    symbols: list[Optional[str]] = []
    bar_sec: list[Sec] = []
    for s in secs:
        chords = progs[s.ref]
        for b in range(s.bars):
            symbols.append(chords[b % len(chords)])
            bar_sec.append(s)
    key_map = [{"beat": 0.0, "key": tonic0.name}]
    if mod_from is not None:
        tonic1 = transpose(tonic0, mod_interval)
        start = secs[mod_from].start_bar
        for gb in range(start, total_bars):
            if symbols[gb]:
                symbols[gb] = _transpose_symbol(symbols[gb], mod_interval)
        for s in secs[mod_from:]:
            s.tonic = tonic1
        # Ô chuyển: át (V7) của giọng mới ở ô cuối đoạn trước, rồi Chorus cuối vào giọng mới.
        symbols[start - 1] = build_chord(transpose(tonic1, "P5"), "7").symbol
        key_map.append({"beat": float(start * BEATS_PER_BAR), "key": tonic1.name})
    if ending == "tag_x3" and last.bars >= 3:
        t = last.tonic
        ii, v, i_ = (build_chord(transpose(t, "M2"), "m7").symbol, build_chord(transpose(t, "P5"), "7").symbol,
                     build_chord(t, "maj7").symbol)
        tag = [ii, v] * 3
        n = last.bars
        seq = (tag + [i_] * n)[:n - 1] + [i_]
        for b in range(n):
            symbols[last.start_bar + b] = seq[b]
    fermata_bar = None
    if ending in ("ritardando_fermata", "tag_x3", "big_hit"):
        fermata_bar = total_bars - 1
        symbols[fermata_bar] = build_chord(last.tonic, "maj7" if ending == "tag_x3" else "maj").symbol

    rng_h = random.Random(_seed_int("harmony", seed, style, *[x or "-" for x in symbols]))
    harmonies: list[Optional[Harmony]] = []
    cache: dict[tuple[str, str], Harmony] = {}
    for gb, sym in enumerate(symbols):
        if not sym:
            harmonies.append(None)
            continue
        ck = (sym, bar_sec[gb].tonic.name)
        if ck not in cache:
            try:
                cache[ck] = harmonize(sym, bar_sec[gb].tonic, pack["color"], rng_h)
            except MusicEngineError as exc:
                raise SongError("BAD_CHORD", f"Không đọc được hợp âm {sym!r}.") from exc
        harmonies.append(cache[ck])
    if not any(harmonies):
        raise SongError("EMPTY_PROGRESSION", "Vòng A cần ít nhất một hợp âm.")

    # 6. dựng từng ô
    hook_inst = song_rules["hook"]["instrument"]
    tracks: dict[str, dict] = {
        "keys": {"instrument": pack["keys"]["instrument"], "events": []},
        "bass": {"instrument": pack["bass"]["instrument"], "events": []},
        "guitar": {"instrument": pack["guitar"]["instrument"], "events": []},
        "drums": {"kit": pack["drums"].get("kit", "acoustic"), "events": []},
        "hook": {"instrument": hook_inst, "events": []},
    }
    first_h = next(h for h in harmonies if h)
    ctx = Ctx(style, pack, grid, tracks, prev_bass=nearest_midi(first_h.roles["1"], 38, *pack["bass"]["range"]))
    silences: list[tuple[float, float, bool]] = []   # (bắt đầu, kết thúc, giữ nhát ở phách đầu)
    thin_bars: list[float] = []                       # ô trước cao trào: rút cymbal + bộ gõ (nguyên tắc 2)
    blocked_hook: set[int] = set()
    fx_events: list[dict] = []
    automation: list[dict] = []

    for s in secs:
        rng_s = random.Random(_seed_int("sec", s.seed, style, s.type, s.occurrence))
        variant = {p: rng_s.randrange(1_000_000) for p in ("keys", "bass", "guitar", "drums", "lh", "perc")}
        nxt_sec = secs[s.idx + 1] if s.idx + 1 < len(secs) else None
        pedal = transpose(s.tonic, "P5") if s.type == "pre" and "bass" in s.parts else None
        for b in range(s.bars):
            gb = s.start_bar + b
            start = gb * BEATS_PER_BAR
            h = harmonies[gb]
            nxt = next((x for x in harmonies[gb + 1:gb + 2] if x), None) or h
            e = s.energy
            # Luật thêm/bớt: đoạn dài hơn 8 ô thêm một lớp từ ô thứ 9 (nguồn [1]).
            if s.bars > 8 and b == 8 and not s.add_layer:
                s.add_layer = True
                s.notes.append("Từ ô 9 thêm một lớp để không quá 8 ô liền giống nhau.")
            last_bar = b == s.bars - 1
            mid_fill = s.bars > 8 and b == 7 and e >= 2
            fill = None
            if last_bar and s is not last and s.transition in ("fill_small", "fill_big", "riser", "reverse_cymbal", "pickup"):
                fill = {"fill_small": "small", "fill_big": "big"}.get(s.transition, "small" if e >= 2 else None)
            elif mid_fill:
                fill = "small"
            crash = b == 0 and s.idx > 0 and (e >= 4 or (e == 3 and s.type in ("verse", "solo", "post", "chorus")))
            # Đoạn dài hơn 8 ô: crash mở câu thứ 3 (ô 9) đánh dấu "câu mới" (luật thêm/bớt).
            crash = crash or (s.bars > 8 and b == 8 and e >= 2)
            build_bars = (min(2, s.bars) if (s.transition == "snare_build" and s is not last) else 0)
            in_build = b >= s.bars - build_bars and build_bars > 0
            special_end = gb == fermata_bar
            if special_end:
                continue
            if in_build:
                blocked_hook.add(gb)
                if b == s.bars - build_bars:
                    _snare_build(start, build_bars, tracks["drums"]["events"])
            else:
                _drums_bar(ctx, s, e, b, start, variant["drums"], fill, crash, tracks["drums"]["events"])
            if h is None:
                continue
            if "keys" in s.parts:
                _keys_bar(ctx, s, e, h, b, start, variant["keys"], variant["lh"], rng_s)
            if "bass" in s.parts:
                _bass_bar(ctx, s, e, h, nxt, b, start, variant["bass"], rng_s, pedal)
            if _guitar_on(pack, s, e):
                _guitar_bar(ctx, s, e, h, b, start, variant["guitar"], rng_s)

        # chuyển đoạn đặc biệt ở cuối đoạn
        end = s.end_beat
        if nxt_sec is not None and nxt_sec.type in ("chorus", "solo") and nxt_sec.energy > s.energy:
            thin_bars.append(end - BEATS_PER_BAR)
            blocked_hook.add(s.start_bar + s.bars - 1)
        if s is not last:
            if s.transition == "drop_bar":
                silences.append((end - 2, end, False))
                blocked_hook.add(s.start_bar + s.bars - 1)
                automation.append({"beat": end - 2, "target": "reverb_return", "value": 0.0, "ramp": 0.05})
                automation.append({"beat": end, "target": "reverb_return", "value": 1.0, "ramp": 0.0})
            elif s.transition == "stop_time":
                silences.append((end - BEATS_PER_BAR, end, True))
                blocked_hook.add(s.start_bar + s.bars - 1)
            elif s.transition == "riser":
                fx_events.append({"beat": end - 2 * BEATS_PER_BAR, "kind": "riser", "dur": 2.0 * BEATS_PER_BAR})
            elif s.transition == "reverse_cymbal":
                fx_events.append({"beat": end - 2, "kind": "reverse_cymbal", "dur": 2.0,
                                  "gain": 0.45 if style in ("jazz", "bossa") else 0.8})
            elif s.transition == "pickup":
                for k, vel in ((3.5, 70), (3.75, 84)):
                    tracks["drums"]["events"].append({"beat": end - BEATS_PER_BAR + k, "drum": "snare", "vel": vel})
        if pedal is not None:
            s.notes.append(f"Bass giữ nốt {pedal.name} (bậc V của giọng) suốt đoạn: pedal point tạo căng, "
                           "\"đòi\" giải quyết ở đoạn sau.")

    # bass nghỉ cả ô trước drop
    for (a, z, keep) in list(silences):
        if not keep and z - a == 2:
            tracks["bass"]["events"] = [ev for ev in tracks["bass"]["events"] if not (z - BEATS_PER_BAR <= ev["beat"] < z)]

    # 7. kết bài
    tail = 0.0
    end_beat = total_bars * BEATS_PER_BAR
    if fermata_bar is not None:
        fb = fermata_bar * BEATS_PER_BAR
        h = harmonies[fermata_bar]
        hold = 6.0 if ending != "big_hit" else 3.0
        kp = pack["keys"]
        if "keys" in last.parts and h is not None:
            v = lead(_thin(h, keys_tones(h, kp["voicing"]), None), ctx.prev_keys, kp["range"][0], kp["range"][1],
                     random.Random(seed), max_span=kp.get("max_span", 12), target_top=kp.get("top", 67))
            tracks["keys"]["events"].append({"beat": fb, "dur": hold, "midi": v, "vel": 96 if ending == "big_hit" else 80,
                                             "art": "roll" if ending != "big_hit" else "block"})
        if "bass" in last.parts and h is not None:
            m = nearest_midi(h.roles["1"], ctx.prev_bass, *pack["bass"]["range"])
            tracks["bass"]["events"].append({"beat": fb, "dur": hold, "midi": [m], "vel": 96, "art": "sustain"})
        if _guitar_on(pack, last, max(last.energy, 3)) and h is not None:
            gv = guitar_voicing(h, pack["guitar"]["voicing"], ctx.prev_gtr, random.Random(seed))
            tracks["guitar"]["events"].append({"beat": fb, "dur": hold, "midi": gv, "vel": 100, "art": "down"})
        if "drums" in last.parts:
            tracks["drums"]["events"].append({"beat": fb, "drum": "crash", "vel": 110 if ending == "big_hit" else 76})
            tracks["drums"]["events"].append({"beat": fb, "drum": "kick", "vel": 110 if ending == "big_hit" else 70})
            if ending == "big_hit":
                tracks["drums"]["events"].append({"beat": fb, "drum": "snare", "vel": 112})
        blocked_hook.add(fermata_bar)
        tail = hold - BEATS_PER_BAR + 1.5
    tempo_map: list[dict] = []
    base_bpm = bpm or pack["default_bpm"]
    if ending in ("ritardando_fermata", "tag_x3"):
        # Chậm dần 15% trong 2 ô cuối (nguồn [1], [6]).
        tempo_map = [{"beat": end_beat - 2 * BEATS_PER_BAR, "bpm": float(base_bpm), "ramp": False},
                     {"beat": end_beat - BEATS_PER_BAR, "bpm": round(base_bpm * 0.85, 2), "ramp": True}]
    if ending == "fade":
        fade_bars = min(4, last.bars)
        automation.append({"beat": end_beat - fade_bars * BEATS_PER_BAR, "target": "master", "value": -40.0,
                           "ramp": fade_bars * BEATS_PER_BAR})
        if pack["fx"].get("lofi"):
            automation.append({"beat": end_beat - fade_bars * BEATS_PER_BAR, "target": "filter", "value": 500.0,
                               "ramp": fade_bars * BEATS_PER_BAR})

    # 8. im lặng (drop, stop-time): bỏ nhát trong cửa sổ, cắt nốt đang ngân vào cửa sổ
    for (a, z, keep_first) in silences:
        for name, track in tracks.items():
            kept = []
            for ev in track["events"]:
                beat = ev["beat"]
                if a <= beat < z and not (keep_first and abs(beat - a) < 1e-9):
                    continue
                if "dur" in ev and beat < a < beat + ev["dur"]:
                    ev = {**ev, "dur": round(a - beat, 6)}
                if keep_first and abs(beat - a) < 1e-9 and "dur" in ev:
                    ev = {**ev, "dur": min(ev["dur"], 0.6)}
                kept.append(ev)
            track["events"] = kept
        if keep_first:
            # Stop-time: cả ban đánh một nhát đồng loạt ở phách 1 (kick + crash), rồi để trống cho giọng hát.
            tracks["drums"]["events"] = [ev for ev in tracks["drums"]["events"] if not abs(ev["beat"] - a) < 1e-9]
            tracks["drums"]["events"] += [{"beat": a, "drum": "kick", "vel": 108}, {"beat": a, "drum": "crash", "vel": 100}]

    # Nguyên tắc 2: ô ngay trước Chorus thưa hơn chính Chorus: bỏ hat/ride/bộ gõ, chỉ còn kick–snare–tom dẫn vào.
    airy = {"hh_c", "hh_o", "hh_p", "br_hh", "ride", "ride_b", "br_ride", "shaker", "tamb", "conga_h", "conga_l", "tri",
            "clap"}
    for a in thin_bars:
        tracks["drums"]["events"] = [ev for ev in tracks["drums"]["events"]
                                     if not (a <= ev["beat"] < a + BEATS_PER_BAR and ev["drum"] in airy)]

    # 9. hook
    rng_hook = random.Random(_seed_int("hook", seed, style, *[x or "-" for x in symbols[:8]]))
    rhythm = rng_hook.choice(song_rules["hook"]["rhythms"])
    contour = rng_hook.choice(HOOK_CONTOURS)
    prev_hook = 76
    hook_count: dict[int, int] = {}
    for s in secs:
        for b, short in _hook_bars(s, blocked_hook):
            gb = s.start_bar + b
            if any(a <= gb * BEATS_PER_BAR < z for a, z, _ in silences):
                continue
            h = harmonies[gb]
            if h is None:
                continue
            evs, prev_hook = _hook_bar(rhythm, contour, h, s.tonic, gb * BEATS_PER_BAR, grid, prev_hook, short)
            if hook_inst == "guitar":
                for ev in evs:
                    ev["art"] = "pick"
            tracks["hook"]["events"] += evs
            hook_count[s.idx] = hook_count.get(s.idx, 0) + 1

    # 10. automation theo đoạn
    def sec_db(sec) -> float:
        # Bù độ to theo vai trò đoạn của từng phong cách (chorus_trim_db trong style pack, đo 02/11/2026): mật độ lớp
        # làm Chorus to hơn Verse rất khác nhau giữa các phong cách (funk +0,6 LU, indie +5,9 LU). Bù dương thì đẩy
        # Chorus lên, bù âm thì đẩy Verse lên (không hạ Chorus), để mọi phong cách về khoảng +2…+4 LU.
        trim = song_rules.get("chorus_trim_db", 0.0)
        extra = trim if (trim > 0 and sec.type == "chorus") else (-trim if (trim < 0 and sec.type == "verse") else 0.0)
        return ENERGY_RECIPE[sec.energy]["db"] + extra

    for s in secs:
        db = sec_db(s)
        automation.append({"beat": s.start_beat, "target": "master", "value": db, "ramp": 0.0})
        reverb = 1.6 if s.type == "bridge" else 1.25 if s.type in ("intro", "outro", "breakdown") else 1.0
        automation.append({"beat": s.start_beat, "target": "reverb", "value": reverb, "ramp": 1.0 if s.idx else 0.0})
        if s.type == "intro" and (pack["fx"].get("lofi") or s.energy <= 1):
            # Intro lọc thấp rồi mở dần bộ lọc trong suốt Intro (nguồn [2]).
            automation.append({"beat": s.start_beat, "target": "filter", "value": 900.0 if pack["fx"].get("lofi") else 2500.0,
                               "ramp": 0.0})
            automation.append({"beat": s.start_beat, "target": "filter", "value": 20000.0, "ramp": float(s.bars * BEATS_PER_BAR)})
        if s.type == "pre" and s.idx + 1 < len(secs):
            # Pre-Chorus dâng dần âm lượng tới mức của đoạn sau (không bật đột ngột).
            nxt_db = sec_db(secs[s.idx + 1])
            automation.append({"beat": s.start_beat + 0.01, "target": "master", "value": (db + nxt_db) / 2 - 0.5,
                               "ramp": float(s.bars * BEATS_PER_BAR) - 0.5})
    # Cùng phách, cùng thông số: điểm "đặt ngay" đứng trước điểm "dốc", vì trình phát áp theo thứ tự và một điểm
    # đặt ngay đến sau sẽ hủy dốc (lỗi đo được 02/11: Outro fade bị mức của đoạn đè, không nhỏ dần).
    automation.sort(key=lambda a: (a["beat"], a["target"], a["ramp"] > 0))

    for track in tracks.values():
        track["events"].sort(key=lambda ev: (ev["beat"], ev.get("drum", "")))

    # 11. kết quả + ghi chú producer
    sections_out = []
    for s in secs:
        sections_out.append({
            "id": raw[s.idx].get("id") or f"s{s.idx + 1}", "type": s.type, "label": s.label,
            "start_beat": s.start_beat, "end_beat": s.end_beat, "bars": s.bars, "progression": s.ref,
            "progression_requested": raw[s.idx].get("progression") or "A",
            "energy": s.energy, "design_energy": s.design_energy, "feel": s.feel, "transition": s.transition if s is not last else None,
            "hook_bars": hook_count.get(s.idx, 0), "key": s.tonic.name,
            "note_vi": _note_vi(s, pack, ending if s is last else None, mod_from == s.idx),
        })
    surprise_out = []
    for sp in surprises:
        s = secs[sp["section"]]
        if sp["kind"] in ("half", "double"):
            surprise_out.append({"beat": s.start_beat, "kind": sp["kind"], "section": s.label,
                                 "label_vi": f"{s.label} chơi {'half-time' if sp['kind'] == 'half' else 'double-time'}"})
        else:
            surprise_out.append({"beat": s.end_beat - (2 if sp["kind"] == "drop_bar" else BEATS_PER_BAR), "kind": sp["kind"],
                                 "section": s.label, "label_vi": f"Cuối {s.label}: {TRANSITION_LABELS[sp['kind']]}"})
    if mod_from is not None:
        surprise_out.append({"beat": secs[mod_from].start_beat, "kind": "modulate", "section": secs[mod_from].label,
                             "label_vi": f"Lên giọng {secs[mod_from].tonic.name} ở {secs[mod_from].label}"})
    bars_out = []
    for gb, h in enumerate(harmonies):
        bars_out.append({"bar": gb, "symbol": symbols[gb], "played": h.color_label if h else None,
                         "section": bar_sec[gb].idx})
    wanted = {r.get("progression") or "A" for r in raw}
    suggestions = {slot: suggest_progression(key, style, slot, progs["A"], seed)
                   for slot in ("B", "C") if slot in wanted and not (progs.get(slot) and any(progs[slot]))}
    total_beats = float(end_beat)
    return {
        "version": SONG_VERSION, "mode": "song", "style": style, "seed": seed, "energy": energy, "key": tonic0.name,
        "bpm": base_bpm, "grid": grid, "bars_per_cycle": total_bars, "cycles": 1, "loop_from_cycle": 0,
        "total_beats": total_beats, "tail_beats": tail, "total_bars": total_bars,
        "duration_sec": round(_duration(total_beats, base_bpm, tempo_map), 2),
        "feel": pack["feel"], "fx": pack["fx"],
        "colors": [{"bar": b["bar"], "symbol": b["symbol"], "played": b["played"]} for b in bars_out],
        "bars": bars_out, "sections": sections_out, "automation": automation, "tempo_map": tempo_map,
        "key_map": key_map, "fx_events": fx_events, "surprises": surprise_out, "ending": ending,
        "suggestions": suggestions, "form": form, "tracks": tracks,
    }


def _duration(total_beats: float, bpm: float, tempo_map: list[dict]) -> float:
    """Giây thật của bài (có tính chậm dần tuyến tính), để hiện phút:giây trên dòng thời gian."""
    if not tempo_map:
        return total_beats * 60 / bpm
    a, b = tempo_map[0], tempo_map[1]
    before = a["beat"] * 60 / bpm
    span = b["beat"] - a["beat"]
    mean = (a["bpm"] + b["bpm"]) / 2
    after = (total_beats - b["beat"]) * 60 / b["bpm"]
    return before + span * 60 / mean + after


_ENERGY_VI = {1: "mộc", 2: "thưa", 3: "dồn", 4: "cao trào", 5: "đỉnh"}


def _note_vi(s: Sec, pack: dict, ending: Optional[str], modulated: bool) -> str:
    """Ghi chú producer 1–2 câu (QĐ 10A): đoạn này làm gì và vì sao."""
    rec = ENERGY_RECIPE[s.energy]
    parts = []
    if s.type == "intro":
        only = [p for p in ("keys", "guitar", "drums", "bass") if p in s.parts]
        names = {"keys": "phím", "guitar": "guitar", "drums": "trống", "bass": "bass"}
        parts.append(f"Intro chỉ {', '.join(names[p] for p in only)} để giới thiệu màu bài" if len(only) < 4
                     else "Intro mộc, bộ lọc mở dần")
    elif s.type == "verse":
        stick = s.energy <= 2 and pack["song"].get("verse_stick")
        parts.append(("Verse thưa: side-stick + hat đóng, " if stick else "Verse thưa: ") +
                     f"phím {rec['notes'] or 'đủ'} nốt tầm trung để chừa chỗ cho giọng hát")
    elif s.type == "pre":
        parts.append("Pre-Chorus dồn căng, âm lượng dâng dần")
    elif s.type == "chorus":
        parts.append(f"{s.label}: đủ ban nhạc, tầm rộng, crash đầu đoạn" + (", thêm tambourine" if s.energy >= 5 else ""))
    elif s.type == "bridge":
        parts.append("Bridge tương phản: vòng khác, reverb dài hơn")
    elif s.type == "breakdown":
        parts.append("Breakdown rút gần hết nhạc cụ để đoạn sau bùng lại")
    elif s.type == "solo":
        parts.append("Solo: ban nhạc đệm đầy hơn để bạn tự ứng tác lên trên")
    elif s.type == "post":
        parts.append("Post-Chorus lặp hook, hạ nhẹ trước đoạn sau")
    elif s.type == "outro":
        parts.append("Outro kết bài")
    if s.add_layer:
        parts.append("thêm một lớp so với lần trước để không lặp y hệt")
    if s.feel == "half":
        parts.append("trống half-time (snare ở phách 3) nghe chậm lại một nửa")
    elif s.feel == "double":
        parts.append("trống double-time cho cao trào chạy gấp đôi")
    if modulated:
        parts.append(f"lên giọng {s.tonic.name}, ô trước là át của giọng mới")
    text = "; ".join(parts) + "."
    text = text[0].upper() + text[1:]
    if ending:
        text += f" Kết bằng {ENDING_LABELS[ending]}."
    elif s.transition and s.transition != "none":
        reason = {"drop_bar": " để Chorus nổ hơn", "snare_build": " để dồn vào đoạn sau", "stop_time": " chừa chỗ cho câu hát",
                  "riser": " dâng lên trước cao trào", "reverse_cymbal": " hút vào đoạn mới"}.get(s.transition, "")
        text += f" Cuối đoạn: {TRANSITION_LABELS[s.transition]}{reason}."
    for n in s.notes:
        text += " " + n
    return text


def drum_events_for_song(key: str, style: str, form: dict, seed: int, energy: int) -> list[dict]:
    events = arrange_song(key, style, form, seed, energy)["tracks"]["drums"]["events"]
    return [{"drum": e["drum"], "start_beat": e["beat"], "velocity": e["vel"]} for e in events]
