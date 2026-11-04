"""GĐ1: bảng mastery của một người học mẫu qua từng lượt (cho báo cáo).

Chạy trên CSDL SQLite tạm, giờ cố định, nên chạy lại luôn ra cùng bảng.
Chạy: python scripts/ai/gd1_nguoi_mau.py   (từ thư mục gốc repo)
"""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

tmp = Path(tempfile.mkdtemp()) / "nguoi_mau.db"
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}"
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from sqlalchemy import select  # noqa: E402

from app.content import versioning  # noqa: E402
from app.content.curriculum_specs import lesson_by_id  # noqa: E402
from app.content.seed_data import seed_initial_data  # noqa: E402
from app.db.models import Exercise, MasteryEvent, ReviewItem, User  # noqa: E402
from app.db.session import SessionLocal, create_schema  # noqa: E402
from app.services import learning_service as ls  # noqa: E402
from app.services.grading_service import is_self_check  # noqa: E402

DAY0 = datetime(2026, 11, 2, 1, 0, tzinfo=timezone.utc)  # 08:00 giờ Việt Nam


def answer(spec: dict) -> str:
    key = spec["answer_key"]
    exp = key.get("expected", (key.get("accepted") or [None])[0])
    return " ".join(exp) if isinstance(exp, list) else exp


def main() -> None:
    create_schema()
    with SessionLocal() as db:
        seed_initial_data(db)
        db.add(User(id="nguoi-mau", display_name="Người mẫu"))
        db.commit()
        uid = "nguoi-mau"

        def do(lesson_id: str, exercise_id: str, now: datetime, wrong: str | None = None) -> None:
            spec = next(e for e in lesson_by_id(lesson_id)["exercises"] if e["id"] == exercise_id)
            version = versioning.current_version(db.get(Exercise, exercise_id))
            ls.submit_attempt(db, uid, version.id, wrong or answer(spec), now=now)

        # Ngày 0: học L01, câu dựng D minor gõ nhầm D F# A (thành D major) rồi sửa đúng: kết quả 0,5.
        for spec in lesson_by_id("L01")["exercises"]:
            if spec["id"] == "L01-Q04":
                do("L01", "L01-Q04", DAY0, wrong="D F# A")
            do("L01", spec["id"], DAY0 + timedelta(minutes=1))
        ls.complete_lesson(db, uid, "L01", now=DAY0 + timedelta(minutes=2))
        # Ngày 1: học L02, ôn 4 thẻ số La Mã ngay sau khi xong bài (chỉ 1 thẻ được tính).
        d1 = DAY0 + timedelta(days=1)
        for spec in lesson_by_id("L02")["exercises"]:
            do("L02", spec["id"], d1)
        ls.complete_lesson(db, uid, "L02", now=d1)
        roman = [i for i in db.scalars(select(ReviewItem).where(ReviewItem.skill_id == "roman.major_seventh",
                                                                ReviewItem.lesson_id == "L02").order_by(ReviewItem.id))
                 if not is_self_check(i.grading_strategy, i.grader_config)]
        for item in roman:
            ls.answer_review(db, uid, item.id, answer({"answer_key": item.answer_key}), "auto", None,
                             now=d1 + timedelta(minutes=5))
        # Ngày 3: thẻ hộp 2 đến hạn.
        ls.answer_review(db, uid, roman[0].id, answer({"answer_key": roman[0].answer_key}), "auto", None,
                         now=DAY0 + timedelta(days=3, minutes=5))

        print("| # | Ngày (giờ VN) | Nguồn | Kỹ năng | Kết quả | Trước | Sau | Ghi chú |")
        print("|---|---|---|---|---|---|---|---|")
        for n, ev in enumerate(db.scalars(select(MasteryEvent).where(MasteryEvent.user_id == uid)
                                          .order_by(MasteryEvent.id)), 1):
            note = "" if ev.counted else ("không cộng: đúng lặp lại" if ev.source == "attempt" else "")
            before = "chưa đánh giá" if ev.score_before is None else f"{ev.score_before:.3f}"
            result = "-" if ev.result is None else f"{ev.result:g}"
            print(f"| {n} | {ev.vn_day} | {ev.source} | {ev.skill_id} | {result} | {before} | {ev.score_after:.3f} | {note} |")
        print("\nLượt ôn không có trong bảng = không thành sự kiện mastery (ôn trước hạn, thẻ tự đánh giá,"
              " hoặc kỹ năng đã có 1 lượt ôn được tính trong ngày).")


if __name__ == "__main__":
    main()
