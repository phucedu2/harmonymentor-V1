"""ADR-042: bộ đếm lượt Gemini khớp số lần gọi HTTP thật, 429 theo phút không làm dừng việc như hết lượt ngày,
và bảng chất lượng AI soạn bài theo phiên bản prompt. AI giả / client giả, không gọi mạng."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.admin import ai_job, ai_service
from app.ai import budget
from app.ai.tutor import llm
from app.ai.tutor.llm import CallCounter, FakeProvider, GeminiProvider, LLMResult, LLMUnavailable
from app.api import ai_tutor
from app.db.models import AdminAuditLog, ChatMessage, User
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import auth
from tests.test_admin_ai_tai_lieu import env, make_admin, new_draft  # noqa: F401  (fixture env dùng lại)
from tests.test_ai_tom_tat_ca_file import BOOK, NOT_THEORY, add_doc, job_env, lesson_json, new_admin  # noqa: F401


# --- client Gemini giả ------------------------------------------------------------------------------------------

class Err(Exception):
    def __init__(self, code: int, text: str = ""):
        super().__init__(f"{code} {text}")
        self.code = code


class FakeClient:
    """Trả lần lượt: Exception thì ném, chuỗi thì thành câu trả lời. Ghi mô hình của từng lần gọi."""

    def __init__(self, script):
        self.script, self.models_called = list(script), []
        self.models = SimpleNamespace(generate_content=self._gen)

    def _gen(self, model, contents, config):
        self.models_called.append(model)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return SimpleNamespace(text=item, usage_metadata=None, candidates=[])


@pytest.fixture(autouse=True)
def _no_sdk(monkeypatch):
    # _call dựng GenerateContentConfig của SDK; test không cần SDK thật.
    monkeypatch.setattr(GeminiProvider, "_call", lambda self, model, s, u, sc, m=None: self._client.models.generate_content(
        model=model, contents=u, config=None))
    llm._last_call.clear()


def provider(script, **kw):
    sleeps: list[float] = []
    client = FakeClient(script)
    p = GeminiProvider(api_key="x", model="lite", fallback_model="flash", client=client, sleep=sleeps.append, **kw)
    return p, client, sleeps


# --- W1: đếm lần gọi HTTP thật ------------------------------------------------------------------------------------

def test_mo_hinh_du_phong_cung_tinh_la_mot_lan_goi():
    p, client, _ = provider([Err(503), "{}"])
    res = p.generate("s", "u", {})
    assert res.attempts == 2 and client.models_called == ["lite", "flash"]


def test_loi_ca_hai_lan_van_bao_so_lan_goi_da_ton():
    p, _, _ = provider([Err(503), Err(503)])
    with pytest.raises(LLMUnavailable) as e:
        p.generate("s", "u", {})
    assert e.value.attempts == 2 and e.value.reason == "unavailable"


def test_loi_khong_thu_lai_tinh_mot_lan():
    p, _, _ = provider([Err(400)])
    with pytest.raises(LLMUnavailable) as e:
        p.generate("s", "u", {})
    assert e.value.attempts == 1


def test_call_counter_cong_ca_lan_loi():
    inner = FakeProvider([LLMUnavailable("timeout", attempts=2), "{}"])
    c = CallCounter(inner)
    with pytest.raises(LLMUnavailable):
        c.generate("s", "u", {})
    c.generate("s", "u", {})
    assert c.http == 3 and c.model == "fake-llm"


def test_http_calls_tin_cu_va_tin_moi():
    assert budget.http_calls(None) == 0
    assert budget.http_calls({"llm_calls": 0}) == 0
    assert budget.http_calls({"llm_calls": 2}) == 1          # tin trước ADR-042: 1 lượt như cũ
    assert budget.http_calls({"llm_calls": 2, "gemini_http": 4}) == 4
    assert budget.http_calls({"llm_calls": 1, "gemini_http": True}) == 1   # giá trị hỏng: không tin


class AttemptsProvider:
    model = "fake"

    def __init__(self, items):
        self.items = list(items)

    def generate(self, system, user, schema, max_output_tokens=None):
        item = self.items.pop(0)
        if isinstance(item, Exception):
            raise item
        return LLMResult("{}", "fake", 1, 1, 1, attempts=item)


@pytest.fixture()
def db_ready():
    with TestClient(app):   # khởi động app = tạo bảng trên SQLite thử
        yield


def _authoring_rows(target_id: str) -> int:
    with SessionLocal() as db:
        return len(db.scalars(select(AdminAuditLog.id).where(AdminAuditLog.action == budget.CALL_ACTION,
                                                             AdminAuditLog.target_id == target_id)).all())


def test_soan_bai_tru_moi_lan_goi_that_ke_ca_du_phong(db_ready):
    tid = uuid4().hex
    with SessionLocal() as db:
        ai_service.call_json(db, AttemptsProvider([3]), None, ("t", tid), "draft", "s", "u", {})
    assert _authoring_rows(tid) == 3


def test_soan_bai_loi_van_tru_du_so_lan_goi(db_ready):
    tid = uuid4().hex
    with SessionLocal() as db, pytest.raises(LLMUnavailable):
        ai_service.call_json(db, AttemptsProvider([LLMUnavailable("timeout", attempts=2)]), None, ("t", tid), "draft", "s", "u", {})
    assert _authoring_rows(tid) == 2


# --- W2: 429 theo phút --------------------------------------------------------------------------------------------

def test_429_theo_phut_cho_roi_thu_lai_cung_mo_hinh():
    p, client, sleeps = provider([Err(429, "Quota exceeded GenerateRequestsPerMinutePerProjectPerModel-FreeTier"), "{}"],
                                 rate_wait_s=30)
    res = p.generate("s", "u", {})
    assert client.models_called == ["lite", "lite"] and sleeps == [30] and res.attempts == 2


def test_429_theo_phut_lan_hai_thi_dung_khong_dot_mo_hinh_du_phong():
    p, client, _ = provider([Err(429, "PerMinute"), Err(429, "PerMinute")], rate_wait_s=30)
    with pytest.raises(LLMUnavailable) as e:
        p.generate("s", "u", {})
    assert client.models_called == ["lite", "lite"]
    assert (e.value.reason, e.value.scope, e.value.attempts) == ("rate_limited", "minute", 2)


def test_429_het_luot_ngay_thi_sang_mo_hinh_du_phong_khong_cho():
    p, client, sleeps = provider([Err(429, "GenerateRequestsPerDayPerProjectPerModel-FreeTier"), "{}"], rate_wait_s=30)
    p.generate("s", "u", {})
    assert client.models_called == ["lite", "flash"] and 30 not in sleeps


def test_tutor_khong_cho_khi_429():
    p, client, sleeps = provider([Err(429, "PerMinute"), "{}"])   # rate_wait_s = 0: học sinh đang chờ
    p.generate("s", "u", {})
    assert client.models_called == ["lite", "flash"] and sleeps == [1.0]


def test_gian_cach_hai_lan_goi_soan_bai():
    now = [100.0]
    p, _, sleeps = provider(["{}", "{}"], min_interval_s=4.5, clock=lambda: now[0])
    p.generate("s", "u", {})
    now[0] += 1.0
    p.generate("s", "u", {})
    assert sleeps == [pytest.approx(3.5)]


def test_get_provider_soan_bai_bat_gian_cach():
    cfg = SimpleNamespace(ai_enabled=True, gemini_api_key="k", gemini_model="m", gemini_fallback_model="f", ai_timeout_seconds=8)
    import app.ai.tutor.llm as mod
    real = mod.GeminiProvider.__init__
    seen = {}

    def spy(self, **kw):
        seen.update(kw)
        real(self, client=object(), **kw)

    mod.GeminiProvider.__init__ = spy
    try:
        mod.get_provider(cfg, authoring=True)
        assert seen["min_interval_s"] == 4.5 and seen["rate_wait_s"] == 30.0
        seen.clear()
        mod.get_provider(cfg)
        assert "min_interval_s" not in seen
    finally:
        mod.GeminiProvider.__init__ = real


def test_thong_bao_loi_tach_phut_va_ngay():
    assert ai_service.unavailable_error(LLMUnavailable("rate_limited", scope="minute")).code == "AI_RATE_MINUTE"
    assert ai_service.unavailable_error(LLMUnavailable("rate_limited", scope="day")).code == "AI_RATE_DAY"
    assert ai_service.unavailable_error(LLMUnavailable("timeout")).code == "AI_UNAVAILABLE"


def test_viec_nen_429_theo_phut_cho_roi_lam_tiep(job_env, monkeypatch):
    client, use = job_env
    monkeypatch.setattr(ai_job, "MINUTE_WAIT_S", 0.0)
    uid, h = new_admin()
    doc = add_doc(uid, BOOK)
    use([lesson_json("Quãng ghép", "Quãng ghép là gì", "Quãng ghép vượt quá một quãng tám."),
         LLMUnavailable("rate_limited", scope="minute"),
         lesson_json("Hợp âm chín", "Hợp âm chín", "Hợp âm chín thêm quãng chín trên hợp âm bảy."), NOT_THEORY])
    job = client.post(f"/api/v1/admin/ai/documents/{doc}/summarize", headers=h).json()
    assert job["status"] == "done" and [p["status"] for p in job["parts"]] == ["done", "done", "not_theory"]


def test_viec_nen_429_theo_phut_hai_lan_thi_dung_voi_ly_do_rieng(job_env, monkeypatch):
    client, use = job_env
    monkeypatch.setattr(ai_job, "MINUTE_WAIT_S", 0.0)
    uid, h = new_admin()
    doc = add_doc(uid, BOOK)
    use([LLMUnavailable("rate_limited", scope="minute"), LLMUnavailable("rate_limited")])
    job = client.post(f"/api/v1/admin/ai/documents/{doc}/summarize", headers=h).json()
    assert job["status"] == "paused" and job["pause_reason"] == "rate_minute"
    assert job["parts"][0]["status"] == "pending"


# --- Tutor ghi gemini_http -----------------------------------------------------------------------------------------

@pytest.fixture()
def tutor():
    app.dependency_overrides[ai_tutor.embedder_dep] = lambda: None
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(ai_tutor.embedder_dep, None)
    app.dependency_overrides.pop(ai_tutor.provider_dep, None)


def _learner() -> str:
    uid = "adr42-" + uuid4().hex[:10]
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="Học sinh thử", email=f"{uid}@example.test"))
        db.commit()
    return uid


def _ask(c, uid, text) -> dict:
    r = c.post("/api/v1/chat/message", headers=auth(uid), json={"message": text})
    assert r.status_code == 200, r.text
    return r.json()


def test_tutor_vong_soan_lai_tinh_hai_luot(tutor):
    fake = FakeProvider(["không phải json", "vẫn sai"])
    app.dependency_overrides[ai_tutor.provider_dep] = lambda: fake
    body = _ask(tutor, _learner(), "Cmaj7 gồm những nốt nào?")
    with SessionLocal() as db:
        msg = db.get(ChatMessage, body["message_id"])
        assert msg.tool_calls["gemini_http"] == 2 and budget.http_calls(msg.tool_calls) == 2


def test_tutor_loi_mang_tinh_so_lan_goi_that(tutor):
    fake = FakeProvider([LLMUnavailable("timeout", attempts=2)])
    app.dependency_overrides[ai_tutor.provider_dep] = lambda: fake
    body = _ask(tutor, _learner(), "Cmaj7 gồm những nốt nào?")
    with SessionLocal() as db:
        assert db.get(ChatMessage, body["message_id"]).tool_calls["gemini_http"] == 2


def test_tutor_tat_ai_khong_tinh_luot(tutor):
    app.dependency_overrides[ai_tutor.provider_dep] = lambda: None
    body = _ask(tutor, _learner(), "Cmaj7 gồm những nốt nào?")
    with SessionLocal() as db:
        tc = db.get(ChatMessage, body["message_id"]).tool_calls
        assert "gemini_http" not in tc and budget.http_calls(tc) == 0


# --- W4: bảng chất lượng ------------------------------------------------------------------------------------------

def test_bang_chat_luong_theo_phien_ban_prompt(env):  # noqa: F811
    client, _ = env
    h = make_admin()
    draft = new_draft(client, h)
    st = draft["content"]["ai_stats"]
    assert st["kept"] == len(draft["content"]["questions"]) and st["dropped"] >= 3
    # Người duyệt bỏ 1 câu và sửa 1 câu: số chụp lúc soạn giữ nguyên, bảng thấy "bị bỏ" và "đã sửa".
    c = draft["content"]
    qs = [dict(q) for q in c["questions"][:-1]]
    qs[0] = {**qs[0], "explanation": qs[0].get("explanation") or "Lời giải.", "edited": True}
    r = client.put(f"/api/v1/admin/ai/drafts/{draft['id']}", headers=h,
                   json={"title": c["title"], "objectives": c["objectives"], "blocks": c["blocks"], "questions": qs})
    assert r.status_code == 200, r.text
    assert r.json()["content"]["ai_stats"] == st
    rep = client.get("/api/v1/admin/ai/quality", headers=h).json()
    row = next(v for v in rep["versions"] if v["prompt_version"] == c["prompt_version"])
    assert row["drafts"] >= 1 and row["removed_by_reviewer"] >= 1 and row["edited"] >= 1
    assert 0 < row["keep_rate"] < 1 and "authoring" in rep["budget"]


def test_bang_chat_luong_hoc_sinh_bi_chan(env):  # noqa: F811
    client, _ = env
    uid = _learner()
    assert client.get("/api/v1/admin/ai/quality", headers=auth(uid)).status_code == 403
