"""Quên/đổi mật khẩu, xác minh email, "Ghi nhớ đăng nhập" (ADR-040)

- users.password_changed_at, users.email_verified_at. Tài khoản có email trước migration được coi là đã xác minh
  (mức "mềm", không ai bị chặn học), nên điền email_verified_at = thời điểm chạy migration.
- refresh_tokens.remember (mặc định true: phiên cũ giữ hành vi cookie lâu dài) và session_started_at = created_at.
- Hai bảng token dùng một lần: password_reset_tokens, email_verification_tokens (chỉ lưu SHA-256).
Hạ phiên bản: bỏ hai bảng và bốn cột.

Revision ID: c3d4e5f6a7b9
Revises: b2c3d4e5f6a8
Create Date: 2026-11-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b9"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _token_table(name: str) -> None:
    op.create_table(
        name,
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requested_ip", sa.String(64), nullable=True),
    )
    op.create_index(f"ix_{name}_user_id", name, ["user_id"])
    op.create_index(f"ix_{name}_token_hash", name, ["token_hash"], unique=True)


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE users SET email_verified_at = CURRENT_TIMESTAMP WHERE email IS NOT NULL")
    with op.batch_alter_table("refresh_tokens") as batch:
        batch.add_column(sa.Column("remember", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch.add_column(sa.Column("session_started_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE refresh_tokens SET session_started_at = created_at")
    _token_table("password_reset_tokens")
    _token_table("email_verification_tokens")


def downgrade() -> None:
    for name in ("email_verification_tokens", "password_reset_tokens"):
        op.drop_index(f"ix_{name}_token_hash", table_name=name)
        op.drop_index(f"ix_{name}_user_id", table_name=name)
        op.drop_table(name)
    with op.batch_alter_table("refresh_tokens") as batch:
        batch.drop_column("session_started_at")
        batch.drop_column("remember")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("email_verified_at")
        batch.drop_column("password_changed_at")
