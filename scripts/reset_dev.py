"""Đưa môi trường dev trên máy về khớp code hiện tại. Chạy sau mỗi lần git pull.

Cách dùng (từ thư mục gốc repo, tắt uvicorn trước):
    python scripts/reset_dev.py           # cài lại phụ thuộc, migrate DB, giữ dữ liệu nếu DB còn dùng được
    python scripts/reset_dev.py --fresh   # sao lưu DB dev rồi tạo mới hoàn toàn

DB dev do create_all tạo (không có bảng alembic_version) thì Alembic không nâng cấp được và nội dung
bài học kẹt ở bản cũ: script tự sao lưu thành harmonymentor_dev.db.bak-<thời điểm> rồi tạo lại.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import subprocess
import sys
from contextlib import closing
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
DEV_DB = BACKEND / "harmonymentor_dev.db"


def needs_rebuild(db: Path) -> bool:
    """True khi DB có sẵn nhưng không do Alembic quản lý (thiếu bảng alembic_version)."""
    if not db.exists():
        return False
    with closing(sqlite3.connect(db)) as conn:
        row = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='alembic_version'").fetchone()
    return row is None


def run(cmd: list[str], cwd: Path) -> None:
    print(f"\n$ {' '.join(cmd)}   (trong {cwd.name}/)", flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Đưa môi trường dev về khớp code hiện tại.")
    parser.add_argument("--fresh", action="store_true", help="luôn sao lưu DB dev rồi tạo mới")
    args = parser.parse_args(argv)

    if os.environ.get("DATABASE_URL"):
        print("DATABASE_URL đã đặt: chỉ chạy migration, không sao lưu hay tạo lại DB.")
    elif DEV_DB.exists() and (args.fresh or needs_rebuild(DEV_DB)):
        backup = DEV_DB.with_name(f"{DEV_DB.name}.bak-{datetime.now():%Y%m%d-%H%M%S}")
        try:
            DEV_DB.rename(backup)
        except PermissionError:
            sys.exit("DB dev đang bị khóa: tắt uvicorn rồi chạy lại.")
        print(f"Đã sao lưu DB cũ thành backend/{backup.name}")

    run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"], BACKEND)
    run([sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"], BACKEND)
    npm = shutil.which("npm") or sys.exit("Không tìm thấy npm (cần Node.js 18+).")
    run([npm, "ci"], FRONTEND)
    print("\nXong. Backend: cd backend && uvicorn app.main:app --reload   Frontend: cd frontend && npm run dev")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(f"Lệnh lỗi (mã {exc.returncode}): {' '.join(exc.cmd)}")
