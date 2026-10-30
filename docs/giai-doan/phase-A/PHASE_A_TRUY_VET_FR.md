# Giai đoạn A · Bảng truy vết FR (SRS v1.3) so với code v0.4.0

Kiểm tra ngày 18/10/2026 bằng cách đọc code và chạy thật (`pytest` 167 passed, `npm run build` đạt). 192 FR lấy tự động từ SRS Phần 6; ưu tiên là giá trị **sau** điều chỉnh `[THAY ĐỔI]`.

- **Có**: chạy được, có test hoặc đã chạy thử.
- **Một phần**: có nền móng nhưng chưa đủ yêu cầu.
- **Lệch**: có nhưng làm khác SRS (xem N1–N9 trong `PHASE_A_PLAN.md`).
- **Giai đoạn**: B nền tảng · C học/luyện tập · D gợi ý · E AI Tutor · F nhạc cụ/sáng tác/admin.

## Tổng hợp

| Ưu tiên | Có | Một phần | Lệch | Thiếu | Ngoài MVP |
|---|---|---|---|---|---|
| P0 | 13 | 11 | 1 | 78 | 0 |
| P1 | 1 | 9 | 1 | 57 | 0 |
| P2+ | 0 | 0 | 0 | 0 | 21 |

## Chi tiết

| FR | Tên | Ưu tiên | Trạng thái | Ghi chú (đối chiếu code v0.4.0) | Giai đoạn |
|---|---|---|---|---|---|
| FR-VIS-01 | Xem trang chủ | P0 | Thiếu | Chưa có trang chủ công khai; app mở thẳng vào Dashboard | B |
| FR-VIS-02 | Xem chương trình học | P0 | Thiếu | Chưa có trang chủ công khai; app mở thẳng vào Dashboard | B |
| FR-VIS-03 | Xem thông tin khóa học | P0 | Thiếu | Chưa có trang chủ công khai; app mở thẳng vào Dashboard | B |
| FR-VIS-04 | Xem giới thiệu tính năng | P1 | Thiếu | Chưa có trang chủ công khai; app mở thẳng vào Dashboard | B |
| FR-VIS-05 | Đăng ký tài khoản | P0 | Thiếu | Chưa có đăng ký/đăng nhập, chưa có route bảo vệ | B |
| FR-VIS-06 | Đăng nhập | P0 | Thiếu | Chưa có đăng ký/đăng nhập, chưa có route bảo vệ | B |
| FR-VIS-07 | Bảo vệ tính năng giới hạn | P0 | Thiếu | Chưa có đăng ký/đăng nhập, chưa có route bảo vệ | B |
| FR-AUTH-01 | Đăng ký người dùng | P0 | Thiếu | Bảng users chỉ có id, display_name; chưa có mật khẩu, JWT, vai trò | B |
| FR-AUTH-02 | Đăng nhập người dùng | P0 | Thiếu | Bảng users chỉ có id, display_name; chưa có mật khẩu, JWT, vai trò | B |
| FR-AUTH-03 | Đăng xuất | P0 | Thiếu | Bảng users chỉ có id, display_name; chưa có mật khẩu, JWT, vai trò | B |
| FR-AUTH-04 | Lưu mật khẩu an toàn | P0 | Thiếu | Bảng users chỉ có id, display_name; chưa có mật khẩu, JWT, vai trò | B |
| FR-AUTH-05 | Token xác thực | P0 | Thiếu | Bảng users chỉ có id, display_name; chưa có mật khẩu, JWT, vai trò | B |
| FR-AUTH-06 | Xem hồ sơ | P0 | Thiếu | Bảng users chỉ có id, display_name; chưa có mật khẩu, JWT, vai trò | B |
| FR-AUTH-07 | Cập nhật hồ sơ | P1 | Thiếu | Chưa có hồ sơ | B |
| FR-AUTH-08 | Mục tiêu học tập | P0 | Thiếu | Chưa có goal_text | D |
| FR-AUTH-09 | Phân quyền | P0 | Thiếu | Bảng users chỉ có id, display_name; chưa có mật khẩu, JWT, vai trò | B |
| FR-AUTH-10 | Nhạc cụ ưa thích | P1 | Thiếu | Chưa có hồ sơ | B |
| FR-LRN-01 | Xem lộ trình học | P0 | Một phần | Trang Learn liệt kê L01–L08; chưa có lộ trình theo khóa/module | C |
| FR-LRN-02 | Xem khóa học | P0 | Thiếu | Chưa có bảng courses/modules | C |
| FR-LRN-03 | Xem module | P0 | Thiếu | Chưa có bảng courses/modules | C |
| FR-LRN-04 | Xem bài học | P0 | Có | L01–L04 chạy thật (LessonRunner, /lessons/{id}/complete) | C |
| FR-LRN-05 | Hoàn thành bài học | P0 | Có | L01–L04 chạy thật (LessonRunner, /lessons/{id}/complete) | C |
| FR-LRN-06 | Kỹ năng tiên quyết | P1 | Một phần | Đồ thị 26 kỹ năng là DAG có test; chưa dùng để khóa/mở bài | C |
| FR-LRN-07 | Gợi ý bài học tiếp theo | P0 | Một phần | Dashboard chọn "bài tiếp theo" theo thứ tự, chưa phải hệ gợi ý | D |
| FR-LRN-08 | Lịch sử học tập | P1 | Một phần | LearningOverview có attempt/progress; thiếu trang lịch sử | C |
| FR-LRN-09 | Học tiếp | P1 | Một phần | LearningOverview có attempt/progress; thiếu trang lịch sử | C |
| FR-LRN-10 | Tìm kiếm bài học | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-LRN-11 | Bảng điều khiển Người học | P0 | Một phần | Dashboard đọc dữ liệu thật; thiếu mục tiêu, kỹ năng yếu, sáng tác gần đây | C |
| FR-REC-01 | Mục tiêu bằng ngôn ngữ tự nhiên | P0 | Thiếu | Chưa có | D |
| FR-REC-02 | Gợi ý lai | P0 | Thiếu | Chưa có | D |
| FR-REC-03 | Giải thích gợi ý | P0 | Thiếu | Chưa có | D |
| FR-REC-04 | Bộ dữ liệu Người học mô phỏng | P0 | Thiếu | Chưa có | D |
| FR-REC-05 | Đánh giá offline | P0 | Thiếu | Chưa có | D |
| FR-REC-06 | Nhật ký gợi ý | P1 | Thiếu | Chưa có | D |
| FR-MUS-01 | Piano tương tác | P0 | Một phần | Piano SVG chỉ hiển thị, chưa bấm được | C |
| FR-MUS-02 | Phát nốt | P0 | Thiếu | Chưa có âm thanh (Tone.js) | C |
| FR-MUS-03 | Phát hợp âm | P0 | Thiếu | Chưa có âm thanh (Tone.js) | C |
| FR-MUS-04 | Tô sáng nốt | P0 | Một phần | Piano tô được nốt đúng/sai trong Practice | C |
| FR-MUS-05 | Phát ví dụ âm nhạc | P0 | Thiếu | Chưa có âm thanh (Tone.js) | C |
| FR-MUS-06 | Trực quan hóa hợp âm | P0 | Một phần | ChordInspector hiện nốt/công thức/chức năng | C |
| FR-MUS-07 | Trực quan hóa âm giai | P1 | Thiếu | Chưa có | C |
| FR-MUS-08 | Hiển thị ký âm | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-MUS-09 | Nhập bằng bàn phím máy tính | P1 | Thiếu | Chưa có | C |
| FR-MUS-10 | Nút bật âm thanh | P0 | Thiếu | Chưa có âm thanh (Tone.js) | C |
| FR-MUS-11 | Giao diện cần đàn guitar | P0 | Thiếu | Chưa có guitar/trống | F |
| FR-MUS-12 | Mẫu trống / Step Sequencer | P0 | Thiếu | Chưa có guitar/trống | F |
| FR-MUS-13 | Đáp án không phụ thuộc nhạc cụ | P0 | Một phần | Engine có chế độ pitch_class_only; chưa có nhập bằng phím đàn | C |
| FR-EX-01 | Bắt đầu bài tập | P0 | Có | Practice + quiz bài học gọi Engine; có đáp án và câu giải thích tiếng Việt | C |
| FR-EX-02 | Nộp câu trả lời | P0 | Có | Practice + quiz bài học gọi Engine; có đáp án và câu giải thích tiếng Việt | C |
| FR-EX-03 | Kiểm tra tất định | P0 | Có | Practice + quiz bài học gọi Engine; có đáp án và câu giải thích tiếng Việt | C |
| FR-EX-04 | Phản hồi đúng | P0 | Có | Practice + quiz bài học gọi Engine; có đáp án và câu giải thích tiếng Việt | C |
| FR-EX-05 | Phản hồi sai | P0 | Có | Practice + quiz bài học gọi Engine; có đáp án và câu giải thích tiếng Việt | C |
| FR-EX-06 | Hiển thị đáp án đúng | P0 | Có | Practice + quiz bài học gọi Engine; có đáp án và câu giải thích tiếng Việt | C |
| FR-EX-07 | Giải thích | P0 | Có | Practice + quiz bài học gọi Engine; có đáp án và câu giải thích tiếng Việt | C |
| FR-EX-08 | Thử lại | P0 | Có | Practice + quiz bài học gọi Engine; có đáp án và câu giải thích tiếng Việt | C |
| FR-EX-09 | Gợi ý | P1 | Thiếu | Chưa có gợi ý | C |
| FR-EX-10 | Lịch sử lượt làm | P1 | Một phần | Lưu attempts; chưa có giao diện lịch sử | C |
| FR-EX-11 | Độ khó | P1 | Thiếu | Chưa có độ khó | C |
| FR-EX-12 | Mẫu bài tập | P1 | Thiếu | Chưa có bảng exercise_templates | C |
| FR-EX-13 | Ngẫu nhiên hóa bài tập | P1 | Một phần | Practice tự random ở frontend; cần chuyển về template ở backend | C |
| FR-EX-14 | Chế độ chấm | P0 | Một phần | Engine hỗ trợ đủ; grading_service chưa truyền grading_mode/root_position_only (CP1) | C |
| FR-EX-15 | Bài tập gõ tiết tấu | P1 | Một phần | Engine + API /grade/tap-rhythm có; chưa có giao diện | C |
| FR-ERR-01 | Phân loại lỗi | P0 | Có | Engine trả mã lỗi SRS 4.5 (+7 mã đề xuất) | C |
| FR-ERR-02 | Lịch sử lỗi | P1 | Một phần | Bảng attempt_errors lưu mã lỗi; chưa có màn xem | C |
| FR-ERR-03 | Phát hiện kỹ năng yếu | P1 | Thiếu | Cần mastery | C |
| FR-ERR-04 | Ôn tập có mục tiêu | P1 | Thiếu | Cần mastery | C |
| FR-ERR-05 | Giải thích sửa lỗi | P0 | Có | message_vi theo mã lỗi | C |
| FR-FL-01 | Xem flashcard | P0 | Có | Thẻ ôn đến hạn hiện ở Progress | C |
| FR-FL-02 | Lật đáp án | P0 | Một phần | Trả lời trực tiếp, chưa có lật thẻ | C |
| FR-FL-03 | Kết quả ôn tập | P1 | Có | Bảng review_attempts | C |
| FR-FL-04 | Hàng đợi ôn tập | P1 | Một phần | Có /review/due; chưa giới hạn 20 thẻ, chưa ưu tiên kỹ năng yếu | C |
| FR-FL-05 | Ôn kỹ năng yếu | P1 | Thiếu | Chưa có | C |
| FR-FL-06 | Thẻ đa phương thức | P1 | Thiếu | Chưa có | C |
| FR-FL-07 | Ôn tập giãn cách | P1 | Lệch | Lịch 1–3–7–14–30 ngày; SRS chốt Leitner 1–2–4–8–16 (N2) | C |
| FR-MAS-01 | Lưu mức thành thạo theo từng kỹ năng | P0 | Thiếu | Chưa có mastery (N6) | C |
| FR-MAS-02 | Cập nhật mức thành thạo từ các lượt làm bài tập | P0 | Thiếu | Chưa có mastery (N6) | C |
| FR-MAS-03 | Phát hiện kỹ năng yếu | P1 | Thiếu | Chưa có mastery (N6) | C |
| FR-MAS-04 | Dùng mức thành thạo để gợi ý | P1 | Thiếu | Chưa có mastery (N6) | C |
| FR-MAS-05 | Hiển thị tiến độ cho Người học | P0 | Một phần | Có tiến độ theo bài, chưa theo kỹ năng | C |
| FR-AI-01 | Tạo phiên chat | P0 | Thiếu | Chưa có AI Tutor | E |
| FR-AI-02 | Gửi câu hỏi | P0 | Thiếu | Chưa có AI Tutor | E |
| FR-AI-03 | Hội thoại theo ngữ cảnh | P0 | Thiếu | Chưa có AI Tutor | E |
| FR-AI-04 | Giải thích khái niệm | P0 | Thiếu | Chưa có AI Tutor | E |
| FR-AI-05 | Giải thích đáp án sai | P0 | Thiếu | Chưa có AI Tutor | E |
| FR-AI-06 | Đưa gợi ý | P1 | Thiếu | Chưa có AI Tutor | E |
| FR-AI-07 | Giải thích sáng tác | P1 | Thiếu | Chưa có AI Tutor | E |
| FR-AI-08 | Lưu lịch sử chat | P0 | Thiếu | Chưa có AI Tutor | E |
| FR-AI-09 | Xem lịch sử chat | P1 | Thiếu | Chưa có AI Tutor | E |
| FR-AI-10 | Xử lý lỗi AI | P0 | Thiếu | Chưa có AI Tutor | E |
| FR-AI-11 | Ngữ cảnh có căn cứ | P0 | Thiếu | Chưa có AI Tutor | E |
| FR-AI-12 | Từ chối kết luận | P1 | Thiếu | Chưa có AI Tutor | E |
| FR-AI-13 | Công cụ Music Engine | P0 | Một phần | tools.py đã khai báo get_chord_tones, get_scale, identify_interval | E |
| FR-AI-14 | Bộ nhớ phiên | P0 | Thiếu | Chưa có AI Tutor | E |
| FR-AI-15 | Hạn mức sử dụng | P0 | Thiếu | Chưa có AI Tutor | E |
| FR-AI-16 | Ngôn ngữ trả lời | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-AI-17 | Đánh giá câu trả lời AI | P1 | Thiếu | Chưa có AI Tutor | E |
| FR-AI-18 | Sinh quiz theo kỹ năng | P0 | Thiếu | Chưa có (sinh quiz bằng Engine làm trước, LLM sau) | E |
| FR-AI-19 | Trích dẫn RAG | P0 | Thiếu | Chưa có AI Tutor | E |
| FR-AI-20 | Kiểm chứng đầu ra AI | P0 | Thiếu | Chưa có AI Tutor | E |
| FR-AI-21 | Chống prompt injection | P1 | Thiếu | Chưa có AI Tutor | E |
| FR-COM-01 | Tạo dự án | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-02 | Đặt tên dự án | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-03 | Lưu dự án | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-04 | Mở dự án | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-05 | Cập nhật dự án | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-06 | Xóa dự án | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-07 | Chọn giọng | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-08 | Chọn tempo | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-09 | Nhịp | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-COM-10 | Thêm hợp âm | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-11 | Sửa hợp âm | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-12 | Xóa hợp âm | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-13 | Sắp xếp lại hợp âm | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-14 | Trường độ hợp âm | P1 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-15 | Thêm nốt giai điệu | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-16 | Sửa cao độ | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-17 | Sửa trường độ | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-18 | Xóa nốt | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-19 | Di chuyển nốt | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-COM-20 | Nhập bằng piano | P1 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-21 | Phát lại | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-22 | Dừng phát | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-23 | Lặp | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-24 | Đổi tempo | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-25 | Tắt giai điệu | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-26 | Tắt hòa âm | P1 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-27 | Máy đếm nhịp | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-31 | Đếm vào | P1 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-28 | Kiểm tra vòng hợp âm | P1 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-29 | Track trống | P0 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-30 | Âm sắc nhạc cụ | P1 | Thiếu | Trang Harmony Lab chỉ là khung tĩnh | F |
| FR-COM-AI-01 | Gợi ý hợp âm tiếp theo | P1 | Thiếu | Chưa có | F |
| FR-COM-AI-02 | Gợi ý hợp âm thay thế | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-COM-AI-03 | Gợi ý câu giai điệu | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-COM-AI-04 | Giải thích gợi ý | P1 | Thiếu | Chưa có | F |
| FR-COM-AI-05 | Nghe thử gợi ý | P1 | Thiếu | Chưa có | F |
| FR-COM-AI-06 | Chấp nhận gợi ý | P1 | Thiếu | Chưa có | F |
| FR-COM-AI-07 | Từ chối gợi ý | P1 | Thiếu | Chưa có | F |
| FR-COM-AI-08 | Phân tích hòa âm | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-COM-AI-09 | Tô sáng nốt trong hợp âm | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-COM-AI-10 | Dự phòng theo luật | P1 | Thiếu | Chưa có | F |
| FR-COM-ADV-01 | Xuất MIDI | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-COM-ADV-02 | Xuất audio | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-COM-ADV-03 | Chia sẻ bản sáng tác | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-COM-ADV-04 | Quản lý phiên bản dự án | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-COM-ADV-05 | Thư viện sáng tác công khai | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-COM-ADV-06 | Thu âm từ bàn phím MIDI | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-COM-ADV-07 | Chấm điểm nhạc cụ qua micro | Future | Ngoài MVP | Không làm (P2) | - |
| FR-ADM-01 | Đăng nhập Admin | P0 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-02 | Xem danh sách người dùng | P0 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-03 | Tìm kiếm người dùng | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-04 | Vô hiệu hóa người dùng | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-05 | Kích hoạt lại người dùng | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-06 | Quản lý vai trò người dùng | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-40 | Khởi tạo Admin đầu tiên | P0 | Thiếu | Chưa có seed_admin | B |
| FR-ADM-07 | Tạo khóa học | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-08 | Cập nhật khóa học | P0 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-09 | Xóa khóa học | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-ADM-10 | Tạo module | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-11 | Cập nhật module | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-12 | Xóa module | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-ADM-13 | Tạo bài học | P0 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-14 | Cập nhật bài học | P0 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-15 | Xóa bài học | P0 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-16 | Sắp xếp lại bài học | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-17 | Xuất bản/Ẩn nội dung | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-18 | Tạo kỹ năng | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-19 | Sửa kỹ năng | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-20 | Xóa kỹ năng | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-21 | Quản lý điều kiện tiên quyết (từ chối chu trình) | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-22 | Gán bài học cho kỹ năng | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-23 | Cấu hình yêu cầu mức thành thạo (mastery) | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-ADM-24 | Tạo bài tập | P0 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-25 | Cập nhật bài tập | P0 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-26 | Xóa bài tập | P0 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-27 | Cấu hình đáp án đúng | P0 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-28 | Cấu hình lời giải thích | P0 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-29 | Đặt độ khó | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-30 | Quản lý mẫu bài tập | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-31 | Tạo flashcard | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-32 | Cập nhật flashcard | P0 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-33 | Xóa flashcard | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-34 | Liên kết flashcard với kỹ năng | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-35 | Quản lý ví dụ audio | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-36 | Quản lý ví dụ hợp âm | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-37 | Quản lý ví dụ âm giai | P1 | Thiếu | Chưa có giao diện/API admin | F |
| FR-ADM-38 | Quản lý nguồn giáo trình | P1 | Một phần | Sổ nguồn source_registry.py có sẵn (chưa có giao diện) | F |
| FR-ADM-39 | Nhập nội dung từ file YAML | P0 | Lệch | Nội dung nạp từ Python curriculum_specs.py, chưa phải YAML/MD (N5) | C |
| FR-ADM-AI-01 | Cấu hình nhà cung cấp AI | P1 | Thiếu | Chưa có (cấu hình AI qua .env trước) | F |
| FR-ADM-AI-02 | Quản lý prompt của tutor | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-ADM-AI-03 | Xem nhật ký lỗi AI | P2 | Ngoài MVP | Không làm (P2) | - |
| FR-ADM-AI-04 | Bật/Tắt tính năng AI | P1 | Thiếu | Chưa có (cấu hình AI qua .env trước) | F |
