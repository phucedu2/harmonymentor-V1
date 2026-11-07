"""Pipeline AI GĐ1: ánh xạ kỹ năng, mastery, lượt is_test, bài kiểm tra đầu vào

Chỉ thêm cột và bảng (quy tắc 5.2 của nhiệm vụ). Không đổi cột cũ, không xóa dữ liệu:
- skills: srs_code, group_code (ADR-008), ready_threshold 0,6, mastery_threshold 0,8 (04 Bảng 19)
- attempts.is_test (nguyên tắc 8), mặc định false nên mọi lượt cũ là lượt thật
- review_attempts.due_before: ngày hẹn trước lượt ôn, cho luật ôn 2A và rebuild_mastery
- mastery_states, mastery_events, placement_results (bảng mới)
Hạ phiên bản: bỏ đúng các phần trên; mastery tính lại được từ lịch sử bằng `python -m app.ai.rebuild_mastery`.

Revision ID: c1a2b3d4e5f6
Revises: b8d5e6f7a9c1
Create Date: 2026-11-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1a2b3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "b8d5e6f7a9c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("skills") as batch:
        batch.add_column(sa.Column("srs_code", sa.String(length=40), nullable=True))
        batch.add_column(sa.Column("group_code", sa.String(length=40), nullable=True))
        batch.add_column(sa.Column("ready_threshold", sa.Float(), server_default="0.6", nullable=False))
        batch.add_column(sa.Column("mastery_threshold", sa.Float(), server_default="0.8", nullable=False))
    op.create_index(op.f("ix_skills_group_code"), "skills", ["group_code"], unique=False)

    with op.batch_alter_table("attempts") as batch:
        batch.add_column(sa.Column("is_test", sa.Boolean(), server_default=sa.false(), nullable=False))
    with op.batch_alter_table("review_attempts") as batch:
        batch.add_column(sa.Column("due_before", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "mastery_states",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("skill_id", sa.String(length=120), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("attempts_count", sa.Integer(), nullable=False),
        sa.Column("last_error_code", sa.String(length=100), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "skill_id", name="uq_mastery_user_skill"),
    )
    op.create_index(op.f("ix_mastery_states_user_id"), "mastery_states", ["user_id"], unique=False)
    op.create_index(op.f("ix_mastery_states_skill_id"), "mastery_states", ["skill_id"], unique=False)

    op.create_table(
        "mastery_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("skill_id", sa.String(length=120), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("result", sa.Float(), nullable=True),
        sa.Column("counted", sa.Boolean(), nullable=False),
        sa.Column("score_before", sa.Float(), nullable=True),
        sa.Column("score_after", sa.Float(), nullable=False),
        sa.Column("vn_day", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("source IN ('attempt', 'review', 'placement')", name="ck_mastery_event_source"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for col in ("user_id", "skill_id", "vn_day", "created_at"):
        op.create_index(op.f(f"ix_mastery_events_{col}"), "mastery_events", [col], unique=False)

    op.create_table(
        "placement_results",
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("taken_count", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('completed', 'skipped')", name="ck_placement_status"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("placement_results")
    for col in ("created_at", "vn_day", "skill_id", "user_id"):
        op.drop_index(op.f(f"ix_mastery_events_{col}"), table_name="mastery_events")
    op.drop_table("mastery_events")
    op.drop_index(op.f("ix_mastery_states_skill_id"), table_name="mastery_states")
    op.drop_index(op.f("ix_mastery_states_user_id"), table_name="mastery_states")
    op.drop_table("mastery_states")
    with op.batch_alter_table("review_attempts") as batch:
        batch.drop_column("due_before")
    with op.batch_alter_table("attempts") as batch:
        batch.drop_column("is_test")
    op.drop_index(op.f("ix_skills_group_code"), table_name="skills")
    with op.batch_alter_table("skills") as batch:
        batch.drop_column("mastery_threshold")
        batch.drop_column("ready_threshold")
        batch.drop_column("group_code")
        batch.drop_column("srs_code")
