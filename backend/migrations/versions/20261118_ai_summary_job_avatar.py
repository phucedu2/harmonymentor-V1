"""Tóm tắt cả tài liệu chạy nền + ảnh đại diện con vật (ADR-029)

Thêm bảng ai_summary_jobs (một việc tóm tắt cả tài liệu, trạng thái từng phần lưu JSON để chạy tiếp được) và cột
users.avatar_key (khóa con vật; rỗng = con vật suy từ id). Không đổi dữ liệu cũ.
Hạ phiên bản: bỏ bảng và cột (bản nháp đã sinh vẫn ở lại trong ai_lesson_drafts).

Revision ID: c7a8b9c0d1e2
Revises: b6f7a8b9c0d1
Create Date: 2026-11-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7a8b9c0d1e2"
down_revision: Union[str, Sequence[str], None] = "b6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("avatar_key", sa.String(length=24), nullable=True))
    op.create_table(
        "ai_summary_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=12), nullable=False),
        sa.Column("pause_reason", sa.String(length=24), nullable=True),
        sa.Column("parts", sa.JSON(), nullable=False),
        sa.Column("skipped_pages", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('running', 'paused', 'done', 'cancelled')", name="ck_ai_summary_jobs_status"),
        sa.ForeignKeyConstraint(["document_id"], ["source_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_summary_jobs_document_id"), "ai_summary_jobs", ["document_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_summary_jobs_document_id"), table_name="ai_summary_jobs")
    op.drop_table("ai_summary_jobs")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("avatar_key")
