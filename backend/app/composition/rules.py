"""Composition Engine (FR-18): gợi ý hợp âm theo luật có tên, mức độ lạ 0–3, và phân tích vòng hợp âm.

Vì sao tách khỏi Music Engine: Music Engine giữ sự thật nhạc lý (tên nốt, quãng, hợp âm, giọng). Module này chỉ
chứa LUẬT SOẠN NHẠC (đổi hợp âm nào thành hợp âm nào), và mọi hợp âm nó đề xuất đều dựng bằng Music Engine
(`transpose`, `build_chord`, `diatonic_chords`, `chord_tones`). Không sửa hành vi Music Engine.

Phạm vi theo Phúc (31/10, câu 1A và 8A): đúng 5 nhóm luật, xếp mức độ lạ:
- 0 trong giọng: thay bằng hợp âm cùng chức năng.
- 1 hợp âm át phụ V7/x, mượn từ giọng thứ cùng tên (iv, ♭VI, ♭VII, ♭III).
- 2 màu điệu thức Dorian/Mixolydian/Lydian, thay thế tritone.
- 3 chromatic mediant.
Giọng thứ chưa hỗ trợ vì số La Mã của Engine chỉ có giọng trưởng (QĐ-2.2).

Nguồn: tên luật theo tài liệu 04 Bảng 23 (chèn át phụ, thay tritone, mượn hợp âm, thay cùng chức năng).
Bảng chức năng (chủ/hạ át/át) và cách gọi màu điệu thức là đề xuất của Claude, CHƯA đối chiếu nguồn đã đọc;
lời giải thích tiếng Việt cần Astra kiểm (ghi ở ADR-010).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from ..music_engine import build_chord, chord_tones, diatonic_chords, parse_chord_symbol, parse_note, transpose
from ..music_engine.chord import ChordSymbol
from ..music_engine.errors import MusicEngineError, NotSupportedInMvp
from ..music_engine.pitch import Note
from ..music_engine.roman import RomanNumeral, roman_numeral
from ..music_engine.scale import build_scale

LEVEL_LABELS = {0: "Quen tai", 1: "Hơi lạ", 2: "Lạ", 3: "Rất lạ"}

RULES = {
    "same_function": (0, "Thay cùng chức năng"),
    "secondary_dominant": (1, "Hợp âm át phụ (V7/x)"),
    "borrowed": (1, "Mượn từ giọng thứ cùng tên"),
    "modal": (2, "Màu điệu thức (Dorian, Mixolydian, Lydian)"),
    "tritone_sub": (2, "Thay thế tritone"),
    "chromatic_mediant": (3, "Chromatic mediant"),
}

_FUNCTION = {1: "tonic", 3: "tonic", 6: "tonic", 2: "subdominant", 4: "subdominant", 5: "dominant", 7: "dominant"}
_FUNCTION_VI = {"tonic": "chủ (nghe ổn định)", "subdominant": "hạ át (chuẩn bị đi tiếp)",
                "dominant": "át (căng, muốn về chủ)"}
# Họ chất lượng để so hợp âm ba với hợp âm bảy cùng gốc (C ~ Cmaj7 ~ C7 khi xét gốc và quãng 3).
_MAJOR_FAMILY = {"maj", "7", "maj7"}
_MINOR_FAMILY = {"min", "m7"}


@dataclass(frozen=True)
class Candidate:
    rule: str
    level: int
    symbol: str
    label: str
    reason_vi: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["rule_label"] = RULES[self.rule][1]
        data["level_label"] = LEVEL_LABELS[self.level]
        return data


class CompositionInputError(ValueError):
    """Đầu vào không dùng được (giọng thứ, ký hiệu hợp âm sai...). `code` theo mã lỗi của Music Engine."""

    def __init__(self, code: str, message_vi: str):
        super().__init__(message_vi)
        self.code = code
        self.message_vi = message_vi


# --- tiện ích dựng hợp âm bằng Music Engine -----------------------------------------------------

def _tonic(key: str) -> Note:
    try:
        tonic = parse_note(key).with_octave(None)
        diatonic_chords(tonic)  # chặn giọng không hỗ trợ ngay từ đầu
    except MusicEngineError as exc:
        raise CompositionInputError(exc.code, f"Giọng {key!r} chưa dùng được: {exc}") from exc
    return tonic


def _parse(symbols: list[str | None]) -> list[ChordSymbol | None]:
    result: list[ChordSymbol | None] = []
    for index, symbol in enumerate(symbols):
        if symbol is None or not str(symbol).strip():
            result.append(None)
            continue
        try:
            result.append(parse_chord_symbol(str(symbol)))
        except MusicEngineError as exc:
            raise CompositionInputError(exc.code, f"Ô {index + 1}: không đọc được hợp âm {symbol!r}.") from exc
    return result


def _rn(tonic: Note, chord: ChordSymbol) -> RomanNumeral | None:
    try:
        return roman_numeral(tonic, ChordSymbol(chord.root, chord.type))
    except (MusicEngineError, NotSupportedInMvp):
        return None


def _family(chord: ChordSymbol) -> str | None:
    if chord.type.id in _MAJOR_FAMILY:
        return "maj"
    if chord.type.id in _MINOR_FAMILY:
        return "min"
    return None


def _same(a: ChordSymbol, root: Note, family: str) -> bool:
    return a.root.pitch_class == root.pitch_class and _family(a) == family


def _names(notes: list[Note]) -> list[str]:
    return [n.name for n in notes]


def _outside(notes: list[Note], scale: list[Note]) -> list[tuple[Note, Note]]:
    """Các nốt ngoài âm giai, kèm nốt cùng chữ cái trong âm giai mà nó thay (Ab thay A)."""
    pairs = []
    for note in notes:
        if any(note.same_spelling(s) for s in scale):
            continue
        same_letter = next((s for s in scale if s.letter_index == note.letter_index), None)
        if same_letter is not None:
            pairs.append((note, same_letter))
    return pairs


def _changed(pairs: list[tuple[Note, Note]]) -> str:
    return ", ".join(f"{new.name} thay cho {old.name}" for new, old in pairs)


def _cap(text: str) -> str:
    # Không dùng str.capitalize: nó viết thường phần còn lại (Bb → bb).
    return text[:1].upper() + text[1:]


def _base_numeral(numeral: str) -> str:
    return "".join(ch for ch in numeral if ch in "IViv")


def _candidate(rule: str, symbol: str, label: str, reason: str) -> Candidate | None:
    try:
        # Đọc lại đúng ký hiệu sẽ lưu vào dự án. Nốt gốc có dấu kép (Bbb) chưa đọc được nên bỏ ứng viên,
        # không tự đổi sang tên đồng âm (việc gọi tên là của Music Engine).
        notes = _names(chord_tones(symbol))
    except MusicEngineError:
        return None
    return Candidate(rule, RULES[rule][0], symbol, label, reason, notes)


def _special_chords(tonic: Note) -> dict[str, tuple[str, Note, str]]:
    """Hợp âm ngoài giọng có tên: nhãn → (luật, nốt gốc, họ chất lượng)."""
    return {
        "iv": ("borrowed", transpose(tonic, "P4"), "min"),
        "♭VI": ("borrowed", transpose(tonic, "m6"), "maj"),
        "♭VII": ("borrowed", transpose(tonic, "m7"), "maj"),
        "♭III": ("borrowed", transpose(tonic, "m3"), "maj"),
        "v": ("modal", transpose(tonic, "P5"), "min"),
        "II": ("modal", transpose(tonic, "M2"), "maj"),
        "i": ("modal", tonic, "min"),
    }


_MODAL_NAME = {"v": "Mixolydian", "II": "Lydian", "i": "Dorian"}


def _symbol(root: Note, family: str) -> str:
    return build_chord(root, family).symbol


# --- gợi ý -----------------------------------------------------------------------------------------

def suggest(key: str, symbols: list[str | None], index: int, max_level: int = 3) -> list[dict]:
    """Ứng viên thay cho hợp âm ở ô `index`, xếp theo độ lạ tăng dần (luật cố định, không cần AI).

    Ô sau ô cuối là ô đầu vì vòng hợp âm được phát lặp.
    """
    tonic = _tonic(key)
    chords = _parse(symbols)
    if not 0 <= index < len(chords):
        raise CompositionInputError("INDEX_OUT_OF_RANGE", "Ô cần gợi ý nằm ngoài lưới.")
    current = chords[index]
    if current is None:
        raise CompositionInputError("EMPTY_BAR", "Ô này chưa có hợp âm. Hãy chọn một hợp âm trong giọng trước.")
    nxt = chords[(index + 1) % len(chords)] if len(chords) > 1 else None
    scale = build_scale(tonic, "major")
    rn = _rn(tonic, current)
    sevenths = len(current.type.intervals) == 4
    out: list[Candidate | None] = []

    # 0. Cùng chức năng: chỉ áp dụng khi hợp âm hiện tại nằm trong giọng.
    if rn is not None:
        function = _FUNCTION[rn.degree]
        for other in diatonic_chords(tonic, sevenths=sevenths):
            if other.degree == rn.degree or _FUNCTION[other.degree] != function:
                continue
            out.append(_candidate(
                "same_function", other.chord.symbol, other.numeral,
                f"{other.chord.symbol} ({other.numeral}) cùng chức năng {_FUNCTION_VI[function]} với {current.symbol} "
                f"({rn.numeral}) và vẫn nằm trong giọng {tonic.name} trưởng, nên đổi màu nhẹ mà không lạc giọng."))

    # 1. Át phụ: V7 của hợp âm ở ô sau (ô sau phải là hợp âm trưởng/thứ trong giọng, không phải bậc I).
    if nxt is not None:
        target = _rn(tonic, nxt)
        if target is not None and target.degree != 1 and _family(nxt) is not None:
            dom = build_chord(transpose(nxt.root, "P5"), "7")
            pairs = _outside(dom.notes, scale)
            label = f"V7/{_base_numeral(target.numeral)}"
            reason = (f"{dom.symbol} là hợp âm át của {nxt.symbol} ({label}): nốt {dom.notes[1].name} cách "
                      f"{nxt.root.name} nửa cung nên kéo tai về {nxt.symbol} ở ô sau.")
            if pairs:
                reason += f" Hợp âm có nốt ngoài giọng ({_changed(pairs)}), đó là chỗ nghe lạ."
            out.append(_candidate("secondary_dominant", dom.symbol, label, reason))

    special = _special_chords(tonic)
    # 1. Mượn từ giọng thứ cùng tên, chọn theo bậc đang đứng để giữ vai trò gần giống.
    if rn is not None:
        borrowed_for = {4: "iv", 2: "iv", 6: "♭VI", 5: "♭VII", 7: "♭VII", 1: "♭III", 3: "♭III"}
        label = borrowed_for[rn.degree]
        _, root, family = special[label]
        symbol = _symbol(root, family)
        pairs = _outside(build_chord(root, family).notes, scale)
        out.append(_candidate(
            "borrowed", symbol, label,
            f"{symbol} ({label}) mượn từ giọng {tonic.name} thứ (cùng nốt chủ {tonic.name}). "
            f"{_cap(_changed(pairs))}: nghe tối và buồn hơn một chút nhưng vẫn quen tai."))

    # 2. Màu điệu thức: Mixolydian cho bậc V, Lydian cho bậc ii/IV, Dorian cho bậc I.
    if rn is not None:
        modal_for = {5: "v", 2: "II", 4: "II", 1: "i"}
        label = modal_for.get(rn.degree)
        if label is not None:
            _, root, family = special[label]
            symbol = _symbol(root, family)
            pairs = _outside(build_chord(root, family).notes, scale)
            mode = _MODAL_NAME[label]
            if label == "v":
                detail = "bậc 7 bị hạ, át không còn kéo mạnh về chủ, nghe thả lỏng kiểu rock/pop."
            elif label == "II":
                detail = "bậc 4 được nâng, nghe sáng và lơ lửng như nhạc phim."
            else:
                iv_root = transpose(tonic, "P4")
                detail = (f"chủ chuyển sang thứ. Màu Dorian rõ nhất khi ô sau là {iv_root.name} trưởng (IV), "
                          f"vì {iv_root.name} có nốt {transpose(tonic, 'M6').name} (bậc 6 trưởng).")
                if nxt is None or not _same(nxt, iv_root, "maj"):
                    detail += f" Ô sau chưa phải {iv_root.name} nên màu Dorian chưa rõ."
            out.append(_candidate("modal", symbol, label,
                                  f"{symbol} ({label}) cho màu {mode} ({_changed(pairs)}): {detail}"))

    # 2. Thay thế tritone: chỉ cho hợp âm át (bậc V hoặc hợp âm bảy át bất kỳ).
    if current.type.id == "7" or (rn is not None and rn.degree == 5 and current.type.id in ("maj", "7")):
        dom = build_chord(current.root, "7")
        sub = build_chord(transpose(current.root, "d5"), "7")
        label = "♭II7" if rn is not None and rn.degree == 5 else "subV7"
        goal = transpose(current.root, "P4")
        out.append(_candidate(
            "tritone_sub", sub.symbol, label,
            f"{sub.symbol} thay cho {current.symbol}: hai hợp âm chung cặp nốt {dom.notes[1].name} và "
            f"{dom.notes[3].name} (cách nhau ba cung) nên vẫn kéo về {goal.name}, nhưng bass đi xuống từng nửa cung "
            f"({sub.root.name} → {goal.name}), nghe trơn kiểu jazz."))

    # 3. Chromatic mediant: cùng loại hợp âm, nốt gốc cách quãng 3 (trưởng hoặc thứ), không thuộc giọng.
    family = _family(current)
    if family is not None:
        for interval, words in (("M3", "lên quãng 3 trưởng"), ("m6", "xuống quãng 3 trưởng"),
                                ("m3", "lên quãng 3 thứ"), ("M6", "xuống quãng 3 thứ")):
            root = transpose(current.root, interval)
            symbol = _symbol(root, family)
            mediant = build_chord(root, family)
            if _rn(tonic, mediant) is not None:
                continue
            common = [n.name for n in mediant.notes if any(n.pitch_class == c.pitch_class for c in current.notes)]
            share = f"chung nốt {', '.join(common)}" if common else "không chung nốt nào"
            out.append(_candidate(
                "chromatic_mediant", symbol, f"mediant ({words})",
                f"{symbol}: nốt gốc {words} so với {current.symbol}, cùng loại hợp âm, {share}. "
                f"Bước nhảy này đổi màu đột ngột kiểu nhạc phim; nên dùng một lần rồi quay về giọng."))

    seen = {current.symbol}
    result = []
    for candidate in out:
        if candidate is None or candidate.level > max_level or candidate.symbol in seen:
            continue
        seen.add(candidate.symbol)
        result.append(candidate)
    result.sort(key=lambda c: c.level)
    return [c.to_dict() for c in result]


# --- phân tích (bài cuối khóa chỉ phân tích, không chấm) ------------------------------------------

def analyze(key: str, symbols: list[str | None]) -> dict:
    """Gọi tên từng hợp âm theo luật, mức độ lạ và cảnh báo (tài liệu 04 Bảng 24). Cảnh báo không chặn lựa chọn."""
    tonic = _tonic(key)
    chords = _parse(symbols)
    special = _special_chords(tonic)
    n = len(chords)
    bars = []
    warnings = []
    for i, chord in enumerate(chords):
        if chord is None:
            bars.append({"bar": i + 1, "symbol": None, "level": None, "rule": None, "label": None, "reason_vi": None})
            continue
        nxt = chords[(i + 1) % n] if n > 1 else None
        prev = chords[(i - 1) % n] if n > 1 else None
        rn = _rn(tonic, chord)
        rule, label, reason = _classify(tonic, chord, rn, prev, nxt, special)
        level = 0 if rule == "diatonic" else (3 if rule == "outside" else RULES[rule][0])
        bars.append({"bar": i + 1, "symbol": chord.symbol, "level": level, "rule": rule, "label": label,
                     "reason_vi": reason})
        if rule == "outside":
            warnings.append({"code": "NOT_IN_KEY", "bar": i + 1,
                             "message_vi": f"Ô {i + 1}: {chord.symbol} ngoài giọng {tonic.name} trưởng và không giải "
                                           f"thích được bằng luật nào ở trên. Vẫn dùng được nếu bạn thích âm thanh đó."})
        is_diatonic_v7 = rn is not None and rn.degree == 5
        if chord.type.id == "7" and not is_diatonic_v7 and nxt is not None and not _resolves(chord, nxt):
            warnings.append({"code": "UNRESOLVED_DOMINANT", "bar": i + 1,
                             "message_vi": f"Ô {i + 1}: {chord.symbol} là hợp âm át nhưng ô sau ({nxt.symbol}) không phải "
                                           f"hợp âm nó kéo về ({transpose(chord.root, 'P4').name})."})
    levels = [b["level"] for b in bars if b["level"] is not None]
    overall = max(levels) if levels else 0
    unusual = [b for b in bars if b["level"]]
    if not levels:
        summary = "Lưới chưa có hợp âm."
    elif not unusual:
        summary = f"Vòng quen tai: mọi hợp âm đều nằm trong giọng {tonic.name} trưởng."
    else:
        parts = [f"ô {b['bar']} ({b['symbol']}, {b['label']})" for b in unusual]
        summary = f"Vòng {LEVEL_LABELS[overall].lower()} (mức {overall}/3). Chỗ lạ: " + "; ".join(parts) + "."
    return {"key": tonic.name, "level": overall, "level_label": LEVEL_LABELS[overall], "summary_vi": summary,
            "bars": bars, "warnings": warnings}


def _resolves(dom: ChordSymbol, target: ChordSymbol) -> bool:
    up_fourth = transpose(dom.root, "P4").pitch_class
    half_below = (dom.root.pitch_class - 1) % 12
    return target.root.pitch_class in (up_fourth, half_below)


def _classify(tonic: Note, chord: ChordSymbol, rn: RomanNumeral | None, prev: ChordSymbol | None,
              nxt: ChordSymbol | None, special: dict) -> tuple[str, str, str]:
    if rn is not None:
        function = _FUNCTION[rn.degree]
        return "diatonic", rn.numeral, (f"Trong giọng {tonic.name} trưởng, bậc {rn.numeral}, chức năng "
                                        f"{_FUNCTION_VI[function]}.")
    family = _family(chord)
    if nxt is not None and family == "maj":
        target = _rn(tonic, nxt)
        if target is not None and target.degree != 1 and chord.root.pitch_class == transpose(nxt.root, "P5").pitch_class:
            label = f"V7/{_base_numeral(target.numeral)}"
            return "secondary_dominant", label, (f"Hợp âm át của {nxt.symbol} ở ô sau: mượn tạm một nốt ngoài giọng "
                                                 f"để kéo tai về {nxt.symbol}.")
    if chord.type.id == "7" and nxt is not None and (chord.root.pitch_class - 1) % 12 == nxt.root.pitch_class:
        return "tritone_sub", "subV7", (f"Thay thế tritone: {chord.symbol} đứng thay hợp âm át của {nxt.symbol}, "
                                        f"bass đi xuống nửa cung về {nxt.root.name}.")
    for label, (rule, root, fam) in special.items():
        if family == fam and chord.root.pitch_class == root.pitch_class:
            if rule == "borrowed":
                return rule, label, f"Mượn từ giọng {tonic.name} thứ (cùng nốt chủ), nghe tối hơn hợp âm trong giọng."
            return rule, label, f"Màu {_MODAL_NAME[label]}: một nốt của âm giai được nâng hoặc hạ nửa cung."
    if prev is not None and family is not None and _family(prev) == family:
        distance = (chord.root.pitch_class - prev.root.pitch_class) % 12
        if distance in (3, 4, 8, 9):
            return "chromatic_mediant", "mediant", (f"Chromatic mediant so với {prev.symbol}: cùng loại hợp âm, nốt gốc "
                                                    f"cách quãng 3, đổi màu đột ngột.")
    return "outside", "ngoài giọng", f"{chord.symbol} không thuộc giọng {tonic.name} trưởng."


# --- thế bấm để phát và vẽ khuông ---------------------------------------------------------------

def _pitch(note: Note) -> dict:
    return {"name": str(note), "midi": note.midi}


def voicing(symbol: str) -> dict:
    """Cao độ cụ thể (có quãng tám) cho một hợp âm, dựng bằng Music Engine để frontend không tự tính.

    Hợp âm: gốc ở quãng tám 4 nếu chữ cái C–F, còn lại quãng tám 3, để mọi hợp âm nằm quanh nốt C4.
    Bass: nốt gốc và nốt thứ ba trong công thức (nốt năm của hợp âm) ở quãng tám 2.
    """
    try:
        chord = parse_chord_symbol(symbol)
    except MusicEngineError as exc:
        raise CompositionInputError(exc.code, f"Không đọc được hợp âm {symbol!r}.") from exc
    octave = 4 if chord.root.letter in "CDEF" else 3
    root = chord.root.with_octave(octave)
    tones = [transpose(root, iv) for iv in chord.type.intervals]
    bass_root = chord.root.with_octave(2)
    bass_fifth = transpose(bass_root, chord.type.intervals[2])
    return {"symbol": chord.symbol, "notes": [n.name for n in chord.notes], "pitches": [_pitch(t) for t in tones],
            "bass": {"root": _pitch(bass_root), "fifth": _pitch(bass_fifth)}}
