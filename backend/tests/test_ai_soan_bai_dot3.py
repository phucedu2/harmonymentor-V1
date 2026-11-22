"""Đợt 3 sửa logic AI soạn bài (ADR-033). Mỗi test tái hiện một nghi vấn (N1–N6, V1–V8, H1–H3): chạy trên phuc-music
fb87071 thì ĐỎ, sau khi sửa thì xanh (bằng chứng ở docs/giai-doan/ai-soan-bai-dot3/BAO_CAO.md). AI giả, không gọi mạng."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.admin import ai_index, ai_job, ai_questions as aq, ai_review, ai_service
from app.ai import budget
from app.ai.tutor import retriever
from app.ai.tutor.chunker import lesson_chunks
from app.db.models import AdminAuditLog, AiLessonDraft, AiSummaryJob, ExerciseVersion, SourceWork, User
from app.db.session import SessionLocal
from tests.auth_helpers import auth
from tests.test_admin_ai_tai_lieu import approve_all, env, make_admin, show  # noqa: F401  (fixture env dùng lại)
from tests.test_ai_tom_tat_ca_file import add_doc, job_env, new_admin, page  # noqa: F401

SKILLS = {"interval.naming", "chord.seventh_build", "chord.triad_build", "scale.major", "function.dominant", "roman.major_seventh"}
one = lambda p: 1  # noqa: E731


def norm(item, **kw):
    return aq.normalize_question({"level": "nho", "page": 1, **item}, SKILLS, one, **kw)


# --- N1: ký hiệu trong đề phải khớp phần kiểm ----------------------------------------------------------------

def test_n1_de_lech_check_thi_loai_cau_khong_de_engine_sua_dap_an_dung_thanh_sai():
    q, why = norm({"kind": "mcq", "prompt": "Quãng từ C lên E là quãng gì?", "skill_id": "interval.naming",
                   "options": ["M3", "m3", "P4"], "answer": "M3", "check": {"type": "interval", "lower": "D", "upper": "F"}})
    assert q is None and "không khớp" in why


def test_n1_dung_hop_am_de_am7_ma_ky_hieu_c_thi_loai():
    q, why = norm({"kind": "build_chord", "prompt": "Dựng hợp âm Am7", "skill_id": "chord.seventh_build", "symbol": "C"})
    assert q is None and "không khớp" in why
    ok, _ = norm({"kind": "build_chord", "prompt": "Dựng hợp âm Am7", "skill_id": "chord.seventh_build", "symbol": "Am7"})
    assert ok is not None and not ok["needs_review"] or ok["review_notes"] == ["Câu chưa gắn với khối lý thuyết nào của bài."]


def test_n1_de_viet_ten_not_tieng_viet_van_doi_chieu_duoc():
    q, why = norm({"kind": "short", "prompt": "Quãng từ Đô lên Mi là gì?", "skill_id": "interval.naming",
                   "check": {"type": "interval", "lower": "C", "upper": "E"}})
    assert why == "" and q["engine_verified"] and not q["needs_review"]


def test_n1_de_khong_neu_ky_hieu_thi_giu_cau_nhung_bat_duyet():
    q, _ = norm({"kind": "short", "prompt": "Quãng ba trưởng viết tắt là gì?", "skill_id": "interval.naming",
                 "check": {"type": "interval", "lower": "C", "upper": "E"}})
    assert q is not None and q["needs_review"] and "không nêu ký hiệu" in q["review_notes"][0]


def test_n1_engine_phai_sua_dap_an_ai_thi_bat_duyet():
    q, _ = norm({"kind": "mcq", "prompt": "Quãng từ C lên E là gì?", "skill_id": "interval.naming",
                 "options": ["m3", "M3", "P4"], "answer": "m3", "check": {"type": "interval", "lower": "C", "upper": "E"}})
    assert q["answer"] == "M3" and q["engine_verified"] and q["needs_review"] and "Engine sửa" in q["engine_note"]


# --- N2: câu Đúng/Sai chỉ Engine quyết khi mọi vế được kiểm --------------------------------------------------

def test_n2_dung_sai_lan_khai_niem_thi_khong_mien_duyet():
    q, _ = norm({"kind": "true_false", "prompt": "Hợp âm C gồm C E G và là hợp âm thứ.", "skill_id": "chord.triad_build",
                 "answer": "Sai"})
    assert q["answer"] == "Sai" and not q["engine_verified"] and q["needs_review"]


def test_n2_phu_dinh_thi_engine_khong_ket_luan():
    assert aq.statement_truth("Hợp âm Cmaj7 không gồm các nốt C E G A.") is None
    assert aq.statement_truth("Hợp âm Cmaj7 gồm các nốt C E G A.") is False
    assert aq.statement_truth("Hợp âm Cmaj7 gồm các nốt C E G B.") is True
    # Vế sai + vế khái niệm: cả câu "A và B" vẫn chắc chắn sai.
    assert aq.statement_truth("Hợp âm Cmaj7 gồm các nốt C E G A và là hợp âm trưởng.") is False


# --- H3: kỹ năng phải khớp loại kiểm -------------------------------------------------------------------------

def test_h3_ky_nang_khong_khop_loai_kiem_thi_bat_duyet():
    q, _ = norm({"kind": "short", "prompt": "Quãng từ C lên E là gì?", "skill_id": "chord.seventh_build",
                 "check": {"type": "interval", "lower": "C", "upper": "E"}})
    assert q["engine_verified"] and q["needs_review"] and any("Kỹ năng" in n for n in q["review_notes"])
    assert not ai_service.counts_for_mastery({**q, "block_ref": 1})
    assert ai_service.counts_for_mastery({**q, "block_ref": 1, "reviewed": True})


# --- N4/V8: cờ trang sai, bám nguồn, chép nguyên văn, hình ------------------------------------------------------

SOURCE = ("Quãng là khoảng cách cao độ giữa hai nốt nhạc. Quãng ba trưởng gồm bốn nửa cung, ví dụ từ C lên E. "
          "Quãng ba thứ gồm ba nửa cung, ví dụ từ A lên C. Xem ví dụ 3.2 trên khuông nhạc để nghe sự khác nhau.")
OTHER = "Nhịp ba bốn có ba phách mỗi ô nhịp, phách đầu mạnh. Điệu valse dùng nhịp ba bốn."


def _content(paragraph: str, page: int = 1, **block) -> dict:
    return {"title": "T", "objectives": [], "questions": [], "dropped_questions": [],
            "blocks": [{"title": "Quãng ba", "paragraphs": [paragraph], "page": page, **block}]}


def test_n4_trang_ngoai_phan_gan_co_khong_kep_lang_le():
    with SessionLocal() as db:
        c = ai_service.normalize_content(db, {"title": "T", "blocks": [{"title": "Quãng", "paragraphs": ["x y z"], "page": 9}],
                                              "questions": []}, 1, 2)
    assert c["blocks"][0]["page"] == 1 and c["blocks"][0]["page_claimed"] == 9
    flags = ai_review.review_flags([SOURCE, OTHER], c, 1, 2)
    assert "page_out_of_range" in {f["type"] for f in flags}


def test_n4_cho_chep_nguyen_van_va_bam_nguon():
    copied = "Quãng ba trưởng gồm bốn nửa cung, ví dụ từ C lên E. Quãng ba thứ gồm ba nửa cung, ví dụ từ A lên C."
    kinds = {f["type"] for f in ai_review.review_flags([SOURCE, OTHER], _content(copied), 1, 2)}
    assert "verbatim" in kinds
    own = "Khoảng cách giữa hai nốt gọi là quãng; quãng ba trưởng rộng bốn nửa cung còn quãng ba thứ ba nửa cung."
    kinds = {f["type"] for f in ai_review.review_flags([SOURCE, OTHER], _content(own), 1, 2)}
    assert "verbatim" not in kinds and "low_grounding" not in kinds
    made_up = "Hợp âm bảy át giải quyết về chủ qua nốt cảm, thường dùng ở cuối câu nhạc pop."
    flags = ai_review.review_flags([SOURCE, OTHER], _content(made_up), 1, 2)
    assert "low_grounding" in {f["type"] for f in flags}


def test_v8_nhac_toi_vi_du_hinh_thi_gan_co():
    flags = ai_review.review_flags([SOURCE], _content("Xem ví dụ 3.2 để thấy quãng ba trưởng rộng hơn quãng ba thứ."), 1, 1)
    kinds = {f["type"] for f in flags}
    assert {"figure_ref", "source_figure"} <= kinds


def test_n4_xuat_ban_bi_chan_toi_khi_doi_chieu_tung_co(env):  # noqa: F811
    client, fake = env
    h = make_admin()
    doc = client.post("/api/v1/admin/ai/documents/text", headers=h, json={
        "text": SOURCE + "\n\n" + OTHER, "source_title": "Sách thử", "consent": True}).json()
    fake.script = [json.dumps({"title": "Quãng ba", "objectives": [], "blocks": [
        {"title": "Quãng ba", "paragraphs": ["Hợp âm bảy át giải quyết về chủ qua nốt cảm ở cuối câu nhạc."], "page": 7}],
        "questions": [{"kind": "short", "level": "nho", "prompt": "Quãng từ C lên E là gì?", "skill_id": "interval.naming",
                       "check": {"type": "interval", "lower": "C", "upper": "E"}, "page": 1, "block_ref": 1}]})]
    d = client.post(f"/api/v1/admin/ai/documents/{doc['id']}/draft", headers=h, json={"page_from": 1, "page_to": 1}).json()
    assert {"page_out_of_range", "low_grounding"} <= {f["type"] for f in d["flags"]}
    r = client.post(f"/api/v1/admin/ai/drafts/{d['id']}/publish", headers=h, json={})
    assert r.status_code == 409 and r.json()["error"]["code"] == "REVIEW_FLAGS"
    approve_all(client, h, d)
    assert client.post(f"/api/v1/admin/ai/drafts/{d['id']}/publish", headers=h, json={}).status_code == 200


# --- N6 + N5 + H2: xuất bản ẩn, xem như học sinh, hiện thì nạp kho Tutor ----------------------------------------

def _learner() -> dict:
    uid = f"lrn-{uuid4().hex[:10]}"
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="HS", email=f"{uid}@example.test", role="learner", is_active=True))
        db.commit()
    return auth(uid)


def _published(client, fake, h, paragraph="Quãng tăng hai nghe giống quãng ba thứ nhưng viết khác tên nốt, gặp trong âm giai thứ hòa thanh."):
    doc = client.post("/api/v1/admin/ai/documents/text", headers=h, json={
        "text": "Quãng tăng hai xuất hiện trong âm giai thứ hòa thanh, giữa bậc sáu và bậc bảy. " * 3,
        "source_title": "Sách thử N5", "source_note": "bản dịch 2019", "consent": True}).json()
    fake.script = [json.dumps({"title": "Quãng tăng hai", "objectives": [], "blocks": [
        {"title": "Quãng tăng hai", "paragraphs": [paragraph], "page": 1}],
        "questions": [{"kind": "short", "level": "nho", "prompt": "Quãng từ C lên E là gì?", "skill_id": "interval.naming",
                       "check": {"type": "interval", "lower": "C", "upper": "E"}, "page": 1, "block_ref": 1}]})]
    d = client.post(f"/api/v1/admin/ai/documents/{doc['id']}/draft", headers=h, json={"page_from": 1, "page_to": 1}).json()
    approve_all(client, h, d)
    r = client.post(f"/api/v1/admin/ai/drafts/{d['id']}/publish", headers=h, json={})
    assert r.status_code == 200, r.text
    return r.json()["lesson_id"]


def test_n6_xuat_ban_tao_bai_an_xem_truoc_roi_moi_hien(env):  # noqa: F811
    client, fake = env
    h = make_admin()
    lesson_id = _published(client, fake, h)
    lh = _learner()
    assert all(row["id"] != lesson_id for row in client.get("/api/v1/lessons").json())
    assert client.get(f"/api/v1/lessons/{lesson_id}", headers=lh).status_code == 404
    assert client.get(f"/api/v1/lessons/{lesson_id}", params={"preview": 1}, headers=lh).status_code == 404   # học sinh không xem trước được
    preview = client.get(f"/api/v1/lessons/{lesson_id}", params={"preview": 1}, headers=h)
    assert preview.status_code == 200 and preview.json()["exercises"]
    assert client.post(f"/api/v1/lessons/{lesson_id}/start", headers=h).status_code == 200   # Quản trị viên làm thử (is_test)
    assert client.post(f"/api/v1/lessons/{lesson_id}/start", headers=lh).status_code == 404
    out = show(client, h, lesson_id)
    assert out["hidden"] is False and out["tutor_index"]["visible"] and out["tutor_index"]["chunks"] >= 1
    assert client.get(f"/api/v1/lessons/{lesson_id}", headers=lh).status_code == 200


def test_n5_bai_ai_dang_hien_vao_kho_tutor_an_thi_go(env):  # noqa: F811
    client, fake = env
    h = make_admin()
    lesson_id = _published(client, fake, h)
    assert all(c.lesson_id != lesson_id for c in lesson_chunks())   # đang ẩn: chưa vào kho
    show(client, h, lesson_id)
    mine = [c for c in lesson_chunks() if c.lesson_id == lesson_id]
    assert mine and mine[0].source == "Sách thử N5 · trang 1"
    hit = retriever.retrieve("quãng tăng hai trong âm giai thứ hòa thanh", None, top_k=4, bm25_min_score=0.0)
    assert hit.hits and hit.hits[0].chunk.lesson_id == lesson_id
    r = client.post(f"/api/v1/admin/lessons/{lesson_id}/visibility", headers=h, json={"hidden": True}).json()
    assert r["tutor_index"]["visible"] is False and r["tutor_index"]["chunks"] == 0
    assert all(c.lesson_id != lesson_id for c in lesson_chunks())
    with SessionLocal() as db:   # H2: ghi chú nguồn không bị dùng làm tên tác giả
        assert db.get(SourceWork, f"doc-{db.scalar(select(AiLessonDraft.document_id).where(AiLessonDraft.published_lesson_id == lesson_id))[:8]}").author is None


def test_n5_qdrant_bat_thi_nap_khi_hien_go_khi_an(env, monkeypatch):  # noqa: F811
    client, fake = env
    h = make_admin()
    lesson_id = _published(client, fake, h)

    class Store:
        def __init__(self):
            self.points, self.deleted = {}, []

        def delete_lesson(self, source, lid):
            self.deleted.append(lid)
            self.points = {k: v for k, v in self.points.items() if v.payload["lesson_id"] != lid}

        def upsert(self, records, vectors, batch=64):
            self.points.update({r.id: r for r in records})
            return len(records)

    store = Store()
    monkeypatch.setenv("QDRANT_URL", "http://qdrant.test:6333")
    monkeypatch.setenv("RAG_ENABLED", "1")
    monkeypatch.setenv("RAG_EMBEDDER", "fake")
    monkeypatch.setattr("app.services.ai_pipeline._store", lambda cfg: store)
    out = show(client, h, lesson_id)["tutor_index"]
    assert out["qdrant"] == "indexed" and out["qdrant_points"] >= 1
    assert all(p.payload["lesson_id"] == lesson_id and p.payload["source"] == "lessons" for p in store.points.values())
    out = client.post(f"/api/v1/admin/lessons/{lesson_id}/visibility", headers=h, json={"hidden": True}).json()["tutor_index"]
    assert out["qdrant"] == "removed" and not store.points


# --- V5: một bộ đếm theo khóa Gemini ------------------------------------------------------------------------------

def test_v5_han_muc_chia_cho_soan_bai_va_tutor(monkeypatch):
    monkeypatch.setenv("GEMINI_DAILY_BUDGET", "30")
    monkeypatch.delenv("GEMINI_AUTHORING_SHARE", raising=False)
    assert budget.limit("authoring") == 12 and budget.limit("tutor") == 18
    monkeypatch.setenv("GEMINI_DAILY_BUDGET", "0")
    assert budget.limit("authoring") is None


def test_v5_viec_nen_khong_co_nguoi_tao_van_bi_dem(monkeypatch):
    with SessionLocal() as db:
        before = budget.used(db, "authoring")
        budget.record_authoring(db, None, "ai_document", "x", "part:1")
        db.commit()
        assert budget.used(db, "authoring") == before + 1
        monkeypatch.setenv("GEMINI_DAILY_BUDGET", str(before + 1))
        monkeypatch.setenv("GEMINI_AUTHORING_SHARE", "1")
        with pytest.raises(budget.BudgetExceeded):
            budget.require(db, "authoring")
        db.execute(delete(AdminAuditLog).where(AdminAuditLog.target_id == "x", AdminAuditLog.action == budget.CALL_ACTION))
        db.commit()


# --- V6: JSON hỏng thử lại 1 lần; V7: không cắt lặng lẽ -----------------------------------------------------------

GOOD_ONE = json.dumps({"title": "Quãng", "objectives": [], "blocks": [{"title": "Quãng", "paragraphs": ["Quãng C lên E là M3."], "page": 1}],
                       "questions": []})


def test_v6_json_hong_lan_dau_thi_thu_lai_mot_lan(env):  # noqa: F811
    client, fake = env
    h = make_admin()
    doc = client.post("/api/v1/admin/ai/documents/text", headers=h, json={"text": SOURCE, "source_title": "S", "consent": True}).json()
    n = len(fake.calls)
    fake.script = list(fake.calls) + ["không phải JSON", GOOD_ONE]   # FakeProvider đếm theo tổng số lời gọi
    r = client.post(f"/api/v1/admin/ai/documents/{doc['id']}/draft", headers=h, json={"page_from": 1, "page_to": 1})
    assert r.status_code == 200, r.text
    assert len(fake.calls) == n + 2 and "không phải JSON hợp lệ" in fake.calls[-1][1]


def test_v7_qua_gioi_han_chu_thi_thu_hep_trang_va_bao(env):  # noqa: F811
    client, fake = env
    h = make_admin()
    doc_id = add_doc(_admin_id(), ["Quãng ba trưởng. " * 600, "Quãng ba thứ. " * 600])
    fake.script = list(fake.calls) + [GOOD_ONE]
    d = client.post(f"/api/v1/admin/ai/documents/{doc_id}/draft", headers=h, json={"page_from": 1, "page_to": 2}).json()
    assert d["page_to"] == 1 and "trang 2–2 chưa được soạn" in d["content"]["truncated"]
    assert "truncated" in {f["type"] for f in d["flags"]}
    assert "[Trang 2]" not in fake.calls[-1][1]


def _admin_id() -> str:
    with SessionLocal() as db:
        return db.scalars(select(User.id).where(User.role == "admin").order_by(User.created_at.desc())).first()


# --- H1: sửa nháp kẹp trang theo phần của bản nháp ---------------------------------------------------------------

def test_h1_sua_nhap_trang_ngoai_khoang_ban_nhap_thi_gan_co(env):  # noqa: F811
    client, fake = env
    h = make_admin()
    doc_id = add_doc(_admin_id(), [SOURCE, OTHER, OTHER])
    fake.script = list(fake.calls) + [GOOD_ONE]
    d = client.post(f"/api/v1/admin/ai/documents/{doc_id}/draft", headers=h, json={"page_from": 1, "page_to": 1}).json()
    c = d["content"]
    saved = client.put(f"/api/v1/admin/ai/drafts/{d['id']}", headers=h, json={
        "title": c["title"], "objectives": c["objectives"], "questions": c["questions"],
        "blocks": [{**c["blocks"][0], "page": 3}]}).json()
    assert saved["content"]["blocks"][0]["page"] == 1 and saved["content"]["blocks"][0]["page_claimed"] == 3


# --- N3, V1, V2: việc chạy nền ------------------------------------------------------------------------------------

def _l01_block_text() -> tuple[str, str]:
    from app.db.models import LessonBlock

    with SessionLocal() as db:
        block = db.scalars(select(LessonBlock).where(LessonBlock.lesson_id == "L01").order_by(LessonBlock.position)).first()
        parts: list[str] = []
        ai_job._strings(block.payload, parts)
        return (block.payload or {}).get("title") or "Khối L01", " ".join(parts)[:1200]


def test_n3_bo_khoi_trung_thi_bo_ca_cau_hoi_cua_khoi(job_env):  # noqa: F811
    client, use = job_env
    uid, h = new_admin()
    title, existing = _l01_block_text()
    doc = add_doc(uid, [page("Chương 1. Ôn và mở rộng", existing + " " + "Quãng tăng hai nằm giữa bậc sáu và bảy của thứ hòa thanh. " * 20)])
    use([json.dumps({"title": "Ôn và mở rộng", "objectives": [], "not_theory": False, "concepts": [],
                     "blocks": [{"title": title, "paragraphs": [existing], "page": 1},
                                {"title": "Quãng tăng hai", "paragraphs": ["Quãng tăng hai nằm giữa bậc sáu và bậc bảy của âm giai thứ hòa thanh."], "page": 1}],
                     "questions": [{"kind": "open", "level": "hieu", "prompt": "Câu về khối cũ đã bỏ?", "skill_id": "interval.naming",
                                    "model_answer": "x", "rubric": ["a", "b"], "page": 1, "block_ref": 1},
                                   {"kind": "open", "level": "hieu", "prompt": "Quãng tăng hai nằm ở đâu?", "skill_id": "interval.naming",
                                    "model_answer": "Giữa bậc 6 và 7.", "rubric": ["bậc 6", "bậc 7"], "page": 1, "block_ref": 2}]})])
    job = client.post(f"/api/v1/admin/ai/documents/{doc}/summarize", headers=h).json()
    part = job["parts"][0]
    assert part["status"] == "done", part
    with SessionLocal() as db:
        content = db.get(AiLessonDraft, part["draft_id"]).content
    assert [b["title"] for b in content["blocks"]] == ["Quãng tăng hai"]
    assert [q["prompt"] for q in content["questions"]] == ["Quãng tăng hai nằm ở đâu?"]
    assert content["questions"][0]["block_ref"] == 1   # đánh số lại sau khi bỏ khối 1
    assert any("đã bỏ vì trùng" in d for d in content["dropped_questions"])
    assert [row["node"] for row in part["log"]] == ["extract", "retrieve", "generate", "dedup", "validate", "flags", "draft"]


def test_v1_v2_ngu_canh_da_co_la_noi_dung_doan_giong_nhat_va_thay_nhap_phan_truoc(job_env):  # noqa: F811
    client, use = job_env
    uid, h = new_admin()
    first = "Quãng ghép vượt quá một quãng tám, ví dụ quãng chín bằng quãng hai cộng một quãng tám."
    doc = add_doc(uid, [page("Chương 1. Quãng ghép", "Quãng ghép là quãng lớn hơn quãng tám đúng. " * 50),
                        page("Chương 2. Ôn quãng ghép", "Ôn lại quãng ghép, quãng chín, quãng mười. " * 50)])
    reply = lambda title: json.dumps({"title": title, "objectives": [], "not_theory": False, "concepts": [],  # noqa: E731
                                      "blocks": [{"title": "Quãng ghép", "paragraphs": [first], "page": 1}], "questions": []})
    fake = use([reply("Quãng ghép"), reply("Ôn quãng ghép")])
    client.post(f"/api/v1/admin/ai/documents/{doc}/summarize", headers=h)
    _, user1 = fake.calls[0]
    _, user2 = fake.calls[1]
    assert "(còn nữa)" not in user1 and "ĐÃ CÓ" in user1
    assert "Bản nháp “Quãng ghép”" in user2 and first[:60] in user2   # V2: phần 2 thấy nội dung nháp phần 1
