"""Bảng media_files: âm thanh ví dụ do Quản trị viên tải lên (FR-ADM-37, Phúc 8A)

Hạ phiên bản: bỏ bảng (khối ví dụ nghe đã tạo sẽ mất file).

Revision ID: b2c3d4e5f6a8
Revises: a1b2c3d4e5f7
Create Date: 2026-11-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a8"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "media_files",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("filename", sa.String(200), nullable=False),
        sa.Column("content_type", sa.String(60), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("created_by", sa.String(64), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("media_files")
