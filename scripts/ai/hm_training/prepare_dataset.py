"""Validate auditable HarmonyMentor examples and export conversational SFT splits.

The demo file is intentionally unapproved. Never use --allow-demo for a real model.
No model or external network access is required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

SPLITS = ("train", "dev", "test")
REQUIRED_ANSWER_KEYS = {
    "reply", "citations", "engine_claims", "hint_level", "suggested_actions", "intent"
}
INTENTS = {
    "concept", "explain_error", "quiz", "study_advice", "composition", "out_of_scope"
}
ALLOWED_TOOLS = {
    "get_chord_tones", "get_scale", "identify_interval", "get_roman_numeral"
}


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{n}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{n}: each line must be a JSON object")
        rows.append(value)
    return rows


def answer_checks(raw: str, allowed_ids: set[str], row_id: str) -> None:
    try:
        answer = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{row_id}: assistant content must be a JSON object") from exc
    if not isinstance(answer, dict) or not REQUIRED_ANSWER_KEYS.issubset(answer):
        raise ValueError(f"{row_id}: assistant is missing required TutorAnswer keys")
    if not isinstance(answer["reply"], str) or not answer["reply"].strip():
        raise ValueError(f"{row_id}: empty reply")
    if answer["intent"] not in INTENTS:
        raise ValueError(f"{row_id}: unknown intent")
    if type(answer["hint_level"]) is not int or not 0 <= answer["hint_level"] <= 3:
        raise ValueError(f"{row_id}: invalid hint_level")
    if not isinstance(answer["citations"], list) or not isinstance(answer["engine_claims"], list):
        raise ValueError(f"{row_id}: invalid citations or engine_claims")
    if not isinstance(answer["suggested_actions"], list) or not all(
        isinstance(s, str) for s in answer["suggested_actions"]
    ):
        raise ValueError(f"{row_id}: invalid suggested_actions")
    # Reuse the application's schema without importing app startup, services or DB.
    if str(REPO_ROOT / "backend") not in sys.path:
        sys.path.insert(0, str(REPO_ROOT / "backend"))
    from app.ai.tutor.schema import TutorAnswer
    try:
        TutorAnswer.model_validate(answer)
    except ValueError as exc:
        raise ValueError(f"{row_id}: runtime TutorAnswer validation failed: {exc}") from exc
    if answer.get("quiz") is not None or "verified" in answer:
        raise ValueError(f"{row_id}: model may not self-declare verified or supply quiz")
    if len(answer["citations"]) > 8 or len(answer["engine_claims"]) > 12:
        raise ValueError(f"{row_id}: exceeding TutorAnswer limits")
    for cite in answer["citations"]:
        if not isinstance(cite, dict) or not all(
            isinstance(cite.get(k), str) and cite[k] for k in ("lesson_id", "block_id", "title")
        ):
            raise ValueError(f"{row_id}: citation missing fields")
        if cite["block_id"] not in allowed_ids:
            raise ValueError(f"{row_id}: fabricated/unapproved citation {cite['block_id']}")
    for claim in answer["engine_claims"]:
        if not isinstance(claim, dict) or claim.get("tool") not in ALLOWED_TOOLS:
            raise ValueError(f"{row_id}: invalid engine tool")
        if "verified" in claim:
            raise ValueError(f"{row_id}: model may not self-declare verified")
        if not isinstance(claim.get("args"), dict) or not isinstance(claim.get("result"), str):
            raise ValueError(f"{row_id}: incomplete engine claim")


def validate(rows: list[dict], allow_demo: bool) -> dict:
    if not rows:
        raise ValueError("No examples found")
    counts = Counter()
    ids = set()
    groups: dict[str, str] = {}
    questions: dict[str, str] = {}
    source_ids = set()
    demo_count = 0
    for n, row in enumerate(rows, start=1):
        row_id = row.get("id")
        if not isinstance(row_id, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{3,80}", row_id):
            raise ValueError(f"row {n}: invalid id")
        if row_id in ids:
            raise ValueError(f"duplicate id: {row_id}")
        ids.add(row_id)
        group = row.get("group_id")
        split = row.get("split")
        if not isinstance(group, str) or not group.strip() or split not in SPLITS:
            raise ValueError(f"{row_id}: invalid group_id or split")
        if group in groups and groups[group] != split:
            raise ValueError(f"{row_id}: group {group} leaks across {groups[group]}/{split}")
        groups[group] = split
        source_id = row.get("source_id")
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError(f"{row_id}: source_id required")
        source_ids.add(source_id)
        if not (row.get("reviewed_by_human") is True and row.get("rights_cleared") is True):
            demo_count += 1
            if not allow_demo:
                raise ValueError(f"{row_id}: requires human review and rights clearance; --allow-demo is ONLY for smoke tests")
        messages = row.get("messages")
        if not isinstance(messages, list) or [m.get("role") for m in messages if isinstance(m, dict)] != [
            "system", "user", "assistant"
        ] or len(messages) != 3:
            raise ValueError(f"{row_id}: messages must be system/user/assistant")
        if not all(isinstance(m["content"], str) and m["content"].strip() for m in messages):
            raise ValueError(f"{row_id}: empty message content")
        allowed = row.get("allowed_block_ids")
        if not isinstance(allowed, list) or not all(isinstance(i, str) for i in allowed):
            raise ValueError(f"{row_id}: allowed_block_ids must be a list")
        answer_checks(messages[-1]["content"], set(allowed), row_id)
        question_key = re.sub(r"\s+", " ", messages[1]["content"].casefold()).strip()
        if question_key in questions and questions[question_key] != split:
            raise ValueError(f"{row_id}: duplicated prompt leaks across splits")
        questions[question_key] = split
        counts[split] += 1
    return {
        "counts": dict(counts), "total": len(rows), "groups": len(groups),
        "demo_or_unapproved": demo_count, "source_ids": sorted(source_ids),
    }


def verify_engine(rows: list[dict]) -> None:
    """Check declared AND recognizable displayed claims. Not proof of all prose."""
    sys.path.insert(0, str(REPO_ROOT / "backend"))
    from app.ai.tutor.guardrail import check_answer, check_declared, scan_reply
    from app.ai.tutor.schema import Claim
    for row in rows:
        answer = json.loads(row["messages"][-1]["content"])
        declared = check_declared([Claim.model_validate(c) for c in answer["engine_claims"]])
        scanned = scan_reply(answer["reply"])
        checked = check_answer(answer["reply"], [Claim.model_validate(c) for c in answer["engine_claims"]]).claims
        invalid = [c for c in checked if c.status != "verified"]
        if invalid:
            raise ValueError(f"{row['id']}: {len(invalid)} Engine claim(s) are contradicted or unsupported")
        def claim_key(c):
            args = dict(c.args)
            if c.tool == "get_roman_numeral":
                args.setdefault("mode", "major")
            return c.tool, tuple(sorted(args.items())), c.engine
        declared_keys = {claim_key(c) for c in declared}
        if any(claim_key(c) not in declared_keys for c in scanned):
            raise ValueError(f"{row['id']}: recognizable reply claim missing from engine_claims")

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(src: Path, out: Path, allow_demo: bool, check_engine: bool = False) -> dict:
    rows = read_jsonl(src)
    summary = validate(rows, allow_demo)
    if check_engine:
        verify_engine(rows)
    out.mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        path = out / (split + ".jsonl")
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                if r["split"] == split:
                    f.write(json.dumps({"messages": r["messages"]}, ensure_ascii=False) + "\n")
    manifest = {
        **summary,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "input_sha256": sha256(src),
        "outputs_sha256": {s: sha256(out / (s + ".jsonl")) for s in SPLITS},
        "engine_verified": check_engine,
        "production_ready": check_engine and summary["demo_or_unapproved"] == 0 and summary["counts"].get("train", 0) >= 50,
        "warning": "Examples are for workflow testing only" if summary["demo_or_unapproved"] else None,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--allow-demo", action="store_true", help="accept unreviewed rows for a smoke test ONLY")
    parser.add_argument("--verify-engine", action="store_true", help="check every declared music claim against current Music Engine")
    args = parser.parse_args()
    print(json.dumps(prepare(args.input, args.out, args.allow_demo, args.verify_engine), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
