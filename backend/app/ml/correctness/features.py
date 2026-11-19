"""Đặc trưng cho từng lượt làm, tính CHỈ từ các lượt trước nó (không rò rỉ tương lai).

Cùng một lớp `UserState` dùng cho cả lúc train (duyệt lịch sử mô phỏng/xuất từ CSDL) và lúc phục vụ API
(duyệt lịch sử thật của người đang đăng nhập), nên đặc trưng hai bên luôn tính giống nhau.

Một sự kiện là dict: {"user", "t" (giây epoch), "kind": "attempt"|"review", "skill", "exercise" (None với lượt ôn),
"correct": bool, "counts": bool (tùy chọn, lượt ôn có được tính vào EMA không; mặc định True)}.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone

from ...ai import mastery as m
from ...ai.skill_mapping import GROUP_CODES, SKILL_MAPPING

# Thứ tự cột cố định: đổi thì tăng FEATURE_VERSION, model cũ không dùng được nữa.
FEATURE_VERSION = "1"
NUMERIC = (
    "ema_skill",         # mastery EMA tái dựng theo đúng luật app.ai.mastery
    "seen_skill",        # 1 nếu đã từng làm kỹ năng này
    "log_n_skill",       # log(1 + số lượt đã làm kỹ năng)
    "acc_skill",         # tỷ lệ đúng của kỹ năng, làm trơn Laplace (đúng+1)/(lượt+2)
    "last_skill",        # kết quả lượt gần nhất của kỹ năng: 1 đúng, 0 sai, 0,5 chưa có
    "tries_exercise",    # số lần đã thử chính câu này (0 với lượt ôn và câu mới)
    "last_ex_wrong",     # 1 nếu lần thử trước của chính câu này sai
    "is_review",         # 1 nếu là lượt ôn thẻ
    "log_gap_days",      # log(1 + số ngày từ lượt gần nhất của kỹ năng), chưa có thì coi 30 ngày
    "acc_user",          # tỷ lệ đúng chung của người học, làm trơn Laplace
    "log_n_user",        # log(1 + tổng số lượt)
    "ema_group",         # EMA trung bình các kỹ năng cùng group_code đã làm
    "prereq_ema",        # EMA nhỏ nhất của các kỹ năng tiên quyết (chưa làm = 0; không có tiên quyết = 1)
)
GROUPS = tuple(GROUP_CODES) + ("khac",)
FEATURE_NAMES = NUMERIC + tuple(f"group={g}" for g in GROUPS)
NO_GAP_DAYS = 30.0
DAY = 86_400


def group_of(skill: str) -> str:
    entry = SKILL_MAPPING.get(skill)
    return entry[1] if entry else "khac"


def _prereqs() -> dict[str, set[str]]:
    from ...content.skill_graph import PREREQUISITES

    out: dict[str, set[str]] = defaultdict(set)
    for skill, pre in PREREQUISITES:
        out[skill].add(pre)
    return out


_PREREQS: dict[str, set[str]] | None = None


def prereqs_of(skill: str) -> set[str]:
    global _PREREQS
    if _PREREQS is None:
        _PREREQS = _prereqs()
    return _PREREQS.get(skill, set())


class UserState:
    """Trạng thái của MỘT người học sau các sự kiện đã thấy."""

    def __init__(self) -> None:
        self.ema: dict[str, float] = {}
        self.n: dict[str, int] = defaultdict(int)
        self.c: dict[str, int] = defaultdict(int)
        self.last: dict[str, int] = {}
        self.last_t: dict[str, int] = {}
        self.ex_hist: dict[str, list[bool]] = defaultdict(list)
        self.review_days: set[tuple[str, str]] = set()
        self.n_user = 0
        self.c_user = 0

    def features(self, skill: str, exercise: str | None, kind: str, t: int) -> list[float]:
        n = self.n[skill]
        hist = self.ex_hist[exercise] if exercise else []
        gap = (t - self.last_t[skill]) / DAY if skill in self.last_t else NO_GAP_DAYS
        group = group_of(skill)
        same = [v for s, v in self.ema.items() if group_of(s) == group]
        pre = prereqs_of(skill)
        prereq = min((self.ema.get(p, 0.0) for p in pre), default=1.0)
        row = [
            self.ema.get(skill, 0.0),
            1.0 if n else 0.0,
            math.log1p(n),
            (self.c[skill] + 1) / (n + 2),
            float(self.last[skill]) if skill in self.last else 0.5,
            float(len(hist)),
            1.0 if hist and not hist[-1] else 0.0,
            1.0 if kind == "review" else 0.0,
            math.log1p(max(0.0, gap)),
            (self.c_user + 1) / (self.n_user + 2),
            math.log1p(self.n_user),
            sum(same) / len(same) if same else 0.0,
            prereq,
        ]
        row += [1.0 if g == group else 0.0 for g in GROUPS]
        return row

    def update(self, ev: dict) -> None:
        skill, ok, t = ev["skill"], bool(ev["correct"]), int(ev["t"])
        if ev["kind"] == "attempt":
            hist = self.ex_hist[ev["exercise"]]
            res = m.exercise_result(hist, ok)
            hist.append(ok)
            if res is not None:
                self.ema[skill] = m.ema(self.ema.get(skill, 0.0), res)
            else:
                self.ema.setdefault(skill, 0.0)
        else:
            day = (skill, m.vn_day(datetime.fromtimestamp(t, tz=timezone.utc)))
            # Luật 2A: tối đa 1 lượt ôn được tính / kỹ năng / ngày VN; ôn trước hạn (counts=False) không tính.
            if ev.get("counts", True) and day not in self.review_days:
                self.review_days.add(day)
                self.ema[skill] = m.ema(self.ema.get(skill, 0.0), m.review_result(ok))
        self.n[skill] += 1
        self.c[skill] += ok
        self.last[skill] = int(ok)
        self.last_t[skill] = t
        self.n_user += 1
        self.c_user += ok


def rows_for_user(events: list[dict]) -> tuple[list[list[float]], list[int]]:
    """X, y cho mọi lượt làm/ôn của một người, theo thời gian. Đặc trưng lấy TRƯỚC khi cập nhật."""
    state = UserState()
    X, y = [], []
    for ev in sorted(events, key=lambda e: int(e["t"])):
        if ev["kind"] not in ("attempt", "review"):
            continue
        X.append(state.features(ev["skill"], ev.get("exercise"), ev["kind"], int(ev["t"])))
        y.append(int(bool(ev["correct"])))
        state.update(ev)
    return X, y


def next_question_features(events: list[dict], skills: list[str], t: int) -> list[list[float]]:
    """Đặc trưng cho "câu MỚI tiếp theo" của từng kỹ năng tại thời điểm t (lượt làm bài, chưa thử câu đó)."""
    state = UserState()
    for ev in sorted(events, key=lambda e: int(e["t"])):
        if ev["kind"] in ("attempt", "review") and int(ev["t"]) <= t:
            state.update(ev)
    return [state.features(s, None, "attempt", t) for s in skills]
