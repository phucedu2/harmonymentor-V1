# Kiểm soát khu Admin, đợt 1: soát bằng trình duyệt (24/11/2026)

Phúc giao (24/11): Claude đóng vai kiểm soát viên trang Admin, ưu tiên AI soạn bài. Phúc chọn 2A: chạy app thật trong
trình duyệt tự động với AI giả, đi hết các màn Admin, ghi lỗi, sửa lỗi nặng/vừa, mở một PR, Phúc duyệt rồi mới gộp vào
`phuc-music`. Phần làm thêm chức năng (tạo/xóa bài, CRUD bài tập, kỹ năng, nâng quyền, công tắc AI) là các PR sau.

## Cách soát

- Backend thật (FastAPI + SQLite + seed nội dung) chạy cổng 8000, frontend `npm run dev` cổng 5173.
- AI giả thay hai provider qua `app.dependency_overrides` (không gọi Gemini, không tốn hạn mức): AI soạn bài trả khối lý
  thuyết lấy câu từ đúng trang tài liệu và 10 câu luyện tập có phần kiểm cho Music Engine; AI Tutor giả trả lời bằng bài
  đầu tiên trong ngữ cảnh được đưa vào, kèm trích dẫn. Retrieval, Engine, cờ duyệt, xuất bản, ẩn/hiện đều là code thật.
- Playwright (Chromium) bấm như người dùng; ảnh minh chứng ở `anh/`.

## Kết quả từng vòng

| Vòng | Bước | Kết quả |
|---|---|---|
| AI soạn bài | Tải tài liệu `.md` 3 chương, đồng ý gửi AI | Đạt; tài liệu qua cổng nhạc lý |
| | "AI soạn bài từ cả tài liệu", chạy nền | Đạt; 1 phần → 1 bản nháp, nhật ký từng bước |
| | Mở bản nháp, tick cờ + câu cần duyệt, "Xuất bản" | **Lỗi AUD-01** (đã sửa), sau sửa: đạt, bài ở trạng thái ẨN |
| | "Xem như học sinh" | Đạt; tiêu đề hiện "Bài 0." (AUD-02, đã sửa) |
| | "Hiện cho học sinh" | Đạt; "AI Tutor đã nạp 1 đoạn". Màn vẫn hiện nút như lúc ẩn (AUD-04, đã sửa) |
| | Người học đăng ký mới thấy bài trong lộ trình | Đạt (Bài 10) |
| | Người học hỏi AI Tutor "Quãng ghép là gì?" | Đạt; retrieval xếp bài AI hạng 1 (0,90), trả lời trích `AI-…-B01` |
| Bài học | Mở bài, sửa tiêu đề khối, lưu nháp, xuất bản, lịch sử, về bản gốc, ẩn, hiện lại | Đạt |
| Người dùng | Tìm "hs1", khóa (hỏi xác nhận), đăng nhập bằng tài khoản bị khóa → 401, mở khóa | Đạt; token cũ của người bị khóa cũng bị chặn |
| Thống kê | 14/30/90 ngày, phễu, kỹ năng, thành thạo | Đạt; đếm thừa 1 người học (AUD-03, đã sửa) |
| Phân quyền | Người học gọi `/admin/stats` | 403, đúng |

## Lỗi tìm thấy

| Mã | Mức | Lỗi | Sửa |
|---|---|---|---|
| AUD-01 | Nặng | Bản nháp có cờ "Ít câu luyện tập" (ADR-034): bấm "Xuất bản" luôn bị chặn lần đầu với "Sửa đổi vừa rồi sinh 1 cờ mới". Lý do: lưu bản nháp viết lại chữ của cờ (bỏ đoạn "sau khi đã gọi bù") nên mã cờ đổi, dấu "Đã đối chiếu" mất. | `update_draft` giữ `question_shortfall` cũ; `refresh_shortfall` giữ nguyên chữ khi số câu không đổi. Bớt/thêm câu thì chữ đổi, phải tick lại (đúng ý). Test `test_luu_ban_nhap_khong_lam_mat_dau_doi_chieu_co_thieu_cau`. |
| AUD-02 | Nhẹ | Xem trước bài đang ẩn hiện "Bài 0." | Bài chưa có số thứ tự hiện "Xem trước: …" (`LessonRunner.tsx`). |
| AUD-03 | Vừa | Thống kê đếm `demo-user` cũ (không email, không đăng nhập được) là người học, tab Người dùng không liệt kê → hai con số lệch nhau. | Thống kê chỉ đếm tài khoản có email, khớp tab Người dùng. Test `test_thong_ke_khong_dem_tai_khoan_khong_email_khop_tab_nguoi_dung`. |
| AUD-04 | Vừa | Sau "Hiện cho học sinh", mở lại bản nháp vẫn thấy nút "Hiện cho học sinh"; danh sách chỉ ghi "Đã xuất bản", không biết bài đang ẩn hay đã hiện. | API bản nháp trả `lesson_hidden`; màn hiện "Học sinh đã thấy bài", danh sách ghi "đang ẩn"/"học sinh thấy". Test `test_ban_nhap_cho_biet_bai_da_xuat_ban_dang_an_hay_da_hien`. |
| AUD-05 | Nhẹ | Tải lên xong, ô chọn tệp vẫn giữ tên tệp cũ (dễ tưởng chưa tải). | Ô chọn tệp trống lại sau khi tải lên. |
| AUD-06 | Vừa | Thông báo kết quả tải lên/duyệt/soạn nằm cuối trang dài, bấm xong không thấy gì. | Thông báo chuyển lên ngay dưới khung tải lên. |
| AUD-07 | Nhẹ | Nhật ký từng bước hiện mã `top_up` thô. | Nhãn "Gọi bù câu luyện tập". |

## Ghi nhận, chưa sửa (không phải lỗi code hoặc cần nhóm quyết)

- Bài 1 có 2 khối mang nhãn "Engine nghi sai" (#9 "Hợp âm ba nốt: dựng bằng hai bước", #16 thẻ ôn nháp). Là nội dung đã
  phát hành: theo quy tắc, Claude không tự sửa; cần Đạt đọc lại.
- Bài 3, 4 và 12 có 0 câu luyện tập (nội dung, không phải code).
- Tài liệu ngắn 3 chương gộp thành 1 phần "Trang 1" (thiết kế `MIN_PART_CHARS`: chương ngắn gộp để đỡ tốn lượt Gemini).
- Bộ đếm "0/7 câu hỏi" ở bài AI không tính câu tự luận mở (chấm theo rubric, không tính mastery): đúng thiết kế.
- Ô chọn tệp hiện chữ tiếng Anh "Choose File" của trình duyệt; đổi cần ô chọn tệp tự vẽ, để PR sau nếu nhóm muốn.
- Chưa có cách xóa/xem tài liệu bị từ chối; chưa có tạo/xóa bài, CRUD bài tập, kỹ năng, nâng quyền, công tắc AI:
  làm ở các PR sau theo 1A–8A.

## Kiểm chứng

- `pytest -q` (SQLite): xem mô tả PR (CI đặt `--min-passed 1586`, thêm 3 test).
- `npm run build` đạt, `npx vitest run` 313/313 đạt.
- Trình duyệt: chạy lại cả vòng sau khi sửa: xuất bản không bị chặn, bản nháp báo "Học sinh đã thấy bài", danh sách
  ghi "Đã xuất bản · học sinh thấy".
