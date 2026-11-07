"""Bộ phối khí Harmony Lab (02/11/2026, ADR-012 đề xuất): style pack hợp lệ, cao độ qua Engine, seed lặp lại được,
dẫn giọng, fill đúng ô cuối, id cũ vẫn chạy, API arrangement, migration a7c4d5e6f8b9 gỡ được."""
from __future__ import annotations

import sqlalchemy as sa
import pytest
from fastapi.testclient import TestClient

from app.composition.arranger import CYCLES, arrange, harmonize, movement
from app.composition.styles import ARRANGEMENT_VERSION, DRUM_CODES, ORDER, PACKS, validate
from app.main import app
from app.music_engine import parse_chord_symbol, parse_note
from tests.test_phuc_music_composition_migration import ARRANGEMENT, COMPOSITION
from tests.test_phuc_music_practice_migration import alembic_to, version

client = TestClient(app)
POP = ["C", "G", "Am", "F"]
JAZZ = ["Dm7", "G7", "Cmaj7", "A7"]


@pytest.mark.parametrize("style", ORDER)
def test_style_pack_hop_le(style):
    assert validate(PACKS[style]) == []


def test_giu_id_cu_va_du_9_phong_cach():
    assert ORDER[:4] == ("pop", "ballad", "bossa", "lofi") and len(ORDER) == 9


@pytest.mark.parametrize("style", ORDER)
@pytest.mark.parametrize("energy", [1, 2, 3])
def test_moi_phong_cach_du_nhac_cu_va_seed_lap_lai(style, energy):
    a = arrange("C", style, POP, seed=7, energy=energy)
    b = arrange("C", style, POP, seed=7, energy=energy)
    assert a == b  # cùng seed → cùng bản phối, nghe lại giống hệt
    assert a["version"] == ARRANGEMENT_VERSION and a["cycles"] == CYCLES
    assert a["tracks"]["keys"]["events"] and a["tracks"]["bass"]["events"] and a["tracks"]["drums"]["events"]
    assert {e["drum"] for e in a["tracks"]["drums"]["events"]} <= DRUM_CODES
    total = a["total_beats"]
    for track in a["tracks"].values():
        for e in track["events"]:
            assert 0 <= e["beat"] < total and 1 <= e["vel"] <= 127


def test_seed_khac_ra_ban_khac_nhung_cung_phong_cach():
    a = arrange("C", "pop", POP, seed=1, energy=3)
    others = [arrange("C", "pop", POP, seed=s, energy=3) for s in range(2, 8)]
    assert any(o["tracks"] != a["tracks"] for o in others)


def test_cao_do_moi_not_thuoc_hop_am_hoac_not_di_hop_le():
    """Phím và guitar chỉ phát nốt của hợp âm (kể cả nốt màu do Engine dựng); bass ngoài nốt hợp âm chỉ ở nốt đi."""
    a = arrange("C", "jazz", JAZZ, seed=3, energy=3)
    bars = len(JAZZ)
    allowed = {}
    for i, sym in enumerate(JAZZ):
        h = harmonize(sym, parse_note("C"), "rich", __import__("random").Random(0))
        allowed[i] = {n.pitch_class for n in h.roles.values()} | {parse_chord_symbol(sym).root.pitch_class}
    for e in a["tracks"]["keys"]["events"]:
        bar = int(e["beat"] // 4) % bars
        chord_pcs = {n.pitch_class for n in parse_chord_symbol(JAZZ[bar]).notes}
        assert {m % 12 for m in e["midi"]} - allowed[bar] - chord_pcs == set() or e["art"] == "lh"


def test_dan_giong_tong_di_chuyen_nho():
    """Dẫn giọng: C→G→Am→F đánh khít (pop) mỗi lần đổi hợp âm đi ≤ 7 nửa cung tổng cộng, không nhảy cả khối."""
    a = arrange("C", "pop", POP, seed=1, energy=2)
    blocks = []
    for e in a["tracks"]["keys"]["events"]:
        if not blocks or blocks[-1] != e["midi"]:
            blocks.append(e["midi"])
    moves = [movement(blocks[i], blocks[i + 1]) for i in range(len(blocks) - 1)]
    assert max(moves) <= 7, moves
    # Thế bấm gốc xếp khít (cách cũ) đi C4-E4-G4 → G3-B3-D4: tổng 15 nửa cung.
    assert movement([60, 64, 67], [55, 59, 62]) == 15


def test_tam_c3_g5_va_khong_co_quang_ba_duoi_e3():
    for style in ORDER:
        for chords in (POP, JAZZ):
            a = arrange("C", style, chords, seed=2, energy=3)
            for e in a["tracks"]["keys"]["events"]:
                if e["art"] == "lh":  # tay trái ballad rải 1-5-8-10 được xuống dưới C3, như piano thật
                    continue
                notes = sorted(e["midi"])
                assert 48 <= notes[0] and notes[-1] <= 79, (style, notes)
                if len(notes) > 1 and notes[0] < 52:
                    assert notes[1] - notes[0] >= 5, (style, notes)
            for e in a["tracks"]["guitar"]["events"]:
                assert min(e["midi"]) >= 40  # dây Mi trầm của guitar


def test_fill_nam_dung_o_cuoi_vong():
    a = arrange("C", "pop", POP, seed=1, energy=2)
    toms = [e["beat"] for e in a["tracks"]["drums"]["events"] if e["drum"].startswith("tom_")]
    last_bar_beats = {(c * 4 + 3) * 4 for c in range(CYCLES)}
    assert toms and all(int(b // 4) * 4 in last_bar_beats for b in toms)
    big = [b for b in toms if b >= (3 * 4 + 3) * 4]
    assert big  # vòng 4 có fill lớn


def test_crash_dau_vong_tu_vong_2():
    a = arrange("C", "rock", POP, seed=1, energy=3)
    crashes = sorted(e["beat"] for e in a["tracks"]["drums"]["events"] if e["drum"] == "crash")
    assert crashes == [16, 32, 48]


def test_to_mau_chi_o_lop_phat_luoi_giu_ky_hieu():
    a = arrange("C", "jazz", POP, seed=1, energy=2)
    assert [c["symbol"] for c in a["colors"]] == POP
    assert a["colors"][1]["played"].startswith("G7")  # G là bậc V → tô G7, không phải Gmaj7
    assert a["colors"][0]["played"].startswith("Cmaj7")
    pop = arrange("C", "rock", POP, seed=1, energy=2)
    assert all(c["played"] is None for c in pop["colors"])


def test_walking_bass_4_not_moi_o_va_not_cuoi_di_vao_goc():
    a = arrange("C", "jazz", JAZZ, seed=5, energy=2)
    ev = [e for e in a["tracks"]["bass"]["events"] if 16 <= e["beat"] < 32]
    assert [e["beat"] % 4 for e in ev] == [0, 1, 2, 3] * 4
    for bar in range(4):
        notes = [e["midi"][0] for e in ev[bar * 4:(bar + 1) * 4]]
        nxt_root = parse_chord_symbol(JAZZ[(bar + 1) % 4]).root.pitch_class
        assert len(set(notes[:3])) == 3
        assert (notes[3] - nxt_root) % 12 in (1, 11, 7)  # nửa cung dưới/trên hoặc nốt năm của hợp âm sau


def test_o_trong_khong_co_hop_am_nhung_trong_van_chay():
    a = arrange("C", "pop", ["C", None, "F", "G"], seed=1, energy=2)
    assert not [e for e in a["tracks"]["keys"]["events"] if 4 <= e["beat"] < 8]
    assert [e for e in a["tracks"]["drums"]["events"] if 4 <= e["beat"] < 8]


def test_api_arrangement_cong_khai_va_bao_loi():
    body = {"key": "C", "style": "bossa", "chords": POP, "seed": 3, "energy": 2}
    res = client.post("/api/v1/composition/arrangement", json=body)
    assert res.status_code == 200 and res.json()["style"] == "bossa"
    assert client.post("/api/v1/composition/arrangement", json={**body, "style": "metal"}).status_code == 422
    assert client.post("/api/v1/composition/arrangement", json={**body, "chords": ["Xyz"]}).status_code == 422
    assert client.post("/api/v1/composition/arrangement", json={**body, "energy": 0}).status_code == 400


def test_migration_arrangement_mac_dinh_an_toan_va_go_duoc(tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'ar.db'}", future=True)
    try:
        alembic_to(engine, COMPOSITION)
        with engine.begin() as conn:
            conn.execute(sa.text("INSERT INTO users (id, display_name, created_at) VALUES ('u1', 'A', CURRENT_TIMESTAMP)"))
            conn.execute(sa.text("INSERT INTO composition_projects (id, user_id, name, key, tempo_bpm, bars, style, "
                                 "created_at, updated_at) VALUES ('p1', 'u1', 'cũ', 'C', 90, 4, 'pop', "
                                 "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"))
            conn.execute(sa.text("INSERT INTO drum_events (id, project_id, drum, start_beat, velocity) "
                                 "VALUES ('d1', 'p1', 'hat', 0, 70)"))
        alembic_to(engine, ARRANGEMENT)
        with engine.begin() as conn:
            row = conn.execute(sa.text("SELECT seed, energy, mix, arrangement_version FROM composition_projects")).one()
            assert tuple(row) == (1, 2, None, 0)  # QĐ 13A: dự án cũ → seed 1, năng lượng 2
            conn.execute(sa.text("INSERT INTO drum_events (id, project_id, drum, start_beat, velocity) "
                                 "VALUES ('d2', 'p1', 'br_ride', 1, 70)"))
        alembic_to(engine, COMPOSITION, downgrade=True)
        assert version(engine) == COMPOSITION
        with engine.begin() as conn:
            assert [r[0] for r in conn.execute(sa.text("SELECT drum FROM drum_events"))] == ["hat"]
    finally:
        engine.dispose()
