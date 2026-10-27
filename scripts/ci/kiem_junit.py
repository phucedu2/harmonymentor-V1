"""Kiểm file JUnit XML của pytest trong CI và in số test thật.

Vì sao cần: pytest trả mã 0 cả khi mọi test bị skip (ví dụ thiếu TEST_DATABASE_URL thì 9 test HM-010 tự bỏ
qua). Script này bắt CI đỏ nếu có skip, có lỗi, hoặc số test đạt ít hơn mức tối thiểu.

Ví dụ: python scripts/ci/kiem_junit.py ket-qua.xml --min-passed 9 --title "PostgreSQL HM-010"
"""

from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET


def dem(path: str) -> dict[str, int]:
    """Đếm theo từng testcase thay vì đọc thuộc tính tổng, để không phụ thuộc định dạng của từng bản pytest."""
    root = ET.parse(path).getroot()
    so = {"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    for case in root.iter("testcase"):
        so["total"] += 1
        if case.find("failure") is not None:
            so["failed"] += 1
        elif case.find("error") is not None:
            so["errors"] += 1
        elif case.find("skipped") is not None:
            so["skipped"] += 1
        else:
            so["passed"] += 1
    # Lỗi lúc thu thập test (import hỏng) nằm ở testsuite chứ không thành testcase.
    for suite in root.iter("testsuite"):
        so["errors"] = max(so["errors"], int(suite.get("errors", 0)))
    return so


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("xml")
    ap.add_argument("--min-passed", type=int, default=1)
    ap.add_argument("--title", default="pytest")
    args = ap.parse_args()

    if not os.path.exists(args.xml):
        print(f"KHÔNG ĐẠT: không thấy {args.xml} (pytest không chạy tới cuối)", file=sys.stderr)
        return 1
    so = dem(args.xml)
    dong = (f"{args.title}: tổng {so['total']}, PASS {so['passed']}, FAIL {so['failed']}, "
            f"ERROR {so['errors']}, SKIP {so['skipped']}")
    print(dong)

    loi = []
    if so["failed"] or so["errors"]:
        loi.append("có test thất bại hoặc lỗi")
    if so["skipped"]:
        loi.append(f"có {so['skipped']} test bị skip (CI không chấp nhận skip)")
    if so["passed"] < args.min_passed:
        loi.append(f"chỉ {so['passed']} test đạt, cần ít nhất {args.min_passed}")

    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(f"### {args.title}\n\n| Tổng | PASS | FAIL | ERROR | SKIP |\n|---|---|---|---|---|\n"
                    f"| {so['total']} | {so['passed']} | {so['failed']} | {so['errors']} | {so['skipped']} |\n\n")
            f.write(("**Không đạt:** " + "; ".join(loi)) if loi else "Đạt.")
            f.write("\n\n")

    if loi:
        print("KHÔNG ĐẠT: " + "; ".join(loi), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
