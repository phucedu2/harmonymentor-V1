"""Lý thuyết L06, L07, L08 (GĐ3 góp ý thầy G2), Claude soạn 08/11/2026, Đạt duyệt 09/11/2026 (Phúc báo).

Đã bỏ status "draft": người học thấy. AI Tutor trích L06, L08; L07 chờ (xem TUTOR_KB_PENDING). Mọi nốt/quãng ghi ở đây được test đối chiếu
Music Engine (tests/test_ai_gd3_l06_l08.py). Engine chưa hỗ trợ hợp âm mở rộng (9, 13) và mixolydian, nên phần đó
kiểm bằng quãng và bằng việc xoay âm giai major, ghi rõ trong báo cáo.
Định vị nguồn từng khối do Claude đề xuất, chưa đối chiếu trang.
"""

from __future__ import annotations

from typing import Any

DRAFT = "draft"
Block = tuple[str, str, dict[str, Any]]

L06_DRAFT_BLOCKS: list[Block] = [
    ("L06-B01", "callout", {
        "title": "Trước khi học hợp âm mượn",
        "prompt": "Bài này dùng lại hợp âm trưởng, thứ và ba chức năng Tonic, Subdominant, Dominant (bài về chức năng "
                  "hòa âm). Nếu chưa chắc F trong C major thuộc nhóm Subdominant, hãy ôn bài đó trước."}),
    ("L06-B02", "theory", {
        "title": "1. Hợp âm mượn là gì",
        "paragraphs": [
            "Mỗi key trưởng có một key thứ \"song song\" (parallel minor) dùng cùng nốt chủ. Với C major, key song song là "
            "C minor. Hai key này cùng tonic là C nhưng khác ở một vài nốt.",
            "Hợp âm mượn (borrowed chord, hay modal mixture) là hợp âm lấy từ key song song để đặt vào đoạn nhạc đang ở "
            "key chính. Trong C major, nhạc sĩ có thể \"mượn\" Fm từ C minor.",
            "Mượn hợp âm không có nghĩa là chuyển giọng. Key chính vẫn là C major, và tiến trình thường quay về hợp âm "
            "của key chính ngay sau đó.",
        ]}),
    ("L06-B03", "glossary", {
        "title": "2. Thuật ngữ",
        "intro": "Bốn thuật ngữ dùng trong cả bài.",
        "terms": [
            {"symbol": "C minor", "term": "Key song song · parallel minor",
             "definition": "Key thứ có cùng nốt chủ với key trưởng. C minor tự nhiên gồm C–D–Eb–F–G–Ab–Bb.",
             "example": "Parallel minor của C major là C minor"},
            {"symbol": "iv", "term": "Hợp âm mượn · borrowed chord",
             "definition": "Hợp âm không thuộc key chính mà lấy từ key song song.",
             "example": "Fm trong C major"},
            {"symbol": "Modal mixture", "term": "Pha trộn điệu thức",
             "definition": "Cách gọi khác của việc mượn hợp âm từ key song song. Màu âm thanh đổi, chức năng không "
                           "nhất thiết đổi.",
             "example": "C → F → Fm → C"},
            {"symbol": "♭VI, ♭VII", "term": "Bậc hạ",
             "definition": "Dấu ♭ trước số La Mã nghĩa là root của hợp âm thấp hơn bậc cùng số trong major một nửa cung.",
             "example": "♭VI trong C major là Ab"},
        ]}),
    ("L06-B04", "theory", {
        "title": "3. Ba hợp âm mượn phổ biến trong C major",
        "items": [
            "iv = Fm (F–Ab–C), mượn từ C minor, thay cho F (F–A–C). Khác F ở nốt Ab so với A.",
            "♭VI = Ab (Ab–C–Eb), mượn từ C minor. Root Ab cách C một quãng 6 thứ.",
            "♭VII = Bb (Bb–D–F), mượn từ C minor. Root Bb cách C một quãng 7 thứ.",
            "Cả ba hợp âm có nốt ngoài C major: Fm có Ab, Ab có Ab và Eb, Bb có Bb. Đó là dấu hiệu nhận ra hợp âm mượn.",
        ]}),
    ("L06-BCP1", "checkpoint", {
        "title": "Nhận ra hợp âm mượn",
        "exercise_id": "L06-Q01",
        "note": "Hợp âm nào trong C major có nốt Ab? Nó thay cho hợp âm nào của key chính?"}),
    ("L06-B05", "progression", {
        "title": "4. Ví dụ: C – F – Fm – C",
        "prompt": "C → F → Fm → C  =  I → IV → iv → I", "key": "C"}),
    ("L06-B06", "audio", {
        "title": "5. Nghe trước và sau khi mượn Fm",
        "prompt": "Nghe C → F → C, rồi nghe C → F → Fm → C. Chú ý Ab trong Fm làm màu âm tối đi, nhưng bạn vẫn nghe "
                  "tiến trình quay về C.",
        "progression": ["C", "F", "Fm", "C"], "key": "C", "bpm": 72}),
    ("L06-B07", "theory", {
        "title": "6. Mượn hợp âm hay chuyển giọng?",
        "paragraphs": [
            "Hợp âm mượn đổi màu (quality) nhiều hơn đổi chức năng. Fm vẫn đóng vai Subdominant như F, chỉ nghe tối hơn.",
            "Hỏi để phân biệt: sau hợp âm mượn, nhạc có quay về key chính không? Có thì key chính không đổi, đó là "
            "hợp âm mượn chứ chưa phải chuyển giọng.",
        ]}),
    ("L06-BCP2", "checkpoint", {
        "title": "Mượn hợp âm có đổi chức năng không",
        "exercise_id": "L06-Q05",
        "note": "Nghĩ tới việc Fm vẫn đóng vai Subdominant như F."}),
    ("L06-B08", "summary", {
        "title": "Ghi nhớ",
        "items": [
            "Key song song của C major là C minor; hai key cùng nốt chủ C.",
            "Hợp âm mượn lấy từ key song song và đặt vào key chính.",
            "Trong C major: iv = Fm, ♭VI = Ab, ♭VII = Bb.",
            "Mượn hợp âm đổi màu âm thanh, chưa phải chuyển giọng.",
        ]}),
]

L07_DRAFT_BLOCKS: list[Block] = [
    ("L07-B01", "callout", {
        "title": "Trước khi học tension và chord-scale",
        "prompt": "Bài này dùng hợp âm bảy và tiến trình ii–V–I (bài về ii–V–I và guide tone). Nếu chưa chắc Dm7–G7–Cmaj7 "
                  "gồm những nốt nào, hãy ôn lại bài đó trước."}),
    ("L07-B02", "theory", {
        "title": "1. Chord tone và tension",
        "paragraphs": [
            "Chord tone là các nốt tạo nên hợp âm bảy: root, quãng 3, quãng 5, quãng 7. Cmaj7 có C–E–G–B.",
            "Tension (còn gọi là extension) là nốt thêm phía trên hợp âm bảy, đánh số 9, 11, 13. Đó là các nốt bậc 2, 4, "
            "6 tính từ root, nhưng nằm ở quãng tám cao hơn.",
            "Chord tone định hình hợp âm. Tension chỉ mở rộng màu sắc, nên chọn theo ngữ cảnh.",
        ]}),
    ("L07-B03", "theory", {
        "title": "2. Tension của ba hợp âm trong ii–V–I ở C major",
        "items": [
            "Dm7 (D–F–A–C): 9 = E, 11 = G, 13 = B.",
            "G7 (G–B–D–F): 9 = A, 11 = C, 13 = E. Nốt 11 (C) cách quãng 3 (B) nửa cung nên nhiều nhạc sĩ tránh nó trên G7.",
            "Cmaj7 (C–E–G–B): 9 = D, 11 = F, 13 = A.",
        ]}),
    ("L07-BCP1", "checkpoint", {
        "title": "Chord tone trước tension",
        "exercise_id": "L07-Q02",
        "note": "Dựng chord tone của Cmaj7 trước khi thêm tension."}),
    ("L07-B04", "glossary", {
        "title": "3. Mode và chord-scale",
        "intro": "Hai thuật ngữ dùng trong phần còn lại.",
        "terms": [
            {"symbol": "Mode", "term": "Điệu thức",
             "definition": "Âm giai tạo ra khi chơi các nốt của major scale nhưng bắt đầu từ một bậc khác.",
             "example": "D Dorian = D–E–F–G–A–B–C, các nốt của C major bắt đầu từ D"},
            {"symbol": "Chord-scale", "term": "Âm giai gắn với hợp âm",
             "definition": "Mode gợi ý cho các nốt (kể cả tension) có thể dùng trên một hợp âm, tùy key và chức năng.",
             "example": "Dm7 trong C major thường đi với D Dorian"},
        ]}),
    ("L07-B05", "theory", {
        "title": "4. Chord-scale cơ bản của ii–V–I ở C major",
        "items": [
            "Dm7 → D Dorian: D–E–F–G–A–B–C.",
            "G7 → G Mixolydian: G–A–B–C–D–E–F.",
            "Cmaj7 → C Ionian (chính là C major): C–D–E–F–G–A–B.",
            "Cả ba mode dùng đúng bảy nốt của C major, chỉ khác nốt bắt đầu.",
        ]}),
    ("L07-B06", "audio", {
        "title": "5. Nghe ii–V–I",
        "prompt": "Nghe Dm7 → G7 → Cmaj7. Mỗi hợp âm có thể đi với mode ở trên, nhưng tai và chức năng hợp âm vẫn quan "
                  "trọng hơn bảng.",
        "progression": ["Dm7", "G7", "Cmaj7"], "key": "C", "bpm": 72}),
    ("L07-BCP2", "checkpoint", {
        "title": "Chord-scale không phải đáp án duy nhất",
        "exercise_id": "L07-Q06",
        "note": "Nghĩ tới key center và chức năng của hợp âm."}),
    ("L07-B07", "summary", {
        "title": "Ghi nhớ",
        "items": [
            "Chord tone: 1, 3, 5, 7. Tension: 9, 11, 13 (bậc 2, 4, 6 ở quãng tám cao).",
            "Mode là major scale bắt đầu từ bậc khác.",
            "ii–V–I ở C major: Dm7 ~ D Dorian, G7 ~ G Mixolydian, Cmaj7 ~ C Ionian.",
            "Chord-scale là công cụ theo ngữ cảnh, không phải bảng đáp án tuyệt đối.",
        ]}),
]

L08_DRAFT_BLOCKS: list[Block] = [
    ("L08-B01", "callout", {
        "title": "Trước khi học shell voicing",
        "prompt": "Bài này dùng hợp âm bảy và guide tone của ii–V–I (bài về ii–V–I và guide tone). Nếu chưa chắc quãng 3 và "
                  "quãng 7 của G7 là nốt nào, hãy ôn lại bài đó trước."}),
    ("L08-B02", "theory", {
        "title": "1. Voicing và shell voicing",
        "paragraphs": [
            "Voicing là cách sắp xếp các nốt của một hợp âm để chơi. Khi chơi piano, bạn không phải chơi đủ mọi chord tone.",
            "Shell voicing chỉ giữ ba nốt: root, quãng 3 và quãng 7. Quãng 5 thường lược đi vì nó ít quyết định màu của "
            "hợp âm hơn quãng 3 và quãng 7.",
            "Dựng đầy đủ hợp âm (đủ mọi chord tone) và dựng một voicing là hai việc khác nhau, nên chấm điểm khác nhau.",
        ]}),
    ("L08-B03", "theory", {
        "title": "2. Shell root–3–7 của ii–V–I ở C major",
        "items": [
            "Dm7: D–F–C.",
            "G7: G–B–F.",
            "Cmaj7: C–E–B.",
        ]}),
    ("L08-BCP1", "checkpoint", {
        "title": "Dựng shell G7",
        "exercise_id": "L08-Q03",
        "note": "Lấy root, quãng 3 và quãng 7 của G7."}),
    ("L08-B04", "theory", {
        "title": "3. Nối voicing bằng guide tone",
        "paragraphs": [
            "Quãng 3 và quãng 7 là guide tone vì chúng dẫn tai từ hợp âm này sang hợp âm kế tiếp.",
            "Từ Dm7 sang G7: F (quãng 3 của Dm7) giữ nguyên, trở thành quãng 7 của G7. C (quãng 7 của Dm7) đi xuống "
            "nửa cung thành B, quãng 3 của G7.",
            "Từ G7 sang Cmaj7: B (quãng 3 của G7) giữ nguyên, trở thành quãng 7 của Cmaj7. F (quãng 7 của G7) đi xuống "
            "nửa cung thành E, quãng 3 của Cmaj7.",
            "Nguyên tắc smooth voice leading: mỗi nốt di chuyển càng ít càng tốt.",
        ]}),
    ("L08-BCP2", "checkpoint", {
        "title": "Nối G7 sang Cmaj7",
        "exercise_id": "L08-Q05",
        "note": "Nốt nào giữ nguyên, nốt nào đi xuống nửa cung?"}),
    ("L08-B05", "audio", {
        "title": "4. Nghe ii–V–I",
        "prompt": "Nghe Dm7 → G7 → Cmaj7 và để ý hai nốt ở giữa (quãng 3 và quãng 7) chuyển rất ít.",
        "progression": ["Dm7", "G7", "Cmaj7"], "key": "C", "bpm": 72}),
    ("L08-B06", "summary", {
        "title": "Ghi nhớ",
        "items": [
            "Shell voicing = root, quãng 3, quãng 7. Quãng 5 thường lược.",
            "Trong C major: Dm7 = D–F–C, G7 = G–B–F, Cmaj7 = C–E–B.",
            "Dm7 → G7 → Cmaj7: F giữ rồi đi xuống E; C đi xuống B rồi giữ.",
            "Nối voicing mượt: mỗi nốt di chuyển càng ít càng tốt.",
        ]}),
]

# Đạt duyệt 09/11/2026 (Phúc báo trong thread): bỏ status draft, người học thấy.
# 10/11/2026: L06 và L08 đã nạp vào kho AI Tutor (nhãn sinh lại, ngưỡng chọn lại, đã đo).
# 11/11/2026: Thắng chốt mở rộng Engine (ADR-019) nên L07 mở cho người học và nạp vào kho; không còn bài nào chờ.
# 12/11/2026: L11 (Vòng hợp âm Pop) mở cho người học nhưng chưa vào kho AI Tutor: nạp cần dựng lại chỉ mục Gemini
# (khóa chỉ có trên máy Phúc) và đo lại định tuyến. Bỏ L11 khỏi tập này khi đã dựng chỉ mục.
TUTOR_KB_PENDING: frozenset[str] = frozenset({"L11"})
