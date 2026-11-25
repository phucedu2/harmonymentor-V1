"""PR 3 hoàn thiện Admin (Phúc 1A, 24/11/2026): kỹ năng, tiên quyết (chặn vòng lặp), nguồn tài liệu.

FR-ADM-18..22, FR-ADM-38. Phần seed chỉ xem (seed ghi lại mỗi lần khởi động); phần Quản trị viên thêm thì sửa/xóa được."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db.models import AdminAuditLog, Skill, SkillPrerequisite, SourceWork
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import auth
from tests.test_admin_quan_tri import make_user

A = "/api/v1/admin"


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
    from app.ai.skill_mapping import reload_custom_mapping
    with SessionLocal() as db:   # dọn kỹ năng/nguồn thử nghiệm
        ids = list(db.scalars(select(Skill.id).where(Skill.id.like("custom.%"))))
        db.execute(delete(SkillPrerequisite).where(SkillPrerequisite.skill_id.in_(ids) | SkillPrerequisite.prerequisite_skill_id.in_(ids)))
        db.execute(delete(Skill).where(Skill.id.in_(ids)))
        db.execute(delete(SourceWork).where(SourceWork.id.like("src-thu-%")))
        db.commit()
    reload_custom_mapping()


@pytest.fixture()
def h():
    return auth(make_user("admin"), "admin")


def skill(client, h, name="Quãng ghép"):
    r = client.post(f"{A}/skills", headers=h, json={"slug": f"thu_{uuid4().hex[:6]}", "name": name, "group_code": "intervals"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_danh_sach_ky_nang_co_tien_quyet_va_bai_dang_dung(client, h):
    rows = {s["id"]: s for s in client.get(f"{A}/skills", headers=h).json()}
    triad = rows["chord.triad_build"]
    assert triad["seed"] and "L01" in triad["lessons"]
    assert set(triad["seed_prerequisites"]) <= set(triad["prerequisites"])


def test_tao_sua_xoa_ky_nang_tu_them_va_khong_sua_ky_nang_seed(client, h):
    sid = skill(client, h)
    assert sid.startswith("custom.")
    r = client.put(f"{A}/skills/{sid}", headers=h, json={"name": "Quãng ghép và quãng đơn", "domain": "theory"})
    assert r.status_code == 200 and r.json()["name"] == "Quãng ghép và quãng đơn"
    seed = client.put(f"{A}/skills/interval.naming", headers=h, json={"name": "Đổi tên"})
    assert seed.status_code == 409 and seed.json()["error"]["code"] == "SEED_SKILL"
    assert client.delete(f"{A}/skills/{sid}", headers=h).status_code == 204
    with SessionLocal() as db:
        assert db.get(Skill, sid) is None
        assert db.scalar(select(AdminAuditLog).where(AdminAuditLog.action == "skill.delete", AdminAuditLog.target_id == sid))


def test_tien_quyet_chan_vong_lap_ca_gian_tiep(client, h):
    a, b, c = skill(client, h, "A"), skill(client, h, "B"), skill(client, h, "C")
    assert client.post(f"{A}/skills/{b}/prerequisites", headers=h, json={"prerequisite_id": a}).status_code == 201   # B cần A
    assert client.post(f"{A}/skills/{c}/prerequisites", headers=h, json={"prerequisite_id": b}).status_code == 201   # C cần B
    loop = client.post(f"{A}/skills/{a}/prerequisites", headers=h, json={"prerequisite_id": c})                    # A cần C: vòng
    assert loop.status_code == 409 and loop.json()["error"]["code"] == "PREREQ_CYCLE"
    self_loop = client.post(f"{A}/skills/{a}/prerequisites", headers=h, json={"prerequisite_id": a})
    assert self_loop.status_code == 409
    assert client.delete(f"{A}/skills/{c}/prerequisites/{b}", headers=h).status_code == 204
    assert client.post(f"{A}/skills/{a}/prerequisites", headers=h, json={"prerequisite_id": c}).status_code == 201   # hết vòng


def test_khong_go_canh_tien_quyet_seed(client, h):
    from app.content.skill_graph import PREREQUISITES
    s, p = PREREQUISITES[0]
    r = client.delete(f"{A}/skills/{s}/prerequisites/{p}", headers=h)
    assert r.status_code == 409 and r.json()["error"]["code"] == "SEED_PREREQ"


def test_ky_nang_dang_duoc_cau_dung_thi_khong_xoa(client, h):
    with SessionLocal() as db:
        used = db.get(Skill, "interval.naming")
        assert used is not None
    r = client.delete(f"{A}/skills/interval.naming", headers=h)
    assert r.status_code == 409   # seed: chặn trước cả khi kiểm câu


def test_nguon_tao_sua_gan_vao_bai_va_giu_it_nhat_mot_nguon(client, h):
    r = client.post(f"{A}/sources", headers=h, json={"title": "Thử Nguồn Nhạc Lý", "author": "Nhóm", "url": "https://example.org/a"})
    assert r.status_code == 201, r.text
    wid = r.json()["id"]
    assert wid.startswith("src-thu-")
    bad = client.post(f"{A}/sources", headers=h, json={"title": "Thử", "url": "javascript:alert(1)"})
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "SOURCE_URL"
    assert client.put(f"{A}/sources/{wid}", headers=h, json={"title": "Thử Nguồn Nhạc Lý (bản 2)"}).status_code == 200
    seed_src = client.get(f"{A}/sources", headers=h).json()
    seed_id = next(s["id"] for s in seed_src if s["seed"])
    assert client.put(f"{A}/sources/{seed_id}", headers=h, json={"title": "x"}).status_code == 409
    # Bài seed: liên kết nguồn do curriculum_specs quản lý.
    assert client.post(f"{A}/lessons/L01/sources", headers=h, json={"source_id": wid}).json()["error"]["code"] == "SEED_LESSON"


def test_gan_va_go_nguon_bai_ai(client, h):
    from app.db.models import Lesson, LessonSource
    lid = f"AI-t{uuid4().hex[:6]}"
    with SessionLocal() as db:
        from sqlalchemy import func
        order = (db.scalar(select(func.max(Lesson.order_index))) or 0) + 1
        db.add(Lesson(id=lid, order_index=order, track="AI soạn từ tài liệu", title="Thử", status="reviewed", objectives=[]))
        db.flush()
        first = LessonSource(lesson_id=lid, source_work_id="admin-thu", locator="trang 1")
        if db.get(SourceWork, "admin-thu") is None:
            db.add(SourceWork(id="admin-thu", title="Thử"))
            db.flush()
        db.add(first)
        db.commit()
        first_id = first.id
    wid = client.post(f"{A}/sources", headers=h, json={"title": "Thử nguồn thứ hai"}).json()["id"]
    link = client.post(f"{A}/lessons/{lid}/sources", headers=h, json={"source_id": wid, "locator": "chương 2"})
    assert link.status_code == 201, link.text
    assert client.post(f"{A}/lessons/{lid}/sources", headers=h, json={"source_id": wid, "locator": "chương 2"}).status_code == 409
    assert client.delete(f"{A}/lesson-sources/{first_id}", headers=h).status_code == 204
    last = client.delete(f"{A}/lesson-sources/{link.json()['id']}", headers=h)
    assert last.status_code == 409 and last.json()["error"]["code"] == "LAST_SOURCE"
    with SessionLocal() as db:
        db.execute(delete(LessonSource).where(LessonSource.lesson_id == lid))
        db.delete(db.get(Lesson, lid))
        db.commit()


def test_nguoi_hoc_bi_chan(client):
    learner = auth(make_user())
    assert client.get(f"{A}/skills", headers=learner).status_code == 403
    assert client.post(f"{A}/sources", headers=learner, json={"title": "x"}).status_code == 403
