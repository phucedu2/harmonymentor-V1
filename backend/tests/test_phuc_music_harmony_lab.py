"""phuc-music Bước 4: Harmony Lab (FR-17, FR-18).

Khẳng định: gợi ý theo luật dựng nốt bằng Music Engine và xếp độ lạ 0–3, phân tích gọi đúng tên chỗ lạ,
dự án lưu dạng ký hiệu theo phách, chỉ chủ dự án thấy (người khác 404), xóa mềm, Admin có is_test.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.composition.presets import STYLES, drum_events
from app.composition.rules import CompositionInputError, analyze, suggest
from app.db.models import CompositionProject, User
from app.db.session import SessionLocal
from app.main import app
from app.music_engine import chord_tones, diatonic_chords
from app.music_engine.key import all_supported_keys
from tests.auth_helpers import auth

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def _schema():
    with TestClient(app):
        yield


def make_user(role: str = "learner") -> str:
    user_id = "hl-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=user_id, display_name="Sáng tác thử", role=role))
        db.commit()
    return user_id


def by_rule(candidates: list[dict]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for c in candidates:
        out.setdefault(c["rule"], []).append(c["symbol"])
    return out


# --- luật gợi ý -------------------------------------------------------------------------------------

def test_goi_y_cho_bac_v_trong_giong_do():
    found = by_rule(suggest("C", ["C", "Am", "F", "G"], 3))
    assert found["same_function"] == ["Bdim"]
    assert found["borrowed"] == ["Bb"]
    assert found["modal"] == ["Gm"]
    assert found["tritone_sub"] == ["Db7"]
    assert set(found["chromatic_mediant"]) == {"B", "Eb", "E"}


def test_at_phu_nham_o_sau_va_moi_ung_vien_co_ly_do():
    candidates = suggest("C", ["C", "Am", "F", "G"], 0)
    dom = next(c for c in candidates if c["rule"] == "secondary_dominant")
    assert dom["symbol"] == "E7" and dom["label"] == "V7/vi"
    assert "G#" in dom["reason_vi"] and "Am" in dom["reason_vi"]
    assert all(c["reason_vi"] and c["level_label"] for c in candidates)
    assert [c["level"] for c in candidates] == sorted(c["level"] for c in candidates)


def test_not_cua_ung_vien_lay_tu_music_engine():
    for candidate in suggest("Eb", ["Eb", "Cm", "Ab", "Bb"], 3):
        assert candidate["notes"] == [n.name for n in chord_tones(candidate["symbol"])]


def test_gioi_han_do_la_toi_da():
    assert {c["level"] for c in suggest("C", ["C", "Am", "F", "G"], 3, max_level=1)} <= {0, 1}


@pytest.mark.parametrize("signature", all_supported_keys("major"), ids=lambda s: s.tonic.name)
def test_ca_15_giong_truong_khong_loi_va_ky_hieu_doc_lai_duoc(signature):
    key = signature.tonic.name
    chords = [rn.chord.symbol for rn in diatonic_chords(key)]
    prog = [chords[0], chords[5], chords[3], chords[4]]
    for index in range(4):
        for candidate in suggest(key, prog, index):
            chord_tones(candidate["symbol"])  # ký hiệu lưu vào dự án phải đọc lại được


def test_giong_thu_va_hop_am_sai_bao_loi_ro():
    with pytest.raises(CompositionInputError):
        suggest("Am", ["Am"], 0)
    with pytest.raises(CompositionInputError) as err:
        suggest("C", ["C", "Hm"], 1)
    assert "Ô 2" in err.value.message_vi


def test_phan_tich_goi_ten_cho_la_va_canh_bao():
    result = analyze("C", ["C", "E7", "Am", "Ab", "Db7", "C", "F#", None])
    labels = [(b["rule"], b["label"]) for b in result["bars"]]
    assert labels[:6] == [("diatonic", "I"), ("secondary_dominant", "V7/vi"), ("diatonic", "vi"),
                          ("borrowed", "♭VI"), ("tritone_sub", "subV7"), ("diatonic", "I")]
    assert result["bars"][6]["rule"] == "outside" and result["level"] == 3
    assert [w["code"] for w in result["warnings"]] == ["NOT_IN_KEY"]
    assert "ô 4 (Ab, ♭VI)" in result["summary_vi"]


def test_phan_tich_at_khong_giai_quyet():
    result = analyze("C", ["C", "A7", "F", "G"])
    assert any(w["code"] == "UNRESOLVED_DOMINANT" and w["bar"] == 2 for w in result["warnings"])


def test_vong_quen_tai_muc_0():
    assert analyze("G", ["G", "Em", "C", "D"])["level"] == 0


def test_mau_nen_trai_dung_so_o():
    for style in STYLES:
        events = drum_events(style, 4)
        assert max(e["start_beat"] for e in events) < 16
        assert {e["drum"] for e in events} <= {"kick", "snare", "hat"}


# --- API -------------------------------------------------------------------------------------------

def project_body(**over):
    body = {"name": "Vòng thử", "key": "C", "tempo_bpm": 90, "bars": 4, "style": "pop",
            "chords": ["C", "Am", None, "G"]}
    body.update(over)
    return body


def test_options_co_giong_mau_nen_va_muc_do_la():
    data = client.get("/api/v1/composition/options").json()
    assert len(data["keys"]) == 15 and data["keys"][0]["chords"][1] == {"symbol": "Dm", "numeral": "ii"}
    assert [s["id"] for s in data["styles"]] == ["pop", "ballad", "bossa", "lofi"]
    assert [lv["level"] for lv in data["levels"]] == [0, 1, 2, 3]


def test_api_goi_y_can_dang_nhap_va_khong_dung_ai():
    body = {"key": "C", "chords": ["C", "Am", "F", "G"], "index": 3}
    assert client.post("/api/v1/composition/suggestions", json=body).status_code == 401
    res = client.post("/api/v1/composition/suggestions", json=body, headers=auth(make_user()))
    assert res.status_code == 200 and res.json()["ai_used"] is False and res.json()["candidates"]
    bad = client.post("/api/v1/composition/suggestions", json={**body, "index": 2, "chords": ["C", "Am", None, "G"]},
                      headers=auth(make_user()))
    assert bad.status_code == 422


def test_luu_mo_sua_xoa_du_an_theo_chu():
    owner, other = make_user(), make_user()
    created = client.post("/api/v1/projects", json=project_body(), headers=auth(owner))
    assert created.status_code == 201
    project = created.json()
    assert project["chords"] == ["C", "Am", None, "G"] and project["time_signature"] == "4/4"
    assert len(project["drum_events"]) == len(drum_events("pop", 4))
    pid = project["id"]

    assert client.get(f"/api/v1/projects/{pid}", headers=auth(other)).status_code == 404
    assert client.put(f"/api/v1/projects/{pid}", json=project_body(), headers=auth(other)).status_code == 404
    assert client.get("/api/v1/projects", headers=auth(other)).json() == []

    updated = client.put(f"/api/v1/projects/{pid}", headers=auth(owner),
                         json=project_body(bars=5, chords=["C", "E7", "Am", "Ab", "G"], style="lofi", tempo_bpm=75))
    assert updated.status_code == 200 and updated.json()["chords"][3] == "Ab" and updated.json()["bars"] == 5
    assert [p["id"] for p in client.get("/api/v1/projects", headers=auth(owner)).json()] == [pid]

    assert client.delete(f"/api/v1/projects/{pid}", headers=auth(owner)).status_code == 204
    assert client.get(f"/api/v1/projects/{pid}", headers=auth(owner)).status_code == 404
    with SessionLocal() as db:
        row = db.scalar(select(CompositionProject).where(CompositionProject.id == pid))
        assert row is not None and row.deleted_at is not None  # xóa mềm, không mất dữ liệu


def test_du_an_luu_thoi_gian_theo_phach():
    uid = make_user()
    pid = client.post("/api/v1/projects", json=project_body(), headers=auth(uid)).json()["id"]
    with SessionLocal() as db:
        project = db.get(CompositionProject, pid)
        assert [(e.start_beat, e.duration_beats, e.symbol) for e in project.chord_events] == [
            (0.0, 4.0, "C"), (4.0, 4.0, "Am"), (12.0, 4.0, "G")]


# 400 = sai kiểu dữ liệu (lớp xác thực chung của app), 422 = Engine hoặc luật dự án từ chối.
@pytest.mark.parametrize("over,code", [
    ({"tempo_bpm": 200}, 400), ({"bars": 3, "chords": ["C", "F", "G"]}, 400), ({"style": "rock"}, 422),
    ({"chords": ["C", "F"]}, 422), ({"chords": ["C", "Xyz", "F", "G"]}, 422), ({"key": "Am"}, 422),
])
def test_du_an_sai_bi_tu_choi(over, code):
    assert client.post("/api/v1/projects", json=project_body(**over), headers=auth(make_user())).status_code == code


def test_du_an_cua_admin_la_is_test():
    uid = make_user("admin")
    pid = client.post("/api/v1/projects", json=project_body(), headers=auth(uid, "admin")).json()["id"]
    with SessionLocal() as db:
        assert db.get(CompositionProject, pid).is_test is True
