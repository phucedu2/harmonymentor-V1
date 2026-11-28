"""Quản trị viên sắp xếp và xóa mềm bài học (FR-ADM-15, FR-ADM-16)

Thêm lessons.sort_key (thứ tự do Quản trị viên đặt; rỗng = theo order_index của seed) và lessons.deleted_at
(xóa mềm, nguyên tắc 7). Seed chỉ ghi order_index nên lần khởi động sau không làm mất thứ tự hay bài đã xóa.
Hạ phiên bản: bỏ hai cột, bài đã xóa hiện lại và thứ tự về như seed.

Revision ID: d8e9f0a1b2c3
Revises: c7a8b9c0d1e2
Create Date: 2026-11-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d8e9f0a1b2c3"
down_revision: Union[str, Sequence[str], None] = "c7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("lessons") as batch:
        batch.add_column(sa.Column("sort_key", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("lessons") as batch:
        batch.drop_column("deleted_at")
        batch.drop_column("sort_key")
