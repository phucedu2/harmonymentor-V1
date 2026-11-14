"""Đánh giá offline hệ gợi ý trên người học mô phỏng (đề GĐ4, 04 mục 8.4, ADR-008 mục 5).

    cd backend && python ../scripts/ai/evaluate_recommender.py --n 2000 --seed 20261104 \
        --out ../docs/giai-doan/ai-gd4/ket_qua_goi_y.json

Không gọi mạng: vector mục tiêu của 4 chân dung đã tính sẵn bằng Gemini (scripts/ai/data/persona_goal_vectors.json),
vector mô tả kỹ năng lấy từ app/content/skill_embeddings.json.

Cách làm:
1. Sinh N người (scripts/ai/sim/nguoi_mo_phong.py, không import bộ gợi ý).
2. Mỗi người: sắp sự kiện theo thời gian, mốc cắt = thời điểm của sự kiện thứ ⌊0,8·n⌋. Chỉ dùng sự kiện TRƯỚC mốc
   (chặt), kể cả của láng giềng: quét toàn bộ sự kiện theo thời gian và gợi ý cho từng người đúng lúc tới mốc của họ.
3. Đáp án chính: các bài người đó bắt đầu LẦN ĐẦU sau mốc (G-3: HitRate/Precision chính chỉ tính bài bắt đầu lần đầu).
   Danh sách gợi ý chính = danh sách xếp hạng bỏ bài đã bắt đầu trước mốc (mục "Bài nên học tiếp").
   Đáp án phụ: mọi bài có hoạt động sau mốc; danh sách phụ = danh sách xếp hạng không lọc.
4. Mastery tính bằng đúng luật GĐ1 (EMA 0,3, D-3, ôn 2A tối đa 1 lần/kỹ năng/ngày); thẻ đến hạn theo Leitner.
5. Phương án: P0 phổ biến (đếm lượt bắt đầu bài trước mốc của mọi người), P1 chỉ luật (qua lọc, theo thứ tự bài),
   P2 luật + nội dung (công thức người học mới 0,55/0,25/0,20, không cộng tác), P3 đủ 3 tầng với 6 cấu hình ADR-008
   (số chiều chung 2/3/4 × dự phòng a/b).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import tempfile
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "ai"))
GOALS = ROOT / "scripts" / "ai" / "data" / "persona_goal_vectors.json"
KS = (1, 3, 5)


def ts(t: int) -> datetime:
    return datetime.fromtimestamp(t, tz=timezone.utc)


def boot_ci(values: list[float], rng: random.Random, n: int = 1000) -> list[float]:
    if not values:
        return [None, None]
    means = []
    for _ in range(n):
        s = [values[rng.randrange(len(values))] for _ in values]
        means.append(sum(s) / len(s))
    means.sort()
    return [round(means[int(0.025 * n)], 4), round(means[int(0.975 * n) - 1], 4)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261104)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    started_at = time.perf_counter()

    tmp = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/eval.db"
    os.environ["AI_ENABLED"] = "0"
    from fastapi.testclient import TestClient

    from app.ai import mastery as m
    from app.ai.recommender.content import embedding_content
    from app.ai.recommender.engine import RecInput, recommend, rule_filter
    from app.ai.recommender.knn import find_neighbors
    from app.ai.recommender.scoring import FULL
    from app.ai.recommender.vector import PoolMatrix, _DIM, build_vector
    from app.ai.skill_mapping import GROUP_CODES, is_mvp
    from app.content import skill_descriptions as sd
    from app.db.session import SessionLocal
    from app.main import app
    from app.services import recommendation_service as rs
    from sim.nguoi_mo_phong import PERSONAS, generate, summary

    import numpy as np

    with TestClient(app):
        with SessionLocal() as db:
            lessons = rs.lesson_infos(db)
            thr = rs.thresholds(db)
    lesson_ids = [l.lesson_id for l in lessons]
    order = {l.lesson_id: l.order for l in lessons}
    lesson_skills = {l.lesson_id: sorted(s for s in l.skills if is_mvp(s)) for l in lessons}

    goals = json.loads(GOALS.read_text(encoding="utf-8"))
    store = sd.load_embeddings()
    assert goals["model"] == store["model"], "vector mục tiêu và vector kỹ năng phải cùng mô hình"
    skill_vecs = {k: v["vector"] for k, v in store["skills"].items()}
    content_by_persona = {p: embedding_content(g["vector"], skill_vecs) for p, g in goals["personas"].items()}

    users = generate(args.n, args.seed)
    uids = sorted(u.uid for u in users)
    row_of = {u: i for i, u in enumerate(uids)}
    by_id = {u.uid: u for u in users}

    # Mốc cắt từng người.
    cutoff: dict[str, int] = {}
    for u in users:
        if len(u.events) >= 5:
            cutoff[u.uid] = u.events[int(0.8 * len(u.events))].t

    # Quét mọi sự kiện theo thời gian; trạng thái mastery hiện tại của từng người.
    G = len(GROUP_CODES)
    skill_scores: dict[str, dict[str, float]] = defaultdict(dict)
    group_sum = np.zeros((len(uids), G))
    group_cnt = np.zeros((len(uids), G))
    history: dict[tuple[str, str], list[bool]] = defaultdict(list)
    review_day: set[tuple[str, str, str]] = set()
    popularity: Counter = Counter()

    def set_score(uid: str, skill: str, new: float) -> None:
        if not is_mvp(skill):
            return
        r, d = row_of[uid], _DIM[skill]
        old = skill_scores[uid].get(skill)
        if old is None:
            group_cnt[r, d] += 1
            group_sum[r, d] += new
        else:
            group_sum[r, d] += new - old
        skill_scores[uid][skill] = new

    def apply(uid: str, e) -> None:
        if e.kind == "start":
            popularity[e.lesson] += 1
        elif e.kind == "attempt":
            res = m.exercise_result(history[(uid, e.exercise)], e.correct)
            history[(uid, e.exercise)].append(e.correct)
            old = skill_scores[uid].get(e.skill, 0.0)
            set_score(uid, e.skill, old if res is None else m.ema(old, res))
        elif e.kind == "review":
            key = (uid, e.skill, m.vn_day(ts(e.t)))
            if key in review_day:  # 2A: tối đa 1 lượt ôn được tính / kỹ năng / ngày VN
                return
            review_day.add(key)
            old = skill_scores[uid].get(e.skill, 0.0)
            set_score(uid, e.skill, m.ema(old, m.review_result(e.correct)))

    all_events = sorted(((e.t, u.uid, e) for u in users for e in u.events), key=lambda x: (x[0], x[1]))
    checkpoints = sorted((t, uid) for uid, t in cutoff.items())

    configs = [("P0", None), ("P1", None), ("P2", None)] + [(f"P3-s{s}{f}", (s, f)) for s in (2, 3, 4) for f in "ab"]
    # Độ nhạy (KHÔNG phải cấu hình đề xuất, không đổi sản phẩm): P2 khi bỏ điều kiện tiên quyết ở bước lọc,
    # để tách phần thua của P1–P3 do luật tiên quyết khỏi phần do cách chấm điểm.
    SENS = "P2-bo-tien-quyet"
    results: dict[str, list[dict]] = {name: [] for name, _ in configs}
    results[SENS] = []
    skipped = Counter()
    truth_excluded = Counter()  # vì sao bài người đó thật sự bắt đầu sau mốc bị bước lọc loại

    def user_state(uid: str, t_cut: int):
        u = by_id[uid]
        before = [e for e in u.events if e.t < t_cut]
        after = [e for e in u.events if e.t >= t_cut]
        started = {e.lesson for e in before if e.kind == "start"}
        truth_main = {e.lesson for e in after if e.kind == "start"} - started
        truth_any = {e.lesson for e in after if e.lesson}
        due: dict[str, int] = {}
        for e in before:
            if e.kind == "complete":
                for s in lesson_skills.get(e.lesson, []):
                    due.setdefault(s, e.t + 86_400)
            elif e.kind == "review":
                due[e.skill] = e.next_due
        due_now = frozenset(s for s, t in due.items() if t <= t_cut)
        return started, truth_main, truth_any, due_now, len(before) == 0

    def score_lists(ranked_ids: list[str], started: set[str]) -> tuple[list[str], list[str]]:
        return [l for l in ranked_ids if l not in started], ranked_ids

    def metrics(main_list, full_list, truth_main, truth_any) -> dict:
        out = {}
        for k in KS:
            top = main_list[:k]
            hits = len(set(top) & truth_main)
            out[f"hit@{k}"] = float(hits > 0)
            out[f"prec@{k}"] = hits / k
            top2 = full_list[:k]
            out[f"hit2@{k}"] = float(bool(set(top2) & truth_any))
            out[f"prec2@{k}"] = len(set(top2) & truth_any) / k
        rank = next((i + 1 for i, l in enumerate(main_list) if l in truth_main), None)
        out["mrr"] = 1 / rank if rank else 0.0
        out["list_len"] = len(main_list)
        return out

    ci = 0
    for t, uid, e in all_events:
        while ci < len(checkpoints) and checkpoints[ci][0] <= t:
            t_cut, target = checkpoints[ci]
            ci += 1
            started, truth_main, truth_any, due_now, empty = user_state(target, t_cut)
            if not truth_main:
                skipped["no_new_lesson_after_cutoff"] += 1
                continue
            persona = by_id[target].persona
            mastery = {s: v for s, v in skill_scores[target].items() if is_mvp(s)}
            base = dict(lessons=lessons, mastery=mastery, due_skills=due_now, content=content_by_persona[persona],
                        k=5, goal_text=by_id[target].goal, thresholds=thr, new_learner=empty)
            # P0: phổ biến, không lọc luật.
            pop = sorted(lesson_ids, key=lambda l: (-popularity[l], order[l]))
            main, full = score_lists(pop, started)
            results["P0"].append({"uid": target, "persona": persona, **metrics(main, full, truth_main, truth_any)})
            # P1: chỉ luật.
            inp = RecInput(neighbor_ids=None, neighbor_mastery={}, **base)
            passed = sorted([l for l in lessons if rule_filter(l, inp) is None], key=lambda l: l.order)
            for l in lessons:
                if l.lesson_id in truth_main:
                    truth_excluded[rule_filter(l, inp) or "passed"] += 1
            main, full = score_lists([l.lesson_id for l in passed], started)
            results["P1"].append({"uid": target, "persona": persona, **metrics(main, full, truth_main, truth_any)})
            # P2: luật + nội dung (công thức người học mới, không cộng tác).
            out = recommend(RecInput(neighbor_ids=None, neighbor_mastery={}, weights=FULL, **base))
            main, full = score_lists([r.lesson_id for r in out.ranked], started)
            results["P2"].append({"uid": target, "persona": persona, "few_eligible": out.few_eligible,
                                  **metrics(main, full, truth_main, truth_any)})
            # Độ nhạy: bỏ tiên quyết (lessons giữ kỹ năng, xóa prereqs).
            relaxed = [l._replace(prereqs=frozenset()) if hasattr(l, "_replace") else
                       type(l)(l.lesson_id, l.order, l.title, l.skills, frozenset()) for l in lessons]
            out = recommend(RecInput(neighbor_ids=None, neighbor_mastery={}, weights=FULL, **{**base, "lessons": relaxed}))
            main, full = score_lists([r.lesson_id for r in out.ranked], started)
            results[SENS].append({"uid": target, "persona": persona, "few_eligible": out.few_eligible,
                                  **metrics(main, full, truth_main, truth_any)})
            # P3: đủ 3 tầng, 6 cấu hình.
            with np.errstate(divide="ignore", invalid="ignore"):
                values = np.where(group_cnt > 0, group_sum / np.maximum(group_cnt, 1), 0.0)
            pool = PoolMatrix(tuple(uids), values, group_cnt > 0)
            target_vec = build_vector(mastery)
            for name, cfg in configs[3:]:
                min_shared, fb = cfg
                nb = find_neighbors(target_vec, pool, k=10, min_shared=min_shared, fallback=fb, exclude=target)
                ids = [n.user_id for n in nb.neighbors]
                nm = {i: {s: v for s, v in skill_scores[i].items() if is_mvp(s)} for i in ids}
                out = recommend(RecInput(neighbor_ids=ids or None, neighbor_mastery=nm, weights=FULL, **base))
                main, full = score_lists([r.lesson_id for r in out.ranked], started)
                results[name].append({"uid": target, "persona": persona, "few_eligible": out.few_eligible,
                                      "fallback": nb.reason, "min_shared_used": nb.min_shared_used,
                                      **metrics(main, full, truth_main, truth_any)})
        apply(uid, e)

    rng = random.Random(args.seed)
    table = {}
    for name, rows in results.items():
        n = len(rows)
        mean = lambda key, rs_=rows: round(sum(r[key] for r in rs_) / len(rs_), 4) if rs_ else None  # noqa: E731
        entry = {"n_users": n}
        for k in KS:
            entry[f"HitRate@{k}"] = mean(f"hit@{k}")
            entry[f"Precision@{k}"] = mean(f"prec@{k}")
            entry[f"HitRate@{k} (phụ)"] = mean(f"hit2@{k}")
            entry[f"Precision@{k} (phụ)"] = mean(f"prec2@{k}")
        entry["MRR"] = mean("mrr")
        entry["CI95 HitRate@1"] = boot_ci([r["hit@1"] for r in rows], rng, args.boot)
        entry["CI95 HitRate@3"] = boot_ci([r["hit@3"] for r in rows], rng, args.boot)
        entry["CI95 MRR"] = boot_ci([r["mrr"] for r in rows], rng, args.boot)
        entry["mean_list_len"] = mean("list_len")
        entry["empty_main_list_rate"] = round(sum(r["list_len"] == 0 for r in rows) / n, 4) if n else None
        if rows and "few_eligible" in rows[0]:
            entry["few_eligible_rate"] = mean("few_eligible")
        if rows and "fallback" in rows[0]:
            reasons = Counter(r["fallback"] or "has_neighbors" for r in rows)
            entry["neighbor_outcome"] = {k: round(v / n, 4) for k, v in reasons.items()}
            entry["min_shared_used"] = dict(Counter(r["min_shared_used"] for r in rows))
        entry["by_persona"] = {}
        for p in PERSONAS:
            pr = [r for r in rows if r["persona"] == p.name]
            if pr:
                entry["by_persona"][p.name] = {"n": len(pr), "HitRate@1": mean("hit@1", pr), "HitRate@3": mean("hit@3", pr),
                                               "MRR": mean("mrr", pr)}
        table[name] = entry

    out = {
        "n": args.n, "seed": args.seed, "bootstrap": args.boot, "lessons": lesson_ids,
        "learnable_lessons_with_mvp_skills": [l for l in lesson_ids if lesson_skills[l]],
        "simulator": summary(users), "skipped": dict(skipped), "evaluated_users": len(results["P0"]),
        "truth_lesson_filter_reason": dict(truth_excluded), "goal_model": goals["model"],
        "results": table, "runtime_s": round(time.perf_counter() - started_at, 1),
    }
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(f"{'Phương án':<10} {'n':>5} {'Hit@1':>7} {'Hit@3':>7} {'Hit@5':>7} {'P@1':>6} {'P@3':>6} {'MRR':>6}  CI95 Hit@1")
    for name, e in table.items():
        print(f"{name:<10} {e['n_users']:>5} {e['HitRate@1']:>7} {e['HitRate@3']:>7} {e['HitRate@5']:>7} "
              f"{e['Precision@1']:>6} {e['Precision@3']:>6} {e['MRR']:>6}  {e['CI95 HitRate@1']}")
    print(json.dumps({k: v for k, v in out.items() if k != "results"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
