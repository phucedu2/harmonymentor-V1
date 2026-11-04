"""Kiểm khẳng định nhạc lý của AI bằng Music Engine (04 mục 3.6, đề GĐ3 mục 6, TC-15).

Hai nguồn khẳng định:
1. engine_claims AI khai: gọi lại công cụ với đúng args, so kết quả AI ghi.
2. Quét reply: mọi "ký hiệu hợp âm + dãy nốt" và "âm giai + dãy nốt", kể cả cái AI không khai, sau khi đổi
   tên nốt tiếng Việt (Đô Mi Sol) sang chữ cái.
Mỗi mục: verified | contradicted | unsupported (Engine không hiểu ký hiệu/công cụ). Nhãn
"Đã kiểm bằng Music Engine" chỉ khi có ít nhất một mục và mọi mục đều verified."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from ...music_engine import tools as engine
from .notes import (CHORD_WITH_NOTES, INTERVAL_WITH_NAME, SCALE_WITH_NOTES, SYMBOL_IN_QUESTION, interval_name,
                    norm_accidentals, solfege_to_letters, split_notes)
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
               "identify_interval": ("lower", "upper")}[tool]
    try:
        out = fn(**{k: v for k, v in args.items() if k in allowed})
    except TypeError:
        return None, {"ok": False, "error": {"code": "BAD_ARGS"}}
    if not out.get("ok"):
        return None, out
    if tool == "identify_interval":
        return out["interval"], out
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


def check_declared(claims: Iterable[Claim]) -> list[CheckedClaim]:
    out = []
    for c in claims:
        value, _ = run_tool(c.tool, c.args)
        out.append(CheckedClaim(c.tool, dict(c.args), c.result, value, _compare(c.tool, c.result, value), "declared"))
    return out


def scan_reply(reply: str) -> list[CheckedClaim]:
    text = solfege_to_letters(reply)
    out = []
    for m in CHORD_WITH_NOTES.finditer(text):
        args = {"symbol": norm_accidentals(m["sym"])}
        claimed = " ".join(split_notes(m["notes"]))
        value, _ = run_tool("get_chord_tones", args)
        out.append(CheckedClaim("get_chord_tones", args, claimed, value,
                                _compare("get_chord_tones", claimed, value), "scanned"))
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
