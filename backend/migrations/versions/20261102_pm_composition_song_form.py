"""composition_projects: thêm cột JSON `form` cho chế độ Bài hát (phuc-music, ADR-013 đề xuất)

Chỉ thêm một cột cho phép NULL (QĐ 9A). NULL = dự án vòng lặp (mọi dự án cũ) → mở ở chế độ Vòng lặp như cũ.
`form` giữ: danh sách đoạn, vòng B/C (vòng A vẫn nằm ở chord_events + bars như cũ, QĐ 1A), cờ hook, lên giọng, kết bài.
Không đổi cột hay ràng buộc nào khác. Chờ Thắng duyệt schema.

Revision ID: b8d5e6f7a9c1
Revises: a7c4d5e6f8b9
Create Date: 2026-11-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8d5e6f7a9c1"
down_revision: Union[str, Sequence[str], None] = "a7c4d5e6f8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("composition_projects") as batch:
        batch.add_column(sa.Column("form", sa.JSON(), nullable=True))


def downgrade() -> None:
    # Hạ phiên bản: dự án bài hát mất cấu trúc đoạn và vòng B/C, còn lại vòng A ở chế độ Vòng lặp.
    with op.batch_alter_table("composition_projects") as batch:
        batch.drop_column("form")
