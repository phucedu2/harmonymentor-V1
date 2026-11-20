"""Tóm tắt CẢ tài liệu, chạy nền, chống trùng kiến thức, bài "Mở rộng", ảnh đại diện (ADR-029). AI giả, không gọi mạng."""

from __future__ import annotations

import hashlib
import json
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.admin import ai_job
from app.admin.router import draft_provider_dep, job_starter_dep
from app.ai.tutor.llm import FakeProvider, LLMUnavailable
from app.auth.avatars import AVATARS, default_avatar
from app.db.models import (AdminAuditLog, AiLessonDraft, AiSummaryJob, ExerciseVersion, Lesson, LessonBlock, MasteryState,
                           SourceDocument, User)
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import auth
from tests.test_admin_ai_tai_lieu import approve_all, env, make_admin  # noqa: F401  (fixture env dùng lại)

LOREM = "Nội dung giải thích chi tiết về chủ đề này cho học sinh. " * 40   # ~2,3 nghìn ký tự: không bị gộp


def page(heading: str | None, body: str = LOREM) -> str:
    return f"{heading}\n{body}" if heading else body


BOOK = [
    "NHẠC LÝ CĂN BẢN\nTác giả A",                                            # 1 bìa
    "MỤC LỤC\nChương 1 Quãng .......... 3\nChương 2 Hợp âm .......... 5\nChương 3 Lời bạt ...... 7\nA ...... 8\nB ..... 9",  # 2
    page("Chương 1. Quãng ghép"),                                            # 3
    page(None),                                                              # 4
    page("Chương 2. Hợp âm chín"),                                           # 5
    page(None),                                                              # 6
    page("Chương 3. Tiểu sử tác giả"),                                       # 7
    "",                                                                      # 8 trống
    "Tài liệu tham khảo\n1. Sách X\n2. Sách Y",                              # 9
]


def lesson_json(title: str, block_title: str, text: str, *, expansion: bool = False, covered: list[str] = ()) -> str:
    return json.dumps({
        "title": title, "objectives": [f"Hiểu {block_title}."], "expansion": expansion, "not_theory": False,
        "concepts": [{"name": block_title, "status": "new"}] + [{"name": c, "status": "covered", "covered_by": "L02"} for c in covered],
        "blocks": [{"title": block_title, "paragraphs": [text], "page": 3}],
        "questions": [{"kind": "true_false", "level": "nho", "prompt": f"{block_title} là kiến thức mới trong tài liệu.",
                       "skill_id": "interval.naming", "answer": "Đúng", "page": 3}],
    })


NOT_THEORY = json.dumps({"title": "x", "objectives": [], "blocks": [], "questions": [], "concepts": [], "not_theory": True})


@pytest.fixture()
def job_env(env, monkeypatch):  # noqa: F811
    client, _ = env
    monkeypatch.setenv("AI_DEDUP_E5", "0")   # TF-IDF tất định, không phụ thuộc máy có mô hình e5 hay không
    sync = {"provider": None}
    app.dependency_overrides[job_starter_dep] = lambda: (lambda job_id, provider: ai_job.run_job(job_id, provider, SessionLocal))

    def use(script):
        fake = FakeProvider(script)
        sync["provider"] = fake
        app.dependency_overrides[draft_provider_dep] = lambda: fake
        return fake

    yield client, use
    app.dependency_overrides.pop(job_starter_dep, None)
    with SessionLocal() as db:
        db.execute(delete(AiSummaryJob))
        db.commit()


def add_doc(admin_headers_user: str, pages: list[str], dropped: list[int] = ()) -> str:
    doc_id = str(uuid4())
    with SessionLocal() as db:
        db.add(SourceDocument(id=doc_id, uploaded_by=admin_headers_user, filename="sach.pdf", kind="pdf", size_bytes=1,
                              sha256=hashlib.sha256(doc_id.encode()).hexdigest(), source_title="Sách thử, 2020", consent=True,
                              pages=pages, relevance_status="accepted", relevance_detail={"dropped_pages": list(dropped)}))
        db.commit()
    return doc_id


def new_admin() -> tuple[str, dict]:
    h = make_admin()
    with SessionLocal() as db:
        uid = db.scalars(select(User.id).where(User.role == "admin").order_by(User.created_at.desc())).first()
    return uid, h


# --- chia phần --------------------------------------------------------------------------------------------

def test_chia_theo_chuong_va_bo_trang_khong_phai_noi_dung():
    parts, skipped = ai_job.plan_parts(BOOK, set())
    assert [(p["page_from"], p["page_to"]) for p in parts] == [(3, 4), (5, 6), (7, 7)]
    assert parts[0]["heading"] == "Chương 1. Quãng ghép" and parts[1]["heading"] == "Chương 2. Hợp âm chín"
    reasons = {s["page"]: s["reason"] for s in skipped}
    assert reasons == {1: "trang bìa", 2: "mục lục", 8: "trang trống hoặc không có chữ", 9: "tài liệu tham khảo"}


def test_chuong_dai_tach_toi_da_15_trang_va_chuong_ngan_duoc_gop():
    long = [page("Chương 1. Âm giai")] + [page(None)] * 19
    parts, _ = ai_job.plan_parts(long, set())
    assert [(p["page_from"], p["page_to"]) for p in parts] == [(1, 10), (11, 20)] or all(len(p["pages"]) <= 15 for p in parts)
    assert all(len(p["pages"]) <= ai_job.PART_PAGES and sum(len(long[n - 1]) for n in p["pages"]) <= ai_job.PART_CHARS for p in parts)
    assert parts[1]["heading"].endswith("(tiếp)")
    short = [page("Bài 1. Nốt", "ngắn " * 20), page("Bài 2. Khóa", "ngắn " * 20), page("Bài 3. Nhịp")]
    merged, _ = ai_job.plan_parts(short, set())
    assert len(merged) == 1 and merged[0]["pages"] == [1, 2, 3]


def test_trang_cong_nhac_ly_da_bo_duoc_ghi_ly_do():
    _, skipped = ai_job.plan_parts(["", page("Chương 1. Quãng")], {1})
    assert skipped == [{"page": 1, "reason": "không liên quan nhạc lý (cổng kiểm tra lúc tải lên)"}]


# --- chạy cả tài liệu -------------------------------------------------------------------------------------

def test_tom_tat_ca_tai_lieu_moi_phan_mot_ban_nhap(job_env):
    client, use = job_env
    uid, h = new_admin()
    doc = add_doc(uid, BOOK)
    fake = use([lesson_json("Quãng ghép", "Quãng ghép là gì", "Quãng ghép vượt quá một quãng tám, ví dụ quãng chín."),
                lesson_json("Hợp âm chín", "Hợp âm chín", "Hợp âm chín thêm quãng chín trên hợp âm bảy.", expansion=True),
                NOT_THEORY])
    r = client.post(f"/api/v1/admin/ai/documents/{doc}/summarize", headers=h)
    assert r.status_code == 200, r.text
    job = r.json()
    assert job["status"] == "done" and job["total"] == 3 and job["finished"] == 3 and job["drafts"] == 2
    assert [p["status"] for p in job["parts"]] == ["done", "done", "not_theory"]
    assert {s["page"] for s in job["skipped_pages"]} == {1, 2, 8, 9}
    # AI nhận danh mục kiến thức đã có (bài chính thức) và chỉ nhận đúng trang của phần.
    system, user = fake.calls[0]
    assert "ĐÃ CÓ" in user and "L01" in user and "[Trang 3]" in user and "[Trang 5]" not in user and "MỤC LỤC" not in user
    with SessionLocal() as db:
        drafts = [db.get(AiLessonDraft, p["draft_id"]) for p in job["parts"][:2]]
        assert drafts[0].content["part"]["heading"] == "Chương 1. Quãng ghép" and drafts[0].content["expansion"] is False
        assert drafts[1].content["expansion"] is True
        assert db.scalar(select(AdminAuditLog.id).where(AdminAuditLog.action == "ai.job.done", AdminAuditLog.target_id == job["id"]))
    # Bấm lại khi việc đã xong thì tạo việc mới; khi đang chạy thì trả việc cũ (xem test tạm dừng).
    listed = client.get("/api/v1/admin/ai/jobs", headers=h).json()
    assert any(j["id"] == job["id"] for j in listed)


def test_kien_thuc_da_co_bi_bo_va_phan_khong_con_gi_moi_thi_khong_tao_bai(job_env):
    client, use = job_env
    uid, h = new_admin()
    with SessionLocal() as db:   # lấy nguyên một khối lý thuyết của bài chính thức L01 làm "kiến thức đã có"
        block = db.scalars(select(LessonBlock).where(LessonBlock.lesson_id == "L01").order_by(LessonBlock.position)).first()
        parts: list[str] = []
        ai_job._strings(block.payload, parts)
        existing = " ".join(parts)[:1200]
        title = (block.payload or {}).get("title") or "Khối L01"
    doc = add_doc(uid, [page("Chương 1. Ôn lại")])
    use([lesson_json("Ôn lại", title, existing, covered=["Khóa Sol"])])
    job = client.post(f"/api/v1/admin/ai/documents/{doc}/summarize", headers=h).json()
    part = job["parts"][0]
    assert part["status"] == "no_new" and part["draft_id"] is None
    by = {d["by"] for d in part["duplicates"]}
    assert by == {"ai", "tfidf"}
    machine = next(d for d in part["duplicates"] if d["by"] == "tfidf")
    assert machine["where"].startswith("L01") and machine["score"] >= ai_job.DUP_BLOCK["tfidf"]


def test_phan_sau_khong_lap_lai_ban_nhap_cua_phan_truoc(job_env):
    client, use = job_env
    uid, h = new_admin()
    doc = add_doc(uid, [page("Chương 1. Quãng ghép"), page("Chương 2. Ôn tập chương 1")])
    same = lesson_json("Quãng ghép", "Quãng ghép là gì", "Quãng ghép vượt quá một quãng tám, ví dụ quãng chín và quãng mười.")
    use([same, same])
    job = client.post(f"/api/v1/admin/ai/documents/{doc}/summarize", headers=h).json()
    assert [p["status"] for p in job["parts"]] == ["done", "no_new"]
    assert job["parts"][1]["duplicates"][0]["where"].startswith("Bản nháp")


def test_het_han_muc_thi_tam_dung_roi_chay_tiep_tu_phan_dang_do(job_env):
    client, use = job_env
    uid, h = new_admin()
    doc = add_doc(uid, BOOK)
    use([lesson_json("Quãng ghép", "Quãng ghép là gì", "Quãng ghép vượt quá một quãng tám."), LLMUnavailable("rate_limited")])
    job = client.post(f"/api/v1/admin/ai/documents/{doc}/summarize", headers=h).json()
    assert job["status"] == "paused" and job["pause_reason"] == "quota"
    assert [p["status"] for p in job["parts"]] == ["done", "pending", "pending"]
    # Bấm "AI soạn" lần nữa khi việc đang dừng: không tạo việc thứ hai.
    again = client.post(f"/api/v1/admin/ai/documents/{doc}/summarize", headers=h).json()
    assert again["id"] == job["id"]
    use([lesson_json("Hợp âm chín", "Hợp âm chín", "Hợp âm chín thêm quãng chín trên hợp âm bảy."), NOT_THEORY])
    resumed = client.post(f"/api/v1/admin/ai/jobs/{job['id']}/resume", headers=h).json()
    assert resumed["status"] == "done" and [p["status"] for p in resumed["parts"]] == ["done", "done", "not_theory"]


def test_hai_phan_loi_lien_tiep_thi_dung_va_chay_tiep_lam_lai_phan_loi(job_env):
    client, use = job_env
    uid, h = new_admin()
    doc = add_doc(uid, BOOK)
    use([LLMUnavailable("timeout"), "khong-phai-json"])
    job = client.post(f"/api/v1/admin/ai/documents/{doc}/summarize", headers=h).json()
    assert job["status"] == "paused" and job["pause_reason"] == "unavailable"
    assert [p["status"] for p in job["parts"]] == ["failed", "failed", "pending"]
    assert "AI trả về sai định dạng" in job["parts"][1]["note"]
    use([lesson_json("A", "Quãng ghép là gì", "Quãng ghép vượt quá một quãng tám."),
         lesson_json("B", "Hợp âm chín", "Hợp âm chín thêm quãng chín."), NOT_THEORY])
    done = client.post(f"/api/v1/admin/ai/jobs/{job['id']}/resume", headers=h).json()
    assert done["status"] == "done" and done["drafts"] == 2


def test_gioi_han_luot_moi_ngay_va_dung_han(job_env, monkeypatch):
    client, use = job_env
    monkeypatch.setattr(ai_job, "DAILY_PART_LIMIT", 1)
    uid, h = new_admin()
    doc = add_doc(uid, BOOK)
    use([lesson_json("A", "Quãng ghép là gì", "Quãng ghép vượt quá một quãng tám.")])
    job = client.post(f"/api/v1/admin/ai/documents/{doc}/summarize", headers=h).json()
    assert job["status"] == "paused" and job["pause_reason"] == "daily_limit" and job["finished"] == 1
    cancelled = client.post(f"/api/v1/admin/ai/jobs/{job['id']}/cancel", headers=h).json()
    assert cancelled["status"] == "cancelled"
    assert client.post(f"/api/v1/admin/ai/jobs/{job['id']}/resume", headers=h).json()["error"]["code"] == "JOB_CANCELLED"


def test_may_chu_khoi_dong_lai_giua_chung_thi_viec_thanh_tam_dung(job_env):
    client, _ = job_env
    uid, h = new_admin()
    doc = add_doc(uid, BOOK)
    parts, skipped = ai_job.plan_parts(BOOK, set())
    parts[0]["status"] = "running"
    job_id = str(uuid4())
    with SessionLocal() as db:
        db.add(AiSummaryJob(id=job_id, document_id=doc, created_by=uid, status="running", parts=parts, skipped_pages=skipped))
        db.commit()
    view = client.get(f"/api/v1/admin/ai/jobs/{job_id}", headers=h).json()
    assert view["status"] == "paused" and view["pause_reason"] == "interrupted" and view["parts"][0]["status"] == "pending"


def test_hoc_vien_khong_goi_duoc_api_tom_tat(job_env):
    client, _ = job_env
    learner = f"hv-{uuid4().hex[:8]}"
    with SessionLocal() as db:
        db.add(User(id=learner, display_name="HV", email=f"{learner}@vd.vn", role="learner", is_active=True))
        db.commit()
    assert client.post(f"/api/v1/admin/ai/documents/{uuid4()}/summarize", headers=auth(learner)).status_code == 403


# --- bài "Mở rộng" và mục "Kiến thức mới" ------------------------------------------------------------------

def test_bai_mo_rong_khong_tinh_thanh_thao_va_khong_vao_quiz_ky_nang(job_env):
    client, use = job_env
    uid, h = new_admin()
    doc = add_doc(uid, [page("Chương 1. Hợp âm chín")])
    use([lesson_json("Hợp âm chín", "Hợp âm chín", "Hợp âm chín thêm quãng chín trên hợp âm bảy.", expansion=True)])
    job = client.post(f"/api/v1/admin/ai/documents/{doc}/summarize", headers=h).json()
    draft_id = job["parts"][0]["draft_id"]
    approve_all(client, h, client.get(f"/api/v1/admin/ai/drafts/{draft_id}", headers=h).json())
    pub = client.post(f"/api/v1/admin/ai/drafts/{draft_id}/publish", headers=h, json={"acknowledge_engine_flags": True})
    assert pub.status_code == 200, pub.text
    lesson_id = pub.json()["lesson_id"]
    with SessionLocal() as db:
        versions = db.scalars(select(ExerciseVersion).where(ExerciseVersion.exercise_id.like(f"{lesson_id}-%"))).all()
        assert versions and all(v.grader_config["counts_for_mastery"] is False for v in versions)
    row = next(l for l in client.get("/api/v1/lessons").json() if l["id"] == lesson_id)
    assert row["ai_generated"] and row["expansion"] and row["published_at"]
    official = next(l for l in client.get("/api/v1/lessons").json() if l["id"] == "L01")
    assert not official["ai_generated"] and not official["expansion"] and official["published_at"] is None

    learner = f"hv-{uuid4().hex[:8]}"
    with SessionLocal() as db:
        db.add(User(id=learner, display_name="HV", email=f"{learner}@vd.vn", role="learner", is_active=True))
        db.commit()
    lesson = client.get(f"/api/v1/lessons/{lesson_id}").json()
    ex = lesson["exercises"][0]
    r = client.post("/api/v1/attempts", headers=auth(learner), json={"exercise_version_id": ex["version_id"], "answer": "Đúng"})
    assert r.status_code == 200, r.text
    with SessionLocal() as db:
        assert db.scalars(select(MasteryState).where(MasteryState.user_id == learner)).all() == []
    quiz = client.get("/api/v1/practice/quiz", params={"skill_id": "interval.naming"}, headers=auth(learner))
    assert quiz.status_code == 200, quiz.text
    assert all(not q["exercise_id"].startswith(lesson_id) for q in quiz.json()["questions"])


def test_quan_tri_vien_tat_nhan_mo_rong_khi_sua_ban_nhap(job_env):
    client, use = job_env
    uid, h = new_admin()
    doc = add_doc(uid, [page("Chương 1. Hợp âm chín")])
    use([lesson_json("Hợp âm chín", "Hợp âm chín", "Hợp âm chín thêm quãng chín.", expansion=True)])
    draft_id = client.post(f"/api/v1/admin/ai/documents/{doc}/summarize", headers=h).json()["parts"][0]["draft_id"]
    d = client.get(f"/api/v1/admin/ai/drafts/{draft_id}", headers=h).json()["content"]
    saved = client.put(f"/api/v1/admin/ai/drafts/{draft_id}", headers=h, json={**{k: d[k] for k in ("title", "objectives", "blocks", "questions")},
                                                                              "expansion": False}).json()
    assert saved["content"]["expansion"] is False and saved["content"]["part"]["heading"] == "Chương 1. Hợp âm chín"
    kept = client.put(f"/api/v1/admin/ai/drafts/{draft_id}", headers=h, json={k: d[k] for k in ("title", "objectives", "blocks", "questions")}).json()
    assert kept["content"]["expansion"] is False   # không gửi trường thì giữ giá trị đang lưu


# --- ảnh đại diện ---------------------------------------------------------------------------------------

def test_anh_dai_dien_mac_dinh_co_dinh_doi_duoc_va_tu_choi_con_vat_la(env):  # noqa: F811
    client, _ = env
    uid = f"av-{uuid4().hex[:8]}"
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="Avatar", email=f"{uid}@vd.vn", role="learner", is_active=True))
        db.commit()
    h = auth(uid)
    me = client.get("/api/v1/me", headers=h).json()
    assert me["avatar"] == default_avatar(uid) and me["avatar"] in AVATARS
    assert client.get("/api/v1/me", headers=h).json()["avatar"] == me["avatar"]   # không nhảy giữa các lần gọi
    other = next(a for a in AVATARS if a != me["avatar"])
    assert client.patch("/api/v1/me", headers=h, json={"avatar": other}).json()["avatar"] == other
    assert client.patch("/api/v1/me", headers=h, json={"avatar": "khung_long"}).status_code == 400
    assert client.patch("/api/v1/me", headers=h, json={"display_name": "Tên mới"}).json()["avatar"] == other
    assert client.patch("/api/v1/me", headers=h, json={"avatar": None}).json()["avatar"] == default_avatar(uid)
