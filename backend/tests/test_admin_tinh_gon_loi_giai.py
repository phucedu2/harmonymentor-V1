"""Tinh gọn Admin và lời giải tự sinh (Phúc chốt 27/11/2026: 1A–6A, 8A). AI giả, không gọi mạng.

- 3A: câu AI Quản trị viên đã sửa thì coi như đã duyệt (vẫn phải có lời giải).
- 4A/5A: Music Engine viết lời giải còn thiếu và lời chỉ chỗ sai cho phương án sai (test ở test_ai_soan_bai_dot4 và đây).
- 6A: nút "Tự điền lời giải" cho bản nháp cũ, không tốn lượt Gemini.
- Lỗi quãng kép: đề hỏi quãng kép mà phần kiểm chỉ có C–D thì Engine tính M9, không M2.
"""

from __future__ import annotations

import json

import pytest

from app.admin import ai_questions as aq
from app.db.models import AdminAuditLog, AiLessonDraft
from app.db.session import SessionLocal
from tests.test_admin_ai_tai_lieu import env, make_admin, upload  # noqa: F401  (fixture env dùng lại)

SKILLS = {"interval.naming", "chord.seventh_build"}
COMPOUND = {"kind": "short", "level": "van_dung", "page": 1, "skill_id": "interval.naming",
            "prompt": "Dựa vào phương pháp suy diễn từ quãng đơn, nếu ta có Quãng 2 Trưởng được mở rộng thành quãng kép tương ứng "
                      "trên cơ sở quãng đơn đó, ta sẽ được tên quãng kép nào?",
            "check": {"type": "interval", "lower": "C", "upper": "D"}}


@pytest.fixture(autouse=True)
def _tfidf(monkeypatch):
    monkeypatch.setenv("AI_GROUND_E5", "0")
    monkeypatch.setenv("AI_DEDUP_E5", "0")


def norm(item, **kw):
    return aq.normalize_question(item, SKILLS, lambda p: 1, **kw)


# --- lỗi quãng kép (ảnh 6 của Phúc) -------------------------------------------------------------------------

def test_de_hoi_quang_kep_engine_tinh_m9_khong_phai_m2():
    q, why = norm(COMPOUND)
    assert why == "" and q["check"] == {"type": "interval", "lower": "C4", "upper": "D5"}
    assert aq.engine_answer(q) == "M9" and aq.engine_accepts(q["check"], "M9") and not aq.engine_accepts(q["check"], "M2")
    assert "quãng kép: 2 + 7 = 9" in q["explanation"] and "M9" in q["explanation"]
    assert q["needs_review"] and any("quãng kép" in n for n in q["review_notes"])   # đề lạ: người đọc lại một lần


@pytest.mark.parametrize("lower,upper,want", [("C", "E", "M10"), ("A", "C", "m10"), ("E", "F", "m9"), ("G", "F", "m14")])
def test_quang_kep_tinh_dung_ca_khi_not_tren_thap_hon_ve_chu_cai(lower, upper, want):
    q, _ = norm({**COMPOUND, "prompt": f"Từ {lower} lên {upper} cách một quãng kép, gọi tên quãng kép đó.",
                 "check": {"type": "interval", "lower": lower, "upper": upper}})
    assert aq.engine_answer(q) == want


def test_de_khong_hoi_quang_kep_thi_giu_quang_don():
    q, _ = norm({**COMPOUND, "prompt": "Từ C lên D là quãng gì?"})
    assert q["check"] == {"type": "interval", "lower": "C", "upper": "D"} and aq.engine_answer(q) == "M2"


def test_mcq_quang_kep_engine_chon_m9_va_giai_thich_phuong_an_m2():
    q, why = norm({**COMPOUND, "kind": "mcq", "options": ["M2", "M9", "m9", "P8"], "answer": "M2"})
    assert why == "" and q["answer"] == "M9" and q["engine_note"]
    assert "quãng 2" in q["option_feedback"]["M2"].lower() or "số của quãng" in q["option_feedback"]["M2"].lower()


# --- 3A: Quản trị viên sửa câu thì không phải tick ----------------------------------------------------------

CONCEPT = {"kind": "mcq", "level": "hieu", "page": 1, "skill_id": "interval.naming", "prompt": "Quãng nào nghe ổn định nhất?",
           "options": ["P8", "m2", "A4"], "answer": "P8", "explanation": "P8 trùng tên nốt, nghe hòa hợp nhất."}


def test_cau_ai_chua_sua_van_phai_tick_sua_roi_thi_tu_duyet():
    untouched, _ = norm(CONCEPT, trust_review=True)
    assert untouched["needs_review"] and not untouched["reviewed"]
    edited, _ = norm({**CONCEPT, "edited": True}, trust_review=True)
    assert edited["reviewed"] and edited["edited"]
    # AI không tự gắn cờ "đã sửa" được: chỉ đường Quản trị viên lưu bản nháp (trust_review) mới tin cờ này.
    sneaky, _ = norm({**CONCEPT, "edited": True})
    assert not sneaky["reviewed"] and "edited" not in sneaky
    # Sửa mà vẫn bỏ trống lời giải câu khái niệm: chưa tính là duyệt.
    no_why, _ = norm({**CONCEPT, "edited": True, "explanation": ""}, trust_review=True)
    assert not no_why["reviewed"] and aq.EXPLANATION_NOTE in no_why["review_notes"]


# --- 6A: tự điền lời giải cho bản nháp cũ -------------------------------------------------------------------

def _draft_json() -> str:
    return json.dumps({"title": "Quãng", "objectives": [], "blocks": [
        {"title": "Quãng kép", "paragraphs": ["Quãng kép bằng quãng đơn cộng 7, ví dụ quãng 2 trưởng thành quãng 9 trưởng."], "page": 1}],
        "questions": [{**COMPOUND, "block_ref": 1},
                      {"kind": "mcq", "level": "nho", "page": 1, "block_ref": 1, "skill_id": "interval.naming",
                       "prompt": "Từ C lên E là quãng gì?", "options": ["m3", "M3", "P4"], "answer": "M3",
                       "check": {"type": "interval", "lower": "C", "upper": "E"}, "explanation": "C–E có 4 nửa cung."},
                      {**CONCEPT, "block_ref": 1, "explanation": ""}]})


def test_nut_tu_dien_loi_giai_cho_ban_nhap_cu_khong_goi_ai(env):  # noqa: F811
    client, fake = env
    fake.script = [_draft_json()]
    h = make_admin()
    doc = upload(client, h).json()
    d = client.post(f"/api/v1/admin/ai/documents/{doc['id']}/draft", headers=h, json={"page_from": 1, "page_to": 1}).json()
    calls = len(fake.calls)
    # Giả bản nháp soạn trước 27/11: câu quãng kép còn phần kiểm C–D (M2) và chưa có lời giải.
    with SessionLocal() as db:
        draft = db.get(AiLessonDraft, d["id"])
        old = json.loads(json.dumps(draft.content))
        old["questions"][0].update(check={"type": "interval", "lower": "C", "upper": "D"}, explanation="", reviewed=True)
        draft.content = old
        db.commit()
    r = client.post(f"/api/v1/admin/ai/drafts/{d['id']}/fill-explanations", headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    qs = body["content"]["questions"]
    assert len(fake.calls) == calls                     # không gọi Gemini, không tốn lượt
    assert body["filled"] == 1 and body["still_missing"] == 1
    assert qs[0]["check"]["upper"] == "D5" and "M9" in qs[0]["explanation"]
    assert qs[1]["explanation"] == "C–E có 4 nửa cung."   # lời giải AI đã có thì giữ
    assert not qs[2]["explanation"]                      # câu khái niệm: báo người viết
    with SessionLocal() as db:
        assert db.query(AdminAuditLog).filter(AdminAuditLog.action == "ai.draft.fill_explanations").count() >= 1
    learner_like = client.post(f"/api/v1/admin/ai/drafts/{d['id']}/fill-explanations")
    assert learner_like.status_code in (401, 403)
