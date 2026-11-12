"""Phạm vi "âm nhạc rộng" của AI Tutor (ADR-020, Phúc chốt 12/11/2026).

Trước ADR-020, câu không phải nhạc lý trong khóa bị từ chối (luồng C). Nay mọi câu liên quan âm nhạc (nhạc lý, hòa âm,
nhạc cụ và cách tập, thể loại, lịch sử, sáng tác) được trả lời; câu ngoài âm nhạc thì từ chối.

Tầng 1 (route_classifier) học theo phạm vi hẹp, nên có thể gán nhãn "ngoài phạm vi" cho "đàn guitar tập thế nào".
Bảng từ khóa dưới đây là chốt chặn tất định: câu có từ khóa âm nhạc mà không dính nhóm cấm thì KHÔNG bị từ chối ở
tầng định tuyến, mà đi luồng B (trả lời kiến thức chung, có nhãn). Gemini là chốt thứ hai: câu không phải nhạc thì
trả intent = out_of_scope và dịch vụ thay bằng câu từ chối viết sẵn.
"""

from __future__ import annotations

import re
import unicodedata


def fold(text: str) -> str:
    """Hạ chữ, bỏ dấu tiếng Việt để so từ khóa (gõ không dấu vẫn khớp)."""
    t = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


# Từ khóa âm nhạc đã bỏ dấu. Cố ý không có "dan" trần ("đàn ông") hay "hat" trần.
_MUSIC = re.compile(
    r"\b(?:"
    r"nhac (?:ly|co|cu|si|truong|nen|jazz|pop|rock|classic|vang|tre|khong loi|dem|phim)|am nhac|nghe nhac|hoc nhac|"
    r"choi nhac|viet nhac|soan nhac|bai nhac|ban nhac|dan nhac|dieu nhac|"
    r"giai dieu|hoa am|hop am|am giai|nhip (?:dieu|phach|\d)|tiet tau|phach|tempo|cung bac|interval|"
    r"guitar|ghi ?ta|piano|organ|violin|cello|ukulele|saxophone|sax|trumpet|clarinet|flute|sao truc|"
    r"dan (?:guitar|piano|organ|tranh|bau|nguyet|nhi|ty ba|ghi ?ta|trong)|trong (?:dien tu|cajon)|drums?|keyboard|synth|"
    r"jazz|blues|pop|rock|bossa|funk|soul|r&b|edm|hip ?hop|classical|co dien|opera|symphony|giao huong|"
    r"bach|mozart|beethoven|chopin|ca khuc|bai hat|"
    r"sang tac|phoi khi|phoi hop am|arrange(?:ment)?|improvis\w*|ngau hung|riff|scale|chord|melody|harmony|"
    r"cadence|modulation|chuyen giong|giong (?:c|d|e|f|g|a|b)\b|giong (?:truong|thu)|dynamics|forte|legato|staccato|vibrato|"
    r"thu am|daw|midi|ear training|luyen tai|ky am|sheet music|tab guitar|"
    r"dien tau|tap (?:dan|guitar|piano|hat|nhac)|luyen (?:ngon|dan|thanh|hat)|ca hat|giong hat"
    r")\b")

# Nhóm vẫn từ chối dù có từ khóa âm nhạc (câu trả lời 2A): bản quyền, tải lậu, mua bán, tấn công.
_BLOCKED = re.compile(
    r"\b(?:loi bai hat|lyrics?|tai (?:nhac )?(?:lau|crack|free|mien phi)|nhac lau|link (?:tai|download)|download|torrent|"
    r"crack|keygen|mua (?:ban|nhac|dan)|ban (?:dan|nhac)|gia (?:dan|bao nhieu)|bao nhieu tien|khuyen mai|"
    r"hack|tan cong|bo qua (?:quy tac|huong dan)|ignore (?:previous|all))\b")


def broad_music(question: str) -> bool:
    """Câu có dấu hiệu liên quan âm nhạc và không thuộc nhóm cấm."""
    f = fold(question)
    return bool(_MUSIC.search(f)) and not _BLOCKED.search(f)


# Câu hỏi cách DÙNG web (không phải học nhạc): giữ luồng D dù có từ khóa âm nhạc ("lưu bài sáng tác", "xuất MIDI").
_APP = re.compile(r"\b(?:web|website|trang|app|ung dung|tai khoan|dang nhap|dang ky|mat khau|nut|menu|bang dieu khien|"
                  r"tien do|muc|o dau|dashboard|harmony lab|luu|xuat|export|import|tai len|backing track|may chu|loi he thong)\b")


def about_app(question: str) -> bool:
    return bool(_APP.search(fold(question)))
