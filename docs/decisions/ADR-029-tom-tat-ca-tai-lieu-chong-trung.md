# ADR-029: Tóm tắt cả tài liệu chạy nền, chống trùng kiến thức, ảnh đại diện, cửa sổ AI Tutor

- Ngày: 18/11/2026
- Trạng thái: Đề xuất (chờ Phúc duyệt PR)
- Người quyết định phạm vi: Phúc (trả lời 12 câu: 1A 2A 3A 4A 5A 6A 7A 8A 9A 10A 11A 12B)
- Liên quan: ADR-025 (AI soạn bản nháp), ADR-028 (AI sinh bài luyện tập)

## Bối cảnh

Admin phải chọn "từ trang … đến trang …" (tối đa 15 trang) mỗi lần soạn, nên một sách 126 trang cần 9 lần bấm và dễ sót.
Phúc muốn: tóm tắt hết tài liệu thành bài học + luyện tập; kiến thức trang web đã có thì không thêm thành bài mới; chỉ
kiến thức hoàn toàn mới mới được đăng và hiện cho mọi người dùng ở một mục riêng.

## Quyết định

1. **Bỏ chọn trang (1A).** Nút "AI soạn bài từ cả tài liệu" tạo một việc (`ai_summary_jobs`) chạy nền trong một luồng của
   máy chủ. Tài liệu được chia phần **bằng luật** (`ai_job.plan_parts`): đầu chương nhận từ dòng "Chương/Bài/Phần/Chapter/
   Part/Lesson/Unit + số" ở đầu trang; mỗi phần ≤ 15 trang và ≤ 24.000 ký tự; chương quá ngắn (< 1.500 ký tự) gộp với chương
   sau. Không dùng thêm một lượt Gemini để chia, nên chạy lại cho ra đúng kết quả cũ và không tốn hạn mức.
2. **Bỏ trang không phải nội dung (2A)**: trang trống, trang cổng nhạc lý đã bỏ lúc tải lên, bìa (một trong hai trang đầu,
   < 300 ký tự, không mở đầu chương, tài liệu > 3 trang), mục lục (tiêu đề hoặc ≥ 50% dòng kết thúc bằng số trang), lời nói
   đầu, lời cảm ơn, tài liệu tham khảo, chỉ mục. Mỗi trang bỏ được ghi lý do. Phần còn lại mà AI thấy không có kiến thức
   nhạc lý (lời bạt, tiểu sử, tài liệu phần mềm) thì AI trả `not_theory` và không tạo bài.
3. **Chạy nền + chạy tiếp (3A).** Trạng thái từng phần lưu JSON (`pending/running/done/no_new/not_theory/failed`).
   Gemini 429 → tạm dừng (`quota`), phần đang làm về "chờ". Hai phần liền nhau lỗi → tạm dừng (`unavailable`). Quá 40 lượt
   soạn phần mỗi Admin trong 24 giờ → tạm dừng (`daily_limit`). Máy chủ khởi động lại giữa chừng → lần xem kế tiếp chuyển
   sang tạm dừng (`interrupted`). Admin bấm "Chạy tiếp" để làm nốt (phần lỗi được làm lại), hoặc "Dừng hẳn".
4. **Chống trùng theo khái niệm (4A, 5A, 6A).** Danh mục "đã có" gồm bài người học đang thấy (chính thức L01–L08 và bài AI
   đã xuất bản), câu luyện tập/quiz của các bài đó, và bản nháp đang chờ duyệt. Hai lớp:
   - AI nhận danh mục (mã bài · tên bài: các khối) và phải liệt kê khái niệm của phần kèm `new`/`covered`; chỉ viết khối và
     câu cho khái niệm mới, kể cả khi tài liệu giải thích hay hơn (6A: bỏ, báo "đã có ở L03").
   - Máy soát lại từng khối và từng câu bằng độ giống cosine: e5 cục bộ nếu máy có mô hình (ngưỡng khối 0,90, câu 0,95),
     không thì TF-IDF trên từ đã tách giữ dấu + bỏ dấu (ngưỡng khối 0,55, câu 0,80). Khối vượt ngưỡng bị bỏ dù AI không nhận ra.
   - Bản nháp vừa soạn được thêm vào danh mục để các phần sau (chương ôn tập) không lặp lại.
   - Phần không còn khối nào → `no_new`, không tạo bản nháp. Báo cáo trùng hiện ở tiến độ và trong bản nháp.
   Ngưỡng là mức ban đầu, chưa hiệu chỉnh trên sách thật của nhóm (xem Rủi ro).
5. **Kiến thức mới (7A).** Bài AI vẫn phải được Admin duyệt và xuất bản như ADR-025/028. Trang Học tách bài AI ra mục
   "Kiến thức mới" phía trên lộ trình (không chen vào thứ tự Bài 1…8), nhãn "Mới" trong 14 ngày đầu.
6. **Bài "Mở rộng" (8A).** AI đặt `expansion` khi kiến thức mới không khớp kỹ năng nào (vẫn chọn kỹ năng gần nhất vì cột
   `exercises.skill_id` bắt buộc); Admin bật/tắt được trong bản nháp. Khi xuất bản, mọi câu của bài nhận
   `grader_config.counts_for_mastery = false`: vẫn chấm, nhưng `mastery_service` bỏ qua (cả lượt làm, ôn thẻ và dựng lại
   mastery) và Quiz kỹ năng không lấy câu này. Không thêm kỹ năng mới, không đổi skill graph (8B cần ADR riêng).
7. **Ảnh đại diện (9A, 10A).** Ảnh đại diện ở góc phải trên mở menu "Hồ sơ" / "Đăng xuất" (mẫu WAI-ARIA Menu Button), cho
   cả người học và Admin; bỏ "Hồ sơ" ở thanh bên. 12 con vật vẽ SVG trong mã; cột `users.avatar_key` (rỗng = con suy từ
   SHA-256 của id, cố định giữa các máy). Không cho tải ảnh lên.
8. **Cửa sổ AI Tutor (11A, 12B).** Màn hình ≥ 640 px: kéo mép/góc để đổi cỡ (tối thiểu 320×360), phóng to/thu về, thu
   nhỏ còn thanh tiêu đề, bấm đúp thanh tiêu đề để phóng to, Alt + mũi tên đổi cỡ bằng bàn phím, nhớ vị trí/cỡ theo máy.
   Biểu tượng mới: bong bóng hội thoại chứa hai nốt móc đơn nối vạch và một tia sáng nhỏ (Claude chọn theo 12B).

## Hệ quả

- Migration `c7a8b9c0d1e2`: bảng `ai_summary_jobs`, cột `users.avatar_key`. Docker tự chạy `alembic upgrade head` khi khởi
  động; SQLite dev cũ báo lỗi rõ cách sửa (`app/db/session.py`).
- API mới: `POST /admin/ai/documents/{id}/summarize`, `GET /admin/ai/jobs`, `GET /admin/ai/jobs/{id}`,
  `POST /admin/ai/jobs/{id}/resume`, `POST /admin/ai/jobs/{id}/cancel`. API cũ `POST /admin/ai/documents/{id}/draft` giữ lại
  (test cũ dùng), giao diện không gọi nữa.
- `LessonSummaryOut` thêm `ai_generated`, `expansion`, `published_at`; `UserOut` thêm `avatar`; `PATCH /me` nhận `avatar`.
- Không đổi Music Engine, không sửa bài đã phát hành.

## Rủi ro

- Luồng nền nằm trong tiến trình uvicorn: chạy nhiều worker thì mỗi worker có danh sách việc riêng. Docker của nhóm chạy 1
  worker. Khởi động lại máy chủ thì việc thành "tạm dừng", không mất dữ liệu.
- Chia chương bằng luật có thể sai với sách không ghi "Chương …" (khi đó chia theo 15 trang). Ngưỡng trùng cần hiệu chỉnh
  khi có kết quả Gemini thật trên 2 cuốn sách nhạc lý của nhóm. Chưa chạy với Gemini thật trong phiên cloud.
