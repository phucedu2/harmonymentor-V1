"""Tìm trong CÂU HỎI những gì Music Engine tính được, và tính luôn (ADR-017, luồng B; đề GĐ1 thầy).

Trước đây chỉ tra ký hiệu hợp âm có hậu tố quen (C7, Dm7…), nên "Csus4 gồm nốt gì", "từ E lên Bb là quãng gì",
"âm giai Rê trưởng" đều không có dữ kiện và bị đẩy sang LLM. Giờ tra 4 công cụ:

- get_chord_tones: ký hiệu hợp âm có hậu tố, hoặc tên nốt đứng sau "hợp âm/chord" (kể cả "hợp âm A thứ").
- identify_interval: "từ X lên Y", "X–Y", "X đến Y" khi câu có chữ quãng/interval.
- get_scale: "âm giai/gam/scale X trưởng|thứ|thứ hòa âm|thứ giai điệu|dorian", nhận cả tên Việt (Rê trưởng).
- get_roman_numeral: "X trong (giọng) Y trưởng là bậc mấy / số La Mã gì".

Hàm chỉ NHẬN DIỆN rồi gọi Engine; không tự tính gì. Ký hiệu Engine không hiểu (C9, Cadd9) được trả về trong
`unknown` để bên gọi nói "không biết" thay vì đoán (quyết định 6A)."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from .guardrail import run_tool
from .notes import NOTE, norm_accidentals, solfege_to_letters
from ...music_engine import interval as _iv, key as _key

_SOLF1 = {"đô": "C", "do": "C", "rê": "D", "re": "D", "mi": "E", "fa": "F", "pha": "F", "sol": "G", "son": "G",
          "la": "A", "si": "B"}
_SOLF_ONE = re.compile(r"\b(Đô|Do|Rê|Re|Mi|Fa|Pha|Sol|Son|La|Si)(\s+(?:thăng|giáng))?(?=\s+(?:trưởng|thứ))",
                       re.IGNORECASE)

# Hậu tố có thể gặp trong câu hỏi, kể cả loại Engine chưa hỗ trợ (để báo "không biết" chứ không bỏ sót).
_SUFFIX = (r"(?:maj9|maj7|M7|Δ7|mM7|m7b5|m7\(b5\)|ø7|ø|dim7|°7|o7|dim|°|aug|\+|m9|m7|m6|min7|min|mi7|7sus4|"
           r"7b9|7#9|7b5|sus2|sus4|add9|add2|add11|13|11|9|6|7|m)")
_SYM = re.compile(rf"(?<![A-Za-z0-9#])(?P<sym>[A-G](?:#|b|♯|♭)?{_SUFFIX})(?![A-Za-z0-9#])")
# Gõ thường cả tên nốt ("cmaj7 la gi"): chỉ nhận khi hậu tố dài, tránh hiểu "a", "em", "do" thành hợp âm.
_SYM_LOWER = re.compile(r"(?<![A-Za-z0-9#])(?P<root>[a-g])(?P<acc>#|b)?(?P<suf>maj7|m7b5|dim7|m7|dim|aug|sus2|sus4)"
                        r"(?![A-Za-z0-9#])")
# Chữ thường được, nhưng tên nốt phải viết hoa: "hợp âm gì" không được hiểu thành hợp âm G.
# Chất lượng bằng chữ, cả tiếng Anh và không dấu. Thiếu "giảm/tăng" thì "hợp âm B diminished" bị hiểu thành B trưởng
# (phiếu dev của Phúc, 09/11).
# "tăng/tang dần, tốc, cường" là nghĩa khác, không phải hợp âm tăng (Thắng đồng ý nhận "tang" không dấu, 09/11).
_KIND_WORDS = (r"trưởng|truong|thứ|thu|major|minor|giảm|giam|diminished|dim|"
               r"(?:tăng|tang)(?!\s+(?:dần|dan|tốc|toc|cường|cuong))|augmented|aug")
_KIND_SUFFIX = {"thứ": "m", "thu": "m", "minor": "m", "giảm": "dim", "giam": "dim", "diminished": "dim", "dim": "dim",
                "tăng": "aug", "tang": "aug", "augmented": "aug", "aug": "aug"}
_CHORD_WORD = re.compile(
    rf"(?i:hợp âm|hop am|chord)\s+(?P<root>{NOTE})(?![A-Za-z0-9#])(?:\s+(?P<kind>(?i:{_KIND_WORDS}))(?![a-zà-ỹ0-9]))?"
    # Tên chất lượng khác đứng sau (half-diminished, sus, dominant…): không đoán là hợp âm trưởng.
    rf"(?!\s+(?i:(?:half|nửa|nua|dominant|bảy|bay|7)\b|sus|maj|add|m7|ø|°))")
# Chất lượng đứng trước nốt gốc: "hợp âm tăng của C", "hop am giam tren B".
_CHORD_KIND_FIRST = re.compile(
    rf"(?i:hợp âm|hop am|chord)\s+(?P<kind>(?i:{_KIND_WORDS}))\s+(?i:của|cua|of|trên|tren|từ|tu)\s+(?P<root>{NOTE})(?![A-Za-z0-9#])")
_INTERVAL_WORDS = re.compile(r"quãng|quang|interval", re.IGNORECASE)
_INTERVAL = re.compile(
    rf"(?:từ|tu|from)?\s*(?<![A-Za-z0-9#])(?P<lo>{NOTE})(?![A-Za-z0-9#])\s*(?:–|—|-|→|lên|len|đến|den|tới|toi|up to|to)\s*"
    rf"(?P<hi>{NOTE})(?![A-Za-z0-9#])")
_SCALE_KIND = [("thứ hòa âm", "harmonic_minor"), ("thu hoa am", "harmonic_minor"), ("harmonic minor", "harmonic_minor"),
               ("thứ giai điệu", "melodic_minor"), ("thu giai dieu", "melodic_minor"),
               ("melodic minor", "melodic_minor"), ("thứ tự nhiên", "natural_minor"), ("thu tu nhien", "natural_minor"),
               ("natural minor", "natural_minor"), ("dorian", "dorian"), ("trưởng", "major"), ("truong", "major"),
               ("major", "major"), ("thứ", "natural_minor"), ("thu", "natural_minor"), ("minor", "natural_minor")]
_KIND_ALT = "|".join(re.escape(k) for k, _ in _SCALE_KIND)
_SCALE = re.compile(rf"(?:âm giai|am giai|gam|scale|giọng|giong)\s+(?P<tonic>{NOTE})(?![A-Za-z0-9#])\s*(?P<kind>{_KIND_ALT})",
                    re.IGNORECASE)
_SCALE_UNKNOWN = re.compile(r"(?:âm giai|am giai|gam|scale)\s+(?-i:[A-G])[#b]?(?![a-zà-ỹ])\s*(?P<kind>[a-zà-ỹ]+(?:\s+[a-zà-ỹ]+)?)",
                            re.IGNORECASE)
_ROMAN_TOKEN = r"(?:vii|VII|iii|III|iv|IV|vi|VI|ii|II|v|V|i|I)(?:maj7|M7|ø7|°7|7|°|ø)?"
# "V7 trong G trưởng gồm những nốt nào?", "bậc ii của C trưởng là hợp âm gì"
_ROMAN_TO_CHORD = re.compile(
    rf"(?<![A-Za-z])(?P<rn>{_ROMAN_TOKEN})(?![A-Za-z0-9])\s+(?i:trong|của|cua|of|in)\s+(?i:giọng\s+|giong\s+)?"
    rf"(?P<key>{NOTE})(?![A-Za-z0-9#])\s*(?i:trưởng|truong|major)")
_ROMAN_Q = re.compile(
    rf"(?<![A-Za-z0-9#])(?P<chord>[A-G](?:#|b)?{_SUFFIX}?)(?![A-Za-z0-9#])\s+(?:trong|của|o|ở|in)\s+(?:giọng\s+|giong\s+|key\s+)?"
    rf"(?P<key>{NOTE})(?![A-Za-z0-9#])\s*(?:trưởng|truong|major)?[^.?!]{{0,30}}(?:bậc|bac|số la mã|so la ma|roman)",
    re.IGNORECASE)


# --- G8 (chấm nhạc lý Gemini, 16/11/2026): các dạng câu Engine tính được nhưng trước đây rơi sang LLM, và LLM tự tính sai
# (Em7 trong G bị nói là bậc 3, B thứ bị nói là 2 dấu giáng, đảo quãng A4 bị nói là P5...). Chỉ NHẬN DIỆN rồi gọi Engine.
_MODE_TYPE = {"natural minor": "natural_minor", "harmonic minor": "harmonic_minor", "melodic minor": "melodic_minor",
              "dorian": "dorian", "mixolydian": "mixolydian", "major": "major", "minor": "natural_minor"}
# "E natural minor scale", "D Mixolydian", "Eb major scale": tên nốt viết hoa, loại đứng sau. "C major" trơ trọi thì bỏ
# qua (có thể là hợp âm).
_SCALE_POST = re.compile(
    rf"(?<![A-Za-z0-9#])(?P<tonic>(?-i:{NOTE}))\s+(?:(?P<kind>natural minor|harmonic minor|melodic minor|dorian|mixolydian)"
    rf"|(?P<kind2>major|minor)\s+(?:scale|mode))(?![A-Za-z])", re.IGNORECASE)
_INTERVAL_AND = re.compile(
    rf"(?:nốt|not)\s+(?P<lo>{NOTE})(?![A-Za-z0-9#])\s+(?:và|va|and)\s+(?:nốt|not)\s+(?P<hi>{NOTE})(?![A-Za-z0-9#])"
    rf"\s+(?:phía trên|phia tren|ở trên|o tren|above)", re.IGNORECASE)
_IV_NAME = r"(?-i:(?:AA|dd|[PMmAd])\d{1,2})"
_INTERVAL_SIZE = re.compile(rf"(?:quãng|quang|interval)\s+(?P<iv>{_IV_NAME})(?![A-Za-z0-9])", re.IGNORECASE)
_SIZE_WORDS = re.compile(r"nửa cung|nua cung|semitone|bao nhiêu cung|bao nhieu cung", re.IGNORECASE)
_INVERT = re.compile(rf"(?:đảo|dao|invert)\s+(?:quãng|quang|interval)?\s*(?P<iv>{_IV_NAME})(?![A-Za-z0-9])", re.IGNORECASE)
_KEY_KIND = r"(?:trưởng|truong|major|thứ|thu|minor)"
_SIG_WORDS = re.compile(r"dấu hóa|dau hoa|dấu hoá|hóa biểu|hoa bieu|hoá biểu|dấu thăng|dau thang|dấu giáng|dau giang|"
                        r"key signature|sharps|flats", re.IGNORECASE)
_KEY_OF = re.compile(rf"(?<![A-Za-z0-9#])(?P<tonic>(?-i:{NOTE})|(?-i:[a-g](?:#|b)?)(?=\s+{_KEY_KIND}))\s*(?P<kind>{_KEY_KIND})(?![a-zà-ỹ])",
                     re.IGNORECASE)
_RELATIVE = re.compile(r"tương quan|tuong quan|relative", re.IGNORECASE)
_SIG_TO_KEY = re.compile(r"(?:có|co|với|voi|hóa biểu|hoa bieu)\s+(?P<n>\d)\s+dấu\s+(?P<kind>thăng|thang|giáng|giang)"
                         r"(?:.{0,30}?(?P<mode>trưởng|truong|thứ|thu))?", re.IGNORECASE)
_SIG_ORDER = re.compile(r"thứ tự\s+(?:của\s+)?(?:các\s+)?dấu\s+(?P<kind>thăng|thang|giáng|giang)", re.IGNORECASE)
# "trong giọng G trưởng, Em7 là bậc mấy" (hợp âm đứng SAU giọng), "trong key A major".
_ROMAN_Q2 = re.compile(
    rf"(?:trong|ở|in)\s+(?:giọng\s+|giong\s+|key\s+)(?P<key>{NOTE})(?![A-Za-z0-9#])\s*(?:trưởng|truong|major)?\s*[,:]?\s*"
    rf"(?P<chord>(?-i:[A-G](?:#|b)?){_SUFFIX}?)(?![A-Za-z0-9#])[^.?!]{{0,30}}(?:bậc|bac|số la mã|so la ma|roman)",
    re.IGNORECASE)


@dataclass
class EngineAnswer:
    facts: list[dict[str, Any]] = field(default_factory=list)     # {tool, args, result, sourced}
    unknown: list[str] = field(default_factory=list)              # ký hiệu/khái niệm Engine không tính được

    @property
    def any(self) -> bool:
        return bool(self.facts)


def _vn_names(text: str) -> str:
    """'Rê trưởng' → 'D trưởng', 'Si giáng thứ' → 'Bb thứ' (một tên nốt đứng trước trưởng/thứ)."""

    def one(m: re.Match) -> str:
        base = _SOLF1[unicodedata.normalize("NFC", m[1]).lower()]
        acc = m[2] or ""
        return base + ("#" if "thăng" in acc else "b" if "giáng" in acc else "")

    return _SOLF_ONE.sub(one, solfege_to_letters(text))


def _chord_for_numeral(key: str, numeral: str) -> str | None:
    """Hợp âm thuận giọng của một số La Mã, lấy từ Music Engine (diatonic_chords), không tự tính."""
    from ...music_engine.roman import diatonic_chords

    want = numeral.replace("maj7", "M7").replace("ø", "ø7").replace("ø77", "ø7")
    for sevenths in (False, True):
        try:
            for rn in diatonic_chords(key, sevenths=sevenths):
                if rn.numeral == want or rn.numeral.replace("M7", "maj7") == numeral:
                    return str(rn.chord)
        except Exception:
            return None
    return None


def _add(out: EngineAnswer, seen: set, tool: str, args: dict[str, str]) -> None:
    key = (tool, tuple(sorted(args.items())))
    if key in seen:
        return
    seen.add(key)
    value, raw = run_tool(tool, args)
    if value is None:
        code = (raw.get("error") or {}).get("code")
        if code in {"UNKNOWN_QUALITY", "INVALID_SYMBOL", "UNKNOWN_SCALE", "NOT_DIATONIC", "UNSUPPORTED"} or tool == "get_chord_tones":
            out.unknown.append(args.get("symbol") or args.get("chord") or " ".join(args.values()))
        return
    sourced = bool(raw.get("verified")) if tool == "get_chord_tones" else True
    out.facts.append({"tool": tool, "args": args, "result": value, "sourced": sourced})


def _local(out: EngineAnswer, seen: set, tool: str, args: dict[str, str], compute) -> None:
    """Dữ kiện lấy trực tiếp từ hàm của Music Engine (key.py, interval.py) cho các công cụ chưa có trong tools.py."""
    from ...music_engine.errors import MusicEngineError

    key = (tool, tuple(sorted(args.items())))
    if key in seen:
        return
    seen.add(key)
    try:
        value = compute()
    except MusicEngineError:
        out.unknown.append(" ".join(args.values()))
        return
    out.facts.append({"tool": tool, "args": args, "result": value, "sourced": True})


def _tonic(raw: str) -> str:
    t = norm_accidentals(raw)
    return t[0].upper() + t[1:]


def _is_minor(kind: str) -> bool:
    return kind.lower() in {"thứ", "thu", "minor"}


def _sig_text(tonic: str, mode: str) -> str:
    ks = _key.key_signature(tonic, mode)
    if ks.count == 0:
        return "không có dấu hóa"
    return f"{ks.count} dấu {'thăng' if ks.kind == 'sharp' else 'giáng'}: {' '.join(n.name for n in ks.accidentals)}"


def _local_facts(text: str, out: EngineAnswer, seen: set) -> None:
    """G8: hóa biểu, giọng tương quan, thứ tự dấu hóa, kích thước và đảo quãng (xem chú thích _SCALE_POST)."""
    if _SIZE_WORDS.search(text):
        for m in _INTERVAL_SIZE.finditer(text):
            _local(out, seen, "interval_size", {"interval": m["iv"]}, lambda m=m: str(_iv.parse_interval(m["iv"]).semitones))
    for m in _INVERT.finditer(text):
        _local(out, seen, "invert_interval", {"interval": m["iv"]}, lambda m=m: _iv.invert(m["iv"]).name)

    keys = [(_tonic(m["tonic"]), "minor" if _is_minor(m["kind"]) else "major") for m in _KEY_OF.finditer(text)]
    if _RELATIVE.search(text):
        for tonic, mode in keys:
            def rel(tonic=tonic, mode=mode):
                return f"{_key.relative_minor(tonic).name} thứ" if mode == "major" else f"{_key.relative_major(tonic).name} trưởng"
            _local(out, seen, "relative_key", {"key": tonic, "mode": mode}, rel)
    elif _SIG_WORDS.search(text) and keys:
        for tonic, mode in keys:
            _local(out, seen, "key_signature", {"key": tonic, "mode": mode}, lambda tonic=tonic, mode=mode: _sig_text(tonic, mode))
        # "Giọng B thứ có mấy dấu hóa" cũng khớp mẫu "giọng X thứ" của âm giai; người học hỏi hóa biểu, không hỏi nốt.
        out.facts = [f for f in out.facts if not (f["tool"] == "get_scale" and f["args"]["tonic"] in {k[0] for k in keys})]
    elif (m := _SIG_ORDER.search(text)):
        sharp = m["kind"].lower() in {"thăng", "thang"}
        order = _key.ORDER_OF_SHARPS if sharp else _key.ORDER_OF_FLATS
        _local(out, seen, "signature_order", {"kind": "thăng" if sharp else "giáng"},
               lambda: " ".join(l + ("#" if sharp else "b") for l in order))
    elif (m := _SIG_TO_KEY.search(text)):
        sharp = m["kind"].lower() in {"thăng", "thang"}
        mode = "minor" if m["mode"] and _is_minor(m["mode"]) else "major"
        n = int(m["n"])

        def from_sig():
            tonic = _key.key_from_signature(n, "sharp" if sharp else "flat", mode).name
            return f"{tonic} {'thứ' if mode == 'minor' else 'trưởng'}"
        _local(out, seen, "key_from_signature", {"count": str(n), "kind": "thăng" if sharp else "giáng", "mode": mode}, from_sig)


def engine_answer(question: str, limit: int = 4) -> EngineAnswer:
    text = _vn_names(question)
    out, seen = EngineAnswer(), set()

    for m in _ROMAN_Q.finditer(text):
        _add(out, seen, "get_roman_numeral", {"key": norm_accidentals(m["key"]), "chord": norm_accidentals(m["chord"])})
    for m in _ROMAN_Q2.finditer(text):
        _add(out, seen, "get_roman_numeral", {"key": norm_accidentals(m["key"]), "chord": norm_accidentals(m["chord"])})
    for m in _ROMAN_TO_CHORD.finditer(text):
        chord = _chord_for_numeral(norm_accidentals(m["key"]), m["rn"])
        if chord is None:
            out.unknown.append(f"{m['rn']} trong {m['key']}")
            continue
        _add(out, seen, "get_roman_numeral", {"key": norm_accidentals(m["key"]), "chord": chord})
        _add(out, seen, "get_chord_tones", {"symbol": chord})
    roman_chords = {f["args"]["chord"] for f in out.facts if f["tool"] == "get_roman_numeral"}
    roman_keys = {f["args"]["key"] for f in out.facts if f["tool"] == "get_roman_numeral"}

    for m in _SCALE.finditer(text):
        if m[0].lower().startswith(("giọng", "giong")) and norm_accidentals(m["tonic"]) in roman_keys:
            continue  # "Am trong giọng C trưởng": chữ giọng chỉ để nói giọng, không hỏi âm giai
        kind = next(v for k, v in _SCALE_KIND if k == m["kind"].lower())
        _add(out, seen, "get_scale", {"tonic": norm_accidentals(m["tonic"]), "scale_type": kind})
    for m in _SCALE_POST.finditer(text):
        kind = _MODE_TYPE[(m["kind"] or ("major" if m["kind2"].lower() == "major" else "minor")).lower()]
        _add(out, seen, "get_scale", {"tonic": norm_accidentals(m["tonic"]), "scale_type": kind})
    if not any(f["tool"] == "get_scale" for f in out.facts):
        for m in _SCALE_UNKNOWN.finditer(text):
            if not re.match(_KIND_ALT, m["kind"], re.IGNORECASE):
                out.unknown.append(f"âm giai {m['kind']}")

    if _INTERVAL_WORDS.search(text):
        for m in _INTERVAL.finditer(text):
            _add(out, seen, "identify_interval", {"lower": norm_accidentals(m["lo"]), "upper": norm_accidentals(m["hi"])})
        for m in _INTERVAL_AND.finditer(text):
            _add(out, seen, "identify_interval", {"lower": norm_accidentals(m["lo"]), "upper": norm_accidentals(m["hi"])})

    for m in _SYM.finditer(text):
        sym = norm_accidentals(m["sym"])
        if sym not in roman_chords:
            _add(out, seen, "get_chord_tones", {"symbol": sym})
    if not any(f["tool"] == "get_chord_tones" for f in out.facts):
        for m in _SYM_LOWER.finditer(text):
            _add(out, seen, "get_chord_tones", {"symbol": m["root"].upper() + (m["acc"] or "") + m["suf"]})
    for m in [*_CHORD_WORD.finditer(text), *_CHORD_KIND_FIRST.finditer(text)]:
        kind = (m["kind"] or "").lower()
        sym = norm_accidentals(m["root"]) + _KIND_SUFFIX.get(kind, "")
        if sym not in roman_chords and not any(f["args"].get("symbol", "").startswith(sym) and
                                               f["args"].get("symbol") != sym for f in out.facts):
            _add(out, seen, "get_chord_tones", {"symbol": sym})

    _local_facts(text, out, seen)
    out.facts = out.facts[:limit]
    return out


def fact_text(f: dict[str, Any]) -> str:
    """Một câu tiếng Việt cho một dữ kiện Engine (khuôn viết sẵn, không qua LLM)."""
    a, r = f["args"], f["result"]
    if f["tool"] == "get_chord_tones":
        return f"{a['symbol']} gồm các nốt {', '.join(r.split())}."
    if f["tool"] == "identify_interval":
        return f"Từ {a['lower']} lên {a['upper']} là quãng {r}."
    if f["tool"] == "get_scale":
        names = {"major": "trưởng", "natural_minor": "thứ tự nhiên", "harmonic_minor": "thứ hòa âm",
                 "melodic_minor": "thứ giai điệu (đi lên)", "dorian": "Dorian"}
        return f"Âm giai {a['tonic']} {names.get(a['scale_type'], a['scale_type'])}: {' '.join(r.split())}."
    if f["tool"] == "get_roman_numeral":
        return f"Trong giọng {a['key']} trưởng, {a['chord']} là {r}."
    mode_vi = {"major": "trưởng", "minor": "thứ"}
    if f["tool"] == "key_signature":
        return f"Giọng {a['key']} {mode_vi[a['mode']]} {r}." if r.startswith("không") else f"Giọng {a['key']} {mode_vi[a['mode']]} có {r}."
    if f["tool"] == "relative_key":
        return f"Giọng tương quan của {a['key']} {mode_vi[a['mode']]} là {r}."
    if f["tool"] == "key_from_signature":
        return f"Hóa biểu {a['count']} dấu {a['kind']} là giọng {r}."
    if f["tool"] == "signature_order":
        return f"Thứ tự các dấu {a['kind']} trong hóa biểu: {r}."
    if f["tool"] == "interval_size":
        return f"Quãng {a['interval']} rộng {r} nửa cung."
    if f["tool"] == "invert_interval":
        return f"Đảo quãng {a['interval']} được quãng {r}."
    return f"{f['tool']}: {r}."

