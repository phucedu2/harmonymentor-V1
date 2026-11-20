"""Phục vụ model: nạp joblib một lần, tính xác suất làm đúng câu MỚI tiếp theo của từng kỹ năng cho một người.

Bật bằng PREDICT_ENABLED=1 (mặc định tắt). Chỉ là thông tin thêm: mastery EMA, mức yếu/đủ/thành thạo và hệ gợi ý
vẫn tính như cũ, không đọc kết quả ở đây (ADR-031).
"""

from __future__ import annotations

import json
import logging
import os
import warnings
from datetime import datetime, timezone
from pathlib import Path

from ...ai.skill_mapping import MAPPING_ROWS, is_mvp
from .features import FEATURE_NAMES, FEATURE_VERSION, group_of, next_question_features

log = logging.getLogger(__name__)
DEFAULT_DIR = Path(__file__).resolve().parents[3] / "models" / "correctness"
# Ngưỡng chia mức chỉ để hiển thị: 60–80% là "vừa sức" (đủ thử thách mà vẫn thường làm được).
BANDS = ((0.6, "kho"), (0.8, "vua_suc"), (1.01, "de"))


class ModelUnavailable(RuntimeError):
    pass


def enabled() -> bool:
    return os.getenv("PREDICT_ENABLED", "0").lower() in ("1", "true", "yes")


def model_dir() -> Path:
    return Path(os.getenv("PREDICT_MODEL_DIR") or DEFAULT_DIR)


_CACHE: dict[str, tuple] = {}


def load(path: Path | None = None):
    """(pipeline, manifest). Lỗi nạp (thiếu file, lệch phiên bản đặc trưng, sklearn quá khác) → ModelUnavailable."""
    path = path or model_dir()
    key = str(path)
    if key in _CACHE:
        return _CACHE[key]
    manifest_path, model_path = path / "manifest.json", path / "model.joblib"
    if not manifest_path.exists() or not model_path.exists():
        raise ModelUnavailable(f"Chưa có model ở {path}: chạy `python -m app.ml.correctness.train`.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("phien_ban_dac_trung") != FEATURE_VERSION or manifest.get("dac_trung") != list(FEATURE_NAMES):
        raise ModelUnavailable("Model train với bộ đặc trưng khác phiên bản hiện tại: cần train lại.")
    import joblib
    import sklearn

    trained = manifest.get("moi_truong", {}).get("sklearn")
    if trained and trained.split(".")[:2] != sklearn.__version__.split(".")[:2]:
        log.warning("Model train bằng scikit-learn %s, đang chạy %s: nên train lại nếu kết quả lạ.",
                    trained, sklearn.__version__)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # cảnh báo lệch phiên bản đã ghi log ở trên
            pipeline = joblib.load(model_path)
    except Exception as exc:  # file hỏng hoặc sklearn không đọc được: tắt tính năng thay vì làm sập API
        raise ModelUnavailable(f"Không nạp được model: {exc}") from exc
    _CACHE[key] = (pipeline, manifest)
    return pipeline, manifest


def mvp_skills() -> list[str]:
    return [skill for skill, _, _ in MAPPING_ROWS if is_mvp(skill)]


def band(p: float) -> str:
    return next(name for limit, name in BANDS if p < limit)


def predict(events: list[dict], skills: list[str], now: datetime | None = None, path: Path | None = None) -> dict:
    pipeline, manifest = load(path)
    now = now or datetime.now(timezone.utc)
    t = int(now.timestamp())
    X = next_question_features(events, skills, t)
    probs = pipeline.predict_proba(X)[:, 1] if skills else []
    col = FEATURE_NAMES.index("ema_skill")
    n_col = FEATURE_NAMES.index("log_n_skill")
    import math

    items = [{"skill_id": s, "group_code": group_of(s), "probability": round(float(p), 4), "band": band(float(p)),
              "ema": round(float(x[col]), 4), "attempts": int(round(math.expm1(x[n_col])))}
             for s, p, x in zip(skills, probs, X)]
    return {"model_version": manifest["phien_ban_model"], "trained_on": manifest["nguon_du_lieu"],
            "chosen_model": manifest["model_chon"], "note": manifest.get("luu_y", ""), "items": items}


def predict_for_user(db, user_id: str, now: datetime | None = None) -> dict:
    from .dataset import db_events

    events = db_events(db, [user_id]).get(user_id, [])
    return predict(events, mvp_skills(), now=now)
