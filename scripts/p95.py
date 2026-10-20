"""Bảng độ trễ p50/p95 theo route từ log truy cập JSON của API (NFR-01, NFR-24).

Cách dùng:
    docker compose logs api --no-log-prefix | python scripts/p95.py
    python scripts/p95.py access.log --min-count 5

Mỗi dòng log là JSON do backend/app/core/middleware.py ghi; dòng khác (log uvicorn) bị bỏ qua.
Gộp theo mẫu route (/api/v1/lessons/{lesson_id}) chứ không theo đường dẫn thật, để các id khác nhau
cùng vào một nhóm.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from typing import Iterable, TextIO


def percentile(values: list[float], pct: float) -> float:
    """Phân vị kiểu nearest-rank: p95 của 20 giá trị là giá trị thứ 19 sau khi sắp xếp."""
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return ordered[rank - 1]


def parse_lines(lines: Iterable[str]) -> dict[str, list[float]]:
    groups: dict[str, list[float]] = defaultdict(list)
    for line in lines:
        start = line.find("{")
        if start < 0:
            continue
        try:
            entry = json.loads(line[start:])
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict) or "duration_ms" not in entry:
            continue
        key = f"{entry.get('method', '?')} {entry.get('route') or entry.get('path', '?')}"
        groups[key].append(float(entry["duration_ms"]))
    return groups


def render(groups: dict[str, list[float]], min_count: int) -> str:
    rows = [(k, v) for k, v in groups.items() if len(v) >= min_count]
    rows.sort(key=lambda kv: percentile(kv[1], 95), reverse=True)
    out = ["| Route | Số request | p50 (ms) | p95 (ms) | Max (ms) |", "|---|---:|---:|---:|---:|"]
    for key, values in rows:
        out.append(f"| `{key}` | {len(values)} | {percentile(values, 50):.1f} | {percentile(values, 95):.1f} | {max(values):.1f} |")
    return "\n".join(out)


def main(argv: list[str] | None = None, stdin: TextIO = sys.stdin) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("logfile", nargs="?", help="File log; bỏ trống thì đọc stdin")
    parser.add_argument("--min-count", type=int, default=1, help="Bỏ route có ít request hơn số này")
    args = parser.parse_args(argv)
    if args.logfile:
        with open(args.logfile, encoding="utf-8") as fh:
            groups = parse_lines(fh)
    else:
        groups = parse_lines(stdin)
    if not groups:
        print("Không tìm thấy dòng log JSON nào có duration_ms.", file=sys.stderr)
        return 1
    print(render(groups, args.min_count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
