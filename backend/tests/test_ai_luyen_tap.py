"""AI sinh bài luyện tập từ tài liệu (ADR-028): trắc nghiệm, Đúng/Sai, chọn nhiều, tự luận ngắn, câu mở; trắc nghiệm Engine
ở Luyện tập; ngân hàng "Từ tài liệu"; nhận xét AI cho câu mở. AI giả (FakeProvider), không gọi mạng."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin import ai_questions as aq
from app.admin.router import draft_provider_dep
from app.ai.tutor.llm import FakeProvider
from app.api.ai_tutor import provider_dep
from app.db.models import PracticeAttempt, User
from app.db.session import SessionLocal
from app.main import app
from app.services import open_answer_service
from app.services.practice_mcq import make_options
from app.services.practice_service import grade_practice
from tests.auth_helpers import auth
from tests.test_admin_ai_tai_lieu import approve_all, env, make_admin, new_draft, show  # noqa: F401  (fixture env dùng lại)

SKILLS = {"interval.naming", "chord.seventh_build", "scale.major", "roman.major_seventh", "function.dominant"}
clamp = lambda p: 1  # noqa: E731


def norm(item, **kw):
    return aq.normalize_question(item, SKILLS, clamp, **kw)


# --- Engine kiểm đáp án câu AI soạn ------------------------------------------------------------------

def test_mcq_co_check_engine_chon_dap_an_va_sua_khi_ai_chon_sai():
    q, why = norm({"kind": "mcq", "level": "nho", "prompt": "Quãng từ C lên E là gì?", "skill_id": "interval.naming", "page": 1,
                   "options": ["m3", "M3", "P4", "d4"], "answer": "m3", "check": {"type": "interval", "lower": "C", "upper": "E"},
                   "option_feedback": [{"option": "m3", "why": "m3 chỉ 3 nửa cung."}]})
    # ADR-033: Engine phải sửa đáp án AI chọn thì câu vẫn giữ nhưng bắt duyệt (trước đợt 3: miễn duyệt).
    assert why == "" and q["answer"] == "M3" and q["engine_verified"] and q["needs_review"]
    assert "Engine sửa" in q["engine_note"] and q["option_feedback"] == {"m3": "m3 chỉ 3 nửa cung."}


def test_mcq_engine_khong_thay_dung_mot_phuong_an_thi_loai():
    q, why = norm({"kind": "mcq", "prompt": "Cmaj7 gồm?", "skill_id": "chord.seventh_build", "page": 1,
                   "options": ["C E G", "C E G A", "C Eb G Bb"], "answer": "C E G A", "check": {"type": "chord_tones", "symbol": "Cmaj7"}})
    assert q is None and "0 phương án đúng" in why


def test_dung_sai_engine_kiem_duoc_thi_tu_chon_dap_an():
    q, _ = norm({"kind": "true_false", "prompt": "Hợp âm Cmaj7 gồm các nốt C E G A.", "skill_id": "chord.seventh_build",
                 "page": 1, "answer": "Đúng"})
    assert q["answer"] == "Sai" and q["engine_verified"] and "engine_note" in q
    concept, _ = norm({"kind": "true_false", "prompt": "Hợp âm át tạo cảm giác muốn về chủ.", "skill_id": "function.dominant",
                       "page": 1, "answer": "Đúng"})
    assert concept["answer"] == "Đúng" and concept["needs_review"] and not concept["reviewed"]


def test_chon_nhieu_theo_not_hop_am_do_engine_tinh():
    q, _ = norm({"kind": "multi_select", "prompt": "Chọn các nốt thuộc G7.", "skill_id": "chord.seventh_build", "page": 1,
                 "options": ["G", "B", "D", "F#", "F", "A"], "answers": ["G", "B", "D", "F#"], "check": {"type": "chord_tones", "symbol": "G7"}})
    assert q["answers"] == ["G", "B", "D", "F"] and q["engine_verified"]


def test_tu_luan_ngan_bat_buoc_co_check_va_cau_mo_can_rubric():
    assert norm({"kind": "short", "prompt": "Quãng C–G?", "skill_id": "interval.naming", "page": 1})[0] is None
    short, _ = norm({"kind": "short", "prompt": "Trong C trưởng, G7 là bậc nào?", "skill_id": "roman.major_seventh", "page": 1,
                     "check": {"type": "roman", "key": "C", "chord": "G7"}})
    assert aq.engine_answer(short) == "V7"
    assert norm({"kind": "open", "prompt": "Vì sao?", "skill_id": "function.dominant", "page": 1, "model_answer": "x", "rubric": ["a"]})[0] is None


def test_ai_khong_tu_danh_dau_da_duyet():
    item = {"kind": "open", "prompt": "Vì sao V7 muốn về I?", "skill_id": "function.dominant", "page": 1, "reviewed": True,
            "model_answer": "Vì có tritone giải quyết.", "rubric": ["Nêu tritone", "Nêu nốt cảm"]}
    assert norm(item)[0]["reviewed"] is False
    assert norm(item, trust_review=True)[0]["reviewed"] is True


# --- trắc nghiệm Engine ở Luyện tập ----------------------------------------------------------------

@pytest.mark.parametrize("kind,question", [
    ("interval", {"lower": "C4", "upper": "E4"}), ("interval", {"lower": "F4", "upper": "B4"}),
    ("chord", {"symbol": "F#m7"}), ("chord", {"symbol": "Bb"}), ("scale", {"tonic": "D", "scale_type": "major"}),
    ("scale", {"tonic": "A", "scale_type": "natural_minor"}), ("roman", {"key": "G", "chord": "Am7"}), ("roman", {"key": "F", "chord": "C"}),
])
def test_phuong_an_luyen_tap_dung_mot_cau_dung(kind, question):
    for seed in range(5):
        options = make_options(kind, question, seed)
        assert len(options) == 4 and len(set(options)) == 4
        right = [o for o in options if grade_practice(kind, question, o.split() if kind in ("chord", "scale") else o)["correct"]]
        assert len(right) == 1


def test_api_phuong_an_va_nop_bang_lua_chon(env):
    client, _ = env
    uid = f"lrn-{uuid4().hex[:10]}"
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="HS", email=f"{uid}@example.test", role="learner", is_active=True))
        db.commit()
    h = auth(uid)
    q = {"lower": "D4", "upper": "F#4"}
    options = client.post("/api/v1/practice/options", headers=h, json={"kind": "interval", "question": q}).json()["options"]
    assert "M3" in options
    r = client.post("/api/v1/practice/attempts", headers=h, json={"kind": "interval", "question": q, "answer": "M3", "input": "choice"})
    assert r.status_code == 200 and r.json()["correct"]
    bad = client.post("/api/v1/practice/options", headers=h, json={"kind": "chord", "question": {"symbol": "Hxyz"}})
    assert bad.status_code == 422
    with SessionLocal() as db:
        row = db.scalar(select(PracticeAttempt).where(PracticeAttempt.user_id == uid))
        assert row.question == {"lower": "D4", "upper": "F#4", "input": "choice"}


# --- từ bản nháp tới người học ---------------------------------------------------------------------

FULL = {
    "title": "Hợp âm bảy và quãng",
    "objectives": ["Gọi tên quãng", "Dựng hợp âm bảy"],
    "blocks": [{"title": "Quãng", "paragraphs": ["Quãng C–E là M3, có 4 nửa cung."], "page": 1, "block_ref": 1}],
    "questions": [
        {"kind": "mcq", "level": "nho", "prompt": "Quãng từ C lên E là gì?", "skill_id": "interval.naming", "page": 1, "block_ref": 1,
         "options": ["m3", "M3", "P4", "d4"], "answer": "M3", "check": {"type": "interval", "lower": "C", "upper": "E"},
         "option_feedback": [{"option": "m3", "why": "m3 chỉ có 3 nửa cung, C–E có 4."}]},
        {"kind": "true_false", "level": "hieu", "prompt": "Hợp âm át tạo cảm giác muốn về chủ.", "skill_id": "function.dominant",
         "page": 1, "block_ref": 1, "answer": "Đúng"},
        {"kind": "multi_select", "level": "van_dung", "prompt": "Chọn các nốt thuộc G7.", "skill_id": "chord.seventh_build", "page": 1, "block_ref": 1,
         "options": ["G", "B", "D", "F#", "F", "A"], "answers": ["G", "B", "D", "F"], "check": {"type": "chord_tones", "symbol": "G7"}},
        {"kind": "short", "level": "van_dung", "prompt": "Quãng đi lên từ A tới E là gì?", "skill_id": "interval.naming", "page": 1, "block_ref": 1,
         "check": {"type": "interval", "lower": "A", "upper": "E"}},
        {"kind": "open", "level": "hieu", "prompt": "Vì sao G7 muốn về C?", "skill_id": "function.dominant", "page": 1, "block_ref": 1,
         "model_answer": "G7 có nốt cảm B đi lên C và quãng 3 cung B–F giải quyết vào C–E.",
         "rubric": ["Nêu nốt cảm B lên C", "Nêu tritone B–F giải quyết"]},
    ],
}


@pytest.fixture()
def published(env):
    client, fake = env
    fake.script = [json.dumps(FULL)]
    h = make_admin()
    draft = new_draft(client, h)
    kinds = [q["kind"] for q in draft["content"]["questions"]]
    assert kinds == ["mcq", "true_false", "multi_select", "short", "open"], draft["content"]["dropped_questions"]
    assert [q["needs_review"] for q in draft["content"]["questions"]] == [False, True, False, False, True]
    blocked = client.post(f"/api/v1/admin/ai/drafts/{draft['id']}/publish", headers=h, json={})
    assert blocked.json()["error"]["code"] == "QUESTIONS_NEED_REVIEW" and "câu 2, 5" in blocked.json()["error"]["message"]
    approve_all(client, h, draft)
    r = client.post(f"/api/v1/admin/ai/drafts/{draft['id']}/publish", headers=h, json={})
    assert r.status_code == 200, r.text
    uid = f"lrn-{uuid4().hex[:10]}"
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="HS", email=f"{uid}@example.test", role="learner", is_active=True))
        db.commit()
    show(client, h, r.json()["lesson_id"])
    lesson = client.get(f"/api/v1/lessons/{r.json()['lesson_id']}", headers=auth(uid)).json()
    return client, auth(uid), lesson, {e["prompt"]: e for e in lesson["exercises"]}


def submit(client, h, ex, answer, method=None):
    return client.post("/api/v1/attempts", headers=h, json={"exercise_version_id": ex["version_id"], "answer": answer, "input_method": method})


def test_hoc_sinh_lam_du_cac_dang(published):
    client, h, lesson, by = published
    mcq = by["Quãng từ C lên E là gì?"]
    wrong = submit(client, h, mcq, "m3", "choice").json()
    assert not wrong["correct"] and wrong["feedback"] == "m3 chỉ có 3 nửa cung, C–E có 4."
    assert submit(client, h, mcq, "M3", "choice").json()["correct"]
    tf = by["Hợp âm át tạo cảm giác muốn về chủ."]
    assert tf["options"] == ["Đúng", "Sai"] and submit(client, h, tf, "Đúng", "choice").json()["correct"]
    multi = by["Chọn các nốt thuộc G7."]
    assert multi["allowed_input_methods"] == ["multi_choice"]
    assert not submit(client, h, multi, ["G", "B", "D"], "multi_choice").json()["correct"]
    assert submit(client, h, multi, ["F", "D", "B", "G"], "multi_choice").json()["correct"]
    assert submit(client, h, multi, ["G", "Z"], "multi_choice").status_code == 422
    assert submit(client, h, multi, "G", "choice").status_code == 422
    short = by["Quãng đi lên từ A tới E là gì?"]
    assert not submit(client, h, short, "P4").json()["correct"] and submit(client, h, short, "P5").json()["correct"]
    opened = by["Vì sao G7 muốn về C?"]
    r = submit(client, h, opened, "Vì có nốt cảm.")
    assert r.status_code == 422 and r.json()["error"]["code"] == "OPEN_QUESTION"
    # câu mở không chặn hoàn thành bài: 4 câu tất định đã đúng là đủ
    done = client.post(f"/api/v1/lessons/{lesson['id']}/complete", headers=h)
    assert done.status_code == 200, done.text


def test_cau_mo_ai_nhan_xet_hoac_tu_doi_chieu(published, monkeypatch):
    client, h, _, by = published
    opened = by["Vì sao G7 muốn về C?"]
    body = {"exercise_version_id": opened["version_id"], "answer": "Vì nốt B đi lên C."}
    app.dependency_overrides[provider_dep] = lambda: None
    off = client.post("/api/v1/practice/open-feedback", headers=h, json=body).json()
    assert off["ai_status"] == "off" and off["model_answer"].startswith("G7") and len(off["rubric"]) == 2
    assert off["counts_for_mastery"] is False
    good = json.dumps({"points": [{"point": "x", "met": "yes", "comment": "Bạn đã nêu nốt cảm."},
                                  {"point": "y", "met": "no", "comment": "Chưa nói tới tritone."}], "summary": "Tốt, bổ sung tritone nhé."})
    fake = FakeProvider([good])
    app.dependency_overrides[provider_dep] = lambda: fake
    ok = client.post("/api/v1/practice/open-feedback", headers=h, json=body).json()
    assert ok["ai_status"] == "ok" and [p["met"] for p in ok["ai"]["points"]] == ["yes", "no"]
    assert ok["ai"]["points"][0]["point"] == "Nêu nốt cảm B lên C"   # tên ý lấy từ rubric đã duyệt, không lấy từ AI
    assert "<<<ANSWER>>>" in fake.calls[0][1]
    wrong = json.dumps({"points": [], "summary": "Hợp âm G7 gồm các nốt G B D F#."})
    app.dependency_overrides[provider_dep] = lambda: FakeProvider([wrong])
    assert client.post("/api/v1/practice/open-feedback", headers=h, json=body).json()["ai_status"] == "flagged"
    monkeypatch.setattr(open_answer_service, "DAILY_LIMIT", 0)
    assert client.post("/api/v1/practice/open-feedback", headers=h, json=body).json()["ai_status"] == "quota"
    app.dependency_overrides.pop(provider_dep, None)
    mcq = by["Quãng từ C lên E là gì?"]
    assert client.post("/api/v1/practice/open-feedback", headers=h,
                       json={"exercise_version_id": mcq["version_id"], "answer": "x"}).status_code == 422


def test_ngan_hang_tu_tai_lieu_va_quiz(published):
    client, h, _, by = published
    skills = client.get("/api/v1/practice/bank/skills", headers=h).json()["skills"]
    assert {"skill_id": "interval.naming", "name": skills[[s["skill_id"] for s in skills].index("interval.naming")]["name"],
            "count": 2} in skills
    bank = client.get("/api/v1/practice/bank", headers=h, params={"skill_id": "function.dominant"}).json()
    assert {q["open"] for q in bank["questions"]} == {True, False}
    hard = client.get("/api/v1/practice/bank", headers=h, params={"skill_id": "interval.naming", "level": "kho"}).json()
    assert [q["prompt"] for q in hard["questions"]] == ["Quãng đi lên từ A tới E là gì?"] and hard["questions"][0]["difficulty"] == "van_dung"
    quiz = client.get("/api/v1/practice/quiz", headers=h, params={"skill_id": "function.dominant"}).json()
    prompts = [q["prompt"] for q in quiz["questions"]]
    assert "Vì sao G7 muốn về C?" not in prompts                 # câu mở không vào quiz (không chấm tất định)
    assert "Hợp âm át tạo cảm giác muốn về chủ." in prompts
    assert all("allowed_input_methods" in q for q in quiz["questions"])


def test_ai_sinh_them_cau_cho_ban_nhap(env):
    client, fake = env
    fake.script = [json.dumps(FULL), json.dumps({"questions": [
        FULL["questions"][0],   # trùng câu đã có → bỏ
        {"kind": "short", "level": "nho", "prompt": "Trong C trưởng, Dm7 là bậc nào?", "skill_id": "roman.major_seventh", "page": 1,
         "check": {"type": "roman", "key": "C", "chord": "Dm7"}},
    ]})]
    h = make_admin()
    draft = new_draft(client, h)
    r = client.post(f"/api/v1/admin/ai/drafts/{draft['id']}/questions", headers=h, json={"kinds": ["short"]})
    assert r.status_code == 200, r.text
    qs = r.json()["content"]["questions"]
    assert len(qs) == 6 and qs[-1]["engine_answer"] == "ii7"
    assert any("trùng" in d for d in r.json()["content"]["dropped_questions"])
    system, user = fake.calls[1]
    assert "Câu đã có" in user and "Quãng từ C lên E là gì?" in user and "short" in user and "CHỈ soạn thêm" in system
    app.dependency_overrides[draft_provider_dep] = lambda: None
    assert client.post(f"/api/v1/admin/ai/drafts/{draft['id']}/questions", headers=h, json={}).status_code == 503
