"""Chế độ Bài hát của Harmony Lab (ADR-013 đề xuất, 02/11/2026).

Khẳng định các luật của sổ tay docs/backing-track/CAU_TRUC_BAI_HAT.md bằng số đo trên bản phối (không cần nghe):
form hợp lệ và giới hạn 160 ô, hook đúng chỗ, lên giọng tắt thì giữ giọng gốc, Verse 2 khác Verse 1, Chorus dày hơn
Verse, chuyển đoạn nằm ở ô cuối, drop im thật, dẫn giọng nối qua ranh giới, cùng seed ra cùng bài, chế độ Vòng lặp
giữ y nguyên từng nốt của bản v1, dự án lưu/mở được form.
"""
from __future__ import annotations

import hashlib
import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.composition.arranger import arrange, movement
from app.composition.song import (
    MAX_BARS, SECTION_TYPES, SONG_VERSION, SongError, arrange_song, default_form, round_bars,
)
from app.composition.styles import ARRANGEMENT_VERSION, DRUM_CODES, ORDER, PACKS
from app.db.models import User
from app.db.session import SessionLocal
from app.main import app
from app.music_engine import parse_chord_symbol
from tests.auth_helpers import auth

client = TestClient(app)
POP4 = ["C", "G", "Am", "F"]
JAZZ4 = ["Dm7", "G7", "Cmaj7", "A7"]


@pytest.fixture(autouse=True, scope="module")
def _schema():
    with TestClient(app):
        yield


def song(style="pop", length="medium", progs=None, seed=1, energy=2, **form_extra):
    form = default_form(style, length, progs or {"A": POP4})
    form.update(form_extra)
    return arrange_song("C", style, form, seed=seed, energy=energy)


def onsets(r, a, z, tracks=("keys", "bass", "guitar", "drums", "hook")):
    return [(t, e) for t in tracks for e in r["tracks"][t]["events"] if a <= e["beat"] < z]


def layers(r, a, z) -> set[str]:
    """"Bộ lớp" nghe được trong [a, z): nhạc cụ có nốt + từng bộ phận trống (tay trái piano là một lớp riêng)."""
    out = set()
    for t, e in onsets(r, a, z):
        if t == "drums":
            out.add(e["drum"])
        elif t == "keys" and e["art"] == "lh":
            out.add("keys_lh")
        else:
            out.add(t)
    return out


def sec_of(r, stype, k=1):
    found = [s for s in r["sections"] if s["type"] == stype]
    return found[k - 1] if k > 0 else found[k]


# --- form ------------------------------------------------------------------------------------------

@pytest.mark.parametrize("style", ORDER)
@pytest.mark.parametrize("length", ["short", "medium", "full"])
def test_khuon_mac_dinh_hop_le_va_duoi_gioi_han(style, length):
    r = song(style, length)
    assert r["version"] == SONG_VERSION and r["mode"] == "song"
    assert r["total_bars"] <= MAX_BARS
    assert sum(s["bars"] for s in r["sections"]) == r["total_bars"]
    assert r["sections"][0]["start_beat"] == 0 and r["sections"][-1]["end_beat"] == r["total_beats"]
    assert all(s["type"] in SECTION_TYPES for s in r["sections"])
    assert all(s["note_vi"] for s in r["sections"])  # ghi chú producer cho mọi đoạn (QĐ 10A)
    assert {e["drum"] for e in r["tracks"]["drums"]["events"]} <= DRUM_CODES
    # ~1 phút / 2–3 phút / 3,5–4,5 phút ở tempo mặc định (mục F)
    lo, hi = {"short": (40, 90), "medium": (110, 190), "full": (195, 275)}[length]
    assert lo <= r["duration_sec"] <= hi


def test_qua_160_o_bao_loi():
    form = default_form("pop", "medium", {"A": POP4})
    form["sections"] = [dict(form["sections"][1], bars=16) for _ in range(11)]
    with pytest.raises(SongError) as exc:
        arrange_song("C", "pop", form)
    assert exc.value.code == "SONG_TOO_LONG"


def test_lam_tron_so_o_theo_do_dai_vong():
    # QĐ 7A: vòng 6 ô → đoạn 8 ô thành 6; đoạn ngắn hơn một vòng (Intro 4, Pre 4) giữ nguyên.
    assert round_bars(8, 6, "verse") == 6 and round_bars(16, 6, "chorus") == 18 and round_bars(4, 6, "intro") == 4
    assert round_bars(8, 4, "verse") == 8 and round_bars(4, 8, "bridge") == 8
    f = default_form("pop", "medium", {"A": ["C", "G", "Am", "F", "Dm", "G"]})
    by_type = {s["type"]: s["bars"] for s in f["sections"]}
    assert by_type["verse"] == 6 and by_type["intro"] == 4 and by_type["pre"] == 4


def test_vong_trong_tam_dung_vong_a_va_co_goi_y():
    # QĐ 3A: chưa nhập B/C thì Chorus/Bridge tạm dùng A, kèm gợi ý vòng B/C dựng bằng Engine để nghe thử.
    r = song("pop", "medium")
    chorus = sec_of(r, "chorus")
    assert chorus["progression"] == "A" and chorus["progression_requested"] == "B"
    assert set(r["suggestions"]) == {"B", "C"}
    for sug in r["suggestions"].values():
        assert len(sug["chords"]) == 4 and all(parse_chord_symbol(c) for c in sug["chords"])
        assert sug["chords"][0] != "C"  # không bắt đầu bằng I như Verse
    r2 = song("pop", "medium", {"A": POP4, "B": ["F", "C", "G", "Am"]})
    assert sec_of(r2, "chorus")["progression"] == "B" and "B" not in r2["suggestions"]
    chorus_bars = [b["symbol"] for b in r2["bars"] if b["section"] == r2["sections"].index(sec_of(r2, "chorus"))]
    assert chorus_bars[:4] == ["F", "C", "G", "Am"]


# --- năng lượng, tương phản, không lặp y hệt --------------------------------------------------------

@pytest.mark.parametrize("style", ORDER)
def test_chorus_day_hon_verse_it_nhat_mot_lop(style):
    r = song(style, "medium", {"A": POP4 if style not in ("jazz", "bossa") else JAZZ4})
    verse = sec_of(r, "verse")
    peak = max(r["sections"], key=lambda s: (s["energy"], s["type"] in ("chorus", "solo")))
    assert peak["energy"] > verse["energy"]
    lv = layers(r, verse["start_beat"], verse["end_beat"] - 4)   # bỏ ô chuyển đoạn
    lc = layers(r, peak["start_beat"], peak["end_beat"] - 4)
    assert len(lc) >= len(lv) + 1, (style, lv, lc)


@pytest.mark.parametrize("style", ORDER)
def test_verse_chua_cho_giong(style):
    # Nguyên tắc 4: số nốt trong tầm C4–C5 (60–72) mỗi ô ở Verse ít hơn ở đoạn cao trào.
    r = song(style, "medium")
    verse = sec_of(r, "verse")
    peak = max(r["sections"], key=lambda s: s["energy"])

    def dense(s):
        # Quạt tắt tiếng (chicken scratch, palm mute) là tiếng gõ không rõ cao độ, không tranh tầm giọng: không đếm.
        n = sum(1 for t, e in onsets(r, s["start_beat"], s["end_beat"], ("keys", "guitar", "hook"))
                if e["art"] not in ("mute", "palm", "dead") for m in e["midi"] if 60 <= m <= 72)
        return n / s["bars"]
    assert dense(verse) < dense(peak), style


@pytest.mark.parametrize("style", ORDER)
def test_verse2_khac_verse1_va_chorus_cuoi_khac_chorus_dau(style):
    r = song(style, "full")
    for stype in ("verse", "chorus"):
        found = [s for s in r["sections"] if s["type"] == stype]
        if len(found) < 2:
            continue
        a, b = found[0], found[-1]

        def shape(s):
            return sorted((t, round(e["beat"] - s["start_beat"], 4), e.get("drum") or tuple(e["midi"]))
                          for t, e in onsets(r, s["start_beat"], s["start_beat"] + 16))
        assert shape(a) != shape(b), (style, stype)
        assert layers(r, b["start_beat"], b["start_beat"] + 16) != layers(r, a["start_beat"], a["start_beat"] + 16) \
            or b["feel"] != a["feel"] or b["energy"] != a["energy"], (style, stype)


@pytest.mark.parametrize("style", ORDER)
def test_moi_8_o_co_thay_doi(style):
    # Nguyên tắc 1 (luật thêm/bớt): không quá 8 ô liền có cùng bộ lớp.
    r = song(style, "full")
    sigs = [frozenset(layers(r, b * 4, b * 4 + 4)) for b in range(r["total_bars"])]
    run = longest = 1
    for i in range(1, len(sigs)):
        run = run + 1 if sigs[i] == sigs[i - 1] else 1
        longest = max(longest, run)
    assert longest <= 8, style


@pytest.mark.parametrize("style", ORDER)
def test_o_truoc_chorus_thua_hon(style):
    # Nguyên tắc 2: ô ngay trước đoạn cao trào có ít lớp hơn ô đầu đoạn cao trào.
    r = song(style, "medium")
    for i, s in enumerate(r["sections"][1:], start=1):
        if s["type"] != "chorus" or r["sections"][i - 1]["energy"] >= s["energy"]:
            continue
        before = layers(r, s["start_beat"] - 4, s["start_beat"])
        first = layers(r, s["start_beat"], s["start_beat"] + 4)
        assert len(before) < len(first), (style, s["label"], before, first)


def test_nang_luong_tong_doi_ca_duong_cong():
    base, up, down = song(energy=2), song(energy=3), song(energy=1)
    for a, b, c in zip(base["sections"], up["sections"], down["sections"]):
        assert b["energy"] == min(5, a["energy"] + 1) and c["energy"] == max(1, a["energy"] - 1)


# --- chuyển đoạn, đột biến, kết bài ----------------------------------------------------------------

@pytest.mark.parametrize("style", ORDER)
def test_dot_bien_1_den_3_o_ranh_gioi(style):
    for seed in (1, 2, 3, 4, 5):
        r = song(style, "medium", seed=seed)
        own = [s for s in r["surprises"] if s["kind"] != "modulate"]
        assert 1 <= len(own) <= 3, (style, seed)
        bounds = {s["start_beat"] for s in r["sections"]} | {s["end_beat"] for s in r["sections"]}
        for sp in own:
            # đặt ở 1 ô cuối của một đoạn, hoặc ngay đầu đoạn (half/double)
            assert any(abs(sp["beat"] - b) <= 4 for b in bounds), (style, sp)


def test_fill_tom_chi_o_o_cuoi_doan_hoac_o_8():
    r = song("pop", "full")
    starts = {}
    for s in r["sections"]:
        for b in range(s["bars"]):
            starts[s["start_beat"] + 4 * b] = (s, b)
    for e in r["tracks"]["drums"]["events"]:
        if e["drum"].startswith("tom"):
            s, b = starts[e["beat"] // 4 * 4]
            assert b == s["bars"] - 1 or b == 7, (s["label"], b)


def test_snare_build_o_2_o_cuoi_luc_tang_dan():
    r = song("pop", "medium")
    pre = sec_of(r, "pre")
    assert pre["transition"] == "snare_build" or pre["transition"] in ("drop_bar", "stop_time", "riser",
                                                                         "reverse_cymbal")
    form = default_form("pop", "medium", {"A": POP4})
    for s in form["sections"]:
        if s["type"] == "pre":
            s["transition"] = "snare_build"
    r = arrange_song("C", "pop", form, seed=1)
    pre = sec_of(r, "pre")
    sn = [e for e in r["tracks"]["drums"]["events"] if e["drum"] == "snare"
          and pre["end_beat"] - 8 <= e["beat"] < pre["end_beat"]]
    assert len(sn) == 8 + 8 + 16
    vels = [e["vel"] for e in sorted(sn, key=lambda e: e["beat"])]
    assert vels == sorted(vels) and vels[-1] > vels[0] + 40
    # không hat/ride trong build (thưa lớp cymbal để cú crash đầu Chorus nổi bật)
    assert not [e for t, e in onsets(r, pre["end_beat"] - 8, pre["end_beat"], ("drums",))
                if e["drum"] in ("hh_c", "hh_o", "ride")]


@pytest.mark.parametrize("style", ORDER)
def test_drop_im_that(style):
    form = default_form(style, "medium", {"A": POP4})
    idx = next(i for i, s in enumerate(form["sections"][1:], start=1) if s["type"] in ("chorus", "solo", "bridge"))
    form["sections"][idx - 1]["transition"] = "drop_bar"
    r = arrange_song("C", style, form, seed=1)
    end = r["sections"][idx - 1]["end_beat"]
    for t in ("keys", "bass", "guitar", "drums", "hook"):
        for e in r["tracks"][t]["events"]:
            assert not (end - 2 <= e["beat"] < end), (style, t, e)
            if "dur" in e:
                assert e["beat"] + e["dur"] <= end - 2 + 1e-6 or e["beat"] >= end, (style, t, e)
    # bass nghỉ cả ô trước drop; reverb tail bị cắt bằng automation
    assert not [e for e in r["tracks"]["bass"]["events"] if end - 4 <= e["beat"] < end]
    assert {"beat": end - 2, "target": "reverb_return", "value": 0.0, "ramp": 0.05} in r["automation"]


def test_stop_time_mot_nhat_roi_im():
    form = default_form("funk", "medium", {"A": POP4})
    form["sections"][1]["transition"] = "stop_time"
    r = arrange_song("C", "funk", form, seed=1)
    end = r["sections"][1]["end_beat"]
    hits = onsets(r, end - 4, end)
    assert hits and all(abs(e["beat"] - (end - 4)) < 1e-9 for _, e in hits)
    assert {"kick", "crash"} <= {e["drum"] for t, e in hits if t == "drums"}


@pytest.mark.parametrize("style,ending", [("ballad", "ritardando_fermata"), ("rock", "big_hit"),
                                          ("jazz", "tag_x3"), ("pop", "fade")])
def test_ket_bai(style, ending):
    r = song(style, "medium")
    assert r["ending"] == ending
    last = r["sections"][-1]
    if ending == "fade":
        assert any(a["target"] == "master" and a["value"] <= -40 for a in r["automation"])
        return
    fb = r["total_beats"] - 4
    hits = onsets(r, fb, fb + 4)
    assert hits and all(e["beat"] == fb for _, e in hits)      # ô cuối: một nhát/nốt ngân duy nhất
    tonic_bar = r["bars"][-1]["symbol"]
    assert parse_chord_symbol(tonic_bar).root.name == "C"      # kết về I
    if ending in ("ritardando_fermata", "tag_x3"):
        assert r["tempo_map"][-1]["bpm"] < r["bpm"] * 0.9 and r["tail_beats"] > 0
    if ending == "tag_x3":
        tag = [b["symbol"] for b in r["bars"][last["start_bar"] if "start_bar" in last else int(last["start_beat"] // 4):]]
        assert tag[:6] == ["Dm7", "G7"] * 3 and tag[-1] == "Cmaj7"


def _replay(points, target, beat):
    """Áp automation theo đúng thứ tự trả về, như trình phát: điểm sau cùng phách hủy dốc của điểm trước."""
    val, ramp_from, start, ramp, to = 0.0, 0.0, 0.0, 0.0, 0.0
    for a in points:
        if a["target"] != target or a["beat"] > beat:
            continue
        cur = val if not ramp or a["beat"] >= start + ramp else ramp_from + (to - ramp_from) * (a["beat"] - start) / ramp
        ramp_from, start, ramp, to = cur, a["beat"], a["ramp"], a["value"]
        val = a["value"] if not a["ramp"] else cur
    if ramp and beat < start + ramp:
        return ramp_from + (to - ramp_from) * (beat - start) / ramp
    return to if ramp else val


@pytest.mark.parametrize("style", [s for s in ORDER if PACKS[s]["song"]["ending"] == "fade"])
def test_fade_that_su_nho_dan(style):
    """Phát lại automation theo thứ tự: cuối bài phải xuống ≤ -30 dB (lỗi cũ: mức Outro đè mất dốc fade)."""
    r = song(style, "medium")
    out = r["sections"][-1]
    assert _replay(r["automation"], "master", r["total_beats"]) <= -30
    assert _replay(r["automation"], "master", out["start_beat"] + 0.5) >= -8


def test_automation_cung_phach_dat_ngay_truoc_doc():
    for style in ORDER:
        pts = song(style, "medium")["automation"]
        for a, b in zip(pts, pts[1:]):
            if a["beat"] == b["beat"] and a["target"] == b["target"]:
                assert not (a["ramp"] > 0 and b["ramp"] == 0), (style, a, b)


# --- hook ------------------------------------------------------------------------------------------

@pytest.mark.parametrize("style", ORDER)
def test_hook_dung_cho(style):
    r = song(style, "full")
    events = r["tracks"]["hook"]["events"]
    assert events, style
    windows = [(a["beat"], a["beat"] + 2) for a in r["automation"] if a["target"] == "reverb_return" and a["value"] == 0]
    for e in events:
        s = next(s for s in r["sections"] if s["start_beat"] <= e["beat"] < s["end_beat"])
        assert s["type"] not in ("pre", "bridge", "breakdown"), (style, s["label"])
        assert 72 <= e["midi"][0] <= 88                                  # trên tầm giọng hát
        assert not any(a <= e["beat"] < z for a, z in windows)
        if s["type"] == "chorus":
            assert int((e["beat"] - s["start_beat"]) // 4) % 2 == 1        # ô 2 và 4 của câu (hỏi–đáp)
    for s in r["sections"]:
        if s["type"] == "verse":
            assert s["hook_bars"] <= 2
        if s.get("transition") == "snare_build":
            assert not [e for e in events if s["end_beat"] - 8 <= e["beat"] < s["end_beat"]]


def test_hook_phach_manh_la_not_hop_am():
    r = song("pop", "medium", {"A": POP4, "B": ["F", "C", "G", "Am"]})
    for e in r["tracks"]["hook"]["events"]:
        if abs(e["beat"] - round(e["beat"])) < 1e-9:
            sym = r["bars"][int(e["beat"] // 4)]["symbol"]
            pcs = {n.pitch_class for n in parse_chord_symbol(sym).notes}
            played = r["bars"][int(e["beat"] // 4)]["played"]
            if played:  # tô màu add9: nốt 9 cũng là nốt hợp âm ở lớp phát
                pcs.add((parse_chord_symbol(sym).root.pitch_class + 2) % 12)
            assert e["midi"][0] % 12 in pcs, (sym, e)


def test_tat_hook_thi_khong_co_hook():
    assert song("pop", "medium", hook=False)["tracks"]["hook"]["events"] == []


# --- lên giọng --------------------------------------------------------------------------------------

def test_len_giong_tat_thi_giu_giong_goc():
    r = song("ballad", "medium", {"A": POP4, "B": ["F", "G", "Em", "Am"]})
    assert r["key_map"] == [{"beat": 0.0, "key": "C"}]
    allowed = set(POP4) | {"F", "G", "Em", "Am"} | {"C"}
    assert {b["symbol"] for b in r["bars"] if b["symbol"]} <= allowed
    assert all(s["key"] == "C" for s in r["sections"])


@pytest.mark.parametrize("semi,new_key,dominant", [(1, "Db", "Ab7"), (2, "D", "A7")])
def test_len_giong_chorus_cuoi(semi, new_key, dominant):
    r = song("ballad", "medium", {"A": POP4, "B": ["F", "G", "Em", "Am"]},
             modulate={"enabled": True, "semitones": semi})
    last = sec_of(r, "chorus", -1)
    assert r["key_map"][-1] == {"beat": last["start_beat"], "key": new_key}
    bars = [b["symbol"] for b in r["bars"]]
    first = int(last["start_beat"] // 4)
    assert bars[first - 1] == dominant                       # ô chuyển = át của giọng mới
    expect = {1: ["Gb", "Ab", "Fm", "Bbm"], 2: ["G", "A", "F#m", "Bm"]}[semi]
    assert bars[first:first + 4] == expect                    # mọi nốt dời qua Engine (đánh vần đúng giọng mới)
    assert any(s["kind"] == "modulate" for s in r["surprises"])


# --- dẫn giọng, seed, tương thích ------------------------------------------------------------------

@pytest.mark.parametrize("style", ["pop", "ballad", "jazz", "rnb"])
def test_dan_giong_qua_ranh_gioi_doan(style):
    r = song(style, "medium", {"A": POP4, "B": ["F", "G", "Em", "Am"], "C": ["Am", "F", "C", "G"]})
    keys = [e for e in r["tracks"]["keys"]["events"] if e["art"] != "lh" and len(e["midi"]) >= 3]
    for s in r["sections"][1:]:
        before = [e for e in keys if e["beat"] < s["start_beat"]]
        after = [e for e in keys if e["beat"] >= s["start_beat"]]
        if before and after:
            assert movement(before[-1]["midi"], after[0]["midi"]) <= 14, (style, s["label"])


def test_cung_seed_cung_bai_seed_khac_khac_bai():
    a, b, c = song(seed=5), song(seed=5), song(seed=6)
    assert a == b
    assert a["tracks"] != c["tracks"]


def test_doi_seed_mot_doan_chi_doi_doan_do():
    f1 = default_form("pop", "medium", {"A": POP4})
    f2 = json.loads(json.dumps(f1))
    for f in (f1, f2):
        f["sections"][2]["transition"] = "fill_small"     # cố định chuyển đoạn để chỉ seed đoạn khác nhau
        for s in f["sections"]:
            s["seed"] = 11
            s["transition"] = s["transition"] if s["transition"] != "auto" else "fill_small"
    f2["sections"][3]["seed"] = 99
    a, b = arrange_song("C", "pop", f1, seed=1), arrange_song("C", "pop", f2, seed=1)
    s3 = a["sections"][3]
    da = [e for e in a["tracks"]["drums"]["events"] if not (s3["start_beat"] <= e["beat"] < s3["end_beat"])]
    db = [e for e in b["tracks"]["drums"]["events"] if not (s3["start_beat"] <= e["beat"] < s3["end_beat"])]
    assert da == db


def test_vong_lap_giu_y_nguyen_tung_not_ban_v1():
    # QĐ 2A: chế độ Vòng lặp không đổi. Băm ra cùng số với nhánh phuc-music @ b96a6dd (trước khi có bài hát).
    h = hashlib.sha256()
    for st in ORDER:
        for ch in (POP4, JAZZ4, ["C", None, "F", "G", "Am", "Em"]):
            for e in (1, 2, 3):
                for sd in (1, 7):
                    h.update(json.dumps(arrange("C", st, ch, sd, e), sort_keys=True).encode())
    assert h.hexdigest() == "6f77551e5b92d861018b18e9d0a6dc86406717f7cae4500758c9e05c204cd5ee"
    assert ARRANGEMENT_VERSION == 1


def test_drum_events_bai_day_du_duoi_5000_dong():
    worst = max(len(song(st, "full")["tracks"]["drums"]["events"]) for st in ORDER)
    assert worst < 5000, worst


# --- API + dự án -----------------------------------------------------------------------------------

def make_user() -> str:
    uid = "song-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="Thử bài hát", role="learner"))
        db.commit()
    return uid


def test_api_song_cong_khai_va_bao_loi():
    body = {"key": "C", "style": "pop", "seed": 3, "energy": 2, "bpm": 100,
            "form": {"length": "short", "progressions": {"A": POP4}}}
    res = client.post("/api/v1/composition/song", json=body)
    assert res.status_code == 200, res.text
    data = res.json()
    assert [s["type"] for s in data["sections"]] == ["intro", "verse", "chorus", "outro"]
    assert data["form"]["sections"][0]["type"] == "intro"     # trả form đã dựng để giao diện sửa tiếp
    bad = {**body, "form": {"progressions": {"A": ["H7"]}}}
    assert client.post("/api/v1/composition/song", json=bad).status_code == 422
    bad = {**body, "form": {"progressions": {"A": POP4}, "sections": [{"type": "kora", "bars": 4, "energy": 2}]}}
    assert client.post("/api/v1/composition/song", json=bad).status_code in (400, 422)  # lỗi kiểu dữ liệu của app
    opts = client.get("/api/v1/composition/options").json()
    assert opts["song"]["max_bars"] == MAX_BARS and "drop_bar" in opts["song"]["transitions"]


def test_du_an_luu_va_mo_form():
    uid = make_user()
    h = auth(uid)
    form = {"length": "medium", "hook": True, "modulate": {"enabled": True, "semitones": 2},
            "progressions": {"A": POP4, "B": ["F", "G", "Em", "Am"], "C": None}}
    body = {"name": "Bài đầu tiên", "key": "C", "tempo_bpm": 100, "bars": 4, "style": "pop", "chords": POP4,
            "seed": 4, "energy": 2, "mix": {"hook": {"volume": 0.6, "muted": False}}, "form": form}
    res = client.post("/api/v1/projects", headers=h, json=body)
    assert res.status_code == 201, res.text
    p = res.json()
    assert p["arrangement_version"] == SONG_VERSION and p["arrangement_outdated"] is False
    assert p["form"]["progressions"]["B"] == ["F", "G", "Em", "Am"] and p["form"]["modulate"]["semitones"] == 2
    assert len(p["form"]["sections"]) == 10
    expected = arrange_song("C", "pop", p["form"], seed=4, energy=2)["tracks"]["drums"]["events"]
    assert len(p["drum_events"]) == len(expected)          # trải đủ cả bài
    # Mở lại → dựng lại ra đúng bài đó
    got = client.get(f"/api/v1/projects/{p['id']}", headers=h).json()
    assert got["form"] == p["form"]
    assert client.get("/api/v1/projects", headers=h).json()[0]["mode"] == "song"
    # Dự án vòng lặp (không form) vẫn như cũ, không bị báo "luật phối đã đổi" oan
    loop = client.post("/api/v1/projects", headers=h, json={**body, "form": None}).json()
    assert loop["form"] is None and loop["arrangement_version"] == ARRANGEMENT_VERSION
    assert loop["arrangement_outdated"] is False
    # Người khác không thấy (404)
    other = auth(make_user())
    assert client.get(f"/api/v1/projects/{p['id']}", headers=other).status_code == 404
