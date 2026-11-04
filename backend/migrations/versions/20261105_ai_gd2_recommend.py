"""Pipeline AI GĐ2: vector mục tiêu và nhật ký gợi ý

Chỉ thêm (quy tắc 5.2):
- users.goal_embedding (JSON), users.goal_embedding_model: 04 ERD ghi vector(384) cho MiniLM; Gemini 768 chiều
  và có thể đổi mô hình (Q-B chờ Thắng), nên lưu JSON kèm tên mô hình thay vì cột pgvector cố định số chiều.
- recommendation_logs theo 04 ERD, thêm context và clicked_at.
Hạ phiên bản: bỏ đúng các phần trên. Vector mục tiêu tính lại được từ goal_text.

Revision ID: d2b3c4d5e6f7
Revises: c1a2b3d4e5f6
Create Date: 2026-11-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "c1a2b3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("goal_embedding", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("goal_embedding_model", sa.String(length=80), nullable=True))

    op.create_table(
        "recommendation_logs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("lesson_ids", sa.JSON(), nullable=False),
        sa.Column("scores", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("clicked_lesson_id", sa.String(length=32), nullable=True),
        sa.Column("clicked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recommendation_logs_user_id"), "recommendation_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_recommendation_logs_created_at"), "recommendation_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_recommendation_logs_created_at"), table_name="recommendation_logs")
    op.drop_index(op.f("ix_recommendation_logs_user_id"), table_name="recommendation_logs")
    op.drop_table("recommendation_logs")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("goal_embedding_model")
        batch.drop_column("goal_embedding")
