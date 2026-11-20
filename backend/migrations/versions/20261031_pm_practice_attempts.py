"""practice_attempts: lịch sử Luyện tập (phuc-music Bước 2, FR-LRN-08)

Chỉ thêm một bảng mới, không sửa bảng hay migration cũ. Chờ Thắng duyệt schema (ADR-009-de-xuat).

Revision ID: e5f1a2b3c4d6
Revises: d3a7f1c2e905
Create Date: 2026-10-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f1a2b3c4d6"
down_revision: Union[str, Sequence[str], None] = "d3a7f1c2e905"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "practice_attempts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("level", sa.String(length=8), nullable=True),
        sa.Column("question", sa.JSON(), nullable=False),
        sa.Column("answer", sa.JSON(), nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("primary_error", sa.String(length=100), nullable=True),
        sa.Column("is_test", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('chord', 'interval', 'scale', 'roman')", name="ck_practice_kind"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_practice_attempts_user_id"), "practice_attempts", ["user_id"], unique=False)
    op.create_index(op.f("ix_practice_attempts_created_at"), "practice_attempts", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_practice_attempts_created_at"), table_name="practice_attempts")
    op.drop_index(op.f("ix_practice_attempts_user_id"), table_name="practice_attempts")
    op.drop_table("practice_attempts")
