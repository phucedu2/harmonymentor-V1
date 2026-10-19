"""add auth columns and refresh tokens

Giai đoạn B (ADR-001, ADR-004): cột xác thực cho users và bảng refresh_tokens. Chỉ cộng thêm;
người dùng cũ (demo-user) giữ nguyên, email để trống.

Revision ID: 01e8306449b3
Revises: c84d7c4b190a
Create Date: 2026-10-19 03:51:07.225866
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '01e8306449b3'
down_revision: Union[str, Sequence[str], None] = 'c84d7c4b190a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('refresh_tokens',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=64), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)
    op.add_column('users', sa.Column('email', sa.String(length=320), nullable=True))
    op.add_column('users', sa.Column('hashed_password', sa.String(length=128), nullable=True))
    op.add_column('users', sa.Column('role', sa.String(length=16), server_default='learner', nullable=False))
    op.add_column('users', sa.Column('preferred_instrument', sa.String(length=16), nullable=True))
    op.add_column('users', sa.Column('goal_text', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False))
    op.add_column('users', sa.Column('is_synthetic', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_column('users', 'is_synthetic')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'goal_text')
    op.drop_column('users', 'preferred_instrument')
    op.drop_column('users', 'role')
    op.drop_column('users', 'hashed_password')
    op.drop_column('users', 'email')
    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
