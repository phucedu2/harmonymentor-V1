"""In đáp án đúng của L01, L02 (lấy từ curriculum_specs) ra JSON cho kịch bản E2E demo 10/11.

    cd backend && python ../scripts/e2e/dap_an_demo_1011.py > /tmp/dap_an.json
Chỉ dùng cho CSDL test; không đưa vào giao diện."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.content.curriculum_specs import lesson_by_id  # noqa: E402
from tests.auth_helpers import correct_answer  # noqa: E402

print(json.dumps({lid: [{"prompt": x["prompt"], "answer": correct_answer(x), "choice": bool(x["options"])}
                        for x in lesson_by_id(lid)["exercises"]] for lid in ("L01", "L02")}, ensure_ascii=False))
