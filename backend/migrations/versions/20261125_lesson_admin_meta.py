"""Cột lessons.admin_meta: tên và mục tiêu bài do Quản trị viên sửa (FR-ADM-14, Phúc 3A)

Seed chạy lại mỗi lần khởi động và ghi đè lessons.title/objectives của bài gốc. Bản sửa của Quản trị viên nằm ở cột
riêng này; seed thấy cột có giá trị thì dùng nó thay cho tên trong đặc tả, nên mọi nơi đang đọc lessons.title vẫn đúng.
Hạ phiên bản: bỏ cột (bài gốc quay về tên trong đặc tả ở lần khởi động sau).

Revision ID: f0a1b2c3d4e5
Revises: e9f0a1b2c3d4
Create Date: 2026-11-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f0a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "e9f0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("lessons") as batch:
        batch.add_column(sa.Column("admin_meta", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("lessons") as batch:
        batch.drop_column("admin_meta")
