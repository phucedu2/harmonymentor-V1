"""Phiên bản câu hỏi bất biến (HM-003, ADR-006).

Mỗi `ExerciseVersion` là một ảnh chụp đủ để chấm lại và hiển thị lại đúng câu người học đã làm:
đề bài, lựa chọn, loại câu, cách chấm, đáp án, cấu hình chấm, lời giải và nguồn. Đã phát hành
(hoặc đã có lượt làm) thì không sửa được nữa; muốn sửa phải phát hành phiên bản n+1.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from ..core.config import settings

# Mọi trường quyết định nghĩa của câu. Đổi bất kỳ trường nào cũng phải tăng version (D-1: kể cả nguồn).
SNAPSHOT_FIELDS = (
    "kind", "prompt", "options", "grading_strategy",
    "answer_key", "grader_config", "explanation", "provenance",
)

STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"
VERSION_STATUSES = (STATUS_DRAFT, STATUS_PUBLISHED)

# seed: do seed tạo từ curriculum_specs; git_history: migration PR-3 khôi phục và đã đối chiếu với git;
# missing: bản cũ không khôi phục được chắc chắn nên không hiển thị và không chấm.
ORIGIN_SEED = "seed"
ORIGIN_GIT_HISTORY = "git_history"
ORIGIN_MISSING = "missing"
SNAPSHOT_ORIGINS = (ORIGIN_SEED, ORIGIN_GIT_HISTORY, ORIGIN_MISSING)


def _nfc(value: Any) -> Any:
    # Cùng một chữ tiếng Việt có thể gõ dựng sẵn hoặc tổ hợp; chuẩn hóa để mã băm không đổi vì chuyện gõ phím.
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_nfc(item) for item in value]
    if isinstance(value, dict):
        return {_nfc(key): _nfc(item) for key, item in value.items()}
    return value


def canonical_snapshot(source: dict[str, Any]) -> dict[str, Any]:
    """Ảnh chụp chuẩn hóa từ một dict có đủ SNAPSHOT_FIELDS (mục spec đã đổi tên, hoặc dòng CSDL)."""
    return {name: _nfc(source.get(name)) for name in SNAPSHOT_FIELDS}


def content_hash(snapshot: dict[str, Any]) -> str:
    """SHA-256 của ảnh chụp; migration PR-3 có bản sao đóng băng của hàm này và test so hai bản."""
    payload = json.dumps(canonical_snapshot(snapshot), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def snapshot_from_spec(item: dict[str, Any]) -> dict[str, Any]:
    """curriculum_specs.q() gọi cách chấm là `strategy`; trong CSDL là `grading_strategy`."""
    return canonical_snapshot({
        "kind": item["kind"], "prompt": item["prompt"], "options": item.get("options"),
        "grading_strategy": item["strategy"], "answer_key": item["answer_key"],
        "grader_config": item.get("grader_config") or {}, "explanation": item.get("explanation"),
        "provenance": item.get("provenance"),
    })


def snapshot_from_row(version: Any) -> dict[str, Any]:
    return canonical_snapshot({name: getattr(version, name) for name in SNAPSHOT_FIELDS})


def visible_statuses() -> set[str]:
    """Bản nháp chỉ hiện khi bật SHOW_DRAFT_CONTENT tường minh (dev/test); mặc định người học chỉ thấy bản đã phát hành."""
    if settings.show_draft_content:
        return {STATUS_DRAFT, STATUS_PUBLISHED}
    return {STATUS_PUBLISHED}


def lesson_visible(lesson: Any) -> bool:
    """Bài nháp (status draft, phuc-music L09–L12) chỉ hiện khi bật SHOW_DRAFT_CONTENT."""
    return lesson.status != STATUS_DRAFT or settings.show_draft_content


def block_visible(payload: dict[str, Any] | None) -> bool:
    """Khối nháp trong bài đã phát hành (mục "Dùng vào sáng tác") ẩn với người học cho tới khi Đạt duyệt."""
    return (payload or {}).get("status") != STATUS_DRAFT or settings.show_draft_content


def current_version(exercise: Any, statuses: set[str] | None = None) -> Any | None:
    """Phiên bản người học được làm lúc này, hoặc None nếu câu bị ẩn.

    Lấy bản có số lớn nhất trong các bản được phép hiện. Bản đó thiếu ảnh chụp thì ẩn cả câu chứ không lùi
    về bản cũ hơn, vì bản cũ hơn đã bị thay và chấm theo nó là chấm sai đề.
    """
    if exercise.deleted_at is not None or not exercise.active:
        return None
    allowed = statuses if statuses is not None else visible_statuses()
    candidates = [v for v in exercise.versions if v.status in allowed]
    if not candidates:
        return None
    latest = max(candidates, key=lambda v: v.version)
    if latest.snapshot_origin == ORIGIN_MISSING:
        return None
    return latest


@dataclass
class SeedConflict:
    code: str
    target: str
    detail: str
    fields: list[str] = field(default_factory=list)

    def describe(self) -> str:
        changed = f" (trường khác: {', '.join(self.fields)})" if self.fields else ""
        return f"- {self.code} {self.target}{changed}: {self.detail}"


class SeedConflictError(RuntimeError):
    """Nội dung trong curriculum_specs lệch với phiên bản đã khóa. Seed rollback toàn bộ, không tự tăng version."""

    def __init__(self, conflicts: list[SeedConflict]):
        self.conflicts = conflicts
        lines = [f"Seed dừng: {len(conflicts)} xung đột phiên bản câu hỏi, CSDL giữ nguyên (HM-003, ADR-006)."]
        lines += [c.describe() for c in conflicts]
        super().__init__("\n".join(lines))


class ImmutableVersionError(RuntimeError):
    """Có đường ghi (ngoài seed) cố sửa hoặc xóa phiên bản đã khóa."""
