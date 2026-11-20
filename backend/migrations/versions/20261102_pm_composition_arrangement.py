"""composition_projects: thêm seed, energy, mix, arrangement_version cho bộ phối khí (phuc-music, ADR-012 đề xuất)

Chỉ thêm cột, có mặc định an toàn cho dự án cũ (QĐ 13A: seed 1, năng lượng 2, mix mặc định = NULL).
`arrangement_version` = 0 nghĩa là dự án lưu bằng mẫu nền cũ; giao diện báo "bản phối đã cập nhật".
Ràng buộc `ck_drum_kind` mở từ 3 mã (kick/snare/hat) ra 22 mã trống/bộ gõ ≤ 8 ký tự (QĐ 6A: không đổi kiểu cột).
Tài liệu 04 Bảng 8 không giới hạn loại trống; ràng buộc 3 mã là do Bước 4 tự đặt. Chờ Thắng duyệt schema.

Revision ID: a7c4d5e6f8b9
Revises: f6a2b3c4d5e7
Create Date: 2026-11-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7c4d5e6f8b9"
down_revision: Union[str, Sequence[str], None] = "f6a2b3c4d5e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW = ("seed", "energy", "mix", "arrangement_version")
OLD_DRUMS = ("kick", "snare", "hat")
# Giữ "hat" để dự án lưu trước 02/11 vẫn hợp lệ; trùng danh sách DRUM_CODES trong app/composition/styles.
DRUMS = ("kick", "snare", "hat", "rim", "xstick", "br_snare", "hh_c", "hh_o", "hh_p", "br_hh", "ride", "ride_b",
         "br_ride", "crash", "tom_h", "tom_m", "tom_f", "conga_h", "conga_l", "shaker", "tamb", "tri", "clap")


def _check(codes: tuple[str, ...]) -> str:
    return "drum IN (" + ", ".join(f"'{c}'" for c in codes) + ")"


def upgrade() -> None:
    with op.batch_alter_table("composition_projects") as batch:
        batch.add_column(sa.Column("seed", sa.Integer(), server_default="1", nullable=False))
        batch.add_column(sa.Column("energy", sa.Integer(), server_default="2", nullable=False))
        batch.add_column(sa.Column("mix", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("arrangement_version", sa.Integer(), server_default="0", nullable=False))
    with op.batch_alter_table("drum_events") as batch:
        batch.drop_constraint("ck_drum_kind", type_="check")
        batch.create_check_constraint("ck_drum_kind", _check(DRUMS))


def downgrade() -> None:
    # Gỡ: trống ngoài 3 mã cũ không còn hợp lệ, nên xóa các sự kiện đó trước (dự án vẫn mở được, trống phát lại theo seed).
    op.execute("DELETE FROM drum_events WHERE drum NOT IN ('kick', 'snare', 'hat')")
    with op.batch_alter_table("drum_events") as batch:
        batch.drop_constraint("ck_drum_kind", type_="check")
        batch.create_check_constraint("ck_drum_kind", _check(OLD_DRUMS))
    with op.batch_alter_table("composition_projects") as batch:
        for name in reversed(NEW):
            batch.drop_column(name)
