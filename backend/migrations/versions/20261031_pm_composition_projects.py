"""composition_projects, chord_events, drum_events: dự án Harmony Lab (phuc-music Bước 4, FR-17)

Chỉ thêm bảng mới theo tài liệu 04 Bảng 8, không sửa bảng hay migration cũ. note_events và ai_suggestions
chưa tạo vì Bước 4 chưa có giai điệu và gợi ý chưa lưu (ADR-010, chờ Thắng duyệt schema).

Revision ID: f6a2b3c4d5e7
Revises: e5f1a2b3c4d6
Create Date: 2026-10-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a2b3c4d5e7"
down_revision: Union[str, Sequence[str], None] = "e5f1a2b3c4d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "composition_projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("key", sa.String(length=8), nullable=False),
        sa.Column("tempo_bpm", sa.Integer(), nullable=False),
        sa.Column("time_signature", sa.String(length=8), server_default="4/4", nullable=False),
        sa.Column("bars", sa.Integer(), nullable=False),
        sa.Column("style", sa.String(length=16), nullable=False),
        sa.Column("is_test", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("tempo_bpm BETWEEN 60 AND 160", name="ck_composition_tempo"),
        sa.CheckConstraint("bars BETWEEN 4 AND 8", name="ck_composition_bars"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_composition_projects_user_id"), "composition_projects", ["user_id"], unique=False)
    op.create_table(
        "chord_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("start_beat", sa.Float(), nullable=False),
        sa.Column("duration_beats", sa.Float(), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["composition_projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chord_events_project_id"), "chord_events", ["project_id"], unique=False)
    op.create_table(
        "drum_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("drum", sa.String(length=8), nullable=False),
        sa.Column("start_beat", sa.Float(), nullable=False),
        sa.Column("velocity", sa.Integer(), nullable=False),
        sa.CheckConstraint("drum IN ('kick', 'snare', 'hat')", name="ck_drum_kind"),
        sa.ForeignKeyConstraint(["project_id"], ["composition_projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_drum_events_project_id"), "drum_events", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_drum_events_project_id"), table_name="drum_events")
    op.drop_table("drum_events")
    op.drop_index(op.f("ix_chord_events_project_id"), table_name="chord_events")
    op.drop_table("chord_events")
    op.drop_index(op.f("ix_composition_projects_user_id"), table_name="composition_projects")
    op.drop_table("composition_projects")
