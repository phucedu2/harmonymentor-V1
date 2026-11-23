# ADR-033: Sửa logic AI soạn bài (đợt 3)

- Trạng thái: Đề xuất (Phúc chốt phương án 22/11/2026, chờ nhóm duyệt Draft PR vào `phuc-music`)
- Ngày: 23/11/2026
- Liên quan: ADR-025 (AI soạn bản nháp), ADR-028 (câu luyện tập), ADR-029 (tóm tắt cả tài liệu, chống trùng), ADR-023 (ẩn bài)
- Báo cáo: `docs/giai-doan/ai-soan-bai-dot3/BAO_CAO.md`

## Bối cảnh

Rà soát luồng Admin "AI soạn bài" (tải tài liệu → cổng nhạc lý → AI tóm tắt chạy nền → chống trùng → nháp → duyệt →
xuất bản → học sinh) thấy đáp án sai có thể tới học sinh mà không ai duyệt (N1, N2), trích dẫn trang giả (N4), bài AI
không vào kho AI Tutor (N5) và bài hiện ngay khi xuất bản (N6). Chi tiết từng nghi vấn và test chứng minh ở báo cáo.

## Quyết định

1. **Đề phải khớp phần kiểm (N1, 4A/5A).** Trích ký hiệu nhạc trong đề (`ai_questions.prompt_symbols`, nhận cả tên nốt
   Đô/Rê…). Ký hiệu trong đề khác ký hiệu AI đưa Engine → loại câu, ghi lý do. Đề không nêu ký hiệu → giữ câu, bắt duyệt
   (Phúc chọn 4A). Engine phải sửa đáp án AI → giữ câu, bắt duyệt.
2. **Đúng/Sai chỉ miễn duyệt khi mọi vế đã kiểm (N2).** `statement_truth`: có từ phủ định/lượng từ (không, chỉ, mọi…)
   → Engine không kết luận; còn từ khái niệm chưa kiểm (trưởng, thứ, bậc, chức năng…) → bắt duyệt; có vế sai → "Sai".
3. **Câu gắn khối (N3).** Schema có `block_ref`; bỏ khối trùng thì bỏ câu của khối, đánh số lại; câu không gắn khối →
   bắt duyệt.
4. **Cờ duyệt là cảnh báo, không chặn cứng (2A).** `admin/ai_review.py` tính lại cờ lúc soạn, sửa và xuất bản: trang ngoài
   phần (không kẹp lặng lẽ nữa), bám nguồn thấp, nhầm trang, chép nguyên văn (≥ 12 từ liên tiếp), nhắc hình/ví dụ không
   có, trang nguồn có ký âm, khối trộn ý cũ (V4), chữ bị cắt (V7), khác ngôn ngữ mà không có e5. Mỗi cờ có mã ổn định;
   phải tick "Đã đối chiếu" từng cờ thì `publish_draft` mới cho (409 `REVIEW_FLAGS`).
   Ngưỡng (3A: ưu tiên recall bắt khối bịa ≥ 95%, tách TF-IDF trong CI và e5 trên máy có mô hình), chọn trên
   `eval/ai_soan_bai/cases.jsonl`:

   | Ngưỡng | TF-IDF | e5-small | Trước |
   |---|---|---|---|
   | Bám nguồn tối thiểu `GROUND_MIN` | 0,30 | 0,89 | không có |
   | Trang khác giống hơn `BETTER_PAGE_MARGIN` (cờ nhầm trang) | 0,05 | 0,02 | không có |
   | Trùng khối `DUP_BLOCK` | 0,70 | 0,95 | 0,55 / 0,90 |

   e5 so ĐỐI XỨNG: cả hai phía dùng tiền tố `query:` (V3). Bộ ca nhỏ (13 khối, 12 cặp) và do Claude soạn, nên ngưỡng là
   tạm, chạy lại script khi Đạt duyệt bộ ca hoặc có số đo Gemini thật.
5. **Mastery chỉ khi kiểu kiểm khớp họ kỹ năng (H3, 5A).** Câu Engine kiểm nhưng `skill_id` khác họ (vd kiểm quãng mà gắn
   kỹ năng hợp âm) → bắt duyệt; khi xuất bản, câu không qua `counts_for_mastery` thì không tính thành thạo.
6. **Xuất bản ở trạng thái ẩn (N6, 7B).** `publish_draft` tạo kèm bản ghi ẩn (ADR-023). Admin mở `/app/hoc?xem_truoc=<id>`
   (API `GET /lessons/{id}?preview=true`, chỉ nhận token admin) để xem đúng trang Học; lượt làm của admin vẫn `is_test`.
   Bấm "Hiện cho học sinh" mới hiện.
7. **Kho AI Tutor đọc bài AI từ CSDL (N5, 1A/6A).** Qdrant là kho chính: hiện bài → gỡ điểm cũ, nạp lại; ẩn bài → gỡ.
   Đường dự phòng (e5 bộ nhớ + BM25) đọc thẳng `ai_index.ai_lesson_chunks`, chỉ cần xóa bộ nhớ đệm. Nguồn trích dẫn theo
   trang của khối ("sách X · trang n"). Lỗi Qdrant không làm hỏng thao tác hiện/ẩn, chỉ báo lại.
8. **Một hạn mức Gemini theo khóa (V5, 12A).** Bản miễn phí 30 lượt/ngày (`GEMINI_DAILY_BUDGET=30`), 40% soạn bài (12),
   60% AI Tutor (18) (`GEMINI_AUTHORING_SHARE=0.4`), đặt lại lúc nửa đêm giờ Thái Bình Dương (15:00 giờ Việt Nam, 14:00
   khi Mỹ theo giờ mùa hè). Mỗi lần gọi soạn bài ghi `ai.llm.call` vào nhật ký Admin, kể cả việc nền không có người tạo.
   `0` = không giới hạn (giữ hành vi cũ cho test).
9. **JSON hỏng thử lại đúng 1 lần (V6, nguyên tắc 2)**; lần 2 vẫn hỏng → lỗi `AI_BAD_FORMAT`, phần đó "failed".
10. **Không cắt lặng lẽ (V7).** API `/draft` cũ bỏ trang không vừa giới hạn chữ, thu hẹp khoảng trang của nháp và gắn cờ.
11. **Ngữ cảnh "đã có" là RAG thật (V1, V2).** Mỗi trang của phần lấy 3 đoạn đã có giống nhất (tối đa 10, 360 ký tự), gồm cả
    nháp của phần trước trong cùng việc nền, thay danh mục tên khối cắt ở 6.000 ký tự.
12. **Nhật ký kiểu n8n.** Mỗi phần ghi các node extract → retrieve → generate → dedup → validate → flags → draft (thời gian,
    số vào/ra, ghi chú) trong `part["log"]`, hiện ở AiDraftTab.
13. **H1, H2.** Sửa nháp kẹp trang theo khoảng trang của nháp; `source_note` ghi vào `LessonSource.note`, không làm tác giả.

## Không làm

- Đọc ký âm từ ảnh (V8): chỉ gắn cờ.
- Tách khối trộn ý cũ + mới tự động (V4): chỉ gắn cờ `mixed_block` theo khái niệm AI báo kèm trang.
- Không đổi Music Engine, không sửa bài đã xuất bản. Bản nháp cũ vẫn đọc được; câu cũ không có `block_ref` thì bắt duyệt.

## Hệ quả

- Admin phải tick thêm (cờ + câu cần duyệt) trước khi xuất bản, và thêm một bước "Hiện cho học sinh".
- Một số câu đúng tình cờ bị loại (vd đề D7 nhưng phần kiểm ghi giọng khác): mất câu thay vì lọt đáp án sai.
- Với embedder Gemini, bài AI chỉ tìm qua Qdrant hoặc BM25 (vector dự phòng của bài AI đặt 0).
