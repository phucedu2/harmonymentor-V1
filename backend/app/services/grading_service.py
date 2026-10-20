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


# Người mới thường gõ "1 b3 5", "Gm7 C7 Fmaj7" hay "T → PD → D → T": cùng một chuỗi nhưng khác
# dấu nối. Câu có `sequence` so từng phần tử, `unordered` bỏ qua thứ tự (ví dụ cặp guide tone B, F).
_SEQUENCE_SPLIT = re.compile(r"\s+(?:và|va|and)\s+|\s*(?:->|=>|→|⇒|>|[,;/\s–—−-])\s*")

# Câu tự luận chấm theo từ khóa (contains_any) dễ chấm nhầm "không biết" là đúng vì có chữ "không".
_UNSURE_PHRASES = ("khong biet", "chua biet", "khong hieu", "khong nho", "ko biet", "k biet", "khong ro",
                   "dont know", "don't know", "idk", "not sure")


def _normalize_sequence(text: str, config: dict[str, Any]) -> str:
    parts = [part for part in _SEQUENCE_SPLIT.split(text) if part]
    if config.get("unordered"):
        parts = sorted(parts)
    return "-".join(parts)


def _normalize_text(value: Any, config: dict[str, Any]) -> str:
    text = str(value).strip()
    if config.get("normalize_dashes"):
        text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    if config.get("normalize_accidentals"):
        text = text.replace("♭", "b").replace("♯", "#")
    if config.get("strip_accents"):
        text = _strip_accents(text)
    text = re.sub(r"\s+", " ", text)
    if not config.get("case_sensitive", False):
        text = text.casefold()
    if config.get("sequence") or config.get("unordered"):
        text = _normalize_sequence(text, config)
    return text


# Học sinh Việt Nam quen tên Đô–Rê–Mi; đổi sang tên chữ cái trước khi đưa cho Music Engine.
# Chỉ đổi tên gọi, không tính nhạc lý: dấu hóa vẫn do Engine kiểm.
_SOLFEGE = {"do": "C", "re": "D", "mi": "E", "fa": "F", "son": "G", "sol": "G", "la": "A", "si": "B"}
_SOLFEGE_RE = re.compile(r"^(do|re|mi|fa|son|sol|la|si)\s*(thang|giang|#|b|♯|♭)?$")


def _solfege_to_letter(token: str) -> str:
    match = _SOLFEGE_RE.match(_strip_accents(token).casefold().replace("đ", "d"))
    if not match:
        return token
    accidental = {"thang": "#", "giang": "b", "♯": "#", "♭": "b"}.get(match.group(2) or "", match.group(2) or "")
    return _SOLFEGE[match.group(1)] + accidental


def _split_notes(answer: Any) -> list[str]:
    if isinstance(answer, list):
        return [_solfege_to_letter(str(x).strip()) for x in answer if str(x).strip()]
    if isinstance(answer, str):
        # "Rê thăng" là một nốt: nối tên Đô–Rê–Mi với dấu hóa viết bằng chữ trước khi tách.
        text = re.sub(r"\s+(thăng|giáng|thang|giang)\b", r"\1", answer.strip(), flags=re.IGNORECASE)
        return [_solfege_to_letter(x) for x in re.split(r"[\s,;–—-]+", text) if x]
    return []


def is_self_check(strategy: str | None, grader_config: dict[str, Any]) -> bool:
    """Thẻ ôn có ý mở (chấm theo từ khóa) để người học tự đánh giá sau khi lật thẻ."""
    return strategy == "rubric" and grader_config.get("mode") == "contains_any"


def _grading_mode(grader_config: dict[str, Any], input_method: str | None) -> str:
    # Phím đàn không mang thông tin chính tả: phím giữa D và E vừa là D# vừa là Eb. Bài nộp bằng
    # piano chỉ chấm cao độ; chính tả tên nốt được chấm ở bài gõ chữ.
    if input_method == "piano":
        return "pitch_class_only"
    return grader_config.get("grading_mode", "strict_spelling")


def grade_payload(strategy: str, answer_key: dict[str, Any], grader_config: dict[str, Any], answer: Any,
                  input_method: str | None = None) -> GradeOutcome:
    if strategy == "music_engine":
        kind = grader_config.get("kind")
        mode = _grading_mode(grader_config, input_method)
        if kind == "build_chord":
            result = grade_build_chord(
                grader_config.get("symbol"),
                _split_notes(answer),
                grading_mode=mode,
                root_position_only=bool(grader_config.get("root_position_only", False)),
            )
        elif kind == "build_scale":
            result = grade_build_scale(
                grader_config.get("tonic"),
                grader_config.get("scale_type", "major"),
                _split_notes(answer),
                grading_mode=mode,
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
            feedback="Chính xác." if correct else "Hãy nhớ lại khái niệm rồi thử lại.",
            errors=[] if correct else [{"code": "INCORRECT_ANSWER"}],
        )

    if strategy == "rubric":
        accepted = answer_key.get("accepted", [])
        got = _normalize_text(answer, grader_config)
        normalized = [_normalize_text(x, grader_config) for x in accepted]
        mode = grader_config.get("mode", "equals_any")
        if mode == "contains_any":
            unsure = any(phrase in _strip_accents(got) for phrase in _UNSURE_PHRASES)
            correct = not unsure and any(candidate and candidate in got for candidate in normalized)
        else:
            correct = got in normalized
        return GradeOutcome(
            correct=correct,
            score=1.0 if correct else 0.0,
            primary_error=None if correct else "RUBRIC_MISS",
            feedback="Ý chính phù hợp." if correct else "Câu trả lời chưa nêu đúng ý chính của câu hỏi.",
            errors=[] if correct else [{"code": "RUBRIC_MISS"}],
        )

    return GradeOutcome(False, 0.0, "UNSUPPORTED_GRADING_STRATEGY", "Chiến lược chấm chưa được hỗ trợ.", [
        {"code": "UNSUPPORTED_GRADING_STRATEGY", "strategy": strategy}
    ])
