"""Nhóm 2 phần Admin còn thiếu (Phúc 9A, 25/11/2026): kỹ năng tự tạo vào mastery và hệ gợi ý, ngưỡng thành thạo (FR-ADM-23),
bài M- vào kho AI Tutor."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.ai.recommender.vector import build_pool, build_vector
from app.ai.skill_mapping import GROUP_CODES, is_mvp, mapping_of, reload_custom_mapping
from app.db.base import Base
from app.db.models import Lesson, Skill, SkillPrerequisite, User
from app.db.session import SessionLocal
from app.main import app
from tests.test_admin_ky_nang import A, h, skill  # noqa: F401  (h, skill dùng lại)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
    with SessionLocal() as db:
        # Dọn sạch dấu vết: bài M- xóa mềm (phiên bản câu không xóa cứng được), kỹ năng tự tạo và mastery của chúng.
        for lesson in db.scalars(select(Lesson)):
            lesson.sort_key = None
            if lesson.id.startswith("M-") and lesson.deleted_at is None:
                lesson.deleted_at = datetime.now(timezone.utc)
        ids = list(db.scalars(select(Skill.id).where(Skill.id.like("custom.%"))))
        for table in Base.metadata.sorted_tables:
            if "skill_id" in table.c and table.name not in ("skills", "exercises", "exercise_versions"):
                db.execute(delete(table).where(table.c.skill_id.in_(ids)))
        db.execute(delete(SkillPrerequisite).where(SkillPrerequisite.skill_id.in_(ids) | SkillPrerequisite.prerequisite_skill_id.in_(ids)))
        db.execute(delete(Skill).where(Skill.id.in_(ids)))
        db.commit()
    reload_custom_mapping()


def test_ky_nang_tu_tao_phai_chon_nhom_va_duoc_tinh_vao_vector(client, h):
    r = client.post(f"{A}/skills", headers=h, json={"slug": "x1", "name": "Quãng ghép", "group_code": "post_mvp_khac"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "SKILL_GROUP"
    assert client.post(f"{A}/skills", headers=h, json={"slug": "x2", "name": "Quãng ghép"}).status_code == 422
    # Nhóm hậu MVP (jazz_voicing…) bị từ chối: kỹ năng tự tạo chỉ vào 10 nhóm MVP.
    assert client.post(f"{A}/skills", headers=h, json={"slug": "x3", "name": "A", "group_code": "jazz_voicing"}).status_code == 422
    sid = skill(client, h)
    assert is_mvp(sid) and mapping_of(sid) == ("intervals", "intervals")
    vec = build_vector({sid: 0.5, "interval.naming": 0.9})
    i = GROUP_CODES.index("intervals")
    assert vec.assessed[i] and abs(vec.values[i] - 0.7) < 1e-9 and sid in vec.skills[i]   # trung bình cùng nhóm
    pool = build_pool([("u1", sid, 0.4), ("u1", "scale.major", 0.8)])
    assert pool.assessed[0][i] and abs(pool.values[0][i] - 0.4) < 1e-9
    # Đổi nhóm thì đổi chiều; xóa kỹ năng thì không còn được tính.
    assert client.put(f"{A}/skills/{sid}", headers=h, json={"name": "Quãng ghép", "domain": "theory", "group_code": "triads"}).status_code == 200
    assert mapping_of(sid) == ("triads", "triads")
    assert client.delete(f"{A}/skills/{sid}", headers=h).status_code == 204
    assert not is_mvp(sid)
    rows = [a for a in client.get(f"{A}/audit", headers=h).json() if a["action"] == "skill.update"]
    assert rows and rows[0]["detail"]["group"] == {"from": "intervals", "to": "triads"}


def test_ky_nang_tu_tao_co_mastery_va_vao_vector_nguoi_hoc(client, h):
    """Làm đúng câu của kỹ năng tự tạo thì có dòng mastery và có mặt trong vector của người học."""
    from sqlalchemy import select

    from app.db.models import MasteryState
    from app.db.session import SessionLocal
    from app.services.recommendation_service import user_mastery
    from tests.auth_helpers import auth
    from tests.test_admin_bai_hoc import MCQ, new_lesson
    from tests.test_admin_quan_tri import make_user
    sid = skill(client, h)
    lid = new_lesson(client, h)
    q = client.post(f"{A}/lessons/{lid}/exercises", headers=h, json={**MCQ, "skill_id": sid})
    assert q.status_code == 201, q.text
    client.post(f"{A}/lessons/{lid}/visibility", headers=h, json={"hidden": False})
    uid = make_user()
    item = client.get(f"/api/v1/lessons/{lid}").json()["exercises"][0]
    r = client.post("/api/v1/attempts", headers=auth(uid), json={"exercise_version_id": item["version_id"], "answer": "M3"})
    assert r.status_code == 200 and r.json()["correct"]
    with SessionLocal() as db:
        row = db.scalars(select(MasteryState).where(MasteryState.user_id == uid, MasteryState.skill_id == sid)).first()
        assert row is not None and row.score > 0
        assert sid in user_mastery(db, uid)   # hệ gợi ý đọc được kỹ năng này


def test_nguong_thanh_thao_moi_ky_nang_seed_khong_ghi_de(client, h):
    from app.content.seed_data import seed_initial_data
    from app.db.models import AdminAuditLog, Skill
    from app.db.session import SessionLocal
    from sqlalchemy import select
    r = client.put(f"{A}/skills/interval.naming/thresholds", headers=h, json={"ready_threshold": 0.5, "mastery_threshold": 0.9})
    assert r.status_code == 200 and r.json()["changed"] is True
    with SessionLocal() as db:
        seed_initial_data(db)
        db.commit()
        s = db.get(Skill, "interval.naming")
        assert (s.ready_threshold, s.mastery_threshold) == (0.5, 0.9)
        log = db.scalars(select(AdminAuditLog).where(AdminAuditLog.action == "skill.thresholds")).all()
        assert log and log[-1].detail["from"] == {"ready": 0.6, "mastered": 0.8}
    rows = {s["id"]: s for s in client.get(f"{A}/skills", headers=h).json()}
    assert rows["interval.naming"]["ready_threshold"] == 0.5
    for bad in ({"ready_threshold": 0.9, "mastery_threshold": 0.5}, {"ready_threshold": 0, "mastery_threshold": 0.8},
                {"ready_threshold": 0.5, "mastery_threshold": 1.2}):
        assert client.put(f"{A}/skills/interval.naming/thresholds", headers=h, json=bad).json()["error"]["code"] == "THRESHOLD_INVALID"
    assert client.put(f"{A}/skills/khong.co/thresholds", headers=h, json={"ready_threshold": 0.5, "mastery_threshold": 0.9}).status_code == 404
    client.put(f"{A}/skills/interval.naming/thresholds", headers=h, json={"ready_threshold": 0.6, "mastery_threshold": 0.8})


def test_bai_tu_tao_dang_hien_vao_kho_tutor_va_sua_chu_thi_cap_nhat(client, h):
    """Phúc 9A: bài M- vào kho AI Tutor khi hiện, gỡ khi ẩn/xóa; chữ khối sửa và xuất bản được Tutor đọc theo."""
    from app.ai.tutor.chunker import lesson_chunks
    from tests.test_admin_bai_hoc import new_lesson
    lid = new_lesson(client, h)

    def mine():
        return [c for c in lesson_chunks() if c.lesson_id == lid]
    assert not mine()                                     # đang ẩn: chưa vào kho
    out = client.post(f"{A}/lessons/{lid}/visibility", headers=h, json={"hidden": False}).json()
    assert out["tutor_index"]["visible"] is True and mine()
    assert "Quãng ghép lớn hơn một quãng tám đúng" in " ".join(c.text for c in mine())
    # Sửa chữ khối rồi xuất bản: Tutor phải thấy chữ mới (trước đây giữ chữ cũ tới lần hiện/ẩn sau).
    blk = client.get(f"{A}/lessons/{lid}", headers=h).json()["blocks"][0]
    payload = {**blk["payload"], "paragraphs": ["Quãng ghép gồm quãng chín, quãng mười và quãng mười một."]}
    block_id = blk["id"]
    rev = client.put(f"{A}/lessons/{lid}/blocks/{block_id}", headers=h, json={"payload": payload, "note": None}).json()
    client.post(f"{A}/revisions/{rev['revision_id']}/publish", headers=h, json={"acknowledge_engine_flags": True})
    text = " ".join(c.text for c in mine())
    assert "quãng chín" in text and "lớn hơn một quãng tám" not in text
    client.delete(f"{A}/lessons/{lid}", headers=h)        # xóa bài thì gỡ khỏi kho
    assert not mine()
