"""Cổng nhạc lý cho tài liệu Admin (góp ý thầy T1, G2)

Thêm 6 cột vào source_documents: trạng thái liên quan (accepted/pending/rejected), điểm, lý do, chi tiết chấm điểm,
người duyệt và lúc duyệt. Tài liệu đã có từ trước coi là accepted (Admin đã chủ động tải và chọn trang).
Hạ phiên bản: bỏ 6 cột.

Revision ID: b6f7a8b9c0d1
Revises: a5e6f7a8b9c0
Create Date: 2026-11-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b6f7a8b9c0d1"
down_revision: Union[str, Sequence[str], None] = "a5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("source_documents") as batch:
        batch.add_column(sa.Column("relevance_status", sa.String(length=10), nullable=False, server_default="accepted"))
        batch.add_column(sa.Column("relevance_score", sa.Float(), nullable=True))
        batch.add_column(sa.Column("relevance_reason", sa.Text(), nullable=True))
        batch.add_column(sa.Column("relevance_detail", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("reviewed_by", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_check_constraint("ck_source_documents_relevance_status", "relevance_status IN ('accepted', 'pending', 'rejected')")


def downgrade() -> None:
    with op.batch_alter_table("source_documents") as batch:
        batch.drop_constraint("ck_source_documents_relevance_status", type_="check")
        for name in ("reviewed_at", "reviewed_by", "relevance_detail", "relevance_reason", "relevance_score", "relevance_status"):
            batch.drop_column(name)
