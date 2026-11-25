"""Curated music knowledge outside HarmonyMentor lessons.

This is a small, human-reviewable fallback catalog. It is deliberately separate
from lesson RAG and Music Engine facts: an entry is only used when its trigger
matches, and its source is shown to the learner.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .general import fold


@dataclass(frozen=True)
class SupplementalAnswer:
    reply: str
    source_title: str
    source_url: str


STRING_BENDING = SupplementalAnswer(
    reply=(
        "String bending (nhấn dây) là kỹ thuật đẩy hoặc kéo ngang dây guitar "
        "khi đang bấm nốt để làm cao độ của nốt tăng lên."
    ),
    source_title="Wikipedia · String bending — Technique",
    source_url="https://en.wikipedia.org/w/index.php?title=String_bending&oldid=1340626148#Technique",
)

B01_COMPOUND_METER = SupplementalAnswer(
    reply=(
        "6/8 là nhịp hai phách kép (compound duple): mỗi ô nhịp có 6 đơn vị "
        "móc đơn, được cảm nhận thành 2 phách; mỗi phách là một nốt đen chấm "
        "và chia thành 3 móc đơn. Số 6 cho biết số đơn vị chia trong ô nhịp, "
        "còn số 8 cho biết móc đơn là đơn vị chia."
    ),
    source_title="Open Music Theory · Compound Meter and Time Signatures",
    source_url="https://viva.pressbooks.pub/openmusictheory/chapter/compound-meters/",
)

B02_INVERSION = SupplementalAnswer(
    reply=(
        "Ở thế đảo một của hợp âm C trưởng, nốt bậc ba E là nốt thấp nhất. "
        "Một cách xếp từ thấp lên cao là E–G–C. Ký hiệu hợp âm thường dùng là "
        "C/E; C vẫn là âm gốc, còn E chỉ là nốt bass."
    ),
    source_title="Open Music Theory · Inversion",
    source_url="https://viva.pressbooks.pub/openmusictheory/chapter/inversion/",
)

B04_PARALLEL_FIFTHS = SupplementalAnswer(
    reply=(
        "Quãng năm đúng song song xảy ra khi hai bè cùng đi lên hoặc cùng đi xuống và tạo thành hai quãng năm đúng liên tiếp. Trong hòa âm và đối vị cổ điển, người viết thường "
        "tránh cách đi bè này vì nó dễ "
        "làm hai bè nghe kém độc lập. Đây là quy tắc của phong cách và ngữ cảnh "
        "cổ điển, không phải quy tắc tuyệt đối cho mọi thể loại hay cách phối khí."
    ),
    source_title="Open Music Theory · First-Species Counterpoint",
    source_url="https://viva.pressbooks.pub/openmusictheory/chapter/first-species-counterpoint/",
)

VIBRATO_COMPARISON = SupplementalAnswer(
    reply=(
        "Trên violin, người chơi thường lắc nhẹ đầu ngón tay đang bấm theo chiều dọc dây, "
        "có thể dùng cổ tay hoặc cánh tay để tạo chuyển động. Cao độ thường hạ nhẹ rồi trở về nốt chính. "
        "Trên guitar, cách tạo vibrato tùy kỹ thuật: guitar cổ điển thường dùng dao động dọc theo "
        "trục dây, còn guitar điện hoặc steel-string thường đẩy/kéo dây ngang theo phím để thay đổi "
        "độ căng và cao độ. Vì vậy, cả hai đều tạo dao động cao độ để tăng tính biểu cảm, nhưng "
        "chuyển động của tay và cảm giác âm thanh có thể khác nhau."
    ),
    source_title="Wikipedia · Finger vibrato",
    source_url="https://en.wikipedia.org/wiki/Finger_vibrato",
)

# Whole-question patterns: a keyword inside code, a lesson-specific question,
# or a compound request is not enough to override the usual router.
_BEND_QUESTIONS = re.compile(
    r"(?:(?:cho (?:em|minh) hoi )?(?:ky thuat )?(?:string bending|(?:nhan|bend) day)"
    r"(?: tren (?:dan )?guitar| guitar)? (?:la gi|nghia la gi)"
    r"|(?:tren tab guitar[, ]+)?(?:ky hieu )?bend (?:tren tab guitar )?"
    r"(?:bao (?:em|minh) lam gi|co nghia gi|nghia la gi))\s*[?.!]*"
)
_B01_QUESTIONS = re.compile(r"(?:nhip )?6/8(?: la gi| la nhip gi| dem the nao| co y nghia gi)\s*[?.!]*")
_B02_QUESTIONS = re.compile(r"(?:(?:the )?dao (?:mot|1) (?:cua )?hop am (?:c|do) truong|hop am c/e|c/e"
    r"|hop am (?:c|do) truong (?:the )?dao (?:mot|1))(?: la gi| gom (?:nhung )?not (?:gi|nao)| co not gi)\s*[?.!]*")
_B04_QUESTIONS = re.compile(r"(?:(?:quang (?:nam|5)(?: dung)? song song|parallel (?:perfect )?fifths) la gi"
    r"|(?:vi sao|tai sao) (?:quang (?:nam|5)(?: dung)? song song|parallel (?:perfect )?fifths)"
    r" (?:bi (?:cam|tranh)|thuong bi tranh)(?: trong (?:hoa am|doi vi) co dien)?)\s*[?.!]*")
_VIBRATO_QUESTIONS = re.compile(
    r"(?:vibrato tren violin khac vibrato tren guitar the nao"
    r"|vibrato cua violin va guitar khac nhau o dau"
    r"|cach tao vibrato tren violin co giong guitar khong)\s*[?.!]*"
)


def answer(question: str) -> SupplementalAnswer | None:
    """Return a curated answer only for a supported, exact knowledge request."""
    normalized = " ".join(fold(question).split())
    if _VIBRATO_QUESTIONS.fullmatch(normalized):
        return VIBRATO_COMPARISON
    if _BEND_QUESTIONS.fullmatch(normalized):
        return STRING_BENDING
    if _B01_QUESTIONS.fullmatch(normalized):
        return B01_COMPOUND_METER
    if _B02_QUESTIONS.fullmatch(normalized):
        return B02_INVERSION
    if _B04_QUESTIONS.fullmatch(normalized):
        return B04_PARALLEL_FIFTHS
    return None
