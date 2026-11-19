"""Nguồn dữ liệu cho model: người học mô phỏng (mặc định) hoặc lịch sử thật xuất từ CSDL.

Không có email, tên hay user_id thật trong file xuất: user được thay bằng mã băm (nguyên tắc 12 mở rộng cho dữ liệu train).
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def sim_events(n_users: int, seed: int, with_true_p: bool = False) -> dict[str, list[dict]]:
    """Sinh người học mô phỏng bằng scripts/ai/sim/nguoi_mo_phong.py (cần chạy từ repo, không có trong image Docker).

    with_true_p: ghi thêm "p_true" = xác suất đúng mà bộ mô phỏng đã dùng để tung kết quả. Chỉ để đo TRẦN lý thuyết
    (không model nào đoán tốt hơn người biết p_true), tuyệt đối không dùng làm đặc trưng.
    """
    sim_dir = ROOT / "scripts" / "ai"
    if not (sim_dir / "sim" / "nguoi_mo_phong.py").exists():
        raise SystemExit("Không thấy scripts/ai/sim: chạy lệnh train từ repo (không phải trong container), hoặc dùng --data.")
    if str(sim_dir) not in sys.path:
        sys.path.insert(0, str(sim_dir))
    from sim import nguoi_mo_phong as sim

    recorded: list[float] = []
    original = sim._p
    if with_true_p:
        # Bọc hàm _p: mỗi lần gọi đúng một lượt làm/ôn được ghi ngay sau đó, nên thứ tự khớp 1-1 với sự kiện.
        # Gọi lại hàm gốc nên dãy số ngẫu nhiên và dữ liệu sinh ra không đổi.
        def _record(theta, rng):
            value = original(theta, rng)
            recorded.append(value)
            return value
        sim._p = _record
    try:
        users = sim.generate(n_users, seed)
    finally:
        sim._p = original
    out: dict[str, list[dict]] = {}
    i = 0
    for u in users:
        rows = []
        for e in u.events:
            if e.kind not in ("attempt", "review"):
                continue
            row = {"user": u.uid, "t": e.t, "kind": e.kind, "skill": e.skill, "exercise": e.exercise,
                   "correct": bool(e.correct)}
            if with_true_p:
                row["p_true"] = recorded[i]
                i += 1
            rows.append(row)
        out[u.uid] = rows
    if with_true_p and i != len(recorded):
        raise RuntimeError("Số lần tung kết quả không khớp số lượt: bộ mô phỏng đã đổi cách sinh, cần sửa dataset.py.")
    return out


def read_jsonl(path: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            ev = json.loads(line)
            out[ev["user"]].append(ev)
    return dict(out)


def _epoch(value: datetime) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return int(value.timestamp())


def db_events(db, user_ids: list[str] | None = None) -> dict[str, list[dict]]:
    """Lịch sử thật: lượt làm bài (bỏ is_test) và lượt ôn, của người học không phải mô phỏng.

    Lượt ôn chỉ "counts" khi có due_before và không ôn trước hạn, giống luật 2A của mastery_service.
    """
    from sqlalchemy import select

    from ...db.models import Attempt, Exercise, ExerciseVersion, ReviewAttempt, ReviewItem, ReviewState, User

    users = select(User.id).where(User.is_synthetic.is_(False))
    if user_ids is not None:
        users = users.where(User.id.in_(user_ids))
    ids = set(db.scalars(users))
    out: dict[str, list[dict]] = defaultdict(list)
    rows = db.execute(
        select(Attempt.user_id, Attempt.created_at, Attempt.correct, ExerciseVersion.exercise_id, Exercise.skill_id)
        .join(ExerciseVersion, ExerciseVersion.id == Attempt.exercise_version_id)
        .join(Exercise, Exercise.id == ExerciseVersion.exercise_id)
        .where(Attempt.is_test.is_(False), Attempt.user_id.in_(ids))
        .order_by(Attempt.created_at, Attempt.id))
    for uid, at, ok, ex, skill in rows:
        out[uid].append({"user": uid, "t": _epoch(at), "kind": "attempt", "skill": skill, "exercise": ex,
                         "correct": bool(ok)})
    rows = db.execute(
        select(ReviewState.user_id, ReviewAttempt.created_at, ReviewAttempt.correct, ReviewAttempt.due_before,
               ReviewItem.skill_id)
        .join(ReviewState, ReviewState.id == ReviewAttempt.review_state_id)
        .join(ReviewItem, ReviewItem.id == ReviewState.review_item_id)
        .where(ReviewState.user_id.in_(ids))
        .order_by(ReviewAttempt.created_at, ReviewAttempt.id))
    for uid, at, ok, due, skill in rows:
        counts = due is not None and _epoch(due) <= _epoch(at)
        out[uid].append({"user": uid, "t": _epoch(at), "kind": "review", "skill": skill, "exercise": None,
                         "correct": bool(ok), "counts": counts})
    return dict(out)


def pseudonym(user_id: str) -> str:
    return "u-" + hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]


def export_main() -> None:
    """python -m app.ml.correctness.dataset --out ../data/correctness/that.jsonl  (chạy trên máy có CSDL thật)."""
    import argparse

    from ...db.session import SessionLocal

    ap = argparse.ArgumentParser(description=export_main.__doc__)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    with SessionLocal() as db:
        data = db_events(db)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for uid, events in sorted(data.items()):
            alias = pseudonym(uid)
            for ev in sorted(events, key=lambda e: e["t"]):
                f.write(json.dumps({**ev, "user": alias}, ensure_ascii=False) + "\n")
                n += 1
    print(f"Đã xuất {n} lượt của {len(data)} người học thật (đã thay mã) vào {path}")


if __name__ == "__main__":
    export_main()
