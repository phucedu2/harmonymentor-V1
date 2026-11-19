"""Kiểm khẳng định nhạc lý của AI bằng Music Engine (04 mục 3.6, đề GĐ3 mục 6, TC-15).

Hai nguồn khẳng định:
1. engine_claims AI khai: gọi lại công cụ với đúng args, so kết quả AI ghi.
2. Quét reply: mọi "ký hiệu hợp âm + dãy nốt" và "âm giai + dãy nốt", kể cả cái AI không khai, sau khi đổi
   tên nốt tiếng Việt (Đô Mi Sol) sang chữ cái.
Mỗi mục: verified | contradicted | unsupported (Engine không hiểu ký hiệu/công cụ). Nhãn
"Đã kiểm bằng Music Engine" chỉ khi có ít nhất một mục và mọi mục đều verified."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from ...music_engine import tools as engine
from ...music_engine.errors import MusicEngineError
from ...music_engine.interval import parse_interval
from ...music_engine.roman import diatonic_chords
from .notes import (CHORD_IS_ROMAN_IN_KEY, CHORD_WITH_NOTES, INTERVAL_PAIR_WITH_NAME, INTERVAL_SIZE_CLAIM,
                    INTERVAL_WITH_NAME, NOTE_SEQ, NOTES_SEMITONE_CLAIM, ROMAN_IN_KEY_IS_CHORD, SCALE_WITH_NOTES,
                    SYMBOL_IN_QUESTION, interval_name, is_comparison, norm_accidentals, semitone_count,
                    solfege_to_letters, split_notes)
from .schema import Claim

_SCALE_KIND = {"major": "major", "trưởng": "major", "natural minor": "natural_minor", "thứ tự nhiên": "natural_minor",
               "minor": "natural_minor", "thứ": "natural_minor"}


@dataclass(frozen=True)
class CheckedClaim:
    tool: str
    args: dict[str, str]
    claimed: str
    engine: str | None
    status: str          # verified | contradicted | unsupported
    origin: str          # declared | scanned

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GuardResult:
    claims: list[CheckedClaim]

    @property
    def contradicted(self) -> list[CheckedClaim]:
        return [c for c in self.claims if c.status == "contradicted"]

    @property
    def all_verified(self) -> bool:
        return bool(self.claims) and all(c.status == "verified" for c in self.claims)


def _norm_seq(s: str) -> list[str]:
    return [norm_accidentals(x) for x in s.replace(",", " ").replace("–", " ").replace("-", " ").split() if x]


def run_tool(tool: str, args: dict[str, str]) -> tuple[str | None, dict]:
    """Gọi Music Engine; trả (kết quả dạng chuỗi, JSON gốc). None khi Engine không trả lời được."""
    fn = engine.TOOLS.get(tool)
    if fn is None:
        return None, {"ok": False, "error": {"code": "UNKNOWN_TOOL"}}
    allowed = {"get_chord_tones": ("symbol",), "get_scale": ("tonic", "scale_type"),
               "identify_interval": ("lower", "upper"), "get_roman_numeral": ("key", "chord")}[tool]
    try:
        out = fn(**{k: v for k, v in args.items() if k in allowed})
    except TypeError:
        return None, {"ok": False, "error": {"code": "BAD_ARGS"}}
    if not out.get("ok"):
        return None, out
    if tool == "identify_interval":
        return out["interval"], out
    if tool == "get_roman_numeral":
        return out["numeral"], out
    return " ".join(out["notes"]), out


def _compare(tool: str, claimed: str, engine_value: str | None) -> str:
    if engine_value is None:
        return "unsupported"
    if tool == "identify_interval":
        return "verified" if claimed.strip() == engine_value else "contradicted"
    a, b = _norm_seq(claimed), engine_value.split()
    if a == b:
        return "verified"
    # Hợp âm liệt kê khác thứ tự (đảo) vẫn đúng tên nốt; âm giai thì phải đúng thứ tự.
    if tool == "get_chord_tones" and sorted(a) == sorted(b):
        return "verified"
    return "contradicted"


def _norm_roman(text: str) -> str:
    # Cùng quy ước chấm bài (ADR-016): maj7 = M7.
    return text.strip().replace("maj7", "M7").replace("∅", "ø")


def check_roman(key: str, chord: str, claimed: str) -> CheckedClaim:
    """Khẳng định "<số La Mã> trong giọng <key> trưởng là <chord>".

    Hợp âm thuận giọng: so số La Mã Engine trả. Hợp âm ngoài giọng (ví dụ G7 trong G trưởng): nếu số La Mã AI
    nêu là một bậc thuận giọng thì hợp âm của bậc đó khác chord → contradicted; còn lại (V/V, I7...) Engine
    chưa đặt tên được → unsupported, không bao giờ verified."""
    args = {"key": norm_accidentals(key), "chord": norm_accidentals(chord)}
    rn = _norm_roman(claimed)
    value, _ = run_tool("get_roman_numeral", args)
    if value is not None:
        return CheckedClaim("get_roman_numeral", args, rn, value, "verified" if rn == value else "contradicted",
                            "scanned")
    try:
        seventh = any(ch in rn for ch in "7ø")
        match = next((d for d in diatonic_chords(args["key"], sevenths=seventh) if d.numeral == rn), None)
    except MusicEngineError:
        match = None
    if match is None:
        return CheckedClaim("get_roman_numeral", args, rn, None, "unsupported", "scanned")
    return CheckedClaim("get_roman_numeral", args, rn, f"{rn} = {match.chord.symbol}", "contradicted", "scanned")


def check_declared(claims: Iterable[Claim]) -> list[CheckedClaim]:
    out = []
    for c in claims:
        if c.tool == "get_roman_numeral":
            checked = check_roman(c.args.get("key", ""), c.args.get("chord", ""), c.result)
            out.append(CheckedClaim(checked.tool, checked.args, checked.claimed, checked.engine, checked.status,
                                    "declared"))
            continue
        value, _ = run_tool(c.tool, c.args)
        out.append(CheckedClaim(c.tool, dict(c.args), c.result, value, _compare(c.tool, c.result, value), "declared"))
    return out


# G8 (19/11/2026): "Shell root–3–7 của G7: G, B, F" là đúng nhưng từng bị so với G7 đầy đủ (G B D F) và báo sai,
# câu trả lời đúng rơi vào dự phòng. Nhìn ngữ cảnh ngay trước ký hiệu để biết câu đang nói một phần hợp âm.
_SHELL_CTX = re.compile(r"shell|root\s*[–\-]\s*3\s*[–\-]\s*7|1\s*[–\-]\s*3\s*[–\-]\s*7", re.IGNORECASE)
_GUIDE_CTX = re.compile(r"guide[\s-]*tone|nốt\s*3\s*(?:và|,)\s*(?:nốt\s*)?7|3rd\s+(?:và|and)\s+7th", re.IGNORECASE)
_PARTIAL_CTX = re.compile(r"voicing|lược|bỏ\s+(?:nốt|quãng)|rút\s+gọn", re.IGNORECASE)
_CTX_BEFORE = 120


def _compare_chord(text: str, start: int, claimed: str, engine_value: str | None) -> str:
    """So dãy nốt AI ghi với hợp âm Engine, có tính ngữ cảnh shell/guide tone/voicing.

    Shell root–3–7 phải đúng 3 nốt gốc–3–7; guide tone đúng 2 nốt 3–7; voicing/lược nốt khác chỉ cần là tập con
    các nốt của hợp âm. Nốt không thuộc hợp âm thì vẫn sai."""
    full = _compare("get_chord_tones", claimed, engine_value)
    if full != "contradicted" or engine_value is None:
        return full
    tones, got = engine_value.split(), _norm_seq(claimed)
    window = text[max(0, start - _CTX_BEFORE):start]
    if len(tones) >= 4 and _SHELL_CTX.search(window):
        return "verified" if sorted(got) == sorted([tones[0], tones[1], tones[3]]) else "contradicted"
    if len(tones) >= 4 and _GUIDE_CTX.search(window):
        return "verified" if sorted(got) == sorted([tones[1], tones[3]]) else "contradicted"
    if _PARTIAL_CTX.search(window) and len(got) >= 2 and set(got) < set(tones):
        return "verified"
    return full


def scan_reply(reply: str) -> list[CheckedClaim]:
    text = solfege_to_letters(reply)
    out = []
    for m in CHORD_WITH_NOTES.finditer(text):
        args = {"symbol": norm_accidentals(m["sym"])}
        claimed = " ".join(split_notes(m["notes"]))
        value, _ = run_tool("get_chord_tones", args)
        out.append(CheckedClaim("get_chord_tones", args, claimed, value,
                                _compare_chord(text, m.start(), claimed, value), "scanned"))
    for m in SCALE_WITH_NOTES.finditer(text):
        args = {"tonic": norm_accidentals(m["tonic"]), "scale_type": _SCALE_KIND[m["kind"].lower()]}
        claimed = " ".join(split_notes(m["notes"]))
        value, _ = run_tool("get_scale", args)
        out.append(CheckedClaim("get_scale", args, claimed, value, _compare("get_scale", claimed, value), "scanned"))
    for m in INTERVAL_WITH_NAME.finditer(text):
        args = {"lower": norm_accidentals(m["lo"]), "upper": norm_accidentals(m["hi"])}
        claimed = interval_name(m)
        value, _ = run_tool("identify_interval", args)
        out.append(CheckedClaim("identify_interval", args, claimed, value,
                                _compare("identify_interval", claimed, value), "scanned"))
    for m in INTERVAL_PAIR_WITH_NAME.finditer(text):
        lo, hi = norm_accidentals(m["lo"]), norm_accidentals(m["hi"])
        claimed = interval_name(m)
        up, _ = run_tool("identify_interval", {"lower": lo, "upper": hi})
        down, _ = run_tool("identify_interval", {"lower": hi, "upper": lo})
        # "B và F" không nói nốt nào ở dưới: đúng nếu khớp một trong hai chiều, sai khi cả hai đều khác.
        hit = next((v for v in (up, down) if v == claimed), None)
        args = {"lower": lo, "upper": hi} if hit in (None, up) else {"lower": hi, "upper": lo}
        out.append(CheckedClaim("identify_interval", args, claimed, hit or up,
                                "unsupported" if up is None and down is None else ("verified" if hit else "contradicted"),
                                "scanned"))
    # G8: số nửa cung AI nêu cho một quãng ("M6 có 8 nửa cung") hoặc cho hai nốt ("A lên C ... 4 nửa cung").
    for m in INTERVAL_SIZE_CLAIM.finditer(text):
        if is_comparison(text, m.start()):
            continue
        code = interval_name(m)
        try:
            size = str(parse_interval(code).semitones)
        except (MusicEngineError, ValueError, KeyError):
            size = None
        claimed = str(semitone_count(m))
        out.append(CheckedClaim("interval_size", {"interval": code}, claimed, size,
                                "unsupported" if size is None else ("verified" if claimed == size else "contradicted"),
                                "scanned"))
    for m in NOTES_SEMITONE_CLAIM.finditer(text):
        if is_comparison(text, m.start()):
            continue
        args = {"lower": norm_accidentals(m["lo"]), "upper": norm_accidentals(m["hi"])}
        _, raw = run_tool("identify_interval", args)
        size = str(raw["semitones"]) if raw.get("ok") else None
        claimed = str(semitone_count(m))
        out.append(CheckedClaim("interval_size", args, claimed, size,
                                "unsupported" if size is None else ("verified" if claimed == size else "contradicted"),
                                "scanned"))
    # "Dm7: D F A C là ii7": chữ C cuối dãy nốt không phải hợp âm C, nên bỏ khớp nằm trong một dãy nốt.
    seqs = [m.span() for m in re.finditer(NOTE_SEQ, text)]
    for pattern in (ROMAN_IN_KEY_IS_CHORD, CHORD_IS_ROMAN_IN_KEY):
        for m in pattern.finditer(text):
            if any(a <= m.start("chord") < b for a, b in seqs):
                continue
            out.append(check_roman(m["key"], m["chord"], m["rn"]))
    return out


def check_answer(reply: str, claims: Iterable[Claim]) -> GuardResult:
    declared = check_declared(claims)
    seen = {(c.tool, tuple(sorted(c.args.items())), c.claimed) for c in declared}
    scanned = [c for c in scan_reply(reply) if (c.tool, tuple(sorted(c.args.items())), c.claimed) not in seen]
    return GuardResult(declared + scanned)


def engine_facts_for(question: str, limit: int = 4) -> list[dict[str, Any]]:
    """Tra trước Music Engine cho ký hiệu hợp âm trong câu hỏi (TC-12: "có lời gọi Music Engine").

    Kết quả đưa vào prompt như dữ kiện đã kiểm, để AI không phải tự tính, và được ghi vào tool_calls."""
    facts, seen = [], set()
    for m in SYMBOL_IN_QUESTION.finditer(solfege_to_letters(question)):
        sym = norm_accidentals(m["sym"])
        if sym in seen:
            continue
        seen.add(sym)
        value, raw = run_tool("get_chord_tones", {"symbol": sym})
        if value is not None:
            facts.append({"tool": "get_chord_tones", "args": {"symbol": sym}, "result": value})
        if len(facts) >= limit:
            break
    return facts
