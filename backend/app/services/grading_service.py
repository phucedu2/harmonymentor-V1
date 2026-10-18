"""Assessment adapter between persisted exercise contracts and deterministic graders."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from ..music_engine.grading import grade_build_chord, grade_build_scale, grade_roman_numeral


@dataclass
class GradeOutcome:
    correct: bool
    score: float
    primary_error: str | None
    feedback: str | None
    errors: list[dict[str, Any]] = field(default_factory=list)


def _strip_accents(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn")


def _normalize_text(value: Any, config: dict[str, Any]) -> str:
    text = str(value).strip()
    if config.get("normalize_dashes"):
        text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    if config.get("strip_accents"):
        text = _strip_accents(text)
    text = re.sub(r"\s+", " ", text)
    if not config.get("case_sensitive", False):
        text = text.casefold()
    return text


def _split_notes(answer: Any) -> list[str]:
    if isinstance(answer, list):
        return [str(x).strip() for x in answer if str(x).strip()]
    if isinstance(answer, str):
        return [x for x in re.split(r"[\s,;–—-]+", answer.strip()) if x]
    return []


def grade_payload(strategy: str, answer_key: dict[str, Any], grader_config: dict[str, Any], answer: Any) -> GradeOutcome:
    if strategy == "music_engine":
        kind = grader_config.get("kind")
        if kind == "build_chord":
            result = grade_build_chord(grader_config.get("symbol"), _split_notes(answer))
        elif kind == "build_scale":
            result = grade_build_scale(
                grader_config.get("tonic"),
                grader_config.get("scale_type", "major"),
                _split_notes(answer),
            )
        elif kind == "roman_numeral":
            result = grade_roman_numeral(
                grader_config.get("key"),
                grader_config.get("chord"),
                str(answer),
            )
        else:
            return GradeOutcome(False, 0.0, "UNSUPPORTED_GRADER", "Dạng chấm bằng Music Engine này chưa được hỗ trợ.", [
                {"code": "UNSUPPORTED_GRADER", "kind": kind}
            ])
        errors = [{"code": e.get("code", "UNKNOWN"), **{k: v for k, v in e.items() if k != "code"}} for e in result.get("errors", [])]
        return GradeOutcome(
            correct=bool(result["correct"]),
            score=1.0 if result["correct"] else 0.0,
            primary_error=result.get("primary_error"),
            feedback=result.get("message_vi"),
            errors=errors,
        )

    if strategy == "exact":
        expected = answer_key.get("expected")
        if isinstance(expected, list):
            got = answer if isinstance(answer, list) else _split_notes(answer)
            correct = [_normalize_text(x, grader_config) for x in got] == [_normalize_text(x, grader_config) for x in expected]
        else:
            correct = _normalize_text(answer, grader_config) == _normalize_text(expected, grader_config)
        return GradeOutcome(
            correct=correct,
            score=1.0 if correct else 0.0,
            primary_error=None if correct else "INCORRECT_ANSWER",
            feedback="Chính xác." if correct else "Chưa đúng; hãy nhớ lại khái niệm rồi thử lại.",
            errors=[] if correct else [{"code": "INCORRECT_ANSWER"}],
        )

    if strategy == "rubric":
        accepted = answer_key.get("accepted", [])
        got = _normalize_text(answer, grader_config)
        normalized = [_normalize_text(x, grader_config) for x in accepted]
        mode = grader_config.get("mode", "equals_any")
        if mode == "contains_any":
            correct = any(candidate and candidate in got for candidate in normalized)
        else:
            correct = got in normalized
        return GradeOutcome(
            correct=correct,
            score=1.0 if correct else 0.0,
            primary_error=None if correct else "RUBRIC_MISS",
            feedback="Ý chính phù hợp." if correct else "Câu trả lời chưa thể hiện đúng ý trọng tâm của rubric.",
            errors=[] if correct else [{"code": "RUBRIC_MISS"}],
        )

    return GradeOutcome(False, 0.0, "UNSUPPORTED_GRADING_STRATEGY", "Chiến lược chấm chưa được hỗ trợ.", [
        {"code": "UNSUPPORTED_GRADING_STRATEGY", "strategy": strategy}
    ])
