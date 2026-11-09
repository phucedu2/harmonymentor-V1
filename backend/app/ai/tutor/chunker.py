"""Chia khối lý thuyết của bài đã phát hành thành đoạn 80–100 từ (04 mục 6.6, đề GĐ3 mục 1).

- Chỉ khối mang lời giảng; bỏ khối bài tập (checkpoint, piano có exercise_id), khối nháp (status draft,
  ví dụ "Thẻ ôn tự diễn đạt" chứa đáp án) và mọi bài nháp (L09–L12).
- Chia theo khối (mỗi khối có tiêu đề), không ghép hai khối, không cắt giữa câu. Một câu dài hơn 100 từ
  đứng riêng thành một đoạn thay vì bị cắt.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any, Iterable

WORDS_MIN, WORDS_MAX = 80, 100
# Khối có lời giảng. checkpoint/piano/compose_link/explorer là tương tác hoặc bài tập, không đưa vào kho.
TEXT_BLOCKS = {"theory", "glossary", "callout", "summary", "audio", "progression", "interactive",
               "key_overview", "notation"}


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    lesson_id: str
    block_id: str
    title: str
    text: str
    source: str
    content_hash: str
    search_hint: str = ""   # chỉ dùng để tìm (câu hỏi mẫu của mục hướng dẫn), không hiện cho người học

    def embed_text(self, lesson_title: str = "") -> str:
        head = f"{lesson_title} — {self.title}" if lesson_title else self.title
        hint = f"\n{self.search_hint}" if self.search_hint else ""
        return f"{head}{hint}\n{self.text}"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", " ".join(str(text).split()))


def block_text(block_type: str, payload: dict[str, Any]) -> str:
    """Văn bản hiển thị của một khối, theo đúng thứ tự trên trang."""
    parts: list[str] = []
    if block_type == "glossary":
        parts.append(payload.get("intro", ""))
        for t in payload.get("terms", []):
            line = f"{t.get('symbol', '')} ({t.get('term', '')}): {t.get('definition', '')}"
            if t.get("example"):
                line += f" Ví dụ: {t['example']}."
            parts.append(line)
    else:
        parts.extend(payload.get("paragraphs", []))
        parts.extend(payload.get("items", []) if all(isinstance(i, str) for i in payload.get("items", [])) else [])
        for key in ("prompt", "caption", "note"):
            if payload.get(key):
                parts.append(payload[key])
    return _nfc(" ".join(p.strip() for p in parts if p and p.strip()))


_SENT = re.compile(r"(?<=[.!?…])\s+(?=[A-ZĐÀ-Ỹ0-9“\"(•–-])")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT.split(text) if s.strip()]


def _words(text: str) -> int:
    return len(text.split())


def _hash(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def chunk_block(lesson_id: str, block_id: str, title: str, text: str, source: str) -> list[Chunk]:
    groups: list[list[str]] = []
    cur: list[str] = []
    for sentence in split_sentences(text):
        if cur and _words(" ".join(cur)) + _words(sentence) > WORDS_MAX:
            groups.append(cur)
            cur = []
        cur.append(sentence)
        if _words(" ".join(cur)) >= WORDS_MIN:
            groups.append(cur)
            cur = []
    if cur:
        # GĐ2 đã thử gộp đuôi ngắn (< 30 từ) vào đoạn trước và thêm ngữ cảnh tìm kiếm cho khối ngắn (GĐ0 lỗ hổng 7):
        # R@1 bộ chuẩn GĐ4 với e5 giảm 90,0% → 83,3% nên KHÔNG giữ (docs/giai-doan/ai-gop-y/02_DU_LIEU.md).
        groups.append(cur)
    out = []
    for n, group in enumerate(groups, start=1):
        body = " ".join(group)
        # Hash chỉ gồm phần được nhúng (không gồm nguồn): đổi nguồn không làm vector cũ "lệch" (GĐ2, nguồn theo khối).
        out.append(Chunk(f"{block_id}#{n}", lesson_id, block_id, _nfc(title), body, source,
                         _hash(lesson_id, block_id, title, body)))
    return out


def lesson_source(spec: dict[str, Any], registry: dict[str, Any]) -> str:
    names = []
    for s in spec.get("sources", []):
        work = registry.get(s["source_id"], {})
        title = work.get("title", s["source_id"]) if isinstance(work, dict) else getattr(work, "title", s["source_id"])
        names.append(f"{title} · {s['locator']}")
    return "; ".join(names)


# Nguồn theo KHỐI (GĐ0 lỗ hổng 8): trước đây mọi đoạn mang nguồn của cả bài, nên câu trả lời về quãng có thể ghi
# tên chương hợp âm bảy. Gắn chủ đề cho khối và cho từng nguồn của bài bằng cùng một bảng từ khóa, rồi giữ các nguồn
# trùng chủ đề. Không trùng chủ đề nào thì giữ nguồn của cả bài (như cũ) chứ không bỏ trống.
# Bảng chủ đề viết dựa trên locator/note của nguồn trong curriculum_specs; nhãn "draft", chờ Đạt duyệt (GĐ2 10A).
_TOPICS = {
    "interval": ("quãng", "nửa cung", "interval", "enharmonic", "đồng âm", "bàn phím", "phím", "tên nốt", "notation"),
    "triad": ("triad", "hợp âm ba", "ba nốt"),
    "scale": ("âm giai", "scale", "major scale", "bậc 1", "giọng"),
    "seventh": ("seventh", "hợp âm bảy", "maj7", "m7", "ø7", "four-part", "four/five-part"),
    "roman": ("la mã", "roman", "diatonic"),
    "function": ("chức năng", "function", "tonic", "predominant", "subdominant", "dominant", "phrase", "cadence"),
    "iivi": ("ii–v–i", "ii-v-i", "ii–v", "guide", "voice leading", "voicing", "common tone"),
}


def topics(text: str) -> set[str]:
    low = text.lower()
    return {t for t, words in _TOPICS.items() if any(w in low for w in words)}


def block_source(spec: dict[str, Any], registry: dict[str, Any], title: str, text: str) -> str:
    """Nguồn của một khối: các nguồn của bài có chủ đề trùng với khối; không trùng thì nguồn cả bài."""
    # Tiêu đề khối nói đúng chủ đề; lời giảng hay nhắc lại khái niệm bài trước ("nửa cung", "triad") nên chỉ dùng
    # khi tiêu đề không mang chủ đề nào.
    want = topics(title) or topics(text)
    picked = [s for s in spec.get("sources", []) if want & topics(f"{s['locator']} {s.get('note', '')}")]
    return lesson_source({"sources": picked}, registry) if picked else lesson_source(spec, registry)


def published_lesson_specs() -> Iterable[dict[str, Any]]:
    """Bài người học thấy và không phải nháp. Bài nháp nằm ở draft_specs nên không bao giờ vào đây."""
    from ...content.curriculum_specs import LESSON_SPECS

    return [s for s in LESSON_SPECS if s.get("status") != "draft"]


def lesson_chunks() -> list[Chunk]:
    from ...content.draft_l06_l08 import TUTOR_KB_PENDING
    from ...content.draft_specs import blocks_with_drafts
    from ...content.source_registry import SOURCE_REGISTRY

    out: list[Chunk] = []
    for spec in published_lesson_specs():
        if spec["id"] in TUTOR_KB_PENDING:
            continue  # bài đã duyệt cho người học nhưng chưa đo lại định tuyến khi nạp vào kho
        for block_id, block_type, payload in blocks_with_drafts(spec):
            if block_type not in TEXT_BLOCKS or (payload or {}).get("status") == "draft":
                continue
            if payload.get("exercise_id"):
                continue  # khối gắn câu bài tập: không đưa đề/đáp án vào kho
            text = block_text(block_type, payload)
            if _words(text) < 5:
                continue
            title = payload.get("title", block_id)
            source = block_source(spec, SOURCE_REGISTRY, title, text)
            out.extend(chunk_block(spec["id"], block_id, title, text, source))
    return out


def lesson_titles() -> dict[str, str]:
    return {s["id"]: s["title"] for s in published_lesson_specs()}
