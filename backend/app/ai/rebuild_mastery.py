"""Tính lại toàn bộ mastery từ lịch sử: `python -m app.ai.rebuild_mastery [--user ID]`.

Dùng để nạp dữ liệu cũ sau migration GĐ1 và để kiểm chứng: chạy hai lần phải ra cùng kết quả.
Lượt ôn trước GĐ1 không có `due_before` nên không được tính (không đoán ngày hẹn cũ).
"""

from __future__ import annotations

import argparse
import hashlib
import json

from sqlalchemy import select

from ..db.models import User
from ..db.session import SessionLocal
from ..services.mastery_service import rebuild_user


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", help="chỉ tính lại một người")
    args = parser.parse_args()
    with SessionLocal() as db:
        ids = [args.user] if args.user else list(db.scalars(select(User.id).order_by(User.id)))
        result = {uid: rebuild_user(db, uid) for uid in ids}
        db.commit()
    digest = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()[:16]
    rows = sum(len(v) for v in result.values())
    print(f"Đã tính lại {len(ids)} người, {rows} dòng mastery. Dấu kiểm: {digest}")


if __name__ == "__main__":
    main()
