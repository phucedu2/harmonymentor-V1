"""Dựng trang nghe mù docs/backing-track/nghe-thu/index.html từ mẫu + ket-qua-thu.json (số đo LUFS thật để cân độ to)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/backing-track/nghe-thu"
data = json.loads((OUT / "ket-qua-thu.json").read_text(encoding="utf-8"))
# Trang chỉ cần phong cách, vòng, BPM và độ to; bỏ thời gian thu để file gọn.
slim = {"date": data["date"], "results": [{k: r[k] for k in ("style", "loop", "bpm", "old_style", "before", "after")} for r in data["results"]]}
tpl = (ROOT / "scripts/backing-track/trang_nghe_mu.template.html").read_text(encoding="utf-8")
html = tpl.replace("/*DATA*/null/*END*/", json.dumps(slim, ensure_ascii=False))
# Mở trực tiếp trong trình duyệt (ngoài claude.ai) cần khung tài liệu đầy đủ.
page = "<!doctype html>\n<html lang=\"vi\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\"></head><body>\n" + html + "\n</body></html>\n"
(OUT / "index.html").write_text(page, encoding="utf-8")
(OUT / "artifact.html").write_text(html, encoding="utf-8")
print("ok", len(slim["results"]), "cặp")
