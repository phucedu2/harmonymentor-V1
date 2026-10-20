"""enable pgvector extension

Giai đoạn B (SRS 10.2): bật extension `vector` để Giai đoạn D–E thêm cột vector(384) và chỉ mục HNSW.
SQLite (dev/test) không có extension nên bỏ qua.

Revision ID: b2c4e6f80a13
Revises: 01e8306449b3
Create Date: 2026-10-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c4e6f80a13'
down_revision: Union[str, Sequence[str], None] = '01e8306449b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    available = bind.execute(sa.text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")).scalar()
    if not available:
        # Báo rõ thay vì bỏ qua: các migration về sau cần cột vector và sẽ hỏng khó hiểu hơn.
        raise RuntimeError(
            "PostgreSQL này chưa cài pgvector. Dùng image pgvector/pgvector:pg16 (docker compose) "
            "hoặc cài gói postgresql-16-pgvector."
        )
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP EXTENSION IF EXISTS vector")
