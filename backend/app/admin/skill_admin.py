"""Quản trị viên quản lý kỹ năng, kỹ năng tiên quyết và nguồn tài liệu (FR-ADM-18..22, FR-ADM-38; Phúc 1A, 24/11/2026).

Seed chạy lại mỗi lần khởi động: ghi lại tên/miền của kỹ năng seed (skill_graph.SKILLS), thêm lại cạnh tiên quyết seed
(PREREQUISITES), ghi lại thông tin nguồn seed (SOURCE_REGISTRY) và dựng lại liên kết nguồn của bài seed. Vì vậy chỉ cho
sửa/xóa phần Quản trị viên tự thêm; phần seed hiện ở chế độ chỉ xem kèm lý do, không để người dùng sửa rồi mất.

Kỹ năng của một bài = kỹ năng của các câu đang chạy (04 mục 6.5), nên "gán bài cho kỹ năng" làm ở ô Kỹ năng của form
câu hỏi (PR 2); ở đây chỉ hiện bài nào đang dùng kỹ năng nào.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai.skill_mapping import SRS_CODES, is_mvp, reload_custom_mapping
from ..content.skill_graph import PREREQUISITES, SKILLS
from ..content.source_registry import SOURCE_REGISTRY
from ..content.versioning import current_version
from ..db.models import Exercise, Lesson, LessonSource, Skill, SkillPrerequisite, SourceWork, User
from .content_service import AdminContentError, audit

SEED_SKILLS = {s[0] for s in SKILLS}
SEED_EDGES = set(PREREQUISITES)
CUSTOM_PREFIX = "custom."
_SLUG = re.compile(r"[^a-z0-9_.]+")


def _ascii(text: str) -> str:
    """Bỏ dấu tiếng Việt để làm mã: "Thử nguồn" → "thu nguon"."""
    plain = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    return "".join(ch for ch in plain if not unicodedata.combining(ch))


def _clean(text: Any, size: int) -> str:
    return str(text or "").strip()[:size]


# --- kỹ năng --------------------------------------------------------------------------------------------

def list_skills(db: Session) -> list[dict[str, Any]]:
    edges = db.execute(select(SkillPrerequisite.skill_id, SkillPrerequisite.prerequisite_skill_id)).all()
    used: dict[str, set[str]] = {}
    for ex in db.scalars(select(Exercise)):
        if current_version(ex) is not None:
            used.setdefault(ex.skill_id, set()).add(ex.lesson_id)
    out = []
    for s in db.scalars(select(Skill).order_by(Skill.domain, Skill.id)):
        out.append({"id": s.id, "name": s.name, "domain": s.domain, "seed": s.id in SEED_SKILLS, "mvp": is_mvp(s.id),
                    "group_code": s.group_code, "ready_threshold": s.ready_threshold, "mastery_threshold": s.mastery_threshold,
                    "prerequisites": sorted(p for k, p in edges if k == s.id),
                    "seed_prerequisites": sorted(p for k, p in SEED_EDGES if k == s.id),
                    "lessons": sorted(used.get(s.id, set()))})
    return out


def _group(raw: Any) -> str:
    group = _clean(raw, 40)
    if group not in SRS_CODES:
        raise AdminContentError("SKILL_GROUP", "Chọn nhóm kỹ năng trong 10 nhóm MVP để kỹ năng được tính mastery và gợi ý: "
                                + ", ".join(SRS_CODES) + ".")
    return group


def create_skill(db: Session, admin: User, slug: str, name: str, domain: str, group_code: str | None = None) -> dict[str, Any]:
    name, domain = _clean(name, 200), _clean(domain, 80) or "theory"
    tail = _SLUG.sub("_", _ascii(_clean(slug, 100)).lower()).strip("._")
    if not name or not tail:
        raise AdminContentError("SKILL_INCOMPLETE", "Kỹ năng cần mã (chữ thường, số, dấu chấm) và tên.")
    skill_id = tail if tail.startswith(CUSTOM_PREFIX) else CUSTOM_PREFIX + tail
    if db.get(Skill, skill_id) is not None:
        raise AdminContentError("SKILL_EXISTS", f"Đã có kỹ năng “{skill_id}”.", 409)
    group = _group(group_code)   # Phúc 9A: kỹ năng tự tạo phải thuộc một nhóm MVP (srs = group, như bảng ADR-008)
    db.add(Skill(id=skill_id, name=name, domain=domain, srs_code=group, group_code=group))
    audit(db, admin, "skill.create", "skill", skill_id, {"name": name, "group": group})
    db.commit()
    reload_custom_mapping()
    return {"id": skill_id, "name": name, "domain": domain, "group_code": group}


def _custom(db: Session, skill_id: str) -> Skill:
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise AdminContentError("SKILL_NOT_FOUND", "Không có kỹ năng này.", 404)
    if skill.id in SEED_SKILLS:
        raise AdminContentError("SEED_SKILL", "Kỹ năng gốc của hệ thống: đổi trong skill_graph.py (seed ghi lại mỗi lần khởi động).", 409)
    return skill


def update_skill(db: Session, admin: User, skill_id: str, name: str, domain: str, group_code: str | None = None) -> dict[str, Any]:
    skill = _custom(db, skill_id)
    name = _clean(name, 200)
    if not name:
        raise AdminContentError("SKILL_INCOMPLETE", "Kỹ năng cần tên.")
    skill.name, skill.domain = name, _clean(domain, 80) or skill.domain
    detail: dict[str, Any] = {"name": name}
    if group_code:
        group = _group(group_code)
        if group != skill.group_code:
            # Đổi nhóm = đổi chiều trong vector gợi ý của mọi người đã có mastery kỹ năng này; vector tính lại ở lần gợi ý sau.
            detail["group"] = {"from": skill.group_code, "to": group}
            skill.srs_code = skill.group_code = group
    audit(db, admin, "skill.update", "skill", skill_id, detail)
    db.commit()
    reload_custom_mapping()
    return {"id": skill.id, "name": skill.name, "domain": skill.domain, "group_code": skill.group_code}


def set_thresholds(db: Session, admin: User, skill_id: str, ready: Any, mastered: Any) -> dict[str, Any]:
    """FR-ADM-23: ngưỡng sẵn sàng/thành thạo riêng của MỌI kỹ năng. Seed chỉ điền ngưỡng khi trống nên không ghi đè."""
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise AdminContentError("SKILL_NOT_FOUND", "Không có kỹ năng này.", 404)
    try:
        r, m = float(ready), float(mastered)
    except (TypeError, ValueError) as exc:
        raise AdminContentError("THRESHOLD_INVALID", "Ngưỡng phải là số.") from exc
    if not (0.0 < r < m <= 1.0):
        raise AdminContentError("THRESHOLD_INVALID", "Cần 0 < ngưỡng sẵn sàng < ngưỡng thành thạo ≤ 1 (ví dụ 0,60 và 0,80).")
    before = {"ready": skill.ready_threshold, "mastered": skill.mastery_threshold}
    if (r, m) == (skill.ready_threshold, skill.mastery_threshold):
        return {"id": skill.id, "ready_threshold": r, "mastery_threshold": m, "changed": False}
    skill.ready_threshold, skill.mastery_threshold = r, m
    audit(db, admin, "skill.thresholds", "skill", skill_id, {"from": before, "to": {"ready": r, "mastered": m}})
    db.commit()
    return {"id": skill.id, "ready_threshold": r, "mastery_threshold": m, "changed": True}


def delete_skill(db: Session, admin: User, skill_id: str) -> None:
    skill = _custom(db, skill_id)
    if db.scalar(select(Exercise.id).where(Exercise.skill_id == skill_id).limit(1)):
        # Câu (kể cả câu đã bỏ) còn trỏ tới kỹ năng: giữ để lượt làm và mastery cũ còn đọc được.
        raise AdminContentError("SKILL_IN_USE", "Kỹ năng đang được câu hỏi dùng (kể cả câu đã bỏ), không xóa được.", 409)
    db.query(SkillPrerequisite).filter((SkillPrerequisite.skill_id == skill_id) |
                                       (SkillPrerequisite.prerequisite_skill_id == skill_id)).delete(synchronize_session=False)
    db.delete(skill)
    audit(db, admin, "skill.delete", "skill", skill_id)
    db.commit()
    reload_custom_mapping()


# --- tiên quyết ------------------------------------------------------------------------------------------

def _reaches(db: Session, start: str, target: str) -> bool:
    """Từ `start` đi theo cạnh "cần học trước" có tới `target` không (tìm chu trình trước khi thêm cạnh)."""
    graph: dict[str, set[str]] = {}
    for k, p in db.execute(select(SkillPrerequisite.skill_id, SkillPrerequisite.prerequisite_skill_id)).all():
        graph.setdefault(k, set()).add(p)
    seen, stack = set(), [start]
    while stack:
        node = stack.pop()
        if node == target:
            return True
        if node in seen:
            continue
        seen.add(node)
        stack.extend(graph.get(node, ()))
    return False


def add_prerequisite(db: Session, admin: User, skill_id: str, prerequisite_id: str) -> dict[str, Any]:
    for sid in (skill_id, prerequisite_id):
        if db.get(Skill, sid) is None:
            raise AdminContentError("SKILL_NOT_FOUND", f"Không có kỹ năng “{sid}”.", 404)
    if skill_id == prerequisite_id:
        raise AdminContentError("PREREQ_CYCLE", "Kỹ năng không thể là tiên quyết của chính nó.", 409)
    if _reaches(db, prerequisite_id, skill_id):
        # FR-ADM-20: đồ thị phải không có chu trình, nếu không lộ trình và hệ gợi ý không biết học gì trước.
        raise AdminContentError("PREREQ_CYCLE", f"Không thêm được: “{prerequisite_id}” đã (gián tiếp) cần “{skill_id}” học trước, "
                                "thêm cạnh này sẽ tạo vòng lặp.", 409)
    exists = db.scalar(select(SkillPrerequisite).where(SkillPrerequisite.skill_id == skill_id,
                                                       SkillPrerequisite.prerequisite_skill_id == prerequisite_id))
    if exists is None:
        db.add(SkillPrerequisite(skill_id=skill_id, prerequisite_skill_id=prerequisite_id))
        audit(db, admin, "skill.prereq.add", "skill", skill_id, {"prerequisite": prerequisite_id})
        db.commit()
    return {"skill_id": skill_id, "prerequisite_id": prerequisite_id}


def remove_prerequisite(db: Session, admin: User, skill_id: str, prerequisite_id: str) -> None:
    if (skill_id, prerequisite_id) in SEED_EDGES:
        raise AdminContentError("SEED_PREREQ", "Cạnh tiên quyết gốc của hệ thống: seed thêm lại mỗi lần khởi động, đổi trong skill_graph.py.", 409)
    row = db.scalar(select(SkillPrerequisite).where(SkillPrerequisite.skill_id == skill_id,
                                                    SkillPrerequisite.prerequisite_skill_id == prerequisite_id))
    if row is None:
        raise AdminContentError("PREREQ_NOT_FOUND", "Không có cạnh tiên quyết này.", 404)
    db.delete(row)
    audit(db, admin, "skill.prereq.remove", "skill", skill_id, {"prerequisite": prerequisite_id})
    db.commit()


# --- nguồn tài liệu (FR-ADM-38) --------------------------------------------------------------------------

def list_sources(db: Session) -> list[dict[str, Any]]:
    links: dict[str, list[dict[str, Any]]] = {}
    for link in db.scalars(select(LessonSource).order_by(LessonSource.lesson_id)):
        links.setdefault(link.source_work_id, []).append({"id": link.id, "lesson_id": link.lesson_id, "locator": link.locator,
                                                          "note": link.note})
    return [{"id": w.id, "title": w.title, "author": w.author, "url": w.url, "seed": w.id in SOURCE_REGISTRY,
             "lessons": links.get(w.id, [])} for w in db.scalars(select(SourceWork).order_by(SourceWork.title))]


def _url(raw: Any) -> str | None:
    url = _clean(raw, 800) or None
    if url and not url.startswith(("https://", "http://")):
        raise AdminContentError("SOURCE_URL", "Liên kết nguồn phải bắt đầu bằng https:// hoặc http://.")
    return url


def create_source(db: Session, admin: User, title: str, author: str | None, url: str | None) -> dict[str, Any]:
    title = _clean(title, 300)
    if not title:
        raise AdminContentError("SOURCE_INCOMPLETE", "Nguồn cần tên tài liệu.")
    base = "src-" + (re.sub(r"[^a-z0-9]+", "-", _ascii(title).lower()).strip("-")[:40] or "nguon")
    work_id, n = base, 2
    while db.get(SourceWork, work_id) is not None:
        work_id, n = f"{base}-{n}", n + 1
    db.add(SourceWork(id=work_id, title=title, author=_clean(author, 200) or None, url=_url(url)))
    audit(db, admin, "source.create", "source_work", work_id, {"title": title})
    db.commit()
    return {"id": work_id, "title": title}


def update_source(db: Session, admin: User, work_id: str, title: str, author: str | None, url: str | None) -> dict[str, Any]:
    work = db.get(SourceWork, work_id)
    if work is None:
        raise AdminContentError("SOURCE_NOT_FOUND", "Không có nguồn này.", 404)
    if work_id in SOURCE_REGISTRY:
        raise AdminContentError("SEED_SOURCE", "Nguồn gốc của hệ thống: đổi trong source_registry.py (seed ghi lại mỗi lần khởi động).", 409)
    title = _clean(title, 300)
    if not title:
        raise AdminContentError("SOURCE_INCOMPLETE", "Nguồn cần tên tài liệu.")
    work.title, work.author, work.url = title, _clean(author, 200) or None, _url(url)
    audit(db, admin, "source.update", "source_work", work_id)
    db.commit()
    return {"id": work.id, "title": work.title}


def _own_lesson(db: Session, lesson_id: str) -> Lesson:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise AdminContentError("LESSON_NOT_FOUND", "Không có bài này.", 404)
    if not lesson.id.startswith(("M-", "AI-")):
        # _sync_sources dựng lại liên kết nguồn của bài seed mỗi lần khởi động.
        raise AdminContentError("SEED_LESSON", "Nguồn của bài gốc đổi trong curriculum_specs (seed dựng lại mỗi lần khởi động).", 409)
    return lesson


def link_source(db: Session, admin: User, lesson_id: str, work_id: str, locator: str, note: str | None) -> dict[str, Any]:
    _own_lesson(db, lesson_id)
    if db.get(SourceWork, work_id) is None:
        raise AdminContentError("SOURCE_NOT_FOUND", "Không có nguồn này.", 404)
    locator = _clean(locator, 300) or "toàn bộ"
    exists = db.scalar(select(LessonSource).where(LessonSource.lesson_id == lesson_id, LessonSource.source_work_id == work_id,
                                                  LessonSource.locator == locator))
    if exists is not None:
        raise AdminContentError("SOURCE_LINKED", "Bài đã gắn nguồn này ở đúng vị trí đó.", 409)
    link = LessonSource(lesson_id=lesson_id, source_work_id=work_id, locator=locator, note=_clean(note, 1000) or None)
    db.add(link)
    audit(db, admin, "source.link", "lesson", lesson_id, {"source": work_id, "locator": locator})
    db.commit()
    return {"id": link.id, "lesson_id": lesson_id, "source_id": work_id, "locator": locator}


def unlink_source(db: Session, admin: User, link_id: int) -> None:
    link = db.get(LessonSource, link_id)
    if link is None:
        raise AdminContentError("SOURCE_LINK_NOT_FOUND", "Không có liên kết nguồn này.", 404)
    _own_lesson(db, link.lesson_id)
    if db.scalar(select(LessonSource.id).where(LessonSource.lesson_id == link.lesson_id, LessonSource.id != link.id).limit(1)) is None:
        # Nguyên tắc 11: mỗi bài phải giữ provenance.
        raise AdminContentError("LAST_SOURCE", "Bài phải còn ít nhất một nguồn (nguyên tắc 11). Thêm nguồn khác trước rồi mới gỡ.", 409)
    db.delete(link)
    audit(db, admin, "source.unlink", "lesson", link.lesson_id, {"source": link.source_work_id})
    db.commit()
