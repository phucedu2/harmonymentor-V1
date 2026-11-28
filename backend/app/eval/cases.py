"""Đọc và kiểm bộ ca đánh giá eval/cases.jsonl."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CASES_PATH = ROOT / "eval" / "cases.jsonl"
BASELINE_PATH = ROOT / "eval" / "baseline.json"
REPORT_PATH = ROOT / "eval" / "report.md"

TYPES = {"retrieval", "followup", "untaught", "offtopic", "attack", "help", "greeting", "bad_citation", "gate"}
FLOWS = {"A", "B", "C", "D", "G"}
MIN_CASES = 60


class CaseError(ValueError):
    pass


def load_cases(path: Path = CASES_PATH) -> list[dict]:
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    validate(cases)
    return cases


def validate(cases: list[dict]) -> None:
    from ..ai.tutor.retriever import knowledge_base

    blocks = {c.block_id for c in knowledge_base()}
    if len(cases) < MIN_CASES:
        raise CaseError(f"Cần ít nhất {MIN_CASES} ca, hiện có {len(cases)}.")
    seen = set()
    for c in cases:
        cid = c.get("id")
        if not cid or cid in seen:
            raise CaseError(f"Mã ca trống hoặc trùng: {cid!r}")
        seen.add(cid)
        if c.get("type") not in TYPES:
            raise CaseError(f"{cid}: type không hợp lệ {c.get('type')!r}")
        if c["type"] == "gate":
            if not c.get("text") or c.get("label") not in {"relevant", "irrelevant", "borderline"}:
                raise CaseError(f"{cid}: ca gate cần text và label relevant|irrelevant|borderline")
            continue
        if not c.get("q") or c.get("flow") not in FLOWS:
            raise CaseError(f"{cid}: thiếu q hoặc flow")
        if c["type"] in {"retrieval", "followup"}:
            bad = [b for b in c.get("blocks", []) if b not in blocks] or ([] if c.get("blocks") else ["(trống)"])
            if bad:
                raise CaseError(f"{cid}: block không có trong kho: {bad}")
