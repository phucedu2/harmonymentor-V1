# Phiếu duyệt nội dung lô 2 sau rà soát (14/11/2026)

Người duyệt: **Đạt**. Toàn bộ nội dung dưới đây do Claude soạn, đang mang `status: "draft"`, chỉ hiện khi bật
`SHOW_DRAFT_CONTENT=1`. Duyệt xong mục nào thì đổi `"draft"` thành `"approved"` (kho hỏi đáp) hoặc `"published"`
(câu hỏi), và xóa `"status": DRAFT` trong khối nghe. Mọi nốt, hợp âm và âm giai đã được Music Engine kiểm trong test
(`backend/tests/test_lo2_rs07_faq.py`, `backend/tests/test_lo2_rs04_cau_nhap.py`); phần cần Đạt đọc là câu chữ và
cách giải thích cho người mới.

Cách xem trên web: đặt `SHOW_DRAFT_CONTENT=1` trong `.env`, chạy lại, mở bài học hoặc hỏi AI Tutor khi AI tắt.

## 1. Kho hỏi đáp cơ bản (RS-07): `backend/app/ai/tutor/faq_co_ban.json`

Dùng khi AI tắt hoặc Gemini lỗi. Câu người học gõ được bỏ dấu, bỏ dấu câu và từ đệm rồi so khớp NGUYÊN CÂU, nên
"hợp âm mượn là gì" không bị trả lời bằng định nghĩa "hợp âm".

| Mã | Câu hỏi khớp (không dấu) | Nội dung trả lời | Bài | Đạt kiểm |
|---|---|---|---|---|
| FAQ-01 | hop am la gi | Hợp âm là gì, hợp âm ba, ví dụ C gồm C E G | L01 | ☐ |
| FAQ-02 | c la not gi, do re mi la c d e | C D E F G A B = Đô Rê Mi Fa Son La Si | L01 | ☐ |
| FAQ-03 | nua cung la gi | Hai phím sát nhau, E–F, C–C# | L01 | ☐ |
| FAQ-04 | mot cung la gi | Hai nửa cung, C–D | L01 | ☐ |
| FAQ-05 | quang la gi | Đếm chữ cái tính cả hai đầu, C–E quãng 3 | L01 | ☐ |
| FAQ-06 | dau thang la gi, dau giang la gi | # nâng, b hạ nửa cung | L01 | ☐ |
| FAQ-07 | hop am truong va thu khac nhau | Quãng 3 trưởng/thứ, C và Cm | L01 | ☐ |
| FAQ-08 | am giai la gi | Khuôn cung/nửa cung, C trưởng | L02 | ☐ |

FAQ-02 viết "Sol" cho khớp khối Đô–Rê–Mi ở Bài 1.

## 2. Câu hỏi bổ sung để mỗi kỹ năng có ít nhất 3 câu (RS-04): `backend/app/content/curriculum_specs.py`

| Mã | Kỹ năng | Đề (rút gọn) | Đáp án | Đạt kiểm |
|---|---|---|---|---|
| L05-Q07 | Át phụ, vận dụng | Tăng lực đi tới Dm trong C major | A7-Dm | ☐ |
| L05-Q08 | Át phụ, vận dụng | Đặt D7 (V7/V) vào C–F–G–C | C-F-D7-G-C | ☐ |
| L05-Q09 | Át phụ, nhận diện | D7 → G trong C major | V7/V | ☐ |
| L06-Q07 | Giọng thứ song song | Parallel minor của G major | G minor | ☐ |
| L06-Q08 | Giọng thứ song song | C minor tự nhiên khác C major ở nốt nào | Eb, Ab, Bb | ☐ |
| L06-Q09 | Hợp âm mượn, vận dụng | C–F–C có iv mượn ở giữa | C-F-Fm-C | ☐ |
| L06-Q10 | Hợp âm mượn, vận dụng | Vòng có ♭VI mượn | C-Ab-G-C | ☐ |
| L07-Q07 | Tên tension | Tension 9 của Cmaj9 | D | ☐ |
| L07-Q08 | Chord-scale theo ngữ cảnh | Vì sao G7 không luôn dùng Mixolydian | (câu chọn) | ☐ |
| L07-Q09 | Chord-scale theo ngữ cảnh | Nốt tránh ngân dài trên G7 | C | ☐ |

Mỗi câu có lời giải và nguồn (OMT, Kostka–Payne, Terefenko, Fankhauser như các câu cùng bài). Lưu ý: L07-Q08 và
L07-Q09 thay cho L07-Q06 (tự luận chấm từ khóa); nếu Đạt duyệt hai câu này thì có thể cho L07-Q06 `retired=True`.

## 3. Khối nghe "vòng hợp âm quen" mỗi bài (RS-11): `backend/app/content/draft_specs.py` (`SONG_BLOCKS`)

Không nêu tên bài hát cụ thể (tránh lỗi RS-30 và bản quyền), chỉ nêu tên vòng và giọng, có nút nghe.

| Bài | Vòng | Ý chính | Đạt kiểm |
|---|---|---|---|
| L01 | C–F–G–C | Ba hợp âm đệm được nhiều bài thiếu nhi, dân ca | ☐ |
| L02 | C–G–Am–F | Vòng I–V–vi–IV của nhạc pop | ☐ |
| L03 | C–Am–F–G | Đi từ chủ qua hạ át tới át rồi muốn về | ☐ |
| L04 | Dm7–G7–Cmaj7 | ii–V–I trong jazz, bossa nova | ☐ |
| L05 | C–E7–Am–F | E7 là át phụ của Am | ☐ |
| L06 | C–F–Fm–C | iv mượn, chỉ đổi A thành Ab | ☐ |
| L07 | Cmaj7–Am7–Dm7–G7 | Vòng hợp âm bảy kiểu lo-fi, R&B | ☐ |
| L08 | Dm7–G7–Cmaj7 | ii–V–I bằng shell voicing | ☐ |

Người kiểm: Đạt ............ Ngày ............
