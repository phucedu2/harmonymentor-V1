# Mở bài L05, L06, L08 cho người học (10/11/2026)

**Yêu cầu:** Phúc nhờ mở khóa bài 4, 5, 7, 8 (L05, L06, L07, L08) vì còn "Sắp có". Phúc chọn: 1A (Đạt đã duyệt câu hỏi, phát hành thật), 2B (L07 chờ), 3A (nạp L06, L08 vào kho AI Tutor và đo lại), 4B (gộp ngay khi CI xanh).

## Nguyên nhân "Sắp có"
Danh sách bài chỉ mở khi bài có câu hỏi đã phát hành (`exercise_count > 0`). Seed (`seed_data.py`) chỉ nạp khối lý thuyết, câu hỏi và thẻ ôn cho `MIGRATED_LESSON_IDS = L01–L04`. L05–L08 có sẵn nội dung trong `curriculum_specs.py` nhưng không vào CSDL, nên 0 khối và 0 câu. Báo cáo 14_ nói L06–L08 "người học thấy" là sai.

## Đã làm
- `MIGRATED_LESSON_IDS` thêm L05, L06, L08. Kết quả `GET /lessons`: L05 11 khối, 6 câu, 8 thẻ; L06 10 khối, 6 câu, 8 thẻ; L08 8 khối, 5 câu, 8 thẻ. Thứ tự hiện 4 = L05, 5 = L06, 6 = L04, 7 = L07, 8 = L08 (theo bảng SRS, không đổi).
- **L07 chưa mở:** dùng hợp âm 9/13 và mixolydian mà Engine chưa hỗ trợ, chờ Thắng quyết.
- **L08-Q06 để `draft`:** tự luận chấm theo từ khóa (`contains_any`), trái quy tắc bài 1–4 (câu tự luận đã đổi thành nút chọn). Chờ Đạt viết lại thành câu chọn, rồi tăng phiên bản. L08 hiện có 5 câu.
- Câu đã phát hành thì khóa theo ADR-006: sửa đề, đáp án hay cách chấm phải tăng `version`.
- L06, L08 vào kho AI Tutor (`TUTOR_KB_PENDING` chỉ còn L07, vì AI không nên trích bài mà người học chưa mở được). Luật "bài sau" của L06, L08 tự tắt.
- Sinh lại dữ liệu nhãn bằng `tao_du_lieu_gd2.py` (câu B của L06, L08 thành A, theo đúng cách đã làm cho L05), đổi nhãn 2 câu trong `router_dev.json`, chọn lại ngưỡng bằng `hieu_chinh_nguong.py` cho bm25 và e5 gốc (mặc định). Hai bản fine-tune (gd2b, gd2c) giữ ngưỡng cũ, chưa chọn lại, không phải mặc định.

## Số đo (e5 gốc; bm25 là phương án dự phòng)
Tập dev 341 câu (router_dev + gd2/dev + phiếu dev 30 câu của Phúc) là tập đã dùng để chọn ngưỡng nên KHÔNG độc lập.

| Tập | B/C bị trả lời như bài (≤ 2%) | A bị từ chối sai (≤ 5%) | Ghi chú |
|---|---|---|---|
| dev 341 (e5) | 1,8% | 4,7% | đạt cả hai, nhưng không độc lập |
| dev 341 (bm25) | 0,9% | 6,5% | A bị từ chối chưa đạt |
| bộ GĐ1 (e5) | 3,5% | 2,7% | 1 câu "Bài hát buồn…" nhãn B, đoán A; không sửa luật để bộ đo giữ độc lập |
| test_tam (e5) | 7,8% | 1,8% | B/C chưa đạt; không đổi so với 09/11 |

Truy xuất bm25 trên 30 câu chuẩn (`rag_gold.json`): đúng ngay lần đầu 15/30, trong top 4 là 26/30, trước và sau đều giống nhau. Lỗi còn lại ở test_tam chủ yếu là câu về chuyển giọng, cadence (nhãn B nhưng L05 có dạy, chờ Đạt kiểm nhãn) và "quartal harmony", "counterpoint" (không bài nào dạy).

## Còn thiếu
- **Chỉ mục Gemini** (`lesson_embeddings.json`) chưa dựng lại cho L06, L08 vì khóa Gemini nằm trên máy Phúc. Hai test (`test_index_file_matches_current_chunks` và nhánh `index_stale` của `test_retriever_falls_back_to_bm25`) đỏ cho tới khi dựng lại. Trong lúc chưa có, AI dùng BM25. Lệnh: `cd backend && AI_ENABLED=1 GEMINI_API_KEY=... python -m app.ai.build_index`.
- Số chính thức chờ 20 câu test của Thắng và Đạt (hạn 12/11).
- Chưa thử bằng tay trên trình duyệt.
- Mở bài làm đổi tập bài hệ gợi ý thấy (L05, L06, L08 có câu hỏi thật), nên `evaluate_recommender.py` chưa chạy lại; số HitRate cũ có thể đổi.
