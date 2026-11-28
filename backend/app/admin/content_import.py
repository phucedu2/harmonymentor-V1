"""Nhập nội dung từ file JSON/YAML (FR-ADM-39, Phúc 4A).

Một file gồm một hay nhiều bài: khối lý thuyết, câu luyện tập, nguồn. Mỗi bài và mỗi câu có mã cố định (`code`, `key`)
nên nhập lại cùng file là CẬP NHẬT chứ không tạo bản trùng:
- bài mới → tạo bài M-<code>, ẩn tới khi Quản trị viên bấm hiện (giống bài tạo bằng form, ADR-035);
- khối đổi → dựng lại các khối theo file (file là nguồn sự thật của bài nhập);
- câu đổi đề/đáp án → thêm phiên bản mới (ADR-006), câu không đổi → giữ nguyên;
- thẻ ôn (`cards`) cũng theo mã `key`: id `<bài>-R-<key>`, đổi nội dung thì ghi đè tại chỗ, thẻ từng xóa mềm mà file còn thì dùng lại;
- câu và thẻ có trong CSDL mà file không còn → KHÔNG tự bỏ, chỉ báo để Quản trị viên quyết.

Kiểm hết rồi mới ghi: một lỗi ở bất kỳ đâu (Engine tính khác đáp án, thiếu lời giải, nguồn không có…) thì không ghi gì
và trả danh sách lỗi kèm vị trí, để file sửa một lần là nhập được.
Chỉ nhập vào bài M-…: bài gốc L01… đổi qua curriculum_specs (seed ghi đè mỗi lần khởi động).
"""

from __future__ import annotations

import json
import re
from typing import Any

import yaml
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..db.models import ContentRevision, Exercise, Lesson, LessonBlock, LessonSource, ReviewItem, SourceWork, User
from . import card_admin as ca
from . import lesson_admin as la
from . import skill_admin
from .content_service import AdminContentError, audit

FORMAT = "harmonymentor/1"
MAX_BYTES = 1_000_000
MAX_LESSONS = 20
_CODE = re.compile(r"^[a-z0-9][a-z0-9-]{1,40}$")

TEMPLATE = """# Mẫu file nhập nội dung HarmonyMentor (FR-ADM-39). Lưu thành .yaml hoặc đổi sang JSON cùng cấu trúc.
format: harmonymentor/1
lessons:
  - code: hop-am-ba-truong          # mã cố định: chữ thường, số, gạch nối. Nhập lại cùng mã = cập nhật bài.
    title: Hợp âm ba trưởng
    objectives:
      - Nhận ra cấu tạo hợp âm ba trưởng
    blocks:
      - title: Cấu tạo
        paragraphs:
          - Hợp âm ba trưởng gồm nốt gốc, quãng 3 trưởng và quãng 5 đúng.
    sources:                         # bắt buộc ít nhất một nguồn: `source_id` có sẵn, hoặc `title` (+ author, url) để tạo mới
      - title: Giáo trình nhạc lý cơ bản
        author: Tên tác giả
        locator: Chương 2, trang 14
    exercises:
      - key: q1                      # mã câu cố định trong bài
        kind: build_chord            # mcq | true_false | multi_select | short | build_chord | build_scale | open
        level: hieu                  # nho | hieu | van_dung
        skill_id: chord.triad_build
        prompt: Hợp âm C gồm những nốt nào?
        symbol: C
        explanation: C – E – G là gốc, quãng 3 trưởng và quãng 5 đúng.
    cards:                           # thẻ ôn (không bắt buộc): recall | self_check | build_chord | build_scale | interval | roman
      - key: t1
        kind: build_scale
        skill_id: scale.major
        front: Viết âm giai G trưởng.
        tonic: G
        scale_type: major
"""


def _parse(raw: bytes, filename: str) -> Any:
    if len(raw) > MAX_BYTES:
        raise AdminContentError("IMPORT_TOO_LARGE", "File nhập tối đa 1 MB.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise AdminContentError("IMPORT_ENCODING", "File phải lưu dạng UTF-8.") from exc
    try:
        if filename.lower().endswith(".json"):
            return json.loads(text)
        return yaml.safe_load(text)   # safe_load: không dựng đối tượng Python tùy ý từ file
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise AdminContentError("IMPORT_SYNTAX", f"File sai cú pháp: {str(exc).splitlines()[0][:200]}") from exc


def _lines(raw: Any) -> list[str]:
    return la._clean_lines(raw, 30, 2000)


def _validate(db: Session, data: Any) -> tuple[list[dict[str, Any]], list[str]]:
    """Kiểm cả file, trả (các bài đã chuẩn hóa, lỗi). Không ghi gì."""
    errors: list[str] = []
    if not isinstance(data, dict) or data.get("format") != FORMAT:
        return [], [f"Dòng đầu phải có `format: {FORMAT}` (tải file mẫu để xem)."]
    lessons = data.get("lessons")
    if not isinstance(lessons, list) or not lessons:
        return [], ["File cần mục `lessons` có ít nhất một bài."]
    if len(lessons) > MAX_LESSONS:
        return [], [f"Mỗi lần nhập tối đa {MAX_LESSONS} bài."]
    out, codes = [], set()
    for i, raw in enumerate(lessons, start=1):
        where = f"Bài {i}"
        if not isinstance(raw, dict):
            errors.append(f"{where}: phải là một mục có code, title, blocks…")
            continue
        code = str(raw.get("code") or "").strip()
        if not _CODE.match(code):
            errors.append(f"{where}: `code` chỉ gồm chữ thường không dấu, số, gạch nối (2–41 ký tự).")
        elif code in codes:
            errors.append(f"{where}: `code` “{code}” bị lặp trong file.")
        codes.add(code)
        where = f"Bài “{code or i}”"
        title = str(raw.get("title") or "").strip()[:240]
        if not title:
            errors.append(f"{where}: thiếu `title`.")
        blocks = []
        for j, b in enumerate(raw.get("blocks") or [], start=1):
            bt = str((b or {}).get("title") or "").strip()[:200] if isinstance(b, dict) else ""
            paras = _lines(b.get("paragraphs")) if isinstance(b, dict) else []
            if not bt or not paras:
                errors.append(f"{where}, khối {j}: cần `title` và ít nhất một đoạn trong `paragraphs`.")
            blocks.append({"title": bt, "paragraphs": paras})
        if not blocks:
            errors.append(f"{where}: cần ít nhất một khối trong `blocks`.")
        sources = []
        for j, src in enumerate(raw.get("sources") or [], start=1):
            sid = str((src or {}).get("source_id") or "").strip() if isinstance(src, dict) else ""
            src_title = str((src or {}).get("title") or "").strip()[:300] if isinstance(src, dict) else ""
            # 27/11/2026 (Phúc 2A): bỏ mục Nguồn khỏi giao diện, nên file được tự khai nguồn mới bằng `title`.
            if not sid and src_title:
                found = db.scalar(select(SourceWork.id).where(SourceWork.title == src_title))
                new = None if found else {"title": src_title, "author": str(src.get("author") or "").strip()[:200] or None,
                                          "url": str(src.get("url") or "").strip()[:500] or None}
                sources.append({"source_id": found, "new": new, "locator": str(src.get("locator") or "").strip()[:300] or "toàn bộ",
                                "note": str(src.get("note") or "").strip()[:1000] or None})
                continue
            if not sid or db.get(SourceWork, sid) is None:
                errors.append(f"{where}, nguồn {j}: không có nguồn “{sid}”. Ghi `title` (tên tài liệu) để tạo nguồn mới.")
                continue
            sources.append({"source_id": sid, "new": None, "locator": str(src.get("locator") or "").strip()[:300] or "toàn bộ",
                            "note": str(src.get("note") or "").strip()[:1000] or None})
        if not (raw.get("sources") or []):
            errors.append(f"{where}: cần ít nhất một nguồn trong `sources` (nguyên tắc 11: giữ nguồn của bài).")
        exercises, keys = [], set()
        for j, item in enumerate(raw.get("exercises") or [], start=1):
            key = str((item or {}).get("key") or "").strip() if isinstance(item, dict) else ""
            if not _CODE.match(key):
                errors.append(f"{where}, câu {j}: `key` chỉ gồm chữ thường không dấu, số, gạch nối.")
                continue
            if key in keys:
                errors.append(f"{where}, câu {j}: `key` “{key}” bị lặp.")
                continue
            keys.add(key)
            try:
                q = la._normalize(db, {k: v for k, v in item.items() if k != "key"})
            except AdminContentError as exc:
                errors.append(f"{where}, câu “{key}”: {exc.message}")
                continue
            exercises.append({"key": key, "q": q})
        cards, ckeys = [], set()
        for j, item in enumerate(raw.get("cards") or [], start=1):
            key = str((item or {}).get("key") or "").strip() if isinstance(item, dict) else ""
            if not _CODE.match(key):
                errors.append(f"{where}, thẻ {j}: `key` chỉ gồm chữ thường không dấu, số, gạch nối.")
                continue
            if key in ckeys:
                errors.append(f"{where}, thẻ {j}: `key` “{key}” bị lặp.")
                continue
            ckeys.add(key)
            try:
                cards.append({"key": key, "n": ca._normalize(db, {k: v for k, v in item.items() if k != "key"})})
            except AdminContentError as exc:
                errors.append(f"{where}, thẻ “{key}”: {exc.message}")
        out.append({"code": code, "title": title, "objectives": la._clean_lines(raw.get("objectives"), 10, 300),
                    "blocks": blocks, "sources": sources, "exercises": exercises, "cards": cards})
    return out, errors


def _sync_blocks(db: Session, lesson: Lesson, blocks: list[dict[str, Any]]) -> bool:
    current = [b.payload for b in sorted(lesson.blocks, key=lambda b: b.position)]
    if current == blocks:
        return False
    # File là nguồn sự thật của bài nhập: dựng lại khối, bỏ bản sửa chữ cũ của các khối đó để không đè lên nội dung mới.
    db.execute(delete(ContentRevision).where(ContentRevision.lesson_id == lesson.id, ContentRevision.kind == "block"))
    db.execute(delete(LessonBlock).where(LessonBlock.lesson_id == lesson.id))
    db.flush()
    db.expire(lesson, ["blocks"])
    for pos, payload in enumerate(blocks, start=1):
        db.add(LessonBlock(id=f"{lesson.id}-B{pos:02d}", lesson_id=lesson.id, position=pos, block_type="theory", payload=payload))
    db.flush()
    return True


def import_content(db: Session, admin: User, raw: bytes, filename: str, dry_run: bool = False) -> dict[str, Any]:
    data = _parse(raw, filename)
    lessons, errors = _validate(db, data)
    if errors:
        raise AdminContentError("IMPORT_INVALID", f"File có {len(errors)} lỗi, chưa nhập gì: " + " | ".join(errors[:30]))
    report: list[dict[str, Any]] = []
    for item in lessons:
        lesson_id = f"M-{item['code']}"
        lesson = db.get(Lesson, lesson_id)
        row: dict[str, Any] = {"id": lesson_id, "title": item["title"], "created": lesson is None, "blocks_changed": False,
                               "exercises_added": [], "exercises_revised": [], "exercises_not_in_file": [], "sources_added": 0,
                               "cards_added": [], "cards_revised": [], "cards_not_in_file": []}
        if lesson is None:
            created = la.create_lesson(db, admin, item["title"], item["objectives"], item["blocks"][0]["title"],
                                       item["blocks"][0]["paragraphs"], lesson_id=lesson_id, commit=False)
            lesson = db.get(Lesson, created["id"])
        elif lesson.deleted_at is not None:
            raise AdminContentError("IMPORT_DELETED", f"Bài {lesson_id} đã bị xóa. Khôi phục bài trước rồi nhập lại.", 409)
        else:
            lesson.title, lesson.objectives = item["title"], item["objectives"]
        changed = _sync_blocks(db, lesson, item["blocks"])
        row["blocks_changed"] = changed and not row["created"]
        for src in item["sources"]:
            if src["new"] is not None:   # nguồn khai trong file: tạo một lần, lần nhập sau tìm theo tên
                src["source_id"] = db.scalar(select(SourceWork.id).where(SourceWork.title == src["new"]["title"])) \
                    or skill_admin.new_source(db, admin, **src["new"])
            exists = db.scalar(select(LessonSource.id).where(LessonSource.lesson_id == lesson_id,
                                                             LessonSource.source_work_id == src["source_id"],
                                                             LessonSource.locator == src["locator"]))
            if exists is None:
                db.add(LessonSource(lesson_id=lesson_id, source_work_id=src["source_id"], locator=src["locator"], note=src["note"]))
                row["sources_added"] += 1
        db.flush()
        wanted = set()
        for ex_item in item["exercises"]:
            ex_id = f"{lesson_id}-{ex_item['key']}"
            wanted.add(ex_id)
            ex = db.get(Exercise, ex_id)
            if ex is None:
                db.refresh(lesson)
                la._insert_exercise(db, lesson, ex_id, ex_item["q"])
                row["exercises_added"].append(ex_id)
            elif ex.deleted_at is not None:
                ex.deleted_at, ex.active = None, True   # câu từng bỏ mà file vẫn có → dùng lại
                version = la._revise_exercise(db, ex, ex_item["q"])
                row["exercises_revised"].append(ex_id if version is None else f"{ex_id} (bản {version})")
            else:
                version = la._revise_exercise(db, ex, ex_item["q"])
                if version is not None:
                    row["exercises_revised"].append(f"{ex_id} (bản {version})")
        db.refresh(lesson)
        row["exercises_not_in_file"] = sorted(e.id for e in lesson.exercises if e.deleted_at is None and e.id not in wanted)
        la._ensure_work(db)
        want_cards = set()
        for c in item["cards"]:
            cid = f"{lesson_id}-R-{c['key']}"
            want_cards.add(cid)
            n = c["n"]
            fields = dict(skill_id=n["skill"], mode=n["mode"], front=n["grader_config"]["form"]["front"], back=n["back"],
                          grading_strategy=n["strategy"], answer_key=n["answer_key"], grader_config=n["grader_config"])
            card = db.get(ReviewItem, cid)
            if card is None:
                db.add(ReviewItem(id=cid, lesson_id=lesson_id, **fields,
                                  provenance=[{"source_id": la.ADMIN_WORK_ID, "locator": None, "note": "Nhập từ file"}]))
                row["cards_added"].append(cid)
            else:
                changed = card.deleted_at is not None or any(getattr(card, k) != v for k, v in fields.items())
                for k, v in fields.items():
                    setattr(card, k, v)
                card.deleted_at = None
                if changed:
                    row["cards_revised"].append(cid)
        db.flush()
        row["cards_activated_for"] = ca.activate_for_completed(db, lesson_id) if row["cards_added"] else 0
        db.refresh(lesson)
        row["cards_not_in_file"] = sorted(c.id for c in lesson.review_items
                                          if c.deleted_at is None and ca._is_admin_card(c) and c.id not in want_cards)
        report.append(row)
    if dry_run:
        db.rollback()
        return {"dry_run": True, "lessons": report}
    audit(db, admin, "content.import", "lesson", ",".join(r["id"] for r in report)[:64],
          {"file": filename[:200], "lessons": [{k: r[k] for k in ("id", "created", "blocks_changed", "exercises_added",
                                                                  "exercises_revised")} for r in report]})
    db.commit()
    for r in report:
        lesson = db.get(Lesson, r["id"])
        la._reindex(db, admin, lesson)
    return {"dry_run": False, "lessons": report}
