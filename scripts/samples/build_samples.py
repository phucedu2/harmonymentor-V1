"""Dựng bộ mẫu âm thanh cho backing track Harmony Lab từ các thư viện giấy phép CC0 / CC-BY.

Chạy:  python scripts/samples/build_samples.py --cache .cache/samples-src
Cần:   git, ffmpeg (có libvorbis), numpy.

Vì sao có script này thay vì tải tay:
- Ghi lại chính xác lấy tệp nào, từ commit nào, giấy phép gì (CREDITS.md sinh tự động), để ai cũng dựng lại được.
- Đo cao độ thật của từng mẫu (YIN) thay vì tin tên tệp: thư viện Karoryfer đặt tên cao hơn tiếng thật 1 quãng tám
  (tệp "eb3" của bass kêu Eb2). Phát sai quãng tám là lỗi nhạc lý, nên script dừng nếu tên và tiếng lệch > 0,5 cung.
- Giữ nguyên tỷ lệ to/nhỏ giữa các lớp lực đánh (chỉ chuẩn hóa một hệ số cho cả nhạc cụ), vì khác biệt âm sắc
  giữa đánh nhẹ và đánh mạnh chính là thứ làm tiếng nghe "thật".
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "frontend" / "public" / "samples"
SR = 44100
NOTE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}

SOURCES = {
    "salamander": dict(url="https://github.com/sfzinstruments/SalamanderGrandPiano.git",
                       name="Salamander Grand Piano V3", author="Alexander Holm",
                       license="CC BY 3.0", license_url="https://creativecommons.org/licenses/by/3.0/"),
    "growlybass": dict(url="https://github.com/sfzinstruments/karoryfer.growlybass.git",
                       name="Growlybass (Squier Jazz Bass)", author="Karoryfer Lecolds",
                       license="CC0 1.0", license_url="https://creativecommons.org/publicdomain/zero/1.0/"),
    "doublebass": dict(url="https://github.com/sfzinstruments/dsmolken.double-bass.git",
                       name="Otto Rubner double bass (pizz)", author="D. Smolken",
                       license="CC0 1.0", license_url="https://creativecommons.org/publicdomain/zero/1.0/"),
    "guitars": dict(url="https://github.com/sfzinstruments/karoryfer.black-and-green-guitars.git",
                    name="Black And Green Guitars (Gretsch Anniversary)", author="Karoryfer Lecolds / Brian Wood",
                    license="CC0 1.0", license_url="https://creativecommons.org/publicdomain/zero/1.0/"),
    "rusty": dict(url="https://github.com/sfzinstruments/karoryfer.big-rusty-drums.git",
                  name="Big Rusty Drums", author="Karoryfer Lecolds",
                  license="CC0 1.0", license_url="https://creativecommons.org/publicdomain/zero/1.0/"),
    "vcsl": dict(url="https://github.com/sgossner/VCSL.git",
                 name="Versilian Community Sample Library (VCSL)", author="Versilian Studios / Sam Gossner",
                 license="CC0 1.0", license_url="https://creativecommons.org/publicdomain/zero/1.0/"),
}


# --- tiện ích âm thanh ------------------------------------------------------------------------------

def load(path: Path) -> np.ndarray:
    """Đọc mẫu thành mảng (kênh, mẫu) float32 ở 44,1 kHz."""
    info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels",
                           "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout
    ch = min(int(info.strip() or 1), 2)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, ch).T.copy()


def stereo(x: np.ndarray) -> np.ndarray:
    return np.vstack([x[0], x[0]]) if x.shape[0] == 1 else x


def onset(x: np.ndarray) -> int:
    """Vị trí bắt đầu có tiếng (vượt -50 dBFS), lùi 2 ms. Cắt khoảng lặng đầu để nốt vang đúng phách."""
    env = np.max(np.abs(x), axis=0)
    idx = np.flatnonzero(env > 10 ** (-50 / 20))
    return max(int(idx[0]) - int(0.002 * SR), 0) if idx.size else 0


def shape(x: np.ndarray, seconds: float, fade: float) -> np.ndarray:
    """Cắt khoảng lặng đầu, giới hạn độ dài, làm mờ đuôi để không nghe "tách" khi cắt."""
    x = x[:, onset(x):]
    n = min(x.shape[1], int(seconds * SR))
    x = x[:, :n].copy()
    f = min(int(fade * SR), n)
    if f:
        x[:, n - f:] *= np.linspace(1, 0, f, dtype=np.float32) ** 2
    return x


def yin(x: np.ndarray, start: float, end: float) -> float:
    """Tần số cơ bản (Hz) bằng YIN trên đoạn [start, end] giây sau khi bắt đầu có tiếng."""
    m = x[:, onset(x):].mean(axis=0).astype(np.float64)
    seg = m[int(start * SR): min(len(m), int(end * SR))]
    seg = seg - seg.mean()
    tmin, tmax = int(SR / 1500), int(SR / 28)
    n = len(seg) - tmax
    if n < SR // 50:
        return float("nan")
    d = np.array([np.sum((seg[:n] - seg[t:t + n]) ** 2) for t in range(tmax)])
    cm = np.ones_like(d)
    cm[1:] = d[1:] * np.arange(1, tmax) / np.maximum(np.cumsum(d[1:]), 1e-12)
    cands = [t for t in range(tmin, tmax - 1) if cm[t] < 0.15 and cm[t] <= cm[t - 1] and cm[t] <= cm[t + 1]]
    t = cands[0] if cands else tmin + int(np.argmin(cm[tmin:]))
    a, b, c = cm[t - 1], cm[t], cm[t + 1]
    return SR / (t + 0.5 * (a - c) / (a - 2 * b + c + 1e-12))


def name_pc(note: str) -> int:
    m = re.fullmatch(r"([a-gA-G])([#b]?)(-?\d)", note)
    letter, acc, _ = m.groups()
    return (NOTE[letter.lower()] + (1 if acc == "#" else -1 if acc == "b" else 0)) % 12


WINDOWS = ((0.08, 0.38), (0.12, 0.7), (0.03, 0.25))


def measured_midi(x: np.ndarray, note_name: str, expected: int) -> tuple[int, float]:
    """Kiểm cao độ thật bằng YIN trên vài đoạn thời gian (YIN đôi khi bắt nhầm quãng tám dưới).

    Trả (midi, lệch tính bằng nửa cung) nếu có đoạn đo khớp `expected`; nốt dưới E2 cho lệch tới 0,9 cung vì dây
    trầm gảy mạnh phô cao lúc đầu. Không khớp ở mọi đoạn thì dừng: thà không dựng còn hơn phát sai cao độ.
    """
    readings = []
    for start, end in WINDOWS:
        f = yin(x, start, end)
        if not np.isfinite(f):
            continue
        exact = 69 + 12 * np.log2(f / 440)
        readings.append(round(float(exact), 2))
        tolerance = 0.9 if expected < 40 else 0.5
        if abs(exact - expected) <= tolerance:
            return expected, float(exact - expected)
    raise SystemExit(f"Cao độ đo được {readings} không khớp tên {note_name} (mong đợi MIDI {expected})")


def encode(x: np.ndarray, path: Path, quality: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ch = x.shape[0]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", str(ch), "-i", "-",
                    "-c:a", "libvorbis", "-q:a", str(quality), str(path)],
                   input=np.ascontiguousarray(x.T).astype(np.float32).tobytes(), check=True)


# --- nguồn (git partial clone, chỉ tải tệp cần) ----------------------------------------------------

class Repo:
    def __init__(self, key: str, cache: Path):
        self.key = key
        self.dir = cache / key
        if not (self.dir / ".git").exists():
            subprocess.run(["git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--no-checkout",
                            SOURCES[key]["url"], str(self.dir)], check=True)
        self.commit = self._git("rev-parse", "HEAD").strip()
        self.files = self._git("ls-tree", "-r", "--name-only", "HEAD").splitlines()

    def _git(self, *args: str) -> str:
        return subprocess.run(["git", "-C", str(self.dir), *args], capture_output=True, text=True, check=True).stdout

    def fetch(self, paths: list[str]) -> None:
        missing = [p for p in paths if not (self.dir / p).exists()]
        for i in range(0, len(missing), 200):
            subprocess.run(["git", "-C", str(self.dir), "checkout", "-q", "HEAD", "--", *missing[i:i + 200]], check=True)

    def glob(self, pattern: str) -> list[str]:
        rx = re.compile(pattern)
        return sorted(f for f in self.files if rx.search(f))


# --- cấu hình từng nhạc cụ -------------------------------------------------------------------------

@dataclass
class Zone:
    sources: list[tuple[str, float]]  # (đường dẫn trong repo, dB) — nhiều mic thì trộn lại
    layer: int
    rr: int
    note: str | None = None
    midi: int | None = None
    cents: float = 0.0
    file: str = ""
    seconds: float = 0.0


@dataclass
class Instrument:
    key: str
    repo: str
    label: str
    layers: int
    seconds: float | dict
    fade: float = 0.25
    quality: float = 5
    mono: bool = False
    lite_layers: list[int] = field(default_factory=list)
    # Tên tệp đã đúng cao độ (VCSL, Salamander): đo chỉ để kiểm, lệch thì ghi cảnh báo (âm FM nhiều họa âm làm YIN bắt nhầm).
    trust_names: bool = False
    octave_shift: int = 0
    zones: dict[str, list[Zone]] = field(default_factory=dict)  # mảnh (piece) → vùng; nhạc cụ có cao độ dùng "notes"


def spread(values: list[int], count: int) -> list[int]:
    """Chọn `count` giá trị trải đều, luôn giữ giá trị lớn nhất (đánh mạnh nhất)."""
    values = sorted(set(values))
    if len(values) <= count:
        return values
    idx = np.linspace(0, len(values) - 1, count).round().astype(int)
    return [values[i] for i in idx]


def grid_notes(names: list[str], low: int, high: int, step: int, pitch_of) -> list[str]:
    """Chọn nốt cách đều `step` nửa cung trong tầm [low, high] (theo cao độ ước lượng từ tên)."""
    by_pitch = {pitch_of(n): n for n in names}
    picked, last = [], -99
    for p in sorted(by_pitch):
        if low <= p <= high and p - last >= step:
            picked.append(by_pitch[p])
            last = p
    return picked


def name_midi(note: str, octave_shift: int = 0) -> int:
    m = re.fullmatch(r"([a-gA-G])([#b]?)(-?\d)", note)
    letter, acc, octave = m.groups()
    return 12 * (int(octave) + 1 + octave_shift) + NOTE[letter.lower()] + (1 if acc == "#" else -1 if acc == "b" else 0)


def pitched(inst: Instrument, repo: Repo, rx: str, low: int, high: int, step: int, layers: list[str],
            rrs: list[int], octave_shift: int = 0) -> None:
    """Nhạc cụ có cao độ: rx bắt các nhóm (note, layer, rr)."""
    found: dict[tuple[str, str, int], str] = {}
    for path in repo.glob(rx):
        m = re.search(rx, path)
        note, layer, rr_raw = m.group("note"), m.group("layer"), m.groupdict().get("rr") or "1"
        rr = ord(rr_raw) - ord("a") + 1 if rr_raw.isalpha() else int(rr_raw)  # rr ghi bằng chữ (a, b) hoặc số
        found[(note, layer, rr)] = path
    names = sorted({k[0] for k in found})
    notes = grid_notes(names, low, high, step, lambda n: name_midi(n, octave_shift))
    zones = []
    for note in notes:
        for li, layer in enumerate(layers):
            for rr in rrs:
                path = found.get((note, layer, rr))
                if path:
                    zones.append(Zone([(path, 0.0)], li, rr, note=note))
    inst.zones["notes"] = zones


def piece(inst: Instrument, repo: Repo, name: str, mics: list[tuple[str, float]], layers: int, rrs: int,
          rx: str = r"vl?(\d+)_rr(\d+)") -> None:
    """Một mảnh trống: các thư mục mic (cùng tên tệp) trộn lại; chọn `layers` lớp lực, `rrs` lần đánh khác nhau."""
    first_dir = mics[0][0]
    files = [f for f in repo.files if f.startswith(first_dir + "/")]
    table: dict[tuple[int, int], str] = {}
    for f in files:
        m = re.search(rx, f.rsplit("/", 1)[1])
        if m:
            table[(int(m.group(1) or 1), int(m.group(2) or 1))] = f.rsplit("/", 1)[1]
    chosen = spread([v for v, _ in table], layers)
    zones = []
    for li, v in enumerate(chosen):
        for rr in sorted({r for (vv, r) in table if vv == v})[:rrs]:
            fname = table[(v, rr)]
            srcs = []
            for d, db in mics:
                cand = f"{d}/{fname}"
                if cand not in repo.files:  # vài thư mục mic đặt tên khác chút → tìm theo vl/rr
                    alt = [f for f in repo.files if f.startswith(d + "/") and re.search(rf"vl?{v}_rr{rr}\b", f)]
                    if not alt:
                        continue
                    cand = alt[0]
                srcs.append((cand, db))
            zones.append(Zone(srcs, li, rr))
    inst.zones[name] = zones


def build_config(repos: dict[str, Repo]) -> list[Instrument]:
    insts: list[Instrument] = []

    # Piano: Salamander, nốt cách quãng 3 thứ (A0..C8), 4 lớp lực (v4, v8, v12, v16 trên 16 lớp gốc).
    piano = Instrument("piano", "salamander", "Piano (Yamaha C5)", 4,
                       seconds={36: 7.0, 60: 5.5, 84: 3.5, 128: 2.5}, fade=1.2, lite_layers=[1, 3],
                       trust_names=True)
    pitched(piano, repos["salamander"], r"Samples/(?P<note>[A-G]#?\d)v(?P<layer>4|8|12|16)\.flac$",
            low=24, high=96, step=3, layers=["4", "8", "12", "16"], rrs=[1])
    insts.append(piano)

    # Phím điện FM (Lo-fi, Jazz, R&B): TX81Z, nốt cách quãng 3 trưởng, 3 lớp.
    ep = Instrument("epiano", "vcsl", "Electric piano (TX81Z FM)", 3, seconds={60: 5.0, 128: 3.5}, fade=1.0,
                    lite_layers=[1], trust_names=True)
    pitched(ep, repos["vcsl"], r"Electrophones/TX81Z/FM Piano/FMPiano_(?P<note>[A-G]#?\d)_vl(?P<layer>[123])\.wav$",
            low=36, high=88, step=4, layers=["1", "2", "3"], rrs=[1])
    insts.append(ep)

    # Clavisynth: ghi chú VCSL nói mẫu "8va"; đo phổ thấy tệp C4 kêu C6 (họa âm thấp nhất 1047 Hz), nên dịch +2 quãng tám.
    clav = Instrument("clav", "vcsl", "Clavi (TX81Z FM)", 3, seconds=2.0, fade=0.5, lite_layers=[1], octave_shift=2)
    pitched(clav, repos["vcsl"], r"Electrophones/TX81Z/Clavisynth/Clavisynth_(?P<note>[A-G]#?\d)_vl(?P<layer>[123])\.wav$",
            low=52, high=88, step=4, layers=["1", "2", "3"], rrs=[1], octave_shift=2)
    insts.append(clav)

    # Bass điện: Growlybass, tên tệp cao hơn tiếng thật 1 quãng tám (đã đo), 3 lớp × 2 lần đánh.
    bass = Instrument("bass", "growlybass", "Electric bass (Squier Jazz)", 3, seconds=3.5, fade=0.6, mono=True,
                      lite_layers=[1, 2], octave_shift=-1)
    pitched(bass, repos["growlybass"], r"^sustain/(?P<note>[a-g]b?\d)_(?P<layer>p|f|ff)_rr(?P<rr>[12])\.wav$",
            low=28, high=60, step=1, layers=["p", "f", "ff"], rrs=[1, 2], octave_shift=-1)
    insts.append(bass)

    # Contrabass gảy (Jazz, Bossa): đặt tên đúng cao độ.
    upright = Instrument("upright", "doublebass", "Upright bass (pizz)", 3, seconds=3.0, fade=0.8, mono=True,
                         lite_layers=[1])
    pitched(upright, repos["doublebass"], r"^pizz/pizz_(?P<note>[a-g]b?\d)_(?P<layer>[pmf])(?P<rr>[ab])\.wav$",
            low=24, high=57, step=1, layers=["p", "m", "f"], rrs=[1, 2])
    insts.append(upright)

    # Guitar điện clean (Gretsch), tên tệp cao hơn 1 quãng tám; 3 lớp × 2 lần đánh; thêm staccato cho funk/rock.
    gtr = Instrument("guitar", "guitars", "Electric guitar (Gretsch, clean)", 3, seconds=3.0, fade=0.8, mono=True,
                     lite_layers=[1], octave_shift=-1)
    pitched(gtr, repos["guitars"], r"Samples/green/ord/twang_(?P<note>[a-g]b?\d)_(?P<layer>p|mf|f)_rr(?P<rr>[12])\.wav$",
            low=40, high=79, step=2, layers=["p", "mf", "f"], rrs=[1, 2], octave_shift=-1)
    insts.append(gtr)

    mute = Instrument("guitar_mute", "guitars", "Electric guitar staccato", 1, seconds=0.6, fade=0.15, mono=True,
                      lite_layers=[0], octave_shift=-1)
    pitched(mute, repos["guitars"], r"Samples/green/stac/staccato_(?P<note>[a-g]b?\d)_rr(?P<rr>[12])\.wav$()(?P<layer>)",
            low=40, high=79, step=3, layers=[""], rrs=[1, 2], octave_shift=-1)
    insts.append(mute)

    # Trống acoustic: Big Rusty Drums, trộn mic gần + overhead thành một mẫu stereo cho mỗi nhát.
    kit = Instrument("drums", "rusty", "Acoustic kit (Big Rusty Drums)", 4, seconds={"default": 1.6}, fade=0.4,
                     lite_layers=[1, 3])
    r = repos["rusty"]
    S = "Samples/"
    piece(kit, r, "kick", [(S + "kick_24/kick/kick", 0), (S + "kick_24/kick/oh", -9)], 4, 3)
    piece(kit, r, "snare", [(S + "snare_14/center/top", 0), (S + "snare_14/center/btm", -10)], 4, 4)
    piece(kit, r, "rim", [(S + "snare_14/rimshot/top", 0), (S + "snare_14/rimshot/btm", -10)], 3, 3)
    piece(kit, r, "xstick", [(S + "snare_14/sidestick/top", 0)], 3, 3)
    piece(kit, r, "br_snare", [(S + "snare_14/brush/top", 0), (S + "snare_14/brush/btm", -12)], 3, 3)
    piece(kit, r, "hh_c", [(S + "hihat_14/tc/cl", 0), (S + "hihat_14/tc/oh", -6)], 4, 4)
    piece(kit, r, "hh_o", [(S + "hihat_14/open/cl", 0), (S + "hihat_14/open/oh", -6)], 3, 2)
    piece(kit, r, "hh_p", [(S + "hihat_14/chik/cl", 0), (S + "hihat_14/chik/oh", -6)], 2, 3)
    piece(kit, r, "br_hh", [(S + "hihat_14/tc_brush/cl", 0), (S + "hihat_14/tc_brush/oh", -6)], 3, 3)
    piece(kit, r, "ride", [(S + "ride_22/rd/cl", -3), (S + "ride_22/rd/oh", 0)], 3, 3)
    piece(kit, r, "ride_b", [(S + "ride_22/bl/cl", -3), (S + "ride_22/bl/oh", 0)], 2, 2)
    piece(kit, r, "br_ride", [(S + "ride_22/brush/cl", -3), (S + "ride_22/brush/oh", 0)], 2, 2)
    piece(kit, r, "crash", [(S + "crash_17/cr/cl", -3), (S + "crash_17/cr/oh", 0)], 3, 2)
    piece(kit, r, "tom_h", [(S + "tom_14/center/cl", 0), (S + "tom_14/center/oh", -8)], 3, 2)
    piece(kit, r, "tom_m", [(S + "tom_15/center/cl", 0), (S + "tom_15/center/oh", -8)], 3, 2)
    piece(kit, r, "tom_f", [(S + "tom_18/center/cl", 0), (S + "tom_18/center/oh", -8)], 3, 2)
    insts.append(kit)

    # Bộ gõ phụ (R&B, Bossa, Indie): VCSL.
    perc = Instrument("perc", "vcsl", "Percussion (VCSL)", 3, seconds={"default": 1.2}, fade=0.3, lite_layers=[0, 1, 2])
    v = repos["vcsl"]
    I = "Idiophones/Struck Idiophones/"
    M = "Membranophones/Struck Membranophones/"
    piece(perc, v, "conga_h", [(M + "Conga", 0)], 2, 2, rx=r"^Quinto_HitN_v(\d+)_rr(\d+)")
    piece(perc, v, "conga_l", [(M + "Conga", 0)], 2, 2, rx=r"^Conga_HitN_v(\d+)_rr(\d+)")
    piece(perc, v, "shaker", [(I + "Shaker, Small", 0)], 1, 2, rx=r"^Mid_ShakerDouble_Down()_rr(\d+)")
    piece(perc, v, "tamb", [(I + "Tambourine 1", 0)], 2, 1, rx=r"^Tamb1_Hit_v(\d+)_rr(\d+)")
    piece(perc, v, "tri", [(I + "Triangles", 0)], 2, 2, rx=r"^Triangle1_Hit_v(\d+)_rr(\d+)")
    piece(perc, v, "clap", [(I + "Claps", 0)], 1, 4, rx=r"^Clap()_rr(\d+)")
    insts.append(perc)
    return insts


def seconds_for(inst: Instrument, midi: int | None) -> float:
    if isinstance(inst.seconds, (int, float)):
        return float(inst.seconds)
    if midi is None:
        return float(inst.seconds["default"])
    for upper, sec in sorted((k, v) for k, v in inst.seconds.items() if k != "default"):
        if midi <= upper:
            return float(sec)
    return 2.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(ROOT / ".cache" / "samples-src"))
    ap.add_argument("--only", nargs="*", help="chỉ dựng các nhạc cụ này")
    args = ap.parse_args()
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)

    repos = {k: Repo(k, cache) for k in SOURCES}
    insts = build_config(repos)
    if args.only:
        insts = [i for i in insts if i.key in args.only]

    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"instruments": {}}
    for inst in insts:
        repo = repos[inst.repo]
        all_zones = [z for zs in inst.zones.values() for z in zs]
        if not all_zones:
            raise SystemExit(f"{inst.key}: không chọn được mẫu nào (kiểm tra regex)")
        repo.fetch(sorted({p for z in all_zones for p, _ in z.sources}))
        rendered = []
        skipped: list[Zone] = []
        for piece_name, zones in inst.zones.items():
            for z in zones:
                mixes = []
                for path, db in z.sources:
                    x = load(repo.dir / path)
                    mixes.append(stereo(x) * (10 ** (db / 20)))
                n = max(m.shape[1] for m in mixes)
                x = np.zeros((2, n), dtype=np.float32)
                for m in mixes:
                    x[:, :m.shape[1]] += m
                if z.note is not None:
                    expected = name_midi(z.note, inst.octave_shift)
                    try:
                        z.midi, z.cents = measured_midi(x, z.note, expected)
                    except SystemExit as exc:
                        if not inst.trust_names:
                            # Mẫu thư viện ghi nhầm cao độ (vd Growlybass "gb3" lớp ff kêu Gb1): bỏ mẫu đó,
                            # lúc phát tự dùng lớp lực gần nhất.
                            print(f"  bỏ {inst.key} {z.note} lớp {z.layer} rr{z.rr}: {exc}")
                            skipped.append(z)
                            continue
                        # Âm FM nhiều họa âm làm YIN bắt nhầm; tên tệp VCSL/Salamander đã đúng nên giữ theo tên.
                        print(f"  cảnh báo {inst.key} {z.note}: {exc} — giữ cao độ theo tên tệp")
                        z.midi, z.cents = expected, 0.0
                if inst.mono or np.allclose(x[0], x[1]):
                    x = x[:1]
                x = shape(x, seconds_for(inst, z.midi), inst.fade)
                z.seconds = x.shape[1] / SR
                base = f"{z.midi}" if z.midi is not None else piece_name
                z.file = f"{inst.key}/{base}_v{z.layer}_r{z.rr}.ogg" if piece_name == "notes" else \
                    f"{inst.key}/{piece_name}_v{z.layer}_r{z.rr}.ogg"
                rendered.append((piece_name, z, x))
        # Một hệ số cho cả nhạc cụ: mẫu to nhất đạt -1 dBFS, giữ nguyên tỷ lệ giữa các lớp lực.
        peak = max(float(np.max(np.abs(x))) for _, _, x in rendered)
        gain = (10 ** (-1 / 20)) / peak
        for _, z, x in rendered:
            encode(x * gain, OUT / z.file, inst.quality)
        src = SOURCES[inst.repo]
        entry = {
            "label": inst.label, "layers": inst.layers, "lite_layers": inst.lite_layers,
            "source": {"name": src["name"], "author": src["author"], "license": src["license"],
                       "license_url": src["license_url"], "repo": src["url"], "commit": repo.commit},
            "pieces": {p: [{"file": z.file, "midi": z.midi, "cents": round(z.cents, 3), "layer": z.layer, "rr": z.rr,
                            "seconds": round(z.seconds, 3), "from": [s for s, _ in z.sources]} for z in zs]
                       for p, zs in inst.zones.items()},
        }
        for p_name in entry["pieces"]:
            entry["pieces"][p_name] = [e for e in entry["pieces"][p_name] if e["file"]]
        entry["skipped"] = [{"note": z.note, "layer": z.layer, "rr": z.rr} for z in skipped]
        manifest["instruments"][inst.key] = entry
        size = sum((OUT / z.file).stat().st_size for _, z, _ in rendered)
        print(f"{inst.key:12s} {len(rendered):4d} mẫu  {size / 1e6:6.2f} MB  ({src['license']})")
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    write_credits(manifest)


def write_credits(manifest: dict) -> None:
    lines = ["# Ghi công mẫu âm thanh (sinh tự động bởi scripts/samples/build_samples.py)", "",
             "Mọi mẫu trong thư mục này lấy từ thư viện có giấy phép CC0 hoặc CC BY. Mẫu đã được cắt độ dài, làm mờ",
             "đuôi, trộn các mic (trống) và nén Ogg Vorbis; cao độ đo lại bằng YIN. Không có mẫu nào giấy phép không rõ.", "",
             "| Nhạc cụ | Thư viện | Tác giả | Giấy phép | Nguồn (commit) | Số mẫu |", "|---|---|---|---|---|---|"]
    for key, inst in manifest["instruments"].items():
        s = inst["source"]
        count = sum(len(v) for v in inst["pieces"].values())
        lines.append(f"| {key} | {s['name']} | {s['author']} | [{s['license']}]({s['license_url']}) | "
                     f"{s['repo']} (`{s['commit'][:10]}`) | {count} |")
    lines += ["", "Salamander Grand Piano V3 © Alexander Holm, giấy phép CC BY 3.0: phải giữ dòng ghi công này khi phân phối.",
              "Các thư viện CC0 không bắt buộc ghi công; vẫn ghi để minh bạch nguồn gốc.", ""]
    (OUT / "CREDITS.md").write_text("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
