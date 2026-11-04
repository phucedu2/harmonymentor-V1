"""Bộ sinh người học mô phỏng cho đánh giá offline (đề GĐ4, 04 mục 8.4).

ĐỘC LẬP với bộ gợi ý: module này chỉ đọc nội dung chương trình (câu hỏi đã phát hành của từng bài, đồ thị
tiên quyết) và KHÔNG import app.ai.recommender hay recommendation_service. Hành vi chọn bài do chân dung
quyết định, không do điểm gợi ý, để tránh việc bộ gợi ý "chấm bài của chính nó".

Mô hình (đơn giản, có chủ đích):
- Mỗi người có năng lực ẩn θ_s ∈ [0, 1] cho từng kỹ năng; mỗi lượt luyện θ tăng theo tốc độ học của chân dung.
- P(đúng) = 0,15 + 0,8·θ_s + nhiễu N(0; 0,08), cắt trong [0,02; 0,98].
- Mỗi ngày học: ôn các thẻ đến hạn (Leitner 5 hộp: 1, 2, 4, 8, 16 ngày), rồi học tiếp bài đang dở, hoặc bắt đầu
  bài mới. Bắt đầu bài mới: khoảng 80% theo tiên quyết (bài nhỏ nhất mà kỹ năng tiên quyết đã vững theo θ),
  khoảng 20% chọn bừa theo sở thích chân dung (không theo tiên quyết).
- Bài xong khi mọi câu đã đúng ít nhất một lần; mỗi câu thử tối đa 3 lần mỗi ngày, mỗi buổi 2–6 lượt.
Seed cố định → cùng dữ liệu mỗi lần chạy.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

DAY = 86_400
LEITNER_DAYS = (1, 2, 4, 8, 16)
LEARNABLE = {"reviewed", "published"}


@dataclass(frozen=True)
class Persona:
    name: str
    goal: str
    base: float                # năng lực khởi đầu trung bình
    lr: float                  # tốc độ học mỗi lượt
    interest: dict[str, float]  # trọng số chọn bài khi không theo tiên quyết
    days: tuple[int, int]      # số ngày học (min, max)
    p_skip_day: float          # xác suất bỏ một ngày


PERSONAS = [
    Persona("Pop", "Mình muốn đệm hát nhạc pop", 0.30, 0.10,
            {"L01": 3, "L02": 2, "L03": 3, "L04": 1}, (12, 30), 0.25),
    Persona("Guitar", "Đệm guitar cho các bài hát mình thích", 0.35, 0.09,
            {"L01": 3, "L02": 1, "L03": 3, "L04": 1}, (12, 30), 0.30),
    Persona("Jazz", "Tôi muốn chơi piano jazz và hiểu vòng ii-V-I", 0.40, 0.11,
            {"L01": 1, "L02": 3, "L03": 1, "L04": 4}, (14, 32), 0.20),
    Persona("Newbie", "Mình mới bắt đầu, chưa biết gì về nhạc lý", 0.10, 0.07,
            {"L01": 4, "L02": 1, "L03": 1, "L04": 1}, (8, 24), 0.40),
]


@dataclass
class Curriculum:
    lessons: list[str]                      # theo thứ tự chương trình
    exercises: dict[str, list[tuple[str, str]]]  # lesson → [(exercise_id, skill)]
    prereqs: dict[str, set[str]]            # skill → tiên quyết


def load_curriculum() -> Curriculum:
    from app.content.curriculum_specs import LESSON_SPECS
    from app.content.skill_graph import PREREQUISITES

    lessons, exercises = [], {}
    for spec in sorted(LESSON_SPECS, key=lambda s: s["order"]):
        rows = [(e["id"], e["skill"]) for e in spec.get("exercises", [])
                if e.get("status", "published") == "published" and not e.get("retired")]
        # Chỉ bài người học thật học được: L05–L08 (source_audited) chưa có câu hỏi chạy trong ứng dụng.
        if rows and spec.get("status") in LEARNABLE:
            lessons.append(spec["id"])
            exercises[spec["id"]] = rows
    prereqs: dict[str, set[str]] = {}
    for skill, pre in PREREQUISITES:
        prereqs.setdefault(skill, set()).add(pre)
    return Curriculum(lessons, exercises, prereqs)


@dataclass
class Event:
    t: int
    kind: str          # start | attempt | complete | review
    lesson: str | None = None
    exercise: str | None = None
    skill: str | None = None
    correct: bool | None = None
    next_due: int | None = None   # review/complete: thời điểm thẻ đến hạn tiếp


@dataclass
class SimUser:
    uid: str
    persona: str
    goal: str
    events: list[Event] = field(default_factory=list)


def _p(theta: float, rng: random.Random) -> float:
    return min(0.98, max(0.02, 0.15 + 0.8 * theta + rng.gauss(0, 0.08)))


def simulate_user(i: int, cur: Curriculum, rng: random.Random) -> SimUser:
    persona = PERSONAS[i % len(PERSONAS)]
    u = SimUser(f"sim-{i:05d}", persona.name, persona.goal)
    skills = sorted({s for rows in cur.exercises.values() for _, s in rows})  # sắp xếp: thứ tự set phụ thuộc PYTHONHASHSEED
    theta = {s: min(0.95, max(0.0, rng.gauss(persona.base, 0.12))) for s in skills}
    start_day = rng.randint(0, 59)
    n_days = rng.randint(*persona.days)
    started, done, solved = set(), set(), set()
    current: str | None = None
    cards: dict[str, tuple[int, int]] = {}   # skill → (hộp, đến hạn)
    clock = 0

    def tick(day: int) -> int:
        nonlocal clock
        clock += 1
        return day * DAY + 8 * 3600 + clock

    def ready(lesson: str) -> bool:
        own = {s for _, s in cur.exercises[lesson]}
        need = set().union(*(cur.prereqs.get(s, set()) for s in own)) - own
        return all(theta.get(p, 0.0) >= 0.6 for p in need if p in theta)

    for d in range(n_days):
        day = start_day + d
        if rng.random() < persona.p_skip_day:
            continue
        for skill, (box, due) in sorted(cards.items()):
            if due <= day * DAY + DAY:
                ok = rng.random() < _p(theta[skill], rng)
                theta[skill] += persona.lr * 0.5 * (1 - theta[skill])
                box = min(len(LEITNER_DAYS) - 1, box + 1) if ok else 0
                t = tick(day)
                cards[skill] = (box, t + LEITNER_DAYS[box] * DAY)
                u.events.append(Event(t, "review", skill=skill, correct=ok, next_due=cards[skill][1]))
        if current is None:
            todo = [l for l in cur.lessons if l not in started]
            if not todo:
                continue
            if rng.random() < 0.8:
                cand = [l for l in todo if ready(l)] or todo[:1]
                current = cand[0]
            else:
                w = [persona.interest.get(l, 1.0) for l in todo]
                current = rng.choices(todo, weights=w)[0]
            started.add(current)
            u.events.append(Event(tick(day), "start", lesson=current))
        budget = rng.randint(2, 6)  # số lượt làm bài trong một buổi học: một bài thường kéo dài vài ngày
        for ex, skill in cur.exercises[current]:
            if ex in solved:
                continue
            if budget <= 0:
                break
            for _ in range(3):
                if budget <= 0:
                    break
                budget -= 1
                ok = rng.random() < _p(theta[skill], rng)
                theta[skill] += persona.lr * (1 - theta[skill])
                u.events.append(Event(tick(day), "attempt", lesson=current, exercise=ex, skill=skill, correct=ok))
                if ok:
                    solved.add(ex)
                    break
        if all(ex in solved for ex, _ in cur.exercises[current]):
            t = tick(day)
            for skill in {s for _, s in cur.exercises[current]}:
                cards.setdefault(skill, (0, t + LEITNER_DAYS[0] * DAY))
            u.events.append(Event(t, "complete", lesson=current))
            done.add(current)
            current = None
    return u


def generate(n: int, seed: int) -> list[SimUser]:
    rng = random.Random(seed)
    cur = load_curriculum()
    return [simulate_user(i, cur, random.Random(rng.getrandbits(64))) for i in range(n)]


def summary(users: list[SimUser]) -> dict:
    n_ev = [len(u.events) for u in users]
    return {"users": len(users), "events_mean": round(sum(n_ev) / len(n_ev), 1),
            "events_median": sorted(n_ev)[len(n_ev) // 2],
            "starts_mean": round(sum(sum(e.kind == "start" for e in u.events) for u in users) / len(users), 2),
            "by_persona": {p.name: sum(u.persona == p.name for u in users) for p in PERSONAS},
            "math_check": math.isfinite(sum(n_ev))}
