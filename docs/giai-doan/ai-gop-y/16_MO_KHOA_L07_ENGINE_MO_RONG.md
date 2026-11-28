# Mở bài L07 và mở rộng Music Engine (11/11/2026)

**Yêu cầu:** Thắng chốt (Phúc báo, trả lời "làm cả hai") mở rộng Engine cho hợp âm 9/13 và mixolydian để mở L07. Xem [ADR-019](../../decisions/ADR-019-engine-hop-am-mo-rong-mixolydian.md).

## Đã làm
- **Engine:** thêm hợp âm `maj9`, `m9`, `9`, `13` và âm giai `mixolydian` (chỉ thêm dữ liệu, không đổi cách tính cũ). Tên nốt suy từ quãng như cũ: Cmaj9 = C E G B D, G13 = G B D F A E, G Mixolydian = G A B C D E F. Nốt 9 và 13 là tension, không có thể đảo. Hợp âm 11, add9, 7#9, 7b9 chưa làm. Claim `MUS-EXT-001`, `MUS-SCALE-009` còn `pending`, loại hợp âm mới `verified=False` như sus2, sus4. Test: `tests/test_engine_extended_l07.py`.
- **L07 mở cho người học:** `MIGRATED_LESSON_IDS` thêm L07 (9 khối, 5 câu, 8 thẻ ôn). **L07-Q06 để `draft`:** tự luận chấm từ khóa, trái quy tắc bài 1–4; chờ Đạt viết lại thành câu chọn rồi tăng phiên bản (giống L08-Q06).
- **AI Tutor:** L07 vào kho (`TUTOR_KB_PENDING` rỗng); mọi luật "bài sau" tắt. Sinh lại dữ liệu nhãn: câu "Âm giai D dorian là gì?" và các câu hợp âm 9 mà Engine nay đọc được chuyển B→A. Chọn lại ngưỡng bm25 và e5 gốc; hàng gd2b/gd2c giữ từ 08/11.
- Sửa test bài học và test định tuyến cho khớp (không còn bài nào "học sau"; câu "hợp âm 11" thay cho "hợp âm 9" làm ví dụ Engine chưa biết).

## Số đo (e5 gốc; KHÔNG độc lập, nhãn do Claude soạn)
| Tập | B/C trả như bài (≤ 2%) | A bị từ chối sai (≤ 5%) | Trước L07 |
|---|---|---|---|
| dev 341 | 3,0% | 6,2% | 1,8% / 4,7% |
| bộ GĐ1 | 3,5% | 2,7% | 3,5% / 2,7% |
| test_tam | 7,8% | 4,5% | 7,8% / 1,8% |

**Dev và test_tam kém hơn trước khi nạp L07: chưa đạt mục tiêu.** Một phần do nhãn: khái niệm mà L07 nay dạy (dorian, hợp âm 9) bị đo như "chưa dạy" hay như "đáp Engine". Một phần là lỗi thật: các câu "Điệu thức Lydian…" (L07 không dạy Lydian) và vài câu ngoài bài vẫn được trả như bài. Số chính thức chờ 20 câu test của Thắng và Đạt.

Truy xuất BM25 trên 30 câu chuẩn: đúng ngay lần đầu 15→14, trong top 4 26→25. Câu "Cmaj7 khác C7 thế nào" nay đẩy L02 ra khỏi top 4 của BM25 (các bài jazz nhắc Cmaj7, C7 nhiều); đường chính là Gemini, chưa đo lại khi chưa có chỉ mục mới.

## Còn thiếu
- **Chỉ mục Gemini** (`lesson_embeddings.json`) phải dựng lại cho L07 trên máy Phúc. Tới lúc đó 2 test (`test_index_file_matches_current_chunks`, `test_retriever_falls_back_to_bm25`) còn đỏ và CI đỏ.
- Đạt viết lại L07-Q06 và L08-Q06; kiểm nhãn (dorian, lydian, hợp âm 9) trong tập dev.
- Số đo gợi ý sau khi mở L07 chưa chạy lại.
