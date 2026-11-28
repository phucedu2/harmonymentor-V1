"""G6 (T6): bộ phân loại tự huấn luyện — suy luận thuần Python khớp scikit-learn, kiểm SHA-256, công tắc cấu hình, không rò dữ liệu."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from app.admin.relevance import classifier as cl
from app.admin.relevance.errors import RelevanceError
from app.admin.relevance.gate import evaluate_pasted_text
from app.admin.relevance.scorer import HybridScorer, default_scorer
from app.core.ai_config import relevance_config
from app.eval.cases import load_cases
from app.ml.relevance_train import build_dataset, max_overlap

MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "relevance"
GOLDEN = json.loads((Path(__file__).parent / "fixtures" / "g6_sklearn_golden.json").read_text(encoding="utf-8"))


def test_manifest_co_phien_ban_va_hash_khop():
    man = cl.read_manifest(MODEL_DIR)
    assert man.version and man.recommended in cl.KINDS
    for name, info in man.files.items():
        assert cl.sha256_file(MODEL_DIR / name) == info["sha256"]


def test_tfidf_thuan_python_khop_sklearn():
    """Giá trị vàng sinh bằng TfidfVectorizer(char_wb)+LogisticRegression của scikit-learn trên cùng dữ liệu."""
    model = cl.TfidfLogReg(cl.load_spec(MODEL_DIR, "tfidf"))
    for g in GOLDEN:
        assert model.predict(g["text"]) == pytest.approx(g["p"], abs=1e-5), g["text"]


def test_char_wb_ngrams_nhu_sklearn():
    assert cl.char_wb_ngrams("ab c", 2, 3) == [" a", "ab", "b ", " ab", "ab ", " c", "c ", " c "]


def test_khong_ro_ri_giua_tai_lieu_thu_va_du_lieu_train():
    docs = [c["text"] for c in load_cases() if c["type"] == "gate"]
    assert len(docs) >= 16
    assert max_overlap(docs, [r["text"] for r in build_dataset()]) < 0.8


def _copy(tmp_path):
    d = tmp_path / "m"
    shutil.copytree(MODEL_DIR, d)
    return d


def test_sai_sha256_bi_tu_choi(tmp_path):
    d = _copy(tmp_path)
    p = d / "tfidf-logreg.json"
    p.write_text(p.read_text(encoding="utf-8") + " ", encoding="utf-8")      # sửa 1 byte là đủ lệch hash
    with pytest.raises(cl.ModelError, match="SHA-256"):
        cl.load_spec(d, "tfidf")


def test_thieu_mo_hinh_thi_lui_ve_hybrid(tmp_path, monkeypatch, caplog):
    monkeypatch.setenv("RELEVANCE_SCORER", "classifier")
    monkeypatch.setenv("RELEVANCE_MODEL_DIR", str(tmp_path / "khong-co"))
    with caplog.at_level("WARNING"):
        s = default_scorer()
    assert isinstance(s, HybridScorer)
    assert "relevance_classifier_unavailable" in caplog.text


def test_sha_sai_thi_default_scorer_lui_ve_hybrid(tmp_path, monkeypatch):
    d = _copy(tmp_path)
    (d / "tfidf-logreg.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("RELEVANCE_SCORER", "classifier")
    monkeypatch.setenv("RELEVANCE_MODEL", "tfidf")
    monkeypatch.setenv("RELEVANCE_MODEL_DIR", str(d))
    assert isinstance(default_scorer(), HybridScorer)


def test_cong_tac_classifier_chay_cong_nhac_ly_16_tai_lieu(monkeypatch):
    monkeypatch.setenv("RELEVANCE_SCORER", "classifier")
    monkeypatch.setenv("RELEVANCE_MODEL", "tfidf")        # chỉ cần chữ: test không phụ thuộc mô hình e5
    cfg = relevance_config()
    scorer = default_scorer(cfg)
    assert scorer.name.startswith("classifier:tfidf@")
    docs = [c for c in load_cases() if c["type"] == "gate" and c["label"] != "borderline"]
    bad = []
    for c in docs:
        try:
            status = evaluate_pasted_text(c["text"], scorer, cfg).status
        except RelevanceError:                              # tài liệu chèn chỉ dẫn bị cổng chặn trước khi chấm: tính là từ chối
            status = "rejected"
        ok = status == "accepted" if c["label"] == "relevant" else status == "rejected"
        if not ok:
            bad.append((c["id"], c["label"], status))
    assert not bad, bad


def test_e5_can_embedder(monkeypatch):
    monkeypatch.setenv("RELEVANCE_MODEL", "e5")
    with pytest.raises(cl.ModelError, match="e5"):
        cl.build_scorer(relevance_config(), None)
