"""Tạo hoặc nâng quyền tài khoản Quản trị viên.

    python -m app.seed_admin --email admin@example.com
Mật khẩu lấy từ biến ADMIN_PASSWORD hoặc hỏi trực tiếp, không nhận qua tham số dòng lệnh
(tránh lưu vào lịch sử shell) và không bao giờ in ra.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
import uuid

from sqlalchemy import select

from .auth.security import hash_password, password_problem
from .auth.service import EMAIL_RE, normalize_email
from .db.models import User
from .db.session import SessionLocal


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tạo hoặc nâng quyền admin.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="Quản trị viên")
    args = parser.parse_args(argv)

    email = normalize_email(args.email)
    if not EMAIL_RE.match(email):
        print("Email chưa đúng định dạng.", file=sys.stderr)
        return 2
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        password = os.getenv("ADMIN_PASSWORD")
        if user is None or password:
            password = password or getpass.getpass("Mật khẩu admin: ")
            problem = password_problem(password)
            if problem:
                print(problem, file=sys.stderr)
                return 2
        if user is None:
            user = User(id=str(uuid.uuid4()), email=email, display_name=args.name)
            db.add(user)
        if password:
            user.hashed_password = hash_password(password)
        user.role = "admin"
        user.is_active = True
        db.commit()
        print(f"Đã đặt quyền admin cho {email}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
