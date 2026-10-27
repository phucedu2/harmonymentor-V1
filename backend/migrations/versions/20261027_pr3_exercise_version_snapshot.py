"""exercise version snapshot, draft/published, soft delete (PR-3, HM-003)

Phiên bản câu hỏi trở thành ảnh chụp bất biến: thêm đề bài, lựa chọn, loại câu, cách chấm vào
exercise_versions; thêm trạng thái draft/published, mã băm nội dung, nguồn gốc ảnh chụp; thêm
exercises.deleted_at (xóa mềm). Xem docs/decisions/ADR-006-phien-ban-bai-tap.md.

Dữ liệu cũ: không xóa, không tạo thêm dòng nào. Mỗi phiên bản đang có trong CSDL được điền ảnh chụp từ
migrations/data/pr3_anh_chup_lich_su.json (trích từ lịch sử git) CHỈ KHI đáp án, cấu hình chấm, lời giải
và danh tính câu khớp đúng với git; bản mới nhất của câu còn phải khớp cả đề bài đang lưu trên exercises.
Không khớp thì snapshot_origin='missing': không bịa đề, lượt làm cũ vẫn giữ, câu đó không hiển thị và không chấm.

downgrade() cố ý từ chối: xóa các cột này làm mất ảnh chụp. Muốn quay lại thì khôi phục từ bản sao lưu.

Revision ID: d3a7f1c2e905
Revises: b2c4e6f80a13
Create Date: 2026-10-27
"""
from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Any, Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3a7f1c2e905"
down_revision: Union[str, Sequence[str], None] = "b2c4e6f80a13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SNAPSHOT_FILE = Path(__file__).resolve().parent.parent / "data" / "pr3_anh_chup_lich_su.json"
# SHA-256 của phần "versions" sau khi chuẩn hóa JSON (không phụ thuộc xuống dòng CRLF/LF khi checkout trên Windows).
SNAPSHOT_SHA256 = "82b4af3d0bf5e1f62474affa72fd3633efa6f4acebae4709b7744eacdd7c8e68"

# Bản sao đóng băng của app.content.versioning (SNAPSHOT_FIELDS, content_hash). Migration không import code
# ứng dụng vì code đó còn đổi về sau; test_pr3 kiểm hai bản cho cùng kết quả.
SNAPSHOT_FIELDS = (
    "kind", "prompt", "options", "grading_strategy",
    "answer_key", "grader_config", "explanation", "provenance",
)


def _nfc(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_nfc(item) for item in value]
    if isinstance(value, dict):
        return {_nfc(key): _nfc(item) for key, item in value.items()}
    return value


def content_hash(snapshot: dict[str, Any]) -> str:
    canonical = {name: _nfc(snapshot.get(name)) for name in SNAPSHOT_FIELDS}
    payload = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_known_snapshots() -> dict[str, dict[str, Any]]:
    versions = json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))["versions"]
    digest = hashlib.sha256(
        json.dumps(versions, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if digest != SNAPSHOT_SHA256:
        raise RuntimeError(f"{SNAPSHOT_FILE.name} đã bị sửa (SHA-256 {digest}); dừng migration để không khôi phục sai đề.")
    return versions


def restore_snapshot(row: dict[str, Any], exercise: dict[str, Any], is_latest: bool,
                     known: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """Ảnh chụp đã đối chiếu cho một dòng exercise_versions, hoặc None nếu không chắc chắn."""
    k = known.get(row["id"])
    if k is None:
        return None
    same_identity = (
        row["exercise_id"] == k["exercise_id"] and row["version"] == k["version"]
        and exercise["lesson_id"] == k["lesson_id"] and exercise["skill_id"] == k["skill_id"]
    )
    # Đáp án, cấu hình chấm, lời giải nằm trên chính dòng phiên bản: khớp git nghĩa là cùng một bản.
    same_grading = (
        (row["answer_key"] or {}) == k["answer_key"] and (row["grader_config"] or {}) == k["grader_config"]
        and row["explanation"] == k["explanation"]
    )
    if not (same_identity and same_grading):
        return None
    if is_latest:
        # Bản mới nhất: exercises đang giữ đúng đề của nó, nên phải khớp nguồn trước khi dùng.
        same_prompt = (
            exercise["kind"] == k["kind"] and exercise["prompt"] == k["prompt"]
            and exercise["options"] == k["options"] and exercise["grading_strategy"] == k["grading_strategy"]
        )
        if not same_prompt:
            return None
    snapshot = {
        "kind": k["kind"], "prompt": k["prompt"], "options": k["options"], "grading_strategy": k["grading_strategy"],
        # Phần còn lại giữ nguyên giá trị đang lưu (kể cả provenance) để không sửa dữ liệu lịch sử.
        "answer_key": row["answer_key"], "grader_config": row["grader_config"],
        "explanation": row["explanation"], "provenance": row["provenance"],
    }
    return snapshot


_versions = sa.table(
    "exercise_versions",
    sa.column("id", sa.String), sa.column("exercise_id", sa.String), sa.column("version", sa.Integer),
    sa.column("kind", sa.String), sa.column("prompt", sa.Text), sa.column("options", sa.JSON),
    sa.column("grading_strategy", sa.String), sa.column("answer_key", sa.JSON), sa.column("grader_config", sa.JSON),
    sa.column("explanation", sa.Text), sa.column("provenance", sa.JSON), sa.column("status", sa.String),
    sa.column("published_at", sa.DateTime(timezone=True)), sa.column("content_hash", sa.String),
    sa.column("snapshot_origin", sa.String), sa.column("created_at", sa.DateTime(timezone=True)),
)
_exercises = sa.table(
    "exercises",
    sa.column("id", sa.String), sa.column("lesson_id", sa.String), sa.column("skill_id", sa.String),
    sa.column("kind", sa.String), sa.column("prompt", sa.Text), sa.column("options", sa.JSON),
    sa.column("grading_strategy", sa.String),
)

_GUARD_FUNCTION = """
CREATE OR REPLACE FUNCTION hm_bao_ve_phien_ban_bai_tap() RETURNS trigger AS $$
DECLARE
    locked boolean;
BEGIN
    locked := OLD.status = 'published'
        OR EXISTS (SELECT 1 FROM attempts WHERE exercise_version_id = OLD.id);
    IF TG_OP = 'DELETE' THEN
        IF locked THEN
            RAISE EXCEPTION 'EXERCISE_VERSION_IMMUTABLE: không xóa phiên bản % (đã phát hành hoặc đã có lượt làm)', OLD.id
                USING ERRCODE = 'check_violation';
        END IF;
        RETURN OLD;
    END IF;
    IF OLD.status = 'published' AND NEW.status <> 'published' THEN
        RAISE EXCEPTION 'EXERCISE_VERSION_IMMUTABLE: phiên bản % đã phát hành, không chuyển về %', OLD.id, NEW.status
            USING ERRCODE = 'check_violation';
    END IF;
    IF locked AND (
        NEW.id IS DISTINCT FROM OLD.id OR NEW.exercise_id IS DISTINCT FROM OLD.exercise_id
        OR NEW.version IS DISTINCT FROM OLD.version OR NEW.kind IS DISTINCT FROM OLD.kind
        OR NEW.prompt IS DISTINCT FROM OLD.prompt OR NEW.options::jsonb IS DISTINCT FROM OLD.options::jsonb
        OR NEW.grading_strategy IS DISTINCT FROM OLD.grading_strategy
        OR NEW.answer_key::jsonb IS DISTINCT FROM OLD.answer_key::jsonb
        OR NEW.grader_config::jsonb IS DISTINCT FROM OLD.grader_config::jsonb
        OR NEW.explanation IS DISTINCT FROM OLD.explanation
        OR NEW.provenance::jsonb IS DISTINCT FROM OLD.provenance::jsonb
        OR NEW.content_hash IS DISTINCT FROM OLD.content_hash
        OR NEW.snapshot_origin IS DISTINCT FROM OLD.snapshot_origin
    ) THEN
        RAISE EXCEPTION 'EXERCISE_VERSION_IMMUTABLE: phiên bản % đã khóa; hãy phát hành phiên bản mới', OLD.id
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

_IDENTITY_FUNCTION = """
CREATE OR REPLACE FUNCTION hm_bao_ve_danh_tinh_cau_hoi() RETURNS trigger AS $$
BEGIN
    IF (NEW.lesson_id IS DISTINCT FROM OLD.lesson_id OR NEW.skill_id IS DISTINCT FROM OLD.skill_id)
       AND EXISTS (SELECT 1 FROM exercise_versions WHERE exercise_id = OLD.id) THEN
        RAISE EXCEPTION 'EXERCISE_IDENTITY_IMMUTABLE: câu % đã có phiên bản; đổi bài hoặc kỹ năng thì tạo câu mới', OLD.id
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    known = load_known_snapshots()
    bind = op.get_bind()

    with op.batch_alter_table("exercise_versions") as batch:
        batch.add_column(sa.Column("kind", sa.String(length=40), nullable=True))
        batch.add_column(sa.Column("prompt", sa.Text(), nullable=True))
        batch.add_column(sa.Column("options", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("grading_strategy", sa.String(length=40), nullable=True))
        # Mặc định an toàn trong lúc chuyển: chưa điền xong thì bị ẩn (draft) và không được chấm (missing).
        batch.add_column(sa.Column("status", sa.String(length=16), server_default="draft", nullable=False))
        batch.add_column(sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("content_hash", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("snapshot_origin", sa.String(length=16), server_default="missing", nullable=False))
    with op.batch_alter_table("exercises") as batch:
        batch.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    exercises = {row["id"]: dict(row) for row in bind.execute(sa.select(_exercises)).mappings()}
    rows = [dict(row) for row in bind.execute(sa.select(_versions)).mappings()]
    latest: dict[str, int] = {}
    for row in rows:
        latest[row["exercise_id"]] = max(latest.get(row["exercise_id"], row["version"]), row["version"])

    for row in rows:
        exercise = exercises[row["exercise_id"]]
        snapshot = restore_snapshot(row, exercise, row["version"] == latest[row["exercise_id"]], known)
        # Mọi bản đang có đều đã từng chạy cho người học, nên giữ "published" (D-3: dữ liệu kế thừa, chưa qua
        # quy trình duyệt mới của Đạt). Không đụng answer_key, grader_config, explanation, provenance.
        values: dict[str, Any] = {"status": "published", "published_at": row["created_at"]}
        if snapshot is None:
            values.update(snapshot_origin="missing")
        else:
            values.update(
                kind=snapshot["kind"], prompt=snapshot["prompt"], options=snapshot["options"],
                grading_strategy=snapshot["grading_strategy"], content_hash=content_hash(snapshot),
                snapshot_origin="git_history",
            )
        bind.execute(sa.update(_versions).where(_versions.c.id == row["id"]).values(**values))

    with op.batch_alter_table("exercise_versions") as batch:
        batch.create_check_constraint("ck_exercise_versions_status", "status IN ('draft', 'published')")
        batch.create_check_constraint(
            "ck_exercise_versions_origin", "snapshot_origin IN ('seed', 'git_history', 'missing')")
        batch.create_check_constraint(
            "ck_exercise_versions_snapshot",
            "snapshot_origin = 'missing' OR (kind IS NOT NULL AND prompt IS NOT NULL "
            "AND grading_strategy IS NOT NULL AND content_hash IS NOT NULL)",
        )

    if bind.dialect.name == "postgresql":
        # Tạo trigger SAU khi điền dữ liệu: từ đây mọi câu UPDATE/DELETE trực tiếp cũng bị chặn, không chỉ qua ORM.
        op.execute(_GUARD_FUNCTION)
        op.execute(
            "CREATE TRIGGER hm_bao_ve_phien_ban_bai_tap BEFORE UPDATE OR DELETE ON exercise_versions "
            "FOR EACH ROW EXECUTE FUNCTION hm_bao_ve_phien_ban_bai_tap()"
        )
        op.execute(_IDENTITY_FUNCTION)
        op.execute(
            "CREATE TRIGGER hm_bao_ve_danh_tinh_cau_hoi BEFORE UPDATE ON exercises "
            "FOR EACH ROW EXECUTE FUNCTION hm_bao_ve_danh_tinh_cau_hoi()"
        )


def downgrade() -> None:
    # Không coi downgrade là đường lùi dữ liệu (yêu cầu của nhóm): xóa cột là mất ảnh chụp đề bài của lượt làm cũ.
    raise RuntimeError(
        "Migration d3a7f1c2e905 (PR-3) không hỗ trợ downgrade vì sẽ xóa ảnh chụp phiên bản câu hỏi. "
        "Muốn quay lại: khôi phục CSDL từ bản sao lưu (pg_dump) chụp trước khi upgrade."
    )
