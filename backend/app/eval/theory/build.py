"""Sinh eval/theory/questions.jsonl: 300 câu, nhóm "bai" (L01–L08) và "ngoai" (âm nhạc ngoài bài).

Chạy: python -m app.eval.theory.build. Tất định (không ngẫu nhiên), nên sinh lại cho cùng tệp.
Đáp án nốt/quãng/giọng/số La Mã lấy từ Music Engine; phần Engine không tính (chức năng, nhịp, cadence...) ghi tay
và đánh dấu ref="nhạc lý chuẩn" để người chấm soát lại."""

from __future__ import annotations

import json
from pathlib import Path

from ...music_engine import tools as T
from ...music_engine.interval import transpose
from ...music_engine.key import key_signature, relative_minor
from ...music_engine.roman import diatonic_chords

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "eval" / "theory" / "questions.jsonl"

NUM_VI = {0: "không", 1: "một", 2: "hai", 3: "ba", 4: "bốn", 5: "năm", 6: "sáu", 7: "bảy"}
IV_VI = {"P": "đúng", "M": "trưởng", "m": "thứ", "A": "tăng", "d": "giảm"}
IV_EN = {"P": "perfect", "M": "major", "m": "minor", "A": "augmented", "d": "diminished"}
ORD_EN = {1: "unison", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth", 7: "seventh", 8: "octave"}
SOLFEGE = {"C": "Đô", "D": "Rê", "E": "Mi", "F": "Fa", "G": "Sol", "A": "La", "B": "Si"}

rows: list[dict] = []


def add(group, topic, q, answer, ref="Music Engine", trap=False, subject=None, **expect):
    row = {"id": f"T{len(rows) + 1:03d}", "group": group, "topic": topic, "q": q, "answer": answer,
           "ref": ref, "trap": trap, "expect": {k: v for k, v in expect.items() if v}}
    if subject:
        row["subject"] = subject              # ký hiệu được hỏi, để test đối chiếu lại Engine
    rows.append(row)


def tones(sym: str) -> list[str]:
    out = T.get_chord_tones(symbol=sym)
    assert out["ok"], (sym, out)
    return out["notes"]


def scale(tonic: str, kind: str) -> list[str]:
    out = T.get_scale(tonic=tonic, scale_type=kind)
    assert out["ok"], (tonic, kind, out)
    return out["notes"]


def sym_variants(sym: str) -> list[str]:
    """Các cách viết cùng một hợp âm được chấp nhận (ADR-016: maj7 = M7 = Δ7; m7b5 = ø7)."""
    for q, alts in (("maj7", ["maj7", "M7", "Δ7", "∆7"]), ("m7b5", ["m7b5", "ø7", "ø", "m7(b5)"]), ("dim7", ["dim7", "°7"]),
                    ("m7", ["m7", "min7", "-7"]), ("7", ["7"]), ("dim", ["dim", "°"]), ("m", ["m", "min"])):
        if sym.endswith(q):
            root = sym[: -len(q)]
            return [root + a for a in alts]
    return [sym]


def numword(n: int) -> list[str]:
    return [str(n), NUM_VI[n]]


def acc_phrases(n: int, kind: str) -> list[str]:
    vi = "thăng" if kind == "sharp" else "giáng"
    en = "sharp" if kind == "sharp" else "flat"
    return [f"{w} dấu {vi}" for w in numword(n)] + [f"{w} {vi}" for w in numword(n)] + [f"{n} {en}"] + [
        f"{w} dấu hóa" for w in numword(n)]


def interval_phrases(name: str) -> list[str]:
    qual, num = name[0], int(name[1:])
    vi = IV_VI[qual]
    nums = [str(num)] + ([NUM_VI[num]] if num in NUM_VI else [])
    out = [name]
    for n in nums:
        out += [f"{n} {vi}", f"quãng {n} {vi}", f"{vi} {n}"]
    if num == 8:
        out += [f"quãng tám {vi}", f"quãng 8 {vi}", "octave", "quãng tám"] if qual == "P" else [f"quãng tám {vi}"]
    if num == 1:
        out += ["đồng âm", "unison"]
    out += [f"{IV_EN[qual]} {ORD_EN[num]}"]
    return out


# --- 1. Hợp âm: thành phần nốt (bài L01, L02; ngoài bài: sus, 9, 13, dim7) --------------------------------------
CHORD_Q = ["Hợp âm {s} gồm những nốt nào?", "Cho mình các nốt của hợp âm {s} với.", "hop am {s} co nhung not gi",
           "What notes are in the {s} chord?", "Hợp âm {s} được cấu tạo từ những nốt nào?", "Liệt kê nốt của hợp âm {s}."]
lesson_chords = ["C", "Dm", "F#m", "Bb", "Eb", "Ab", "Bdim", "F#dim", "Caug", "Gm", "Db", "E",
                 "Cmaj7", "Dm7", "G7", "Fmaj7", "Bm7b5", "Ebmaj7", "Abmaj7", "Bbm7", "F#m7", "C#m7b5", "D7",
                 "E7", "B7", "Gbmaj7", "Dbmaj7", "G#m7", "Ebm7b5", "Fø7"]
for i, s in enumerate(lesson_chords):
    n = tones(s)
    add("bai", "thanh_phan_hop_am", CHORD_Q[i % len(CHORD_Q)].format(s=s), " ".join(n), subject=s, notes_all=n)
outside_chords = ["Gsus4", "Dsus2", "Csus4", "Cmaj9", "Dm9", "G9", "G13", "Fmaj9", "Am9", "Bb9", "C#dim7", "Bbdim7",
                  "Ebdim7", "F#dim7"]
for i, s in enumerate(outside_chords):
    n = tones(s)
    add("ngoai", "thanh_phan_hop_am", CHORD_Q[i % len(CHORD_Q)].format(s=s), " ".join(n), subject=s, notes_all=n)

# Bẫy tiền đề sai về thành phần hợp âm
for s, wrong in [("Cmaj7", "Bb"), ("G7", "F#"), ("Dm7b5", "A"), ("Ebm7b5", "A"), ("Bbmaj7", "Ab"), ("F#m", "A#"),
                 ("A7", "C"), ("E7", "G")]:
    n = tones(s)
    add("bai", "bay_thanh_phan", f"Vì sao hợp âm {s} lại có nốt {wrong}?", f"{s} = {' '.join(n)}; không có {wrong}",
        trap=True, notes_all=n)

# --- 2. Âm giai (L02; thứ hòa âm/giai điệu, mode là ngoài bài) -----------------------------------------------------
SCALE_Q = {"major": ["Âm giai {t} trưởng gồm những nốt nào?", "Viết âm giai {t} major giúp mình.",
                     "am giai {t} truong co nhung not nao"],
           "natural_minor": ["Âm giai {t} thứ tự nhiên gồm những nốt nào?", "{t} natural minor scale có nốt gì?"],
           "harmonic_minor": ["Âm giai {t} thứ hòa âm gồm những nốt nào?"],
           "melodic_minor": ["Âm giai {t} thứ giai điệu đi lên gồm những nốt nào?"],
           "dorian": ["{t} Dorian gồm những nốt nào?"], "mixolydian": ["{t} Mixolydian gồm những nốt nào?"]}
for i, t in enumerate(["G", "D", "E", "F#", "C#", "Bb", "Eb", "Ab", "Db", "Gb"]):
    n = scale(t, "major")
    add("bai", "am_giai", SCALE_Q["major"][i % 3].format(t=t), " ".join(n), notes_all=n)
for i, t in enumerate(["A", "E", "F#", "D", "C", "F", "C#", "G#"]):
    n = scale(t, "natural_minor")
    add("bai", "am_giai", SCALE_Q["natural_minor"][i % 2].format(t=t), " ".join(n), notes_all=n)
for kind, tonics in (("harmonic_minor", ["A", "C", "E", "D"]), ("melodic_minor", ["A", "D", "G"]),
                     ("dorian", ["E", "A"]), ("mixolydian", ["D", "A"])):
    for t in tonics:
        n = scale(t, kind)
        add("ngoai", "am_giai", SCALE_Q[kind][0].format(t=t), " ".join(n), notes_all=n)
for t, kind, name in (("D", "dorian", "D Dorian"), ("G", "mixolydian", "G Mixolydian")):
    n = scale(t, kind)
    add("bai", "chord_scale", f"{name} gồm những nốt nào?", " ".join(n), notes_all=n)
# Mode Engine chưa có: ghi tay, người chấm soát
for q, ans in [("F Lydian gồm những nốt nào?", "F G A B C D E"), ("E Phrygian gồm những nốt nào?", "E F G A B C D"),
               ("B Locrian gồm những nốt nào?", "B C D E F G A"),
               ("Âm giai ngũ cung C trưởng (C major pentatonic) gồm những nốt nào?", "C D E G A"),
               ("Âm giai ngũ cung A thứ (A minor pentatonic) gồm những nốt nào?", "A C D E G"),
               ("Âm giai blues C gồm những nốt nào?", "C Eb F Gb G Bb")]:
    add("ngoai", "am_giai", q, ans, ref="nhạc lý chuẩn", notes_all=ans.split())

# --- 3. Quãng (L01) -----------------------------------------------------------------------------------------------
IV_Q = ["Quãng từ {a} lên {b} là quãng gì?", "{a} lên {b} là quãng mấy?", "Nốt {a} và nốt {b} phía trên cách nhau quãng gì?",
        "What interval is {a} up to {b}?", "quang tu {a} len {b} la quang gi"]
pairs = [("C", "E"), ("C", "Eb"), ("C", "G"), ("C", "F#"), ("C", "Gb"), ("D", "F"), ("D", "F#"), ("E", "Bb"),
         ("F", "B"), ("A", "C"), ("A", "C#"), ("G", "F#"), ("Eb", "A"), ("Bb", "D"), ("E", "C"), ("C", "A"),
         ("C", "Ab"), ("D", "C#"), ("C", "D#"), ("C", "Bbb"), ("Ab", "F"), ("C#", "E")]
for i, (a, b) in enumerate(pairs):
    out = T.identify_interval(lower=a, upper=b)
    assert out["ok"], (a, b, out)
    name = out["interval"]
    add("bai", "quang", IV_Q[i % len(IV_Q)].format(a=a, b=b), f"{name} ({out['semitones']} nửa cung)",
        any=[interval_phrases(name)])
for name, semis in [("M3", 4), ("m3", 3), ("P5", 7), ("P4", 5), ("M7", 11), ("m7", 10), ("A4", 6), ("M6", 9)]:
    add("bai", "quang", f"Quãng {name} có bao nhiêu nửa cung?", f"{semis} nửa cung", ref="nhạc lý chuẩn",
        any=[[f"{semis} nửa cung", f"{semis} cung nửa", f"{semis} semitone", f"{NUM_VI.get(semis, semis)} nửa cung"]])
for a, b, ans in [("M3", "m6", "m6"), ("P4", "P5", "P5"), ("m2", "M7", "M7"), ("A4", "d5", "d5")]:
    add("bai", "quang", f"Đảo quãng {a} thì được quãng gì?", ans, ref="nhạc lý chuẩn", any=[interval_phrases(ans)])
add("bai", "bay_quang", "Quãng C lên G là quãng 4 đúng phải không?", "Không, C–G là P5 (quãng 5 đúng)", trap=True,
    any=[interval_phrases("P5")])
add("bai", "bay_quang", "C–F# và C–Gb là cùng một quãng đúng không?", "Cùng 6 nửa cung nhưng khác tên: A4 và d5",
    trap=True, any=[interval_phrases("A4"), interval_phrases("d5")])
add("bai", "bay_quang", "Quãng E lên F là một cung nguyên đúng không?", "Không, E–F là nửa cung (m2)", trap=True,
    any=[["nửa cung", "m2", "2 thứ", "half step", "semitone"]])

# --- 4. Hóa biểu và giọng (L01) -----------------------------------------------------------------------------------
KEY_Q = ["Giọng {k} trưởng có mấy dấu hóa?", "{k} major có bao nhiêu dấu thăng/giáng?", "giong {k} truong co may dau hoa"]
for i, k in enumerate(["G", "D", "E", "B", "F#", "C#", "F", "Eb", "Ab", "Db", "Gb", "C"]):
    ks = key_signature(k)
    n = len(ks.accidentals)
    accs = [str(x) for x in ks.accidentals]
    ans = "không có dấu hóa" if n == 0 else f"{n} dấu {'thăng' if ks.kind == 'sharp' else 'giáng'}: {' '.join(accs)}"
    exp = {"any": [["không có dấu", "0 dấu", "không dấu hóa", "no sharps"]]} if n == 0 else {
        "any": [acc_phrases(n, ks.kind)], "notes_all": accs}
    add("bai", "hoa_bieu", KEY_Q[i % 3].format(k=k), ans, **exp)
for k in ["E", "B", "F#", "C", "G", "D"]:
    ks = key_signature(k, "minor")
    n = len(ks.accidentals)
    accs = [str(x) for x in ks.accidentals]
    ans = "không có dấu hóa" if n == 0 else f"{n} dấu {'thăng' if ks.kind == 'sharp' else 'giáng'}: {' '.join(accs)}"
    exp = {"any": [["không có dấu", "0 dấu", "không dấu hóa"]]} if n == 0 else {
        "any": [acc_phrases(n, ks.kind)], "notes_all": accs}
    add("bai", "hoa_bieu", f"Giọng {k} thứ có mấy dấu hóa?", ans, **exp)
for k in ["C", "G", "D", "F", "Bb", "Eb", "E", "Db"]:
    rm = str(relative_minor(k))
    add("bai", "giong_tuong_quan", f"Giọng thứ tương quan của {k} trưởng là gì?", f"{rm} thứ",
        any=[[f"{rm} thứ", f"{rm} minor", f"{rm}m", f"{rm} thu"]])
for n, kind in [(3, "sharp"), (4, "flat"), (2, "flat"), (5, "sharp"), (1, "sharp"), (6, "flat")]:
    from ...music_engine.key import key_from_signature
    k = str(key_from_signature(n, kind))
    vi = "thăng" if kind == "sharp" else "giáng"
    add("bai", "hoa_bieu", f"Hóa biểu có {n} dấu {vi} là giọng trưởng nào?", f"{k} trưởng",
        any=[[f"{k} trưởng", f"{k} major", f"{k} truong"]])
add("bai", "hoa_bieu", "Thứ tự các dấu thăng trong hóa biểu là gì?", "F C G D A E B", ref="nhạc lý chuẩn",
    any=[["F C G D A E B", "F, C, G, D, A, E, B", "F–C–G–D–A–E–B", "F-C-G-D-A-E-B", "FCGDAEB"]])
add("bai", "hoa_bieu", "Thứ tự các dấu giáng trong hóa biểu là gì?", "Bb Eb Ab Db Gb Cb Fb", ref="nhạc lý chuẩn",
    any=[["B E A D G C F", "B, E, A, D, G, C, F", "Bb Eb Ab Db Gb Cb Fb", "Bb, Eb, Ab, Db, Gb, Cb, Fb", "BEADGCF",
          "B–E–A–D–G–C–F", "Bb–Eb–Ab–Db–Gb–Cb–Fb"]])
add("bai", "bay_hoa_bieu", "Giọng F trưởng có 1 dấu thăng đúng không?", "Không, F trưởng có 1 dấu giáng (Bb)",
    trap=True, notes_all=["Bb"], any=[["giáng", "flat"]])
add("bai", "bay_hoa_bieu", "D trưởng có 3 dấu thăng phải không?", "Không, D trưởng có 2 dấu thăng: F# C#", trap=True,
    notes_all=["F#", "C#"], any=[acc_phrases(2, "sharp")])

# --- 5. Số La Mã trong giọng trưởng (L02) -------------------------------------------------------------------------
ROMAN_Q = ["Trong giọng {k} trưởng, {c} là hợp âm bậc mấy?", "{c} trong key {k} major là số La Mã gì?",
           "trong giong {k} truong, {c} la bac may"]
picks = [("C", 1), ("C", 5), ("G", 5), ("G", 3), ("D", 1), ("F", 3), ("F", 6), ("Bb", 1), ("Bb", 4), ("Eb", 1),
         ("A", 5), ("A", 6), ("E", 6), ("Ab", 1)]
for i, (k, deg) in enumerate(picks):
    sev = i % 2 == 0
    d = diatonic_chords(k, sevenths=sev)[deg]
    rn = d.numeral
    alts = [rn] + ([rn.replace("M7", "maj7"), rn.replace("M7", "Δ7")] if "M7" in rn else []) + (
        [rn.replace("ø7", "m7b5")] if "ø7" in rn else [])
    add("bai", "so_la_ma", ROMAN_Q[i % 3].format(k=k, c=d.chord.symbol), rn, roman_any=alts)
for i, (k, deg) in enumerate([("Bb", 1), ("Eb", 4), ("A", 1), ("D", 4), ("F", 6), ("G", 2), ("E", 4), ("Ab", 6)]):
    d = diatonic_chords(k, sevenths=True)[deg]
    add("bai", "so_la_ma", f"Hợp âm {d.numeral} trong giọng {k} trưởng là hợp âm gì?", d.chord.symbol,
        any=[sym_variants(d.chord.symbol)])
add("bai", "bay_so_la_ma", "Trong C trưởng, G7 là hợp âm IV đúng không?", "Không, G7 là V7", trap=True,
    roman_any=["V7"])
add("bai", "bay_so_la_ma", "Trong giọng C trưởng hợp âm bậc vii là Bm phải không?", "Không, vii° = Bdim (B D F)",
    trap=True, any=[["Bdim", "B°", "vii°", "Bm7b5", "Bø7", "giảm", "diminished"]], notes_all=["B", "D", "F"])

# --- 6. Chức năng (L03) -------------------------------------------------------------------------------------------
for c, fn, alts in [("F", "PD (tiền át / subdominant)", ["PD", "SD", "tiền át", "subdominant", "hạ át", "predominant"]),
                    ("G7", "D (át / dominant)", ["dominant", "át", " D "]),
                    ("Dm7", "PD", ["PD", "SD", "tiền át", "predominant", "subdominant", "hạ át"]),
                    ("Cmaj7", "T (chủ / tonic)", ["tonic", "chủ", " T "]),
                    ("Bdim", "D (át)", ["dominant", "át", " D "]),
                    ("Am", "T (thay thế chủ)", ["tonic", "chủ", " T "])]:
    add("bai", "chuc_nang", f"Trong giọng C trưởng, hợp âm {c} thường có chức năng gì?", fn, ref="nhạc lý chuẩn",
        any=[alts])
add("bai", "chuc_nang", "Chuỗi chức năng T → PD → D → T có nghĩa là gì?", "Chủ → tiền át → át → về chủ",
    ref="nhạc lý chuẩn", any=[["chủ", "tonic"], ["át", "dominant"]])
add("bai", "bay_chuc_nang", "Chức năng hòa âm chính là tên loại hợp âm (trưởng, thứ) đúng không?",
    "Không; chức năng là vai trò trong giọng (T/PD/D), không phải loại hợp âm", ref="nhạc lý chuẩn", trap=True,
    any=[["không phải", "không đồng nghĩa", "khác", "không giống"]])

# --- 7. ii–V–I (L04) ----------------------------------------------------------------------------------------------
IIVI_Q = ["Vòng ii–V–I trong giọng {k} trưởng gồm những hợp âm nào?", "ii-V-I in {k} major là gì?",
          "vong ii V I giong {k} truong"]
for i, k in enumerate(["C", "F", "Bb", "Eb", "Ab", "Db", "G", "D", "A", "E", "B", "Gb"]):
    ds = diatonic_chords(k, sevenths=True)
    seq = [ds[1].chord.symbol, ds[4].chord.symbol, ds[0].chord.symbol]
    add("bai", "ii_V_I", IIVI_Q[i % 3].format(k=k), " – ".join(seq), any=[sym_variants(s) for s in seq])

# --- 8. Guide tone, shell voicing (L04, L08) ----------------------------------------------------------------------
for s in ["Dm7", "G7", "Cmaj7", "Fmaj7", "Bb7", "Em7", "A7", "Ebmaj7"]:
    n = tones(s)
    add("bai", "guide_tone", f"Guide tone (nốt 3 và nốt 7) của {s} là những nốt nào?", f"{n[1]} và {n[3]}",
        notes_all=[n[1], n[3]])
add("bai", "guide_tone", "Khi G7 giải về Cmaj7, guide tone F đi đâu?", "F đi xuống E (nửa cung)", ref="bài L04-B05",
    notes_all=["E"])
add("bai", "guide_tone", "Khi G7 giải về Cmaj7, nốt B đi đâu?", "B giữ nguyên (thành nốt 7 của Cmaj7)",
    ref="bài L04-B05", any=[["giữ", "đứng yên", "không đổi", "common tone", "chung"]])
add("bai", "guide_tone", "Vì sao nốt 3 và nốt 7 quan trọng trong hợp âm bảy?",
    "Quyết định chất lượng hợp âm (trưởng/thứ, loại 7) và dẫn giọng mượt", ref="nhạc lý chuẩn",
    any=[["chất lượng", "tính chất", "loại hợp âm", "màu sắc", "quality"]])
for s in ["Dm7", "G7", "Cmaj7", "Fmaj7", "Bb7", "Em7", "A7", "Ebmaj7"]:
    n = tones(s)
    add("bai", "shell_voicing", f"Shell voicing root–3–7 của {s} gồm những nốt nào?", f"{n[0]} {n[1]} {n[3]}",
        notes_all=[n[0], n[1], n[3]])

# --- 9. Át phụ (L05) ----------------------------------------------------------------------------------------------
for k, deg, label in [("C", 1, "ii"), ("C", 2, "iii"), ("C", 3, "IV"), ("C", 4, "V"), ("C", 5, "vi"), ("G", 4, "V"),
                      ("G", 5, "vi"), ("G", 1, "ii"), ("F", 4, "V"), ("F", 1, "ii"), ("Bb", 4, "V"), ("D", 3, "IV"),
                      ("Eb", 5, "vi"), ("A", 1, "ii")]:
    target = diatonic_chords(k)[deg].chord.root
    dom = f"{transpose(target, 'P5')}7"
    n = tones(dom)
    add("bai", "at_phu", f"V7/{label} trong giọng {k} trưởng là hợp âm gì?", f"{dom} ({' '.join(n)})",
        any=[[dom]], notes_all=None)
add("bai", "at_phu", "Vì sao không có V7/vii° trong giọng trưởng?", "vii° là hợp âm giảm, không làm chủ tạm thời",
    ref="bài L05-B05", any=[["giảm", "diminished"]])
add("bai", "bay_at_phu", "Trong C trưởng, A7 là hợp âm vi đúng không?", "Không, A7 là V7/ii (át phụ của Dm)",
    trap=True, any=[["V7/ii", "V/ii", "át phụ", "secondary dominant"]])

# --- 10. Hợp âm mượn (L06) ----------------------------------------------------------------------------------------
for k in ["C", "G", "F", "D", "Bb"]:
    from ...music_engine.interval import transpose as tp
    iv, b6, b7 = f"{tp(k, 'P4')}m", str(tp(k, "m6")), str(tp(k, "m7"))
    add("bai", "hop_am_muon", f"Ba hợp âm mượn phổ biến iv, ♭VI, ♭VII trong {k} trưởng là gì?", f"{iv}, {b6}, {b7}",
        any=[[iv], [b6, b6 + "maj7"], [b7, b7 + "7"]])
add("bai", "hop_am_muon", "Hợp âm mượn là gì?", "Hợp âm lấy từ giọng song song (cùng chủ âm, khác thể)",
    ref="nhạc lý chuẩn", any=[["song song", "cùng chủ âm", "parallel", "cùng tonic"]])
add("bai", "bay_hop_am_muon", "Fm trong C trưởng được mượn từ A thứ phải không?",
    "Không, mượn từ C thứ (giọng song song)", trap=True, any=[["C thứ", "C minor", "Cm", "C thu"]])

# --- 11. Tension và chord-scale (L07) -----------------------------------------------------------------------------
for s, ten in [("Dm7", {"9": "E", "11": "G", "13": "B"}), ("G7", {"9": "A", "11": "C", "13": "E"}),
               ("Cmaj7", {"9": "D", "11": "F", "13": "A"})]:
    add("bai", "tension", f"Các tension 9, 11, 13 của {s} là nốt nào?", ", ".join(f"{k}={v}" for k, v in ten.items()),
        ref="bài L07-B03", notes_all=list(ten.values()))
for s, mode, notes in [("Dm7", "D Dorian", scale("D", "dorian")), ("G7", "G Mixolydian", scale("G", "mixolydian")),
                       ("Cmaj7", "C Ionian", scale("C", "major"))]:
    add("bai", "chord_scale", f"Trong ii–V–I ở C trưởng, {s} đi với chord-scale nào?", f"{mode}: {' '.join(notes)}",
        any=[[mode, mode.replace(" ", "-"), mode.split()[1]]])
add("bai", "tension", "Vì sao nhiều người tránh nốt 11 (C) trên G7?", "C cách nốt 3 (B) nửa cung, nghe chỏi",
    ref="bài L07-B03", notes_all=["B"], any=[["nửa cung", "m9", "b9", "chỏi", "xung đột", "va chạm"]])

# --- 12. Kiến thức nền L01 ----------------------------------------------------------------------------------------
for q, ans, exp in [
    ("Có bao nhiêu tên nốt cơ bản?", "7 (C D E F G A B)", {"any": [["7", "bảy"]], "notes_all": list("CDEFGAB")}),
    ("Một quãng tám có bao nhiêu nửa cung?", "12", {"any": [["12", "mười hai"]]}),
    ("Giữa E và F cách nhau bao nhiêu?", "Nửa cung", {"any": [["nửa cung", "half step", "semitone"]]}),
    ("Giữa B và C cách nhau bao nhiêu?", "Nửa cung", {"any": [["nửa cung", "half step", "semitone"]]}),
    ("C# và Db có phải cùng một phím đàn không?", "Cùng phím (đồng âm khác tên)", {"any": [["cùng", "đồng âm", "enharmonic"]]}),
    ("Đô giữa trên piano ký hiệu là gì?", "C4", {"any": [["C4"]]}),
    ("Có tổng cộng bao nhiêu giọng trưởng và thứ?", "24 (12 trưởng, 12 thứ)", {"any": [["24", "hai mươi bốn"]]}),
    ("Hợp âm ba trưởng dựng bằng những quãng nào từ nốt gốc?", "M3 và P5", {"any": [interval_phrases("M3"), interval_phrases("P5")]}),
    ("Hợp âm ba giảm khác hợp âm ba thứ ở điểm nào?", "Quãng 5 giảm (d5) thay vì 5 đúng", {"any": [interval_phrases("d5") + ["giảm"]]}),
    ("Phím đen trên piano được gọi tên thế nào?", "Theo nốt trắng bên cạnh thêm thăng hoặc giáng", {"any": [["thăng", "sharp", "#"], ["giáng", "flat"]]}),
    ("Bbb là nốt gì? Nó có trùng phím với nốt nào?", "Si giáng kép, cùng phím với A", {"notes_all": ["A"], "any": [["giáng kép", "double flat", "hai dấu giáng"]]}),
    ("E# có tồn tại không, hay chỉ là F?", "Có tồn tại; E# cùng phím F nhưng khác tên", {"notes_all": ["F"], "any": [["tồn tại", "có", "khác tên", "đồng âm"]]}),
]:
    add("bai", "nen_tang", q, ans, ref="nhạc lý chuẩn", **exp)
add("bai", "bay_nen_tang", "Cb chính là B nên viết Cb hay B đều như nhau trong mọi trường hợp đúng không?",
    "Cùng phím nhưng cách viết phụ thuộc giọng/hợp âm, không thay tùy ý", ref="nhạc lý chuẩn", trap=True,
    any=[["phụ thuộc", "tùy giọng", "tùy theo", "ngữ cảnh", "không phải lúc nào", "không hoàn toàn", "khác tên"]])

# --- 13. Ngoài bài: nhịp, cadence, đảo, thay thế tritone ... -----------------------------------------------------
for q, ans, exp in [
    ("Nhịp 6/8 là nhịp đơn hay nhịp kép?", "Nhịp kép (2 phách, mỗi phách là nốt đen chấm)", {"any": [["kép", "compound"]]}),
    ("Nhịp 3/4 có mấy phách mỗi ô?", "3 phách nốt đen", {"any": [["3", "ba"]]}),
    ("Trong 4/4, nốt đen chấm dôi dài bao nhiêu phách?", "1,5 phách", {"any": [["1,5", "1.5", "một phách rưỡi", "1 phách rưỡi", "rưỡi"]]}),
    ("Nốt tròn trong 4/4 bằng mấy phách?", "4 phách", {"any": [["4", "bốn"]]}),
    ("Nốt móc đơn bằng bao nhiêu nốt đen?", "Nửa nốt đen", {"any": [["nửa", "1/2", "0,5", "0.5"]]}),
    ("Cadence V–I gọi là gì?", "Kết hoàn toàn (authentic cadence)", {"any": [["authentic", "hoàn toàn", "kết trọn", "kết chính", "perfect"]]}),
    ("Cadence IV–I gọi là gì?", "Kết plagal (kết Amen)", {"any": [["plagal", "amen"]]}),
    ("Câu nhạc dừng ở hợp âm V gọi là kết gì?", "Kết nửa (half cadence)", {"any": [["half", "nửa", "lửng", "bán"]]}),
    ("Cadence V–vi gọi là gì?", "Kết lừa (deceptive cadence)", {"any": [["deceptive", "lừa", "ngắt", "interrupted"]]}),
    ("C/E là thế đảo nào của hợp âm C?", "Thế đảo 1 (nốt 3 ở bass)", {"any": [["đảo 1", "đảo thứ nhất", "first inversion", "thế đảo một", "đảo một"]]}),
    ("C/G là thế đảo nào của hợp âm C?", "Thế đảo 2", {"any": [["đảo 2", "đảo thứ hai", "second inversion", "đảo hai"]]}),
    ("G7/F là thế đảo mấy của G7?", "Thế đảo 3 (nốt 7 ở bass)", {"any": [["đảo 3", "đảo thứ ba", "third inversion", "đảo ba"]]}),
    ("Hợp âm thay thế tritone của G7 là gì?", "Db7", {"any": [["Db7", "C#7"]]}),
    ("Hợp âm thay thế tritone của D7 là gì?", "Ab7", {"any": [["Ab7", "G#7"]]}),
    ("Tritone trong G7 là hai nốt nào?", "B và F", {"notes_all": ["B", "F"]}),
    ("Hợp âm Napoli (Neapolitan) trong C trưởng là gì?", "Db (♭II), thường ở thế đảo 1", {"any": [["Db", "♭II", "bII"]]}),
    ("Vòng quãng năm đi từ C theo chiều thăng là những giọng nào?", "C G D A E B F# C#", {"notes_all": ["G", "D", "A", "E", "B", "F#"]}),
    ("Quãng năm song song là gì và vì sao hòa âm cổ điển tránh nó?", "Hai bè cách P5 cùng đi song song; làm mất độc lập bè", {"any": [["độc lập", "hòa lẫn", "mất", "rỗng", "independence"]]}),
    ("Giọng song song của C trưởng là gì?", "C thứ", {"any": [["C thứ", "C minor", "Cm"]]}),
    ("Hợp âm sus4 có nốt 3 không?", "Không; nốt 4 thay nốt 3", {"any": [["không", "thay"]]}),
    ("Âm giai thứ hòa âm khác thứ tự nhiên ở bậc nào?", "Nâng bậc 7 nửa cung", {"any": [["bậc 7", "bậc bảy", "7th", "nốt 7"]]}),
    ("Hợp âm bảy giảm (dim7) có đặc điểm gì về quãng?", "Chồng các quãng 3 thứ; chia quãng tám thành 4 phần bằng nhau", {"any": [["3 thứ", "ba thứ", "m3", "minor third"]]}),
    ("Hợp âm 13 thường bỏ nốt nào khi chơi trên piano?", "Thường bỏ nốt 11 (và có thể bỏ 5)", {"any": [["11"]]}),
    ("Tempo 120 BPM nghĩa là gì?", "120 phách mỗi phút", {"any": [["phách mỗi phút", "phách/phút", "beats per minute", "nhịp mỗi phút", "phách một phút"]]}),
    ("Đàn guitar tiêu chuẩn có mấy dây và lên dây thế nào?", "6 dây: E A D G B E", {"notes_all": ["E", "A", "D", "G", "B"], "any": [["6", "sáu"]]}),
]:
    add("ngoai", "ngoai_bai", q, ans, ref="nhạc lý chuẩn", **exp)
for q, ans, exp in [
    ("Vì sao hợp âm G7 giải về C trưởng lại cần nốt F#?", "G7 không có F#; F là nốt 7 đi xuống E", {"notes_all": ["F", "E"]}),
    ("Nhịp 6/8 có 6 phách nên đếm nhanh như 6/4 đúng không?", "Không; 6/8 là 2 phách chấm dôi", {"any": [["2 phách", "hai phách", "kép", "compound"]]}),
    ("Hợp âm Cdim7 có nốt Bb đúng không?", "Không; Cdim7 = C Eb Gb Bbb", {"notes_all": ["C", "Eb", "Gb", "Bbb"]}),
    ("Tritone substitution của G7 là C#7 hay Db7, cái nào đúng hơn? Hay là E7?", "Db7 (C#7 cùng phím); không phải E7", {"any": [["Db7"]]}),
]:
    add("ngoai", "bay_ngoai_bai", q, ans, ref="nhạc lý chuẩn", trap=True, **exp)
for q, ans, exp in [
    ("Viết hợp âm Cmaj7 nhưng dùng tên Đô Rê Mi giúp mình.", "Đô Mi Sol Si", {"any": [["Đô"], ["Mi"], ["Sol"], ["Si"]]}),
    ("Hợp âm Rê thứ bảy (Dm7) gồm những nốt nào theo tên Đô Rê Mi?", "Rê Fa La Đô", {"any": [["Rê"], ["Fa"], ["La"], ["Đô"]]}),
    ("Sol bảy (G7) gồm những nốt nào?", "Sol Si Rê Fa (G B D F)", {"notes_all": None, "any": [["Si", "B"], ["Fa", "F"]]}),
]:
    add("bai", "ten_not_viet", q, ans, ref="Music Engine", **exp)

if __name__ == "__main__":
    ids = [r["q"] for r in rows]
    assert len(ids) == len(set(ids)), "trùng câu hỏi"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    from collections import Counter
    print(len(rows), Counter(r["group"] for r in rows), sum(r["trap"] for r in rows), "bẫy")
    print(Counter(r["topic"] for r in rows))
