"""Dựng trang nghe docs/backing-track/bai-hat/index.html (+ artifact.html) từ mẫu + ket-qua-bai-hat.json.

Số liệu trên trang là số đo thật từ thu_bai_hat.mjs (LUFS từng đoạn, đường độ to ngắn hạn, đỉnh thật); không sửa tay.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/backing-track/bai-hat"
data = json.loads((OUT / "ket-qua-bai-hat.json").read_text(encoding="utf-8"))
KEEP = ("name", "style", "length", "progressions", "modulate", "bpm", "seconds", "total_bars", "ending", "lufs",
        "true_peak_dbtp", "clipped_samples", "chorus_minus_verse_lu")
slim = []
for r in data["results"]:
    s = {k: r[k] for k in KEEP}
    s["sections"] = [{k: x[k] for k in ("type", "label", "energy", "design_energy", "transition", "start", "end", "note_vi", "lufs")}
                     for x in r["sections"]]
    s["surprises"] = [{"sec": round(x["sec"], 2), "label_vi": x["label_vi"]} for x in r["surprises"]]
    # Đường độ to: một điểm mỗi giây là đủ cho biểu đồ, file gọn.
    s["curve"] = [p for p in r["curve"] if abs(p[0] - round(p[0])) < 0.05]
    slim.append(s)
tpl = (ROOT / "scripts/backing-track/trang_bai_hat.template.html").read_text(encoding="utf-8")
html = tpl.replace("/*DATA*/null/*END*/", json.dumps({"date": data["date"], "results": slim}, ensure_ascii=False))
page = ("<!doctype html>\n<html lang=\"vi\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" "
        "content=\"width=device-width,initial-scale=1,viewport-fit=cover\"></head><body>\n" + html + "\n</body></html>\n")
(OUT / "index.html").write_text(page, encoding="utf-8")
(OUT / "artifact.html").write_text(html, encoding="utf-8")
print("ok", len(slim), "bài")
