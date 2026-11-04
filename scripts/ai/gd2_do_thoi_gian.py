"""Đo thời gian gợi ý cho một người khi có N người mô phỏng làm ứng viên láng giềng (E11, ADR-008 mục 5).

    cd backend && python ../scripts/ai/gd2_do_thoi_gian.py --n 2000 --lan 50

Chạy trên CSDL SQLite tạm, không đụng CSDL dev. Người mô phỏng ở đây có is_synthetic=true và điểm ngẫu nhiên,
chỉ để đo thời gian; bộ sinh hành vi thật (độc lập với bộ gợi ý) là việc của GĐ4.
"""

from __future__ import annotations

import argparse
import os
import random
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(ROOT))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--lan", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20261105)
    args = ap.parse_args()

    tmp = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/do.db"
    os.environ["AI_ENABLED"] = "0"
    from fastapi.testclient import TestClient

    from app.ai.skill_mapping import is_mvp
    from app.content.skill_graph import SKILLS
    from app.db.models import MasteryState, User
    from app.db.session import SessionLocal
    from app.main import app
    from app.services import recommendation_service as rs

    rng = random.Random(args.seed)
    mvp = [s for s, _, _ in SKILLS if is_mvp(s)]
    with TestClient(app):
        with SessionLocal() as db:
            for i in range(args.n):
                uid = f"syn-{i:05d}"
                db.add(User(id=uid, display_name="mô phỏng", is_synthetic=True))
                for s in rng.sample(mvp, rng.randint(3, len(mvp))):
                    db.add(MasteryState(user_id=uid, skill_id=s, score=round(rng.random(), 3), attempts_count=3))
            db.add(User(id="nguoi-do", display_name="đo"))
            for s in mvp[:6]:
                db.add(MasteryState(user_id="nguoi-do", skill_id=s, score=0.7, attempts_count=3))
            db.commit()
            user = db.get(User, "nguoi-do")
            times = []
            for _ in range(args.lan):
                t = time.perf_counter()
                out = rs.recommend_for_user(db, user)
                times.append((time.perf_counter() - t) * 1000)
    times.sort()
    p95 = times[max(0, int(round(0.95 * len(times))) - 1)]
    print(f"N={args.n} ứng viên, {args.lan} lần, seed {args.seed}: trung vị {statistics.median(times):.1f} ms, "
          f"p95 {p95:.1f} ms, lớn nhất {times[-1]:.1f} ms; cf_source={out['cf_source']}, "
          f"neighbors={out['neighbors_count']}, next={[x['lesson_id'] for x in out['next']]}")


if __name__ == "__main__":
    main()
