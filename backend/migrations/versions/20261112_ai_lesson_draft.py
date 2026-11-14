"""AI tóm tắt tài liệu thành bài nháp (ADR-025)

Thêm source_documents (chữ đã trích theo trang, không giữ file gốc) và ai_lesson_drafts. Không đổi bảng cũ.
Hạ phiên bản: bỏ hai bảng (bài đã xuất bản vẫn ở lại vì nằm trong lessons/exercises).

Revision ID: a5e6f7a8b9c0
Revises: f4d5e6f7a8b9
Create Date: 2026-11-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a5e6f7a8b9c0"
down_revision: Union[str, Sequence[str], None] = "f4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "source_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("uploaded_by", sa.String(length=64), nullable=True),
        sa.Column("filename", sa.String(length=240), nullable=False),
        sa.Column("kind", sa.String(length=8), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("source_title", sa.String(length=300), nullable=False),
        sa.Column("source_note", sa.String(length=300), nullable=True),
        sa.Column("consent", sa.Boolean(), nullable=False),
        sa.Column("pages", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_source_documents_uploaded_by"), "source_documents", ["uploaded_by"], unique=False)
    op.create_table(
        "ai_lesson_drafts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("page_from", sa.Integer(), nullable=False),
        sa.Column("page_to", sa.Integer(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("engine_report", sa.JSON(), nullable=False),
        sa.Column("model", sa.String(length=80), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("published_lesson_id", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('draft', 'published', 'rejected')", name="ck_ai_lesson_drafts_status"),
        sa.ForeignKeyConstraint(["document_id"], ["source_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_lesson_drafts_document_id"), "ai_lesson_drafts", ["document_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_lesson_drafts_document_id"), table_name="ai_lesson_drafts")
    op.drop_table("ai_lesson_drafts")
    op.drop_index(op.f("ix_source_documents_uploaded_by"), table_name="source_documents")
    op.drop_table("source_documents")
