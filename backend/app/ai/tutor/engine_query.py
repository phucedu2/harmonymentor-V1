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
from dataclasses import dataclass, field
from typing import Any

from .guardrail import run_tool
from .notes import NOTE, ROMAN_MODE, roman_mode, norm_accidentals, normalize_key_names

# Hậu tố có thể gặp trong câu hỏi, kể cả loại Engine chưa hỗ trợ (để báo "không biết" chứ không bỏ sót).
_SUFFIX = (r"(?:maj9|maj7|M7|Δ7|mM7|m7b5|m7\(b5\)|ø7|ø|dim7|°7|o7|dim|°|aug|\+|m9|m7|m6|min7|min|mi7|7sus4|"
           r"7b9|7#9|7b5|sus2|sus4|add9|add2|add11|13|11|9|6|7|m)")
# Nhận cả hợp âm có bass riêng: "C/E", "G7/B" (trước đây "C/E" chỉ được hiểu là C, mất nốt bass).
_SYM = re.compile(rf"(?<![A-Za-z0-9#/])(?P<sym>{NOTE}(?:{_SUFFIX}(?:/{NOTE})?|/{NOTE}))(?![A-Za-z0-9#])")
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
    rf"(?:từ|tu|from)?\s*(?<![A-Za-z0-9#])(?P<lo>{NOTE})(?![A-Za-z0-9#])\s*(?:–|—|-|→|lên|len|đến|den|tới|toi|to)\s*"
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
    rf"(?P<key>{NOTE})(?![A-Za-z0-9#])\s*(?P<mode>(?i:{ROMAN_MODE}))(?![\wÀ-ỹ])")
_ROMAN_Q = re.compile(
    rf"(?<![A-Za-z0-9#])(?P<chord>{NOTE}{_SUFFIX}?)(?![A-Za-z0-9#])\s+(?:trong|của|o|ở)\s+(?:giọng\s+|giong\s+)?"
    rf"(?P<key>{NOTE})(?![A-Za-z0-9#])\s*(?P<mode>{ROMAN_MODE})?(?![\wÀ-ỹ])[^.?!]{{0,30}}(?:bậc|bac|số la mã|so la ma|roman)",
    re.IGNORECASE)


# Cùng ý với _ROMAN_Q nhưng đảo thứ tự: "Fm là bậc mấy trong C thứ?", "Tính bậc của Am trong C trưởng".
_ROMAN_Q_WORD_FIRST = (
    re.compile(
        rf"(?<![A-Za-z0-9#])(?P<chord>{NOTE}{_SUFFIX}?)(?![A-Za-z0-9#])\s+(?i:là|la)\s+"
        rf"(?i:bậc mấy|bac may|bậc nào|bac nao|số la mã nào|so la ma nao|số la mã gì|so la ma gi)\s+"
        rf"(?i:trong|ở|o|của)\s+(?i:giọng\s+|giong\s+)?(?P<key>{NOTE})(?![A-Za-z0-9#])\s*"
        rf"(?P<mode>(?i:{ROMAN_MODE}))?(?![\wÀ-ỹ])"),
    re.compile(
        rf"(?i:bậc|bac|số la mã|so la ma|roman)\s+(?i:của|cua|of)\s+(?i:hợp âm\s+|hop am\s+)?"
        rf"(?<![A-Za-z0-9#])(?P<chord>{NOTE}{_SUFFIX}?)(?![A-Za-z0-9#])\s+(?i:trong|ở|o)\s+"
        rf"(?i:giọng\s+|giong\s+)?(?P<key>{NOTE})(?![A-Za-z0-9#])\s*"
        rf"(?P<mode>(?i:{ROMAN_MODE}))?(?![\wÀ-ỹ])"),
)


@dataclass
class EngineAnswer:
    facts: list[dict[str, Any]] = field(default_factory=list)     # {tool, args, result, sourced}
    unknown: list[str] = field(default_factory=list)              # ký hiệu/khái niệm Engine không tính được

    context_used: bool = False
    context_note: str | None = None

    @property
    def any(self) -> bool:
        return bool(self.facts)


def _vn_names(text: str) -> str:
    return normalize_key_names(text)

def _chord_for_numeral(key: str, numeral: str, mode: str = "major") -> str | None:
    """Hợp âm thuận giọng của một số La Mã, lấy từ Music Engine (diatonic_chords), không tự tính."""
    from ...music_engine.roman import diatonic_chords

    want = numeral.replace("maj7", "M7").replace("ø", "ø7").replace("ø77", "ø7")
    for sevenths in (False, True):
        try:
            for rn in diatonic_chords(key, sevenths=sevenths, mode=mode):
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
        if code in {"UNKNOWN_QUALITY", "INVALID_SYMBOL", "UNKNOWN_SCALE", "NOT_DIATONIC", "NOT_SUPPORTED_IN_MVP", "UNSUPPORTED"} or tool == "get_chord_tones":
            if tool == "get_roman_numeral" and args.get("mode") == "unspecified_minor":
                out.unknown.append("Cần làm rõ giọng thứ tự nhiên, hòa âm hay giai điệu trước khi phân tích số La Mã")
            elif tool == "get_roman_numeral" and args.get("mode") == "natural_minor" and code == "NOT_DIATONIC":
                out.unknown.append(f"{args['chord']} không thuộc tập hợp âm thuận giọng {args['key']} thứ tự nhiên; không đồng nghĩa sai nhạc lý")
            else:
                out.unknown.append(args.get("symbol") or args.get("chord") or " ".join(args.values()))
        return
    sourced = bool(raw.get("verified")) if tool == "get_chord_tones" else True
    fact = {"tool": tool, "args": args, "result": value, "sourced": sourced}
    if tool == "get_chord_tones" and raw.get("bass"):
        fact["bass"] = raw["bass"]  # C/E: nốt bass E do Engine trả, không suy ra từ chữ
    out.facts.append(fact)


# "Em đếm / Em muốn…" là cách người học tự xưng, không phải hợp âm Mi thứ.
# Xét từng lần xuất hiện để vẫn nhận hợp âm trong "Em hỏi về hợp âm Em".
_EM_PRONOUN_TAIL = re.compile(r"\s+(?:đếm|dem|hỏi|hoi|muốn|muon|đang|dang|chưa|chua|cần|can|nên|nen"
                              r"|chỉ|chi|thấy|thay|biết|biet|hiểu|hieu|vẫn|van|mới|moi|thử|vừa|vua|đã)\b", re.I)
_EXPLICIT_CHORD_PREFIX = re.compile(r"\b(?:hợp âm|hop am|chord)\s+$", re.I)
# Câu hỏi đòi xác định bậc của một hợp âm cụ thể ("là bậc mấy", "xác định bậc"). Thiếu giọng hoặc thiếu hợp âm thì phải
# hỏi lại, không đoán. Câu hỏi khái niệm ("số La Mã là gì") không khớp mẫu này nên vẫn đi theo bài học.
_ROMAN_DETERMINE = re.compile(r"bậc mấy|bac may|xác định bậc|xac dinh bac|là bậc nào|la bac nao|bậc nào|bac nao", re.I)


def _symbol_matches(text: str):
    for match in _SYM.finditer(text):
        if (match["sym"] == "Em" and _EM_PRONOUN_TAIL.match(text, match.end())
                and not _EXPLICIT_CHORD_PREFIX.search(text, 0, match.start())):
            continue
        yield match


def engine_answer(question: str, limit: int = 4, *, context: dict | None = None) -> EngineAnswer:
    from .context import clean_context
    context = clean_context(context)
    text = _vn_names(question)
    out, seen = EngineAnswer(), set()
    def question_mode(match):
        if match["mode"] is None:
            if (norm_accidentals(match["key"]) == context.get("selected_key")
                    and context.get("mode") in ("major", "natural_minor")):
                out.context_used = True
                return context["mode"]
            return None
        mode = roman_mode(match["mode"])
        if mode == "unspecified_minor" and norm_accidentals(match["key"]) == context.get("selected_key"):
            if context.get("mode") == "natural_minor":
                out.context_used = True
                return "natural_minor"
        return mode

    for m in (mm for rx in (_ROMAN_Q, *_ROMAN_Q_WORD_FIRST) for mm in rx.finditer(text)):
        mode = question_mode(m)
        if mode is None:
            out.context_note = "Bạn cho mình biết giọng trưởng hay thứ; nếu là thứ, bạn muốn xét dạng thứ nào nhé."
            continue
        args = {"key": norm_accidentals(m["key"]), "chord": norm_accidentals(m["chord"])}
        if mode != "major":
            args["mode"] = mode
        _add(out, seen, "get_roman_numeral", args)
    for m in _ROMAN_TO_CHORD.finditer(text):
        mode = question_mode(m)
        chord = _chord_for_numeral(norm_accidentals(m["key"]), m["rn"], mode=mode)
        if chord is None:
            reason = ("cần làm rõ loại giọng thứ" if mode == "unspecified_minor"
                      else "ngoài phạm vi hợp âm thuận giọng đang hỗ trợ")
            out.unknown.append(f"{m['rn']} trong {m['key']} {m['mode']}: {reason}")
            continue
        _add(out, seen, "get_roman_numeral", {"key": norm_accidentals(m["key"]), "chord": chord, **({"mode": mode} if mode != "major" else {})})
        _add(out, seen, "get_chord_tones", {"symbol": chord})
    roman_chords = {f["args"]["chord"] for f in out.facts if f["tool"] == "get_roman_numeral"}
    roman_keys = {f["args"]["key"] for f in out.facts if f["tool"] == "get_roman_numeral"}

    for m in _SCALE.finditer(text):
        if m[0].lower().startswith(("giọng", "giong")) and norm_accidentals(m["tonic"]) in roman_keys:
            continue  # "Am trong giọng C trưởng": chữ giọng chỉ để nói giọng, không hỏi âm giai
        kind = next(v for k, v in _SCALE_KIND if k == m["kind"].lower())
        _add(out, seen, "get_scale", {"tonic": norm_accidentals(m["tonic"]), "scale_type": kind})
    if not any(f["tool"] == "get_scale" for f in out.facts):
        for m in _SCALE_UNKNOWN.finditer(text):
            if not re.match(_KIND_ALT, m["kind"], re.IGNORECASE):
                out.unknown.append(f"âm giai {m['kind']}")

    if _INTERVAL_WORDS.search(text):
        for m in _INTERVAL.finditer(text):
            _add(out, seen, "identify_interval", {"lower": norm_accidentals(m["lo"]), "upper": norm_accidentals(m["hi"])})

    for m in _symbol_matches(text):
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

    before = len(out.facts)
    _add_context_facts(text, out, seen, context)
    out.context_used = out.context_used or len(out.facts) > before
    out.facts = out.facts[:limit]
    return out


def fact_text(f: dict[str, Any]) -> str:
    """Một câu tiếng Việt cho một dữ kiện Engine (khuôn viết sẵn, không qua LLM)."""
    a, r = f["args"], f["result"]
    if f["tool"] == "get_chord_tones":
        bass = f"; nốt bass là {f['bass']} (nốt thấp nhất)" if f.get("bass") else ""
        return f"{a['symbol']} gồm các nốt {', '.join(r.split())}{bass}."
    if f["tool"] == "identify_interval":
        return f"Từ {a['lower']} lên {a['upper']} là quãng {r}."
    if f["tool"] == "get_scale":
        names = {"major": "trưởng", "natural_minor": "thứ tự nhiên", "harmonic_minor": "thứ hòa âm",
                 "melodic_minor": "thứ giai điệu (đi lên)", "dorian": "Dorian"}
        return f"Âm giai {a['tonic']} {names.get(a['scale_type'], a['scale_type'])}: {' '.join(r.split())}."
    if f["tool"] == "get_roman_numeral":
        label = "thứ tự nhiên" if a.get("mode") == "natural_minor" else "trưởng"
        return f"Trong giọng {a['key']} {label}, {a['chord']} là {r.replace('M7', 'maj7')}."
    return f"{f['tool']}: {r}."



def _add_context_facts(text, out, seen, context):
    """Resolve deictic questions without modifying the original user message."""
    from .context import clean_context
    ctx = clean_context(context)
    roman_request = re.search(r"bậc|bac|la mã|la ma|roman", text, re.I)
    referent = re.search(r"này|nay|đang chọn|dang chon|đang xem|dang xem|hiện tại|hien tai|this|selected", text, re.I)
    determine = bool(_ROMAN_DETERMINE.search(text)) and not any(f["tool"] == "get_roman_numeral" for f in out.facts)
    # Không có context thì giữ hành vi cũ, trừ khi câu hỏi đòi xác định bậc mà thiếu giọng/hợp âm: khi đó hỏi lại.
    if not ctx and not (roman_request and (referent or determine)):
        return
    key, mode = ctx.get("selected_key"), ctx.get("mode")
    # Explicit key/mode in the question always overrides UI. Bare/unsupported
    # explicit keys must not fall back to a different selected key.
    explicit = re.search(rf"(?:giọng|giong|trong|ở|o|của|cua|in|of|gam|scale|âm giai|am giai)\s+(?:giọng\s+|giong\s+)?(?P<key>{NOTE})(?![A-Za-z0-9#])\s*(?P<mode>{ROMAN_MODE})?", text, re.I)
    if explicit:
        key = norm_accidentals(explicit["key"])
        mode = roman_mode(explicit["mode"]) if explicit["mode"] else None
        if mode == "unspecified_minor" and key == ctx.get("selected_key") and ctx.get("mode") == "natural_minor":
            mode = "natural_minor"
        elif mode not in ("major", "natural_minor"):
            return
    chords = [f["args"].get("symbol") for f in out.facts if f["tool"] == "get_chord_tones"]
    chord = chords[0] if len(chords) == 1 else None
    # Unknown explicitly named chords must not become the selected chord.
    if (not chord and (referent or (determine and not chords)) and not out.unknown
            and next(_symbol_matches(text), None) is None and not _CHORD_WORD.search(text)):
        chord = ctx.get("selected_chord")
    if roman_request and (referent or determine) and (not key or not mode or not chord):
        out.context_note = ("Bạn chọn giọng và loại giọng để mình xác định bậc của hợp âm nhé. Nốt gốc của hợp âm không tự xác định giọng."
                            if not key or not mode else "Bạn chọn hợp âm ở phần khám phá hoặc ghi rõ tên hợp âm nhé.")
        return
    if referent and re.search(r"hợp âm|hop am|chord", text, re.I) and not chord:
        out.context_note = "Bạn chọn loại hợp âm ở phần khám phá hoặc ghi rõ tên hợp âm nhé; chỉ nốt gốc chưa đủ để xác định hợp âm."
        return
    if roman_request and key and mode and chord:
        if not any(f["tool"] == "get_roman_numeral" for f in out.facts):
            _add(out, seen, "get_roman_numeral", {"key": key, "mode": mode, "chord": chord})
    elif referent and re.search(r"hợp âm|hop am|chord", text, re.I) and chord and not chords:
        _add(out, seen, "get_chord_tones", {"symbol": chord})
    # Roman -> chord for a selected explicit key, e.g. 'bậc iiø7 gồm nốt nào?'.
    rn = re.search(rf"(?<![A-Za-z])(?P<rn>{_ROMAN_TOKEN})(?![A-Za-z0-9])", text)
    if rn and key and mode and not any(f["tool"] == "get_roman_numeral" for f in out.facts) and not out.unknown:
        symbol = _chord_for_numeral(key, rn["rn"], mode)
        if symbol:
            _add(out, seen, "get_roman_numeral", {"key": key, "mode": mode, "chord": symbol})
            _add(out, seen, "get_chord_tones", {"symbol": symbol})
    if referent and re.search(r"âm giai|am giai|scale", text, re.I) and key and mode and not any(f["tool"] == "get_scale" for f in out.facts):
        _add(out, seen, "get_scale", {"tonic": key, "scale_type": mode})
