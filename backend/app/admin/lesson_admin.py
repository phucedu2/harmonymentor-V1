"""Quản trị viên tạo, xóa, sắp xếp bài và soạn câu luyện tập bằng form (FR-ADM-13/15/16, FR-ADM-24..29; Phúc 1A, 5A).

Bài do seed tạo (L01…) vẫn sửa chữ qua lớp bản sửa (ADR-023) và đổi câu qua curriculum_specs (ADR-006): seed chạy lại mỗi
lần khởi động, nên câu sửa ở đây cho bài seed sẽ bị seed ghi đè. Vì vậy form câu hỏi và thêm khối chỉ mở cho bài
Quản trị viên tạo (M-…) và bài AI (AI-…). Xóa và sắp xếp thì dùng được cho mọi bài vì nằm ở cột seed không ghi.

Câu hỏi đi qua đúng bộ chuẩn hóa của AI soạn bài (ai_questions): Music Engine tính đáp án, đề phải khớp ký hiệu, câu
phải có lời giải. Khác AI ở chỗ: Engine tính khác đáp án người soạn thì TỪ CHỐI và nói rõ, không tự sửa giúp.
Sửa câu đã có thì thêm phiên bản mới (version + 1), lượt làm cũ vẫn chấm theo bản cũ (ADR-006).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..content import overrides
from ..content.versioning import content_hash, current_version, snapshot_from_spec
from ..db.models import ContentRevision, Exercise, ExerciseVersion, Lesson, LessonBlock, Skill, SourceWork, User
from . import ai_index
from . import ai_questions as aq
from .content_service import AdminContentError, audit

ADMIN_TRACK = "Quản trị viên soạn"
ADMIN_WORK_ID = "admin-authored"
EDITABLE_PREFIXES = ("M-", "AI-")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _lesson(db: Session, lesson_id: str, *, alive: bool = True) -> Lesson:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None or (alive and lesson.deleted_at is not None):
        raise AdminContentError("LESSON_NOT_FOUND", "Không có bài này.", 404)
    return lesson


def _editable(lesson: Lesson) -> None:
    if not lesson.id.startswith(EDITABLE_PREFIXES):
        raise AdminContentError("SEED_LESSON", "Bài gốc của hệ thống: câu hỏi đổi qua curriculum_specs (ADR-006), "
                                "chữ khối lý thuyết sửa ở nút “Sửa nội dung”.", 409)


def _clean_lines(raw: Any, limit: int, size: int) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(x).strip()[:size] for x in raw if isinstance(x, str) and x.strip()][:limit]


# --- bài học ----------------------------------------------------------------------------------------------

def create_lesson(db: Session, admin: User, title: str, objectives: Any, block_title: str, paragraphs: Any) -> dict[str, Any]:
    title, block_title = (title or "").strip()[:240], (block_title or "").strip()[:200]
    paras = _clean_lines(paragraphs, 30, 2000)
    if not title or not block_title or not paras:
        raise AdminContentError("LESSON_INCOMPLETE", "Bài cần tên, tiêu đề khối lý thuyết đầu tiên và ít nhất một đoạn văn.")
    lesson_id = f"M-{uuid4().hex[:8]}"
    order = (db.scalar(select(func.max(Lesson.order_index))) or 0) + 1
    has_custom = db.scalar(select(func.count()).select_from(Lesson).where(Lesson.sort_key.is_not(None))) or 0
    top = db.scalar(select(func.max(overrides.lesson_sort_key())))
    lesson = Lesson(id=lesson_id, order_index=max(order, 200), track=ADMIN_TRACK, title=title, status="reviewed",
                    objectives=_clean_lines(objectives, 10, 300), sort_key=(top or 0) + 10 if has_custom else None)
    db.add(lesson)
    db.flush()
    db.add(LessonBlock(id=f"{lesson_id}-B01", lesson_id=lesson_id, position=1, block_type="theory",
                       payload={"title": block_title, "paragraphs": paras}))
    # Giống bài AI (ADR-033, 7B): bài mới ẩn tới khi Quản trị viên xem trước và bấm hiện, để bài dở dang không lọt ra.
    db.add(ContentRevision(id=str(uuid4()), lesson_id=lesson_id, kind="visibility", target=overrides.LESSON_TARGET,
                           payload={"hidden": True}, status="published", created_by=admin.id, published_by=admin.id,
                           published_at=_now(), note="Bài mới tạo: ẩn tới khi Quản trị viên bấm hiện"))
    audit(db, admin, "lesson.create", "lesson", lesson_id, {"title": title})
    db.commit()
    return {"id": lesson_id, "title": title, "hidden": True}


def add_block(db: Session, admin: User, lesson_id: str, title: str, paragraphs: Any) -> dict[str, Any]:
    lesson = _lesson(db, lesson_id)
    _editable(lesson)
    title, paras = (title or "").strip()[:200], _clean_lines(paragraphs, 30, 2000)
    if not title or not paras:
        raise AdminContentError("BLOCK_INCOMPLETE", "Khối cần tiêu đề và ít nhất một đoạn văn.")
    pos = max((b.position for b in lesson.blocks), default=0) + 1
    block_id = f"{lesson_id}-B{pos:02d}"
    db.add(LessonBlock(id=block_id, lesson_id=lesson_id, position=pos, block_type="theory",
                       payload={"title": title, "paragraphs": paras}))
    audit(db, admin, "lesson.add_block", "lesson", lesson_id, {"block": block_id})
    db.commit()
    _reindex(db, admin, lesson)
    return {"id": block_id, "position": pos}


def delete_lesson(db: Session, admin: User, lesson_id: str) -> dict[str, Any]:
    lesson = _lesson(db, lesson_id)
    lesson.deleted_at = _now()
    audit(db, admin, "lesson.delete", "lesson", lesson_id, {"title": lesson.title})
    db.commit()
    _reindex(db, admin, lesson)
    return {"id": lesson_id, "deleted": True}


def restore_lesson(db: Session, admin: User, lesson_id: str) -> dict[str, Any]:
    lesson = _lesson(db, lesson_id, alive=False)
    lesson.deleted_at = None
    audit(db, admin, "lesson.restore", "lesson", lesson_id)
    db.commit()
    _reindex(db, admin, lesson)
    return {"id": lesson_id, "deleted": False, "hidden": overrides.lesson_hidden(db, lesson_id)}


def reorder(db: Session, admin: User, lesson_ids: list[str]) -> list[str]:
    alive = {lid for lid in db.scalars(select(Lesson.id).where(Lesson.deleted_at.is_(None)))}
    if len(lesson_ids) != len(set(lesson_ids)) or set(lesson_ids) != alive:
        raise AdminContentError("ORDER_MISMATCH", "Danh sách sắp xếp phải gồm đúng mọi bài chưa xóa, mỗi bài một lần. "
                                "Tải lại trang rồi thử lại.", 409)
    for i, lid in enumerate(lesson_ids, start=1):
        db.get(Lesson, lid).sort_key = i * 10
    audit(db, admin, "lesson.reorder", "lesson", "*", {"order": lesson_ids})
    db.commit()
    return lesson_ids


def _reindex(db: Session, admin: User, lesson: Lesson) -> None:
    """Bài AI đang ở kho AI Tutor: xóa/khôi phục/thêm khối thì đồng bộ lại (bài đã xóa được tính là ẩn)."""
    if lesson.track == ai_index.AI_TRACK:
        out = ai_index.sync_lesson(db, lesson.id)
        audit(db, admin, "ai.lesson.index", "lesson", lesson.id, out)
        db.commit()


# --- câu luyện tập -------------------------------------------------------------------------------------------

def _skills(db: Session) -> set[str]:
    return set(db.scalars(select(Skill.id)))


def _normalize(db: Session, item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise AdminContentError("QUESTION_INVALID", "Câu hỏi không hợp lệ.")
    # Người soạn là Quản trị viên: câu coi như đã duyệt; vẫn chạy đủ kiểm của Engine.
    q, why = aq.normalize_question({**item, "page": 1, "reviewed": True}, _skills(db), lambda p: 1, trust_review=True)
    if q is None:
        raise AdminContentError("QUESTION_INVALID", f"Câu chưa lưu được: {why}.")
    if q.get("engine_note"):
        note = (q["engine_note"].replace("AI chọn", "Bạn chọn").replace("AI cho là", "Bạn cho là")
                .replace("Engine sửa thành", "Engine tính là"))
        raise AdminContentError("ENGINE_DISAGREES", f"Music Engine tính đáp án khác bạn chọn: {note} "
                                "Sửa đáp án hoặc đề rồi lưu lại.", 409)
    if q["kind"] != "open" and not q.get("explanation"):
        raise AdminContentError("NO_EXPLANATION", "Câu cần lời giải (vì sao đáp án đúng) để học sinh làm sai còn học được.")
    return q


def _snapshot(ex_id: str, q: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    item = aq.exercise_spec(ex_id, q, ADMIN_WORK_ID)
    item["provenance"] = [{"source_id": ADMIN_WORK_ID, "locator": None, "note": "Quản trị viên soạn bằng form"}]
    item["grader_config"] = {**item["grader_config"], "source": "admin_form", "counts_for_mastery": q["kind"] != "open"}
    if q.get("check") and q["kind"] in ("mcq", "true_false", "multi_select"):
        item["grader_config"]["form_check"] = q["check"]   # giữ phần kiểm Engine để mở form sửa lần sau không mất
    return item, snapshot_from_spec(item)


def _ensure_work(db: Session) -> None:
    if db.get(SourceWork, ADMIN_WORK_ID) is None:
        db.add(SourceWork(id=ADMIN_WORK_ID, title="Quản trị viên HarmonyMentor soạn", author=None, url=None))
        db.flush()


def _engine_answer(q: dict[str, Any]) -> Any:
    out = aq.engine_answer(q)
    if out is None and isinstance(q.get("check"), dict) and q["kind"] != "true_false":
        out = aq.engine_answer_for_check(q["check"])
    return out


def _view(ex: Exercise) -> dict[str, Any]:
    v = current_version(ex)
    q = question_from_version(v, ex.skill_id) if v else None
    return {"id": ex.id, "version": v.version if v else None, "retired": v is None, "position": ex.position,
            "skill_id": ex.skill_id, "question": q, "engine_answer": _engine_answer(q) if q else None}


def add_exercise(db: Session, admin: User, lesson_id: str, item: Any) -> dict[str, Any]:
    lesson = _lesson(db, lesson_id)
    _editable(lesson)
    q = _normalize(db, item)
    _ensure_work(db)
    taken = {e.id for e in lesson.exercises}
    n = 1
    while f"{lesson_id}-M{n:02d}" in taken:
        n += 1
    ex_id = f"{lesson_id}-M{n:02d}"
    _, snap = _snapshot(ex_id, q)
    pos = max((e.position for e in lesson.exercises), default=0) + 1
    ex = Exercise(id=ex_id, lesson_id=lesson_id, skill_id=q["skill_id"], position=pos, kind=snap["kind"], prompt=snap["prompt"],
                  options=snap["options"], grading_strategy=snap["grading_strategy"])
    db.add(ex)
    db.flush()
    db.add(ExerciseVersion(id=f"{ex_id}-v1", exercise_id=ex_id, version=1, **snap, status="published", published_at=_now(),
                           content_hash=content_hash(snap), snapshot_origin="seed"))
    audit(db, admin, "exercise.create", "exercise", ex_id, {"lesson": lesson_id, "kind": q["kind"]})
    db.commit()
    db.refresh(ex)
    return _view(ex)


def _exercise(db: Session, exercise_id: str) -> Exercise:
    ex = db.get(Exercise, exercise_id)
    if ex is None:
        raise AdminContentError("EXERCISE_NOT_FOUND", "Không có câu này.", 404)
    _editable(ex.lesson)
    return ex


def update_exercise(db: Session, admin: User, exercise_id: str, item: Any) -> dict[str, Any]:
    ex = _exercise(db, exercise_id)
    if ex.deleted_at is not None:
        raise AdminContentError("EXERCISE_RETIRED", "Câu đã bỏ, không sửa được.", 409)
    q = _normalize(db, item)
    _, snap = _snapshot(ex.id, q)
    latest = max(ex.versions, key=lambda v: v.version)
    if content_hash(snap) == latest.content_hash:
        return _view(ex)   # không đổi gì thì không tạo phiên bản mới
    version = latest.version + 1
    # ADR-006: phiên bản đã phát hành bất biến; sửa đề/đáp án/cách chấm = thêm bản mới, bản cũ giữ để chấm lại lượt cũ.
    db.add(ExerciseVersion(id=f"{ex.id}-v{version}", exercise_id=ex.id, version=version, **snap, status="published",
                           published_at=_now(), content_hash=content_hash(snap), snapshot_origin="seed"))
    ex.skill_id, ex.kind, ex.prompt, ex.options, ex.grading_strategy = (q["skill_id"], snap["kind"], snap["prompt"],
                                                                         snap["options"], snap["grading_strategy"])
    audit(db, admin, "exercise.update", "exercise", ex.id, {"version": version})
    db.commit()
    db.refresh(ex)
    return _view(ex)


def retire_exercise(db: Session, admin: User, exercise_id: str) -> dict[str, Any]:
    ex = _exercise(db, exercise_id)
    ex.deleted_at, ex.active = _now(), False   # xóa mềm: lượt làm và phiên bản cũ giữ nguyên
    audit(db, admin, "exercise.retire", "exercise", ex.id)
    db.commit()
    return {"id": ex.id, "retired": True}


def list_exercises(db: Session, lesson_id: str) -> dict[str, Any]:
    lesson = _lesson(db, lesson_id)
    editable = lesson.id.startswith(EDITABLE_PREFIXES)
    rows = []
    for e in sorted(lesson.exercises, key=lambda x: x.position):
        v = current_version(e)
        if v is None:
            continue
        if editable:
            rows.append(_view(e))
        else:   # bài seed: chỉ xem, không dựng lại form
            rows.append({"id": e.id, "version": v.version, "retired": False, "position": e.position, "skill_id": e.skill_id,
                         "question": None, "engine_answer": None, "prompt": v.prompt})
    return {"editable": editable, "exercises": rows,
            "skills": sorted(_skills(db)), "levels": list(aq.LEVELS), "kinds": list(aq.KINDS)}


def question_from_version(v: ExerciseVersion, skill_id: str) -> dict[str, Any]:
    """Dựng lại form câu hỏi từ ảnh chụp phiên bản (câu do exercise_spec tạo: bài M-… và AI-…)."""
    cfg, key = v.grader_config or {}, v.answer_key or {}
    q: dict[str, Any] = {"prompt": v.prompt, "skill_id": skill_id, "level": cfg.get("difficulty", "hieu"),
                         "explanation": v.explanation or ""}
    expected = key.get("expected")
    if v.grading_strategy == "open_rubric":
        return {**q, "kind": "open", "model_answer": key.get("model_answer", ""), "rubric": list(key.get("rubric") or [])}
    if cfg.get("kind") == "build_chord":
        return {**q, "kind": "build_chord", "symbol": cfg.get("symbol")}
    if cfg.get("kind") == "build_scale":
        return {**q, "kind": "build_scale", "tonic": cfg.get("tonic"), "scale_type": cfg.get("scale_type")}
    if v.grading_strategy == "music_engine":
        check = {"identify_interval": lambda: {"type": "interval", "lower": cfg.get("lower"), "upper": cfg.get("upper")},
                 "roman_numeral": lambda: {"type": "roman", "key": cfg.get("key"), "chord": cfg.get("chord")},
                 "identify_chord": lambda: {"type": "chord_name", "notes": cfg.get("notes")}}.get(cfg.get("kind"), lambda: None)()
        return {**q, "kind": "short", "check": check}
    if cfg.get("form_check"):
        q["check"] = cfg["form_check"]
    if cfg.get("unordered"):
        return {**q, "kind": "multi_select", "options": list(v.options or []), "answers": list(expected or [])}
    kind = "true_false" if v.kind == "true_false" else "mcq"
    return {**q, "kind": kind, "options": list(v.options or []), "answer": expected}
