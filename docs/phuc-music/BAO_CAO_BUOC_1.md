# Báo cáo Bước 1: gộp khu học v0.5.3 vào nền main

Ngày: 31/10/2026. Nhánh `phuc-music`, Draft PR #18. Phúc chọn M-1..M-5 = A.

## 1. Đã làm gì

Bước 0 cho thấy khu học trên main thực ra là khu học của v0.5.3 đã được sửa tiếp. Vì vậy Bước 1 chỉ đưa lại **phần trình bày** còn thiếu, không chép lại trang nào:

1. **Khung khu học kiểu v0.5.3** (`AppLayout.tsx`): thanh bên tối, mục đang mở nổi khối, chân thanh bên có tên, email, nút Đăng xuất và phiên bản. Trên điện thoại là dải tab tối chia đều cột, có nút Đăng xuất ở góc. Route bảo vệ, `NavLink` và đăng xuất về trang chủ vẫn giữ của main.
2. **Nút "Từng bước / Xem cả bài"** trong bài học (`LessonRunner.tsx`). "Xem cả bài" hiện mọi bước trên một trang như v0.5.3. Hai chế độ dùng chung một danh sách bước và cùng trạng thái chấm, nên đổi qua lại không mất câu đã đúng. Lựa chọn được nhớ trong trình duyệt.
3. Màu khung đặt thành token `--color-shell-*` trong `@theme` (`index.css`) để Bước 3 đổi bảng màu ở một chỗ.
4. Phiên bản lấy từ `package.json` qua Vite `define`, không ghi cứng. README dòng đầu đổi thành `v0.5.4-dev`.

Mọi quyết định chọn bên nằm ở `01_NHAT_KY_GOP.md` (17 dòng).

**Không đổi:** backend, CSDL, Music Engine, nội dung bài, logic chấm, lời giải, 409, phiên bản câu hỏi, Leitner, trang công khai.

## 2. File

| File | Thay đổi |
|---|---|
| `frontend/src/components/layout/AppLayout.tsx` | Khung tối kiểu v0.5.3 |
| `frontend/src/components/layout/Logo.tsx` | Thêm prop `inverted` (chữ trắng trên nền tối) |
| `frontend/src/components/learning/LessonRunner.tsx` | Chế độ "Xem cả bài" |
| `frontend/src/index.css` | Token `--color-shell-*` |
| `frontend/src/styles.css` | 4 lớp cho nút chọn cách xem và trang cả bài |
| `frontend/vite.config.ts`, `frontend/src/globals.d.ts` | Hằng `__APP_VERSION__` |
| `README.md` | Dòng đầu |
| `scripts/phuc-music/luong_buoc1.cjs` | Kịch bản Playwright chạy luồng và chụp ảnh |
| `docs/phuc-music/01_NHAT_KY_GOP.md`, `BAO_CAO_BUOC_1.md`, `anh/buoc-1/` | Tài liệu và ảnh |

## 3. Kiểm tra (chạy thật ngày 31/10/2026)

| Lệnh | Kết quả |
|---|---|
| `cd backend && pytest -q` | 325 passed, 21 skipped (giống main, backend không đổi) |
| `cd frontend && npm run build` | Đạt (`tsc -b` + Vite) |
| `node scripts/phuc-music/luong_buoc1.cjs <thư mục>` (backend :8000 SQLite mới, frontend :5173) | Đạt cả 1440px và 390px, xem bảng dưới |
| Tương phản màu khung (công thức WCAG) | Chữ thường `#c8cfdd` trên `#151a27`: 11,1:1; chữ phụ `#9da7bd` trên `#252c3d`: 5,77:1 (thấp nhất); đều ≥ 4,5:1 |
| CI trên PR #18 | Xem trạng thái check trên PR |

Kết quả luồng (in ra từ kịch bản, cả hai cỡ màn hình giống nhau):

| Bước | Kết quả |
|---|---|
| Chưa đăng nhập, mở `/app` | Chuyển tới `/dang-nhap?next=%2Fapp` |
| Đăng ký | Vào thẳng `/app` |
| Đăng xuất | Về `/` |
| Đăng nhập | Vào `/app` |
| Bài 1, câu "Quãng từ F lên A là gì?" chọn M3 | "Chính xác! Giải thích: F–A dùng ba tên chữ F–G–A và cách nhau 4 nửa cung, nên là M3." Tiến độ 1/6 |
| Bấm "Xem cả bài" | 17 bước trên một trang, vẫn ghi đúng 1/6 |
| Đăng xuất | Về `/` |

**Chưa có test tự động cho frontend trong CI.** Main chưa cài Vitest (Vitest đến cùng PR #12). Bước 2 dựng trên PR #12 (câu 4A), nên test cho "Xem cả bài" sẽ thêm ở đó. Ở bước này, bằng chứng là kịch bản Playwright ở trên, chạy tay chứ chưa nằm trong CI.

## 4. Ảnh (`anh/buoc-1/`, mỗi ảnh có bản `-may-tinh` 1440px và `-dien-thoai` 390px)

`01-trang-chu`, `02-dang-ky`, `03-dang-nhap`, `04-khu-hoc-tong-quan`, `05-hoc`, `06-bai-1-tung-buoc`, `07-bai-1-tra-loi-dung`, `08-bai-1-xem-ca-bai`, `09-dang-xuat-ve-trang-chu`.

## 5. Xung đột có thể gặp khi gộp các PR đang mở

| PR | File chung | Cách xử lý |
|---|---|---|
| #16 logo | `Logo.tsx`, có thể cả `AppLayout.tsx` | Logo mới cần có bản cho nền tối (prop `inverted` hoặc tương đương) |
| #12 HM-001 | Không chung file ở bước này | Bước 2 dựng trên #12 |
| #14, #15, #17 | Không chung | — |

## 6. Việc còn lại và câu cần nhóm quyết

- Không có câu mới cần quyết. Bước 2 làm theo các lựa chọn đã chốt (2B kèm M-5A, 3A, 4A).
- Thắng hoặc Phúc nên xem `AppLayout.tsx` trên điện thoại thật: lưới 6 mục trên màn 360px khá chật (chữ "Luyện tập", "Tiến độ" xuống 2 dòng như ở v0.5.3).
