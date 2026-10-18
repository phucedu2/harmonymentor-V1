"""add item-level source provenance

Revision ID: c84d7c4b190a
Revises: 097c446166e1
Create Date: 2026-10-17

Phase 0.4B keeps the old exercise versions valid while allowing audited versions and review
items to carry the exact source locators used to verify their learning claim. Existing rows are
nullable intentionally: a legacy version without provenance must remain distinguishable from a
source-audited version rather than being silently relabeled as audited.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c84d7c4b190a"
down_revision: Union[str, Sequence[str], None] = "097c446166e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("exercise_versions", sa.Column("provenance", sa.JSON(), nullable=True))
    op.add_column("review_items", sa.Column("provenance", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("review_items", "provenance")
    op.drop_column("exercise_versions", "provenance")
