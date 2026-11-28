# Nhật ký gộp khu học v0.5.3-dev vào main (Bước 1)

Nguyên tắc Phúc chọn: **bố cục v0.5.3, logic main**. Mỗi dòng là một quyết định chọn bên. Khảo sát nền ở `00_KHAO_SAT.md`; Phúc chọn M-1..M-5 = A ngày 31/10/2026.

| # | Chỗ | Tag v0.5.3-dev | Main | Chọn | Lý do |
|---|---|---|---|---|---|
| 1 | Khung khu học (`AppLayout.tsx`) | Thanh bên tối `#151a27`, mục đang mở nổi khối `#252c3d` | Thanh bên trắng, mục đang mở nền xanh nhạt | **Bố cục tag** | Phúc chọn bố cục v0.5.3 |
| 2 | Điều hướng | `useState` + nút, không có URL | `NavLink` theo route `/app/*` | **Logic main** | Có URL thì F5, nút Back, link chia sẻ mới chạy |
| 3 | Bảo vệ route | Không có đăng nhập | `RequireAuth` → `/dang-nhap?next=…` | **Main** | Yêu cầu Bước 1 |
| 4 | Nhãn phụ tiếng Anh (HOME, LEARN…) | Có | Không | **Bỏ** (M-3) | Giao diện tiếng Việt |
| 5 | Tên mục sáng tác | "Harmony Lab" | "Sáng tác" | **"Sáng tác"** (M-4) | Quyết định M3 theo SRS |
| 6 | Phiên bản trên thanh bên | Ghi cứng `v0.5.3-dev` dưới logo | Không có | **Hiện ở chân thanh bên, lấy từ `package.json`** | Giữ ý của tag, không ghi cứng (Vite `define __APP_VERSION__`) |
| 7 | Ghi chú "Phase 2.2 / Lesson 1 pedagogy rewrite" ở chân | Có | Không | **Bỏ** | Thuật ngữ dev, người học không cần |
| 8 | Tên, email, Đăng xuất | Không có | Có | **Main**, đổi màu cho nền tối | Đăng xuất về `/` |
| 9 | Điện thoại | Dải tab tối, 5 cột bằng nhau | Dải tab sáng, cuộn ngang, bị cắt chữ | **Bố cục tag** (lưới chia đều, nền tối) + nút Đăng xuất của main | Không còn mục bị che |
| 10 | Logo | Chữ "H" trong ô trắng | `Logo` của main (♪) | **Main**, thêm `inverted` cho nền tối | PR #16 sẽ thay logo; chỉ thêm 1 prop để dễ gộp |
| 11 | Bài học (`LessonRunner.tsx`) | Cuộn một trang | Chia bước (PR #6) | **Giữ chia bước, thêm nút "Xem cả bài"** (M-1) | Không mất tính năng PR #6; ai thích kiểu v0.5.3 vẫn có |
| 12 | Ô "Bài này bắt đầu từ con số 0" | Có (khối `L01-B01`) | Có, là bước 2 | **Không đổi** | Khối đã nằm trong nội dung của main |
| 13 | Trang Harmony Lab | Khung 4 dòng | "Sắp mở" | **Main** | Bước 4 làm xưởng sáng tác thật |
| 14 | Tổng quan, Học, Luyện tập, Tiến độ | Bản gốc | Bản sửa tiếp của tag (Việt hóa, mức Dễ/Vừa/Khó, Leitner…) | **Main** | Main đã chứa bố cục tag; chỉ khác chữ và logic |
| 15 | Backend | `user_id="demo-user"` từ client | `user_id` từ token | **Main** | Nguyên tắc bất biến số 4; không có gì cần khôi phục |
| 16 | Màu khung | — | — | **Token tạm `--color-shell-*`** trong `@theme` (M-2) | Bước 3 đổi sang "Đồng & Gỉ" ở một chỗ |
| 17 | README dòng đầu | `v0.5.3-dev` | — | **`v0.5.4-dev`** theo `frontend/package.json` | Yêu cầu Bước 1 |
