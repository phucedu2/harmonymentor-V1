"""In đáp án đúng của bài và thẻ ôn (lấy từ curriculum_specs) ra JSON cho test giao diện chạy với backend thật.

    cd backend && python ../scripts/e2e/dap_an_giao_dien.py > dap-an.json
Chỉ dùng cho CSDL test; không đưa vào giao diện. frontend/e2e-live/chay-backend.mjs gọi script này khi khởi động."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.content.curriculum_specs import lesson_by_id  # noqa: E402
from tests.auth_helpers import correct_answer  # noqa: E402

LESSONS = ("L01",)
print(json.dumps({
    lid: {
        "title": lesson_by_id(lid)["title"],
        "exercises": [{"id": x["id"], "prompt": x["prompt"], "answer": correct_answer(x), "choice": bool(x["options"]), "options": x["options"] or []}
                      for x in lesson_by_id(lid)["exercises"]],
        "cards": [{"front": c["front"], "answer": correct_answer(c)} for c in lesson_by_id(lid)["review_items"]],
    } for lid in LESSONS
}, ensure_ascii=False))
