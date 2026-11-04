"""GĐ0: đếm câu/thẻ đã xuất bản theo kỹ năng và mô phỏng ngày mở khóa L01–L04.

Vì sao có script này: với EMA 0,3 và luật "đúng lặp lại cùng câu không cộng", số câu khác nhau
của một kỹ năng quyết định mastery tối đa. Script đọc thẳng nội dung thật (curriculum_specs,
skill_graph), không đọc CSDL, nên chạy lại luôn ra cùng số.

Người học mô phỏng ở đây là người "lý tưởng": làm đúng mọi câu ngay lần đầu, ôn mọi thẻ đến hạn mỗi
ngày, học bài kế ngay khi tiên quyết đủ 0,60. Người thật chỉ chậm hơn, nên đây là cận dưới số ngày.

Chạy: python scripts/ai/gd0_mo_phong_mo_khoa.py   (từ thư mục gốc repo)
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.content import curriculum_specs as cs  # noqa: E402
from app.content import skill_graph as g  # noqa: E402
from app.services.grading_service import is_self_check  # noqa: E402

ALPHA, READY, MASTER = 0.3, 0.60, 0.80
LEITNER = [1, 2, 4, 8, 16]  # 04 mục 6.4
LESSONS = ["L01", "L02", "L03", "L04"]
POST_MVP = {"voicing.guide_tones", "voicing.voice_leading"}  # C7: chấm nhưng không cộng mastery
DAYS = 90


def ema(old: float, result: float) -> float:
    return old + ALPHA * (result - old)


def published_counts():
    ex, rv_auto, rv_self = defaultdict(list), defaultdict(list), defaultdict(list)
    for e in cs.all_exercises():
        if e["status"] == "published" and not e["retired"] and e["id"][:3] in LESSONS:
            ex[e["skill"]].append(e["id"])
    for r in cs.all_review_items():
        if r["id"][:3] in LESSONS:
            bucket = rv_self if is_self_check(r["strategy"], r["grader_config"]) else rv_auto
            bucket[r["skill"]].append((r["id"][:3], r["id"]))
    return ex, rv_auto, rv_self


def lesson_prereqs(lesson: str) -> set[str]:
    own = set(g.LESSON_SKILLS[lesson])
    # PREREQUISITES là (kỹ năng, kỹ năng tiên quyết của nó).
    req = {pre for skill, pre in g.PREREQUISITES if skill in own}
    return req - own


def simulate(count_auto_reviews: bool, count_self_reviews: bool, one_event_per_skill_per_day: bool,
             follow_prereq: bool = True):
    """follow_prereq=False: người học tự mở bài theo thứ tự, mỗi ngày một bài (tầng 1 chỉ gợi ý,
    không khóa quyền mở bài). Khi đó kết quả là ngày bài trở thành "đủ điều kiện" cho hệ gợi ý."""
    ex, rv_auto, rv_self = published_counts()
    mastery: dict[str, float] = {}
    cards: dict[str, dict] = {}  # id -> {skill, box, due, self}
    unlocked_day: dict[str, int | None] = {l: None for l in LESSONS}
    done: set[str] = set()
    for day in range(DAYS):
        # Học mọi bài đã đủ tiên quyết (người lý tưởng học ngay).
        progressed = True
        while progressed:
            progressed = False
            for lesson in LESSONS:
                if lesson in done:
                    continue
                eligible = all(mastery.get(s, 0.0) >= READY for s in lesson_prereqs(lesson))
                if eligible and unlocked_day[lesson] is None:
                    unlocked_day[lesson] = day
                if (eligible if follow_prereq else LESSONS.index(lesson) <= day):
                    for skill in g.LESSON_SKILLS[lesson]:
                        if skill in POST_MVP:
                            continue
                        for _ in ex.get(skill, []):  # mỗi câu khác nhau đúng lần đầu = 1
                            mastery[skill] = ema(mastery.get(skill, 0.0), 1.0)
                    for src, is_self in ((rv_auto, False), (rv_self, True)):
                        for skill, items in src.items():
                            for les, cid in items:
                                if les == lesson:
                                    cards[cid] = {"skill": skill, "box": 0, "due": day, "self": is_self}
                    done.add(lesson)
                    progressed = True
                    break
        if not follow_prereq:
            for lesson in LESSONS:
                if unlocked_day[lesson] is None and all(mastery.get(x, 0.0) >= READY for x in lesson_prereqs(lesson)):
                    unlocked_day[lesson] = day
        # Ôn mọi thẻ đến hạn hôm nay. Thẻ máy chấm xét trước thẻ tự đánh giá.
        counted_today: set[str] = set()
        for cid, c in sorted(cards.items(), key=lambda kv: kv[1]["self"]):
            if c["due"] > day:
                continue
            skill = c["skill"]
            allowed = count_self_reviews if c["self"] else count_auto_reviews
            if allowed and skill not in POST_MVP and not (one_event_per_skill_per_day and skill in counted_today):
                mastery[skill] = ema(mastery.get(skill, 0.0), 0.5 if c["self"] else 1.0)
                counted_today.add(skill)
            c["box"] = min(c["box"] + 1, 4)
            c["due"] = day + LEITNER[c["box"]]
        # Kiểm lại sau buổi ôn: đạt 0,60 trong ngày thì bài đủ điều kiện ngay ngày đó.
        for lesson in LESSONS:
            if unlocked_day[lesson] is None and all(mastery.get(x, 0.0) >= READY for x in lesson_prereqs(lesson)):
                unlocked_day[lesson] = day
    return unlocked_day, mastery


def main() -> None:
    ex, rv_auto, rv_self = published_counts()
    print("## Câu và thẻ đã xuất bản theo kỹ năng (L01–L04)\n")
    print("| Kỹ năng | Bài | Câu | Thẻ máy chấm | Thẻ tự đánh giá | Mastery tối đa chỉ bằng câu | Là tiên quyết của |")
    print("|---|---|---|---|---|---|---|")
    users = defaultdict(list)
    for lesson in LESSONS:
        for s in lesson_prereqs(lesson):
            users[s].append(lesson)
    for lesson in LESSONS:
        for s in g.LESSON_SKILLS[lesson]:
            n = len(ex.get(s, []))
            cap = "post_mvp" if s in POST_MVP else f"{1 - (1 - ALPHA) ** n:.3f}"
            print(f"| {s} | {lesson} | {n} | {len(rv_auto.get(s, []))} | {len(rv_self.get(s, []))} | {cap} | {', '.join(users.get(s, [])) or '-'} |")
    scenarios = [
        ("Chỉ câu bài tập (hiện trạng)", False, False, True),
        ("2A: + thẻ máy chấm đến hạn, tối đa 1 lượt/kỹ năng/ngày", True, False, True),
        ("2A + 1A: + thẻ tự đánh giá đến hạn tính 0,5", True, True, True),
        ("2A không giới hạn mỗi ngày (để so sánh)", True, False, False),
    ]
    for title, follow in (("A. Người học chỉ mở bài khi hệ gợi ý coi là đủ điều kiện", True),
                          ("B. Người học tự mở bài theo thứ tự, mỗi ngày một bài (bài vẫn mở được, tầng 1 chỉ gợi ý)", False)):
        table(title, scenarios, follow)


def table(title, scenarios, follow) -> None:
    print(f"\n## {title}\n")
    print("Ô là ngày đầu tiên mọi kỹ năng tiên quyết của bài đạt 0,60 (ngày 0 = ngày bắt đầu).\n")
    print("| Kịch bản | L01 | L02 | L03 | L04 | pitch.spelling | chord.seventh_quality | roman.major_seventh |")
    print("|---|---|---|---|---|---|---|---|")
    for name, a, s, one in scenarios:
        days, m = simulate(a, s, one, follow)
        cell = lambda l: "không mở" if days[l] is None else f"ngày {days[l]}"
        print(f"| {name} | " + " | ".join(cell(l) for l in LESSONS)
              + f" | {m.get('pitch.spelling', 0):.3f} | {m.get('chord.seventh_quality', 0):.3f} | {m.get('roman.major_seventh', 0):.3f} |")
    print(f"\n(Mô phỏng {DAYS} ngày; cột kỹ năng là mastery cuối kỳ mô phỏng.)")


if __name__ == "__main__":
    main()
