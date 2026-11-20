"""ADR-030: model định tuyến train sẵn. Kiểm: chia dữ liệu không rò, model chỉ nạp khi đủ điều kiện, mặc định nạp
đúng vai nhóm đã bật, số đo khớp manifest."""

import hashlib
import json
import shutil

import pytest

from app.ai.tutor import route_classifier as rc
from app.ml import route_train as rt


@pytest.fixture(autouse=True)
def _fresh_model():
    rc.model.cache_clear()
    yield
    rc.model.cache_clear()


def test_chia_du_lieu_khong_ro_cau_gan_trung():
    data = rt.remove_leaks(rt.splits())
    held = [(rt.norm(r["q"]), rt._grams(r["q"])) for r in data["val"] + data["test"]]
    for r in data["train"]:
        key = (rt.norm(r["q"]), rt._grams(r["q"]))
        assert not any(rt._near(key, h) for h in held), r["q"]
    test_keys = [(rt.norm(r["q"]), rt._grams(r["q"])) for r in data["test"]]
    for r in data["val"]:
        assert not any(rt._near((rt.norm(r["q"]), rt._grams(r["q"])), t) for t in test_keys), r["q"]
    assert {r["label"] for r in data["test"]} == set(rt.LABELS)


def test_moi_cau_train_co_nhom_de_groupkfold():
    rows = rt.remove_leaks(rt.splits())["train"]
    assert all(r["group"] for r in rows)


def test_du_lieu_claude_soan_ghi_ro_nguon_va_draft():
    d = json.loads((rt.TUTOR / "route_data_ml.json").read_text(encoding="utf-8"))
    assert d["status"] == "draft" and "Claude" in d["author"]
    assert {i["label"] for i in d["items"]} <= set(rt.LABELS)


def test_manifest_khop_sha256():
    manifest = json.loads((rt.MODEL_DIR / "manifest.json").read_text(encoding="utf-8"))
    for info in manifest["models"].values():
        data = (rt.MODEL_DIR / info["file"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == info["sha256"]


def test_mac_dinh_nap_dung_vai_duoc_bat(monkeypatch):
    import sklearn

    manifest = json.loads((rt.MODEL_DIR / "manifest.json").read_text(encoding="utf-8"))
    monkeypatch.delenv("ROUTE_MODEL", raising=False)
    pipe, needs_prep = rc.model()
    if manifest["sklearn"] != sklearn.__version__:
        assert needs_prep is True
        return
    # Nhóm bật công thức cũ trên dữ liệu đã bỏ câu rò (2B); model thí nghiệm TF-IDF + e5 không tự chạy.
    assert manifest["models"]["primary"]["kind"] == "old_recipe_clean" and manifest["models"]["primary"]["enabled"]
    assert manifest["models"]["experiment"]["enabled"] is False
    assert needs_prep is False and [n for n, _ in pipe.steps] == ["vec", "clf"]
    assert rc.classify_route("Hợp âm C gồm những nốt nào?").label == "nhac_ly"
    assert rc.classify_route("thời tiết hà nội mai thế nào").label == "ngoai_pham_vi"


def test_route_model_old_luon_dung_model_cu(monkeypatch):
    monkeypatch.setenv("ROUTE_MODEL", "old")
    _, needs_prep = rc.model()
    assert needs_prep is True
    assert rc.classify_route("Hợp âm C gồm những nốt nào?").label == "nhac_ly"


def test_route_model_new_nap_joblib_khi_cung_phien_ban(monkeypatch):
    import sklearn

    manifest = json.loads((rt.MODEL_DIR / "manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setenv("ROUTE_MODEL", "new")
    _, needs_prep = rc.model()
    if manifest["sklearn"] != sklearn.__version__:
        assert needs_prep is True      # khác phiên bản: không tin file joblib, lùi về model cũ
        return
    assert needs_prep is False
    res = rc.classify_route("cam on ban nhieu nha")
    assert res.label in rt.LABELS and abs(sum(res.probs.values()) - 1) < 1e-3


def test_sai_sha256_thi_khong_nap(monkeypatch, tmp_path):
    for f in rt.MODEL_DIR.iterdir():
        shutil.copy(f, tmp_path / f.name)
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    for info in manifest["models"].values():
        (tmp_path / info["file"]).write_bytes(b"hong")
    monkeypatch.setattr(rc, "MODEL_DIR", tmp_path)
    assert rc._load_trained("new") is None


def test_sai_phien_ban_sklearn_thi_khong_nap(monkeypatch, tmp_path):
    for f in rt.MODEL_DIR.iterdir():
        shutil.copy(f, tmp_path / f.name)
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    manifest["sklearn"] = "0.0.0"
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(rc, "MODEL_DIR", tmp_path)
    assert rc._load_trained("new") is None


def test_danh_gia_va_bootstrap():
    rows = [{"q": q, "label": lab, "src": "t"} for q, lab in
            [("a", "nhac_ly"), ("b", "huong_dan"), ("c", "chao_hoi"), ("d", "ngoai_pham_vi"), ("e", "nhac_ly")]]
    pred = ["nhac_ly", "huong_dan", "chao_hoi", "ngoai_pham_vi", "huong_dan"]
    m = rt.evaluate(lambda qs: pred, rows)
    assert m["accuracy"] == 0.8 and len(m["errors"]) == 1
    assert sum(map(sum, m["confusion"]["rows_true_cols_pred"])) == 5
    same = rt.bootstrap_diff(rows, pred, pred, n=50)
    assert same["ci95"] == [0.0, 0.0]


def test_so_do_da_luu_khop_manifest_va_quyet_dinh():
    res = json.loads((rt.RESULT_DIR / "DO_LUONG.json").read_text(encoding="utf-8"))
    manifest = json.loads((rt.MODEL_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert res["data"]["include_claude_data"] is False          # quyết định 1A
    assert manifest["models"]["primary"]["test_macro_f1"] == res["models"]["old_recipe_clean"]["test"]["macro_f1"]
    old, exp = res["models"]["old"], res["models"][res["winner_gridsearch"]]
    wins = exp["val"]["macro_f1"] > old["val"]["macro_f1"] and exp["test"]["macro_f1"] > old["test"]["macro_f1"]
    assert res["enabled"]["experiment_passes_rule"] == wins and res["enabled"]["experiment"] is False
