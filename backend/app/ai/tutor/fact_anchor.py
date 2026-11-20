"""Neo câu trả lời vào dữ kiện Music Engine (G8, chấm nhạc lý Gemini 16/11/2026).

Guardrail cũ chỉ bắt khi AI VIẾT SAI một nốt/quãng/số La Mã mà nó khai là của Engine. Lượt chấm đầu cho thấy hai lỗi nó
không bắt được: (1) AI không nêu kết quả mà từ chối ("mình không tự tính nốt"), (2) AI nêu kết quả khác Engine ở các mục
guardrail không quét (hóa biểu, giọng tương quan, đảo quãng, bậc ghi sai hoa/thường). Ở đây: câu hỏi đòi MỘT dữ kiện trực
tiếp và Engine đã tính được, thì câu trả lời phải chứa kết quả đó, nếu không thì soạn lại 1 lần rồi dùng câu Engine viết sẵn.
Chỉ nhận diện và đối chiếu, không tự tính nhạc lý."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Sequence

from .notes import norm_accidentals, solfege_to_letters

# Câu đòi dữ kiện trực tiếp. Câu khái niệm ("vì sao G7 muốn về C?") không khớp nên không bị ép nêu kết quả.
_DIRECT = re.compile(
    r"gồm|nốt nào|nốt gì|not nao|not gi|liệt kê|liet ke|các nốt|cac not|cấu tạo|cau tao|quãng gì|quang gi|quãng mấy|"
    r"quang may|là quãng|bậc mấy|bac may|số la mã|so la ma|dấu hóa|dau hoa|hóa biểu|hoa bieu|tương quan|tuong quan|"
    r"đảo quãng|dao quang|nửa cung|nua cung|giọng .{0,20} nào|notes? (?:are|in)|what interval|which key|how many|"
    r"guide tone|shell voicing|hợp âm gì|hợp âm nào|những hợp âm|hợp âm mượn.{0,40}(?:là gì|nào)|ii.?v.?i in ",
    re.IGNORECASE)
_NOTE = re.compile(r"(?<![\w#])([A-G](?:bb|b|##|#)?)(?![\w#])")
_NUM_WORD = {"1": ("1", "một", "nhất"), "2": ("2", "hai", "nhì"), "3": ("3", "ba"), "4": ("4", "bốn", "tư"),
             "5": ("5", "năm"), "6": ("6", "sáu"), "7": ("7", "bảy"), "8": ("8", "tám")}
_QUALITY = {"P": ("đúng",), "M": ("trưởng",), "m": ("thứ",), "A": ("tăng",), "d": ("giảm", "bớt")}


def _fold(text: str) -> str:
    t = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _notes(text: str) -> set[str]:
    return set(_NOTE.findall(norm_accidentals(solfege_to_letters(text))))


def _interval_named(reply: str, name: str) -> bool:
    if re.search(rf"(?<![\w]){re.escape(name)}(?![\w])", reply):
        return True
    quality, num = name[0], name[1:]
    folded = _fold(reply)
    words = "|".join(re.escape(_fold(w)) for w in _NUM_WORD.get(num, (num,)))
    quals = "|".join(re.escape(_fold(q)) for q in _QUALITY.get(quality, ()))
    if not quals:
        return False
    return bool(re.search(rf"\b(?:{words})\s+(?:{quals})\b|\b(?:{quals})\s+(?:{words})\b", folded))


def honoured(reply: str, f: dict[str, Any]) -> bool:
    """Câu trả lời có nêu đúng kết quả của dữ kiện Engine f không."""
    tool, args, result = f["tool"], f["args"], str(f["result"])
    if tool in ("get_chord_tones", "get_scale", "signature_order"):
        want = set(norm_accidentals(result).replace("#", "#").split())
        return want <= _notes(reply)
    if tool in ("identify_interval", "invert_interval"):
        return _interval_named(reply, result)
    if tool == "get_roman_numeral":
        base = re.sub(r"(?:maj7|M7|ø7|°7|7)$", "", result)
        return re.search(rf"(?<![A-Za-z]){re.escape(base)}(?![A-Za-z°ø])", reply) is not None
    if tool == "interval_size":
        return re.search(rf"(?<!\d){re.escape(result)}(?!\d)", reply) is not None
    if tool == "key_signature":
        if result.startswith("không"):
            return "không" in reply.lower() or "khong" in _fold(reply)
        names = set(norm_accidentals(result.split(":", 1)[1]).split())
        return names <= _notes(reply)
    if tool == "secondary_dominant":
        return set(norm_accidentals(result.split(": ")[1]).split()) <= _notes(reply)
    if tool in ("guide_tones", "shell_voicing"):
        return set(norm_accidentals(result).split()) <= _notes(reply)
    if tool in ("two_five_one", "borrowed_chords"):
        syms = [c.strip() for c in re.split(r"[–\s]+", result) if c.strip()]
        seven = lambda c: c.replace("maj7", "(?:maj7|M7|Δ7|∆7)")
        return all(re.search(rf"(?<![A-Za-z0-9#]){seven(re.escape(c)) if 'maj7' not in c else seven(c)}(?![A-Za-z0-9#])", reply)
                   for c in syms)
    if tool in ("relative_key", "key_from_signature"):
        return result.split()[0] in _notes(reply)
    return True


def direct(question: str) -> bool:
    """Câu đòi dữ kiện trực tiếp (nốt, quãng, bậc, hóa biểu...), khác câu khái niệm hay câu hỏi cách dùng web."""
    return bool(_DIRECT.search(question))


# Từ chối vô cớ hoặc lộ chữ nội bộ khi Engine ĐÃ có đáp án: sai cả với câu hỏi "vì sao" có tiền đề sai (lượt 3 G8: "Dựa trên ENGINE_FACTS" lộ ra cho người học).
_REFUSED = re.compile(r"không (?:thể )?tự tính|khong (?:the )?tu tinh|engine_facts|"
                      r"chưa trả lời được|dữ liệu (?:chính xác )?từ hệ thống|quy tắc không cho phép",
                      re.IGNORECASE)


def refused(reply: str) -> bool:
    return bool(_REFUSED.search(reply))


def missing(question: str, reply: str, facts: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dữ kiện Engine mà câu trả lời đáng ra phải nêu nhưng không nêu. Câu hỏi đòi dữ kiện trực tiếp thì kiểm kết quả;
    câu khác chỉ bị coi là thiếu khi AI từ chối hoặc lộ chữ nội bộ dù Engine đã có đáp án."""
    if not facts or len(facts) > 2:
        return []
    if direct(question):
        return [f for f in facts if not honoured(reply, f)]
    return list(facts) if refused(reply) else []


# G8 (19/11/2026): Gemini thỉnh thoảng vẫn viết "theo ENGINE_FACTS" (T020) hay "theo kết quả từ hệ thống" (T069, T148)
# dù câu trả lời đúng. Soạn lại cả câu vì vài chữ là phí một lượt Gemini, nên máy chủ tự thay bằng lời người học hiểu.
_SYSTEM_SOURCE = re.compile(r"\s*,?\s*(?:theo|dựa\s+(?:trên|vào)|như)\s+(?:các\s+|những\s+)?(?:kết quả|dữ liệu)"
                            r"(?:\s+chính xác)?\s+(?:từ|của)\s+hệ thống", re.IGNORECASE)
_INTERNAL_NAMES = ((re.compile(r"\bENGINE_FACTS\b"), "Music Engine"), (re.compile(r"\bLESSON_CHUNKS\b"), "bài học"))


def scrub_internal(reply: str) -> str:
    """Bỏ chữ nội bộ của prompt khỏi câu trả lời cho người học; không đổi nội dung nhạc lý."""
    out = _SYSTEM_SOURCE.sub("", reply)
    for pattern, plain in _INTERNAL_NAMES:
        out = pattern.sub(plain, out)
    return out
