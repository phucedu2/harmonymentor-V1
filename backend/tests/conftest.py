"""Test chạy trên SQLite tạm riêng mỗi lần, không đụng DB dev backend/harmonymentor_dev.db.

Phải đặt biến môi trường ở đây, trước khi test nào import app (config đọc env lúc import).
Đặt DATABASE_URL tường minh (như job PostgreSQL của CI) thì giữ nguyên.
"""

import os
import tempfile
from pathlib import Path

_db = Path(tempfile.mkdtemp(prefix="hm-pytest-")) / "test.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_db.as_posix()}")
os.environ.setdefault("AUTO_CREATE_SCHEMA", "1")
