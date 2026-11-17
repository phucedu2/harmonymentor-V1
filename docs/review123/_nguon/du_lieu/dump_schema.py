"""Đọc SQLAlchemy models (backend/app/db/models.py) ra schema.json để Table Design, ERD và sơ đồ quan hệ
luôn khớp code. Không đọc CSDL thật, nên chạy được trên máy không có PostgreSQL.

Chạy từ thư mục gốc repo:  python docs/review123/_nguon/du_lieu/dump_schema.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import CheckConstraint, UniqueConstraint  # noqa: E402
from sqlalchemy.dialects import postgresql  # noqa: E402

from app.db import models  # noqa: E402,F401  (nạp mọi bảng vào metadata)
from app.db.base import Base  # noqa: E402


def _default(col):
    if col.default is None:
        return None
    arg = col.default.arg
    if callable(arg):
        name = getattr(getattr(arg, "__wrapped__", arg), "__name__", "")
        if "utcnow" in name or "utcnow" in repr(arg):
            return "utcnow()"
        # SQLAlchemy bọc hàm mặc định; list/dict nghĩa là JSON rỗng [] / {}
        return {"list": "[]", "dict": "{}"}.get(name, f"{name}()")
    return repr(arg)


def _server_default(col):
    if col.server_default is None:
        return None
    arg = col.server_default.arg
    return str(getattr(arg, "text", arg))


def main() -> None:
    tables = []
    order = [cls.__tablename__ for cls in Base.registry._class_registry.values() if hasattr(cls, "__tablename__")]
    by_name = {t.name: t for t in Base.metadata.sorted_tables}
    # Giữ đúng thứ tự khai báo trong models.py để người đọc dò lại dễ.
    declared = [n for n in order if n in by_name]
    for name in declared:
        t = by_name[name]
        cols = []
        for c in t.columns:
            cols.append({
                "name": c.name,
                "type": str(c.type.compile(dialect=postgresql.dialect())),
                "pk": c.primary_key,
                "nullable": c.nullable,
                "unique": bool(c.unique),
                "index": bool(c.index),
                "fk": [[f.target_fullname, f.ondelete] for f in c.foreign_keys],
                "default": _default(c),
                "server_default": _server_default(c),
                "onupdate": "utcnow()" if c.onupdate is not None else None,
            })
        tables.append({
            "name": name,
            "columns": cols,
            "uniques": [{"name": u.name, "columns": [x.name for x in u.columns]}
                        for u in t.constraints if isinstance(u, UniqueConstraint) and len(u.columns) > 1],
            "checks": [{"name": c.name, "sql": str(c.sqltext)} for c in t.constraints if isinstance(c, CheckConstraint)],
        })
    out = Path(__file__).with_name("schema.json")
    out.write_text(json.dumps(tables, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(tables)} bảng -> {out}")


if __name__ == "__main__":
    main()
