"""Khối ví dụ do Quản trị viên thêm vào bài tự tạo (FR-ADM-35..37, Phúc 8A, 25/11/2026).

- example_chord: gõ ký hiệu hợp âm, Music Engine tính các nốt; người học bấm nút nghe (Web Audio).
- example_scale: chủ âm + loại âm giai, Engine tính các nốt; nghe từng nốt đi lên.
- example_audio: tải file mp3/wav (tối đa 5 MB) kèm nguồn và giấy phép bắt buộc, vì đây là âm thanh người khác có thể có bản quyền.

Các nốt tính lúc lưu và nằm trong khối; câu mô tả (`paragraphs`) cũng do Engine dựng nên vào được kho AI Tutor.
Chỉ bài M-/AI-; muốn đổi thì xóa khối rồi thêm lại (khối không có phiên bản).
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from ..db.models import LessonBlock, MediaFile, User
from ..music_engine import tools as engine
from ..music_engine.scale import SCALE_TYPES
from . import lesson_admin as la
from .content_service import AdminContentError, audit
from .question_templates import SCALE_VI

MAX_AUDIO = 5 * 1024 * 1024
AUDIO_TYPES = {".mp3": "audio/mpeg", ".wav": "audio/wav"}


def _s(value: Any, size: int) -> str:
    return str(value or "").strip()[:size]


def _append(db: Session, admin: User, lesson_id: str, block_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    lesson = la._lesson(db, lesson_id)
    la._editable(lesson)
    pos = max((b.position for b in lesson.blocks), default=0) + 1
    block_id = la._next_block_id(db, lesson_id)
    db.add(LessonBlock(id=block_id, lesson_id=lesson_id, position=pos, block_type=block_type, payload=payload))
    audit(db, admin, "lesson.add_example", "lesson", lesson_id, {"block": block_id, "block_type": block_type})
    db.commit()
    la._reindex(db, admin, lesson)
    return {"id": block_id, "position": pos, "block_type": block_type, "payload": payload}


def add_chord(db: Session, admin: User, lesson_id: str, item: Any) -> dict[str, Any]:
    item = item if isinstance(item, dict) else {}
    symbol, title = _s(item.get("symbol"), 40), _s(item.get("title"), 200)
    out = engine.get_chord_tones(symbol=symbol) if symbol else {"ok": False}
    if not out.get("ok"):
        raise AdminContentError("EXAMPLE_CHORD", f"Music Engine không hiểu hợp âm “{symbol}”. Kiểm lại ký hiệu (ví dụ Cmaj7, Ebm7b5).")
    notes = out["notes"]
    payload = {"title": title or f"Hợp âm {out['symbol']}", "symbol": out["symbol"], "notes": notes,
               "paragraphs": [f"Hợp âm {out['symbol']} gồm các nốt {'–'.join(notes)}."]}
    if _s(item.get("note"), 600):
        payload["note"] = _s(item.get("note"), 600)
    return _append(db, admin, lesson_id, "example_chord", payload)


def add_scale(db: Session, admin: User, lesson_id: str, item: Any) -> dict[str, Any]:
    item = item if isinstance(item, dict) else {}
    tonic, st, title = _s(item.get("tonic"), 8), _s(item.get("scale_type"), 40), _s(item.get("title"), 200)
    if st not in SCALE_TYPES:
        raise AdminContentError("EXAMPLE_SCALE", "Loại âm giai phải là: " + ", ".join(SCALE_TYPES) + ".")
    out = engine.get_scale(tonic=tonic, scale_type=st) if tonic else {"ok": False}
    if not out.get("ok"):
        raise AdminContentError("EXAMPLE_SCALE", f"Music Engine không hiểu chủ âm “{tonic}”. Kiểm lại tên nốt (ví dụ C, F#, Bb).")
    notes = out["notes"]
    name = f"{tonic} {SCALE_VI.get(st, st)}"
    payload = {"title": title or f"Âm giai {name}", "tonic": tonic, "scale_type": st, "notes": notes,
               "paragraphs": [f"Âm giai {name} gồm các nốt {'–'.join(notes)}."]}
    if _s(item.get("note"), 600):
        payload["note"] = _s(item.get("note"), 600)
    return _append(db, admin, lesson_id, "example_scale", payload)


def _sniff(ext: str, data: bytes) -> bool:
    """Đuôi file có thể bị đổi tên: kiểm byte đầu để không nhận file lạ làm âm thanh."""
    if ext == ".wav":
        return data[:4] == b"RIFF" and data[8:12] == b"WAVE"
    return data[:3] == b"ID3" or (len(data) > 2 and data[0] == 0xFF and data[1] & 0xE0 == 0xE0)


def add_audio(db: Session, admin: User, lesson_id: str, filename: str, data: bytes, form: dict[str, Any]) -> dict[str, Any]:
    la._editable(la._lesson(db, lesson_id))
    ext = "." + filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in AUDIO_TYPES:
        raise AdminContentError("AUDIO_TYPE", "Chỉ nhận file .mp3 hoặc .wav.")
    if not data:
        raise AdminContentError("AUDIO_EMPTY", "File rỗng.")
    if len(data) > MAX_AUDIO:
        raise AdminContentError("AUDIO_TOO_LARGE", "File âm thanh tối đa 5 MB.")
    if not _sniff(ext, data):
        raise AdminContentError("AUDIO_CONTENT", f"Nội dung file không đúng định dạng {ext}.")
    source, licence, title = _s(form.get("source"), 300), _s(form.get("license"), 200), _s(form.get("title"), 200)
    if not source or not licence:
        raise AdminContentError("AUDIO_LICENSE", "Cần ghi nguồn và giấy phép của file (ví dụ: tự thu, hoặc CC0 từ …).")
    if not title:
        raise AdminContentError("AUDIO_TITLE", "Cần tiêu đề cho ví dụ nghe.")
    media_id = uuid4().hex
    db.add(MediaFile(id=media_id, filename=_s(filename, 200), content_type=AUDIO_TYPES[ext], size=len(data), data=data,
                     created_by=admin.id))
    db.flush()
    payload = {"title": title, "src": f"/api/v1/media/{media_id}", "media_id": media_id, "source": source, "license": licence}
    if _s(form.get("note"), 600):
        payload["note"] = _s(form.get("note"), 600)
    return _append(db, admin, lesson_id, "example_audio", payload)


def _block(db: Session, lesson_id: str, block_id: str, types: tuple[str, ...]) -> LessonBlock:
    lesson = la._lesson(db, lesson_id)
    la._editable(lesson)
    block = next((b for b in lesson.blocks if b.id == block_id), None)
    if block is None or block.block_type not in types:
        raise AdminContentError("EXAMPLE_NOT_FOUND", "Không có khối ví dụ này trong bài.", 404)
    return block


def update(db: Session, admin: User, lesson_id: str, block_id: str, item: Any) -> dict[str, Any]:
    """Sửa khối ví dụ tại chỗ (ví dụ hợp âm/âm giai tính lại bằng Engine; ví dụ nghe sửa chữ, giữ file). Giá trị cũ vào nhật ký."""
    item = item if isinstance(item, dict) else {}
    block = _block(db, lesson_id, block_id, ("example_chord", "example_scale", "example_audio"))
    old = dict(block.payload)
    note = _s(item.get("note"), 600)
    if block.block_type == "example_audio":
        title, source, licence = _s(item.get("title"), 200), _s(item.get("source"), 300), _s(item.get("license"), 200)
        if not title or not source or not licence:
            raise AdminContentError("AUDIO_LICENSE", "Ví dụ nghe cần tiêu đề, nguồn và giấy phép.")
        new = {**old, "title": title, "source": source, "license": licence}
    elif block.block_type == "example_chord":
        symbol = _s(item.get("symbol"), 40)
        out = engine.get_chord_tones(symbol=symbol) if symbol else {"ok": False}
        if not out.get("ok"):
            raise AdminContentError("EXAMPLE_CHORD", f"Music Engine không hiểu hợp âm “{symbol}”. Kiểm lại ký hiệu (ví dụ Cmaj7, Ebm7b5).")
        new = {"title": _s(item.get("title"), 200) or f"Hợp âm {out['symbol']}", "symbol": out["symbol"], "notes": out["notes"],
               "paragraphs": [f"Hợp âm {out['symbol']} gồm các nốt {'–'.join(out['notes'])}."]}
    else:
        tonic, st = _s(item.get("tonic"), 8), _s(item.get("scale_type"), 40)
        out = engine.get_scale(tonic=tonic, scale_type=st) if tonic and st in SCALE_TYPES else {"ok": False}
        if not out.get("ok"):
            raise AdminContentError("EXAMPLE_SCALE", "Chủ âm hoặc loại âm giai không hợp lệ.")
        name = f"{tonic} {SCALE_VI.get(st, st)}"
        new = {"title": _s(item.get("title"), 200) or f"Âm giai {name}", "tonic": tonic, "scale_type": st, "notes": out["notes"],
               "paragraphs": [f"Âm giai {name} gồm các nốt {'–'.join(out['notes'])}."]}
    if note:
        new["note"] = note
    else:
        new.pop("note", None)
    block.payload = new
    audit(db, admin, "lesson.update_example", "lesson", lesson_id, {"block": block_id, "from": old, "to": new})
    db.commit()
    la._reindex(db, admin, la._lesson(db, lesson_id))
    return {"id": block_id, "block_type": block.block_type, "payload": new}
