"""Dịch vụ gợi ý: đọc CSDL, dựng đầu vào cho các hàm thuần trong app/ai/recommender, ghi nhật ký.

Ba danh sách theo G-3 cách B (Thắng chốt 31/10): "Tiếp tục bài đang học" (bài đã bắt đầu, chỉ là điều hướng
tiến độ, không qua bộ gợi ý), "Bài nên học tiếp" (bài chưa bắt đầu) và "Bài nên ôn lại" (bài đã hoàn thành).
Hai danh sách sau đi qua cùng ba tầng nhưng không tranh nhau top 5.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai.embedder import Embedder, EmbeddingUnavailable
from ..ai.recommender.content import embedding_content, tfidf_content
from ..ai.recommender.engine import LessonInfo, RecInput, Ranked, recommend
from ..ai.recommender.knn import find_neighbors
from ..ai.recommender.vector import GroupVector, build_vector
from ..ai.skill_mapping import SKILL_GROUP_MAP_VERSION, is_mvp
from ..content import skill_descriptions as sd
from ..content import versioning
from ..core.config import settings
from ..db.models import (
    LessonProgress, MasteryState, RecommendationLog, ReviewItem, ReviewState, Skill, SkillPrerequisite, User,
)
from . import learning_service

ALGORITHM_VERSION = "gd2-2026-11-05"
GOAL_TASK = "RETRIEVAL_QUERY"


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


# --- Đọc dữ liệu --------------------------------------------------------------------------------

def user_mastery(db: Session, user_id: str) -> dict[str, float]:
    """Chỉ kỹ năng MVP đã đánh giá (có dòng mastery_states)."""
    return {s.skill_id: s.score for s in db.scalars(select(MasteryState).where(MasteryState.user_id == user_id))
            if is_mvp(s.skill_id)}


def user_vector(db: Session, user_id: str) -> GroupVector:
    return build_vector(user_mastery(db, user_id))


def due_skills(db: Session, user_id: str, now: datetime) -> frozenset[str]:
    rows = db.execute(select(ReviewState.due_at, ReviewItem.skill_id)
                      .join(ReviewItem, ReviewItem.id == ReviewState.review_item_id)
                      .where(ReviewState.user_id == user_id, ReviewState.status == "active")).all()
    return frozenset(skill for due_at, skill in rows if _aware(due_at) <= now)


def lesson_infos(db: Session) -> list[LessonInfo]:
    lessons = learning_service.visible_lessons(db)
    orders = learning_service.display_order(lessons)
    prereq_rows = db.execute(select(SkillPrerequisite.skill_id, SkillPrerequisite.prerequisite_skill_id)).all()
    prereqs: dict[str, set[str]] = {}
    for skill, pre in prereq_rows:
        prereqs.setdefault(skill, set()).add(pre)
    out = []
    for lesson in lessons:
        # 04 mục 6.5: kỹ năng của bài = skill_id của các câu đang chạy (đã phát hành, chưa retired).
        own = frozenset(e.skill_id for e in lesson.exercises if versioning.current_version(e) is not None)
        req = frozenset(set().union(*(prereqs.get(s, set()) for s in own)) - own) if own else frozenset()
        out.append(LessonInfo(lesson.id, orders[lesson.id], lesson.title, own, req))
    return out


def thresholds(db: Session) -> dict[str, tuple[float, float]]:
    return {s.id: (s.ready_threshold, s.mastery_threshold) for s in db.scalars(select(Skill))}


def neighbor_pool(db: Session, user_id: str) -> tuple[dict[str, GroupVector], dict[str, dict[str, float]], str]:
    """Tập ứng viên láng giềng theo 9A: người học thật khi đủ người, nếu không thì người mô phỏng.

    Admin không bao giờ là ứng viên (lượt is_test không tạo mastery, nhưng loại hẳn cho rõ)."""
    rows = db.execute(select(MasteryState.user_id, MasteryState.skill_id, MasteryState.score, User.is_synthetic)
                      .join(User, User.id == MasteryState.user_id)
                      .where(User.role != "admin", User.id != user_id)).all()
    mastery: dict[bool, dict[str, dict[str, float]]] = {True: {}, False: {}}
    for uid, skill, score, synthetic in rows:
        if is_mvp(skill):
            mastery[bool(synthetic)].setdefault(uid, {})[skill] = score
    real = {u: build_vector(m) for u, m in mastery[False].items()}
    enough = sum(1 for v in real.values() if v.assessed_count >= settings.knn_real_min_dims)
    if enough >= settings.knn_real_min_users:
        return real, mastery[False], "real"
    synthetic = {u: build_vector(m) for u, m in mastery[True].items()}
    if synthetic:
        return synthetic, mastery[True], "synthetic"
    return {}, {}, "none"


# --- Tầng nội dung ------------------------------------------------------------------------------

def embed_goal(db: Session, user: User, embedder: Embedder | None) -> bool:
    """Tính vector mục tiêu nếu có thể. Chỉ gửi đúng văn bản mục tiêu (03 Bảng 3)."""
    if embedder is None or not user.goal_text:
        return False
    try:
        vec = embedder.embed([user.goal_text], GOAL_TASK)[0]
    except EmbeddingUnavailable:
        return False
    user.goal_embedding, user.goal_embedding_model = vec, embedder.model
    return True


def content_scores(user: User) -> tuple[dict[str, float], str, bool]:
    """(điểm theo kỹ năng, nguồn "embedding" | "tfidf" | "none", có dùng mô tả nháp không)."""
    rows = sd.usable(sd.load_descriptions(), allow_draft=settings.allow_draft_skill_descriptions)
    rows = {k: v for k, v in rows.items() if is_mvp(k)}
    if not user.goal_text or not rows:
        return {}, "none", False
    draft = any(r["status"] == "draft" for r in rows.values())
    store = sd.load_embeddings()
    if user.goal_embedding and user.goal_embedding_model == store.get("model"):
        vecs = {s: store["skills"][s]["vector"] for s, r in rows.items()
                if s in store["skills"] and store["skills"][s]["hash"] == sd.description_hash(r["text"])}
        if vecs:
            return embedding_content(user.goal_embedding, vecs), "embedding", draft
    return tfidf_content(user.goal_text, {s: r["text"] for s, r in rows.items()}), "tfidf", draft


# --- Gợi ý --------------------------------------------------------------------------------------

def _item(r: Ranked, **extra) -> dict[str, Any]:
    return {"lesson_id": r.lesson_id, "order": r.order, "title": r.title, "score": round(r.score, 4),
            "components": {"content": round(r.content, 4), "mastery": round(r.mastery, 4), "due": round(r.due, 4),
                           "cf": None if r.cf is None else round(r.cf, 4)},
            "reason_code": r.reason_code, "reason": r.reason, "badge": r.badge, "skills": list(r.skills), **extra}


def recommend_for_user(db: Session, user: User, *, k: int = 5, now: datetime | None = None,
                       embedder: Embedder | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    if user.goal_text and user.goal_embedding is None and embed_goal(db, user, embedder):
        db.flush()
    mastery = user_mastery(db, user.id)
    target = build_vector(mastery)
    pool, pool_mastery, cf_source = neighbor_pool(db, user.id)
    nb = find_neighbors(target, pool, k=settings.rec_neighbors_k, min_shared=settings.rec_min_shared_dims,
                        fallback=settings.rec_fallback, exclude=user.id)
    neighbor_ids = [n.user_id for n in nb.neighbors]
    content, content_source, draft = content_scores(user)

    infos = lesson_infos(db)
    status = {p.lesson_id: p.status for p in db.scalars(select(LessonProgress).where(LessonProgress.user_id == user.id))}
    common = dict(mastery=mastery, due_skills=due_skills(db, user.id, now), content=content,
                  neighbor_ids=neighbor_ids, neighbor_mastery=pool_mastery, k=k, goal_text=user.goal_text,
                  thresholds=thresholds(db))
    nxt = recommend(RecInput(lessons=[i for i in infos if i.lesson_id not in status], **common))
    rev = recommend(RecInput(lessons=[i for i in infos if status.get(i.lesson_id) == "completed"], **common))
    cont = [{"lesson_id": i.lesson_id, "order": i.order, "title": i.title, "status": "started"}
            for i in infos if status.get(i.lesson_id) == "started"]

    context = {
        "algorithm_version": ALGORITHM_VERSION, "skill_group_map_version": SKILL_GROUP_MAP_VERSION,
        "weights_mode": "full" if neighbor_ids else "cold", "cf_source": cf_source if neighbor_ids else "none",
        "fallback_reason": nb.reason, "min_shared_dims": nb.min_shared_used, "fallback": settings.rec_fallback,
        "neighbors_count": len(neighbor_ids), "excluded_pairs": dict(nb.excluded),
        "content_source": content_source, "draft_descriptions": draft,
    }
    next_items = [_item(r) for r in nxt.ranked]
    review_items = [_item(r, label="Ôn lại") for r in rev.ranked]
    log = RecommendationLog(
        id="rec-" + uuid4().hex, user_id=user.id, lesson_ids=[x["lesson_id"] for x in next_items],
        scores=[dict(x, list="next") for x in next_items] + [dict(x, list="review") for x in review_items],
        explanation="\n".join(f"{x['lesson_id']}: {x['reason']}" for x in next_items + review_items) or None,
        context=dict(context, review_ids=[x["lesson_id"] for x in review_items]), created_at=now,
    )
    db.add(log)
    db.commit()
    return {**context, "generated_at": now, "log_id": log.id, "few_eligible": nxt.few_eligible,
            "continue": cont, "next": next_items, "review": review_items}


class LogNotFound(LookupError):
    pass


def record_click(db: Session, user_id: str, log_id: str, lesson_id: str, now: datetime | None = None) -> None:
    log = db.get(RecommendationLog, log_id)
    if log is None or log.user_id != user_id:
        raise LogNotFound(log_id)  # log của người khác cũng là 404 (nguyên tắc 4)
    if lesson_id not in set(log.lesson_ids) | set(log.context.get("review_ids", [])):
        raise ValueError("LESSON_NOT_IN_RECOMMENDATION")
    log.clicked_lesson_id, log.clicked_at = lesson_id, now or datetime.now(timezone.utc)
    db.commit()


def set_goal(db: Session, user: User, goal_text: str | None, embedder: Embedder | None) -> bool:
    text = " ".join((goal_text or "").split()) or None
    user.goal_text, user.goal_embedding, user.goal_embedding_model = text, None, None
    embedded = embed_goal(db, user, embedder)
    db.commit()
    return embedded
