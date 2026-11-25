"""Cột review_items.deleted_at: xóa mềm thẻ ôn do Quản trị viên soạn (FR-ADM-31..34, Phúc 6A)

Thẻ bị xóa mềm không còn hiện ở hàng đợi ôn và không được kích hoạt cho người học mới; lượt ôn cũ và mastery giữ nguyên.
Hạ phiên bản: bỏ cột (thẻ đã xóa mềm hiện lại).

Revision ID: a1b2c3d4e5f7
Revises: f0a1b2c3d4e5
Create Date: 2026-11-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f7"
down_revision: Union[str, Sequence[str], None] = "f0a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("review_items") as batch:
        batch.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("review_items") as batch:
        batch.drop_column("deleted_at")
