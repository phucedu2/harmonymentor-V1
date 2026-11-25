"""Nhóm 4 phần Admin còn thiếu (Phúc 7A, 8A, 25/11/2026): mẫu câu hỏi có tham số (FR-ADM-30), khối ví dụ (FR-ADM-35..37)."""

from __future__ import annotations

from sqlalchemy import select

from app.db.models import AdminAuditLog, Exercise, LessonBlock, MediaFile
from app.db.session import SessionLocal
from tests.test_admin_bai_hoc import A, client, h, new_lesson  # noqa: F401  (fixture dùng lại)
from tests.test_admin_the_on import client as _unused  # noqa: F401

WAV = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 20
TPL = {"template": "chord_tones", "skill_id": "chord.triad_build", "level": "hieu",
       "params": {"roots": "C, Eb", "qualities": "-, m7b5"}}


def test_mau_cau_xem_truoc_roi_luu_va_khong_trung(client, h):
    lid = new_lesson(client, h)
    cat = client.get(f"{A}/question-templates", headers=h).json()
    assert {t["id"] for t in cat["templates"]} >= {"chord_tones", "scale_notes", "interval_name", "roman_numeral"}
    r = client.post(f"{A}/lessons/{lid}/exercise-templates/preview", headers=h, json=TPL)
    assert r.status_code == 200, r.text
    items = {i["prompt"]: i for i in r.json()["items"]}
    assert set(items) == {f"Hợp âm {s} gồm những nốt nào?" for s in ("C", "Cm7b5", "Eb", "Ebm7b5")}
    assert items["Hợp âm Ebm7b5 gồm những nốt nào?"]["answer"] == "Eb–Gb–Bbb–Db"   # Engine tính, không gõ tay
    with SessionLocal() as db:
        assert not db.scalars(select(Exercise).where(Exercise.lesson_id == lid)).all()   # xem trước không ghi gì
    r = client.post(f"{A}/lessons/{lid}/exercise-templates", headers=h, json=TPL)
    assert r.status_code == 201 and len(r.json()["added"]) == 4
    again = client.post(f"{A}/lessons/{lid}/exercise-templates", headers=h, json=TPL)
    assert again.status_code == 201 and again.json()["added"] == [] and len(again.json()["duplicates"]) == 4
    with SessionLocal() as db:
        log = db.scalars(select(AdminAuditLog).where(AdminAuditLog.action == "exercise.from_template")).all()
        assert log


def test_mau_cau_loai_to_hop_engine_khong_dung_duoc_va_bao_loi_tham_so(client, h):
    lid = new_lesson(client, h)
    body = {"template": "roman_numeral", "skill_id": "roman.major_seventh", "level": "hieu",
            "params": {"keys": "C", "chords": "Dm7, F#7"}}
    r = client.post(f"{A}/lessons/{lid}/exercise-templates/preview", headers=h, json=body)
    assert r.status_code == 200, r.text
    out = r.json()
    assert [i["answer"] for i in out["items"]] == ["ii7"] and len(out["skipped"]) == 1   # F#7 ngoài giọng C
    bad = client.post(f"{A}/lessons/{lid}/exercise-templates/preview", headers=h, json={**TPL, "skill_id": "khong-co"})
    assert bad.json()["error"]["code"] == "TEMPLATE_SKILL"
    many = {**TPL, "params": {"roots": "C,D,E,F,G,A,B", "qualities": "-, m, 7, maj7, m7"}}
    assert client.post(f"{A}/lessons/{lid}/exercise-templates/preview", headers=h, json=many).json()["error"]["code"] == "TEMPLATE_TOO_MANY"
    assert client.post(f"{A}/lessons/L01/exercise-templates", headers=h, json=TPL).json()["error"]["code"] == "SEED_LESSON"


def test_khoi_vi_du_hop_am_va_am_giai_do_engine_tinh(client, h):
    lid = new_lesson(client, h)
    r = client.post(f"{A}/lessons/{lid}/examples/chord", headers=h, json={"symbol": "Ebm7b5"})
    assert r.status_code == 201, r.text
    assert r.json()["payload"]["notes"] == ["Eb", "Gb", "Bbb", "Db"] and r.json()["block_type"] == "example_chord"
    r = client.post(f"{A}/lessons/{lid}/examples/scale", headers=h, json={"tonic": "E", "scale_type": "major", "title": "E trưởng"})
    assert r.status_code == 201 and r.json()["payload"]["notes"] == ["E", "F#", "G#", "A", "B", "C#", "D#"]
    assert client.post(f"{A}/lessons/{lid}/examples/chord", headers=h, json={"symbol": "Hxyz"}).json()["error"]["code"] == "EXAMPLE_CHORD"
    assert client.post(f"{A}/lessons/{lid}/examples/scale", headers=h, json={"tonic": "C", "scale_type": "lạ"}).json()["error"]["code"] == "EXAMPLE_SCALE"
    blocks = client.get(f"/api/v1/lessons/{lid}")
    detail = client.get(f"{A}/lessons/{lid}", headers=h).json()
    assert [b["block_type"] for b in detail["blocks"]][1:] == ["example_chord", "example_scale"]
    assert client.post(f"{A}/lessons/L01/examples/chord", headers=h, json={"symbol": "C"}).json()["error"]["code"] == "SEED_LESSON"
    assert blocks is not None


def _upload(client, h, lid, name="vi-du.wav", data=WAV, **form):
    form = {"title": "Nghe C trưởng", "source": "Tự thu", "license": "CC0", **form}
    return client.post(f"{A}/lessons/{lid}/examples/audio", headers=h, data=form, files={"file": (name, data, "audio/wav")})


def test_khoi_vi_du_nghe_kiem_dinh_dang_dung_luong_va_giay_phep(client, h):
    lid = new_lesson(client, h)
    r = _upload(client, h, lid)
    assert r.status_code == 201, r.text
    src = r.json()["payload"]["src"]
    got = client.get(src)
    assert got.status_code == 200 and got.headers["content-type"] == "audio/wav" and got.content == WAV
    assert client.get("/api/v1/media/khong-co").status_code == 404
    assert _upload(client, h, lid, license="").json()["error"]["code"] == "AUDIO_LICENSE"
    assert _upload(client, h, lid, name="a.ogg").json()["error"]["code"] == "AUDIO_TYPE"
    assert _upload(client, h, lid, name="gia.mp3", data=b"khong phai nhac").json()["error"]["code"] == "AUDIO_CONTENT"
    big = b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * (5 * 1024 * 1024)
    assert _upload(client, h, lid, data=big).json()["error"]["code"] == "AUDIO_TOO_LARGE"
    assert _upload(client, h, lid, name="a.mp3", data=b"ID3\x04" + b"\x00" * 30).status_code == 201
    with SessionLocal() as db:
        assert len(db.scalars(select(MediaFile)).all()) >= 2
        assert [b.block_type for b in db.scalars(select(LessonBlock).where(LessonBlock.lesson_id == lid))].count("example_audio") == 2


def test_sua_khoi_vi_du_tai_cho_va_xoa_khoi_nghe_xoa_file(client, h):
    lid = new_lesson(client, h)
    c = client.post(f"{A}/lessons/{lid}/examples/chord", headers=h, json={"symbol": "C"}).json()
    r = client.put(f"{A}/lessons/{lid}/examples/{c['id']}", headers=h, json={"symbol": "Dm7", "note": "ii trong C"})
    assert r.status_code == 200 and r.json()["payload"]["notes"] == ["D", "F", "A", "C"] and r.json()["payload"]["note"] == "ii trong C"
    assert client.put(f"{A}/lessons/{lid}/examples/{c['id']}", headers=h, json={"symbol": "Hxyz"}).json()["error"]["code"] == "EXAMPLE_CHORD"
    s = client.post(f"{A}/lessons/{lid}/examples/scale", headers=h, json={"tonic": "C", "scale_type": "major"}).json()
    r = client.put(f"{A}/lessons/{lid}/examples/{s['id']}", headers=h, json={"tonic": "A", "scale_type": "natural_minor"})
    assert r.json()["payload"]["notes"] == ["A", "B", "C", "D", "E", "F", "G"]
    a = _upload(client, h, lid).json()
    r = client.put(f"{A}/lessons/{lid}/examples/{a['id']}", headers=h, json={"title": "Đổi tên", "source": "Tự thu", "license": "CC0"})
    assert r.json()["payload"]["title"] == "Đổi tên" and r.json()["payload"]["src"] == a["payload"]["src"]
    assert client.put(f"{A}/lessons/{lid}/examples/{a['id']}", headers=h, json={"title": "x"}).json()["error"]["code"] == "AUDIO_LICENSE"
    assert client.put(f"{A}/lessons/{lid}/examples/{lid}-B01", headers=h, json={}).json()["error"]["code"] == "EXAMPLE_NOT_FOUND"
    assert client.get(a["payload"]["src"]).status_code == 200
    assert client.delete(f"{A}/lessons/{lid}/blocks/{a['id']}", headers=h).status_code == 200
    assert client.get(a["payload"]["src"]).status_code == 404   # file đi cùng khối, không mồ côi


def test_loi_nho_tu_ra_soat_tu_dong(client, h):
    lid = new_lesson(client, h)
    bad = {**TPL, "params": {"roots": 5, "qualities": "-"}}
    r = client.post(f"{A}/lessons/{lid}/exercise-templates/preview", headers=h, json=bad)
    assert r.status_code == 422 and r.json()["error"]["code"] == "TEMPLATE_PARAM"   # không còn lỗi 500
    # Byte thứ hai của khung MPEG phải có 3 bit đầu = 111: 0xFF 0x01 không phải MP3.
    assert _upload(client, h, lid, name="gia.mp3", data=b"\xff\x01" + b"\x00" * 30).json()["error"]["code"] == "AUDIO_CONTENT"
    assert _upload(client, h, lid, name="that.mp3", data=b"\xff\xfb" + b"\x00" * 30).status_code == 201
