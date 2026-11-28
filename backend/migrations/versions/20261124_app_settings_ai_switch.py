"""Bảng app_settings: công tắc bật/tắt AI do Quản trị viên đổi qua web (ADR-036, Phúc 8A)

Chỉ lưu cờ bật/tắt; khóa Gemini vẫn chỉ ở .env. Bảng rỗng = AI theo .env như trước, không đổi hành vi cũ.
Hạ phiên bản: bỏ bảng (AI quay về chỉ theo .env).

Revision ID: e9f0a1b2c3d4
Revises: c7a8b9c0d1e2
Create Date: 2026-11-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e9f0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "d8e9f0a1b2c3"   # nối sau migration bài học (ADR-035)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("updated_by", sa.String(length=64), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
