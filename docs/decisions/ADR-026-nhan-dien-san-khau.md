# ADR-026 · Nhận diện màu "Sân khấu" thay Đồng & Gỉ làm mặc định

Trạng thái: **Chấp nhận 17/11/2026**. Phúc báo nhóm chọn phương án Sân khấu. Liên quan ADR-007 (logo), đợt soi lỗi frontend (`docs/SOI_LOI_FRONTEND.md` mục 1e, 1f), Draft PR #61.

## Bối cảnh

Đề soi lỗi frontend (16/11/2026) yêu cầu 1–2 phương án nhận diện mới dạng theme token, bật bằng một biến, giữ Đồng & Gỉ làm mặc định. Ngày 17/11 có hai phương án, mỗi cái có sáng và tối:

- **Sân khấu**: tím đêm, nút tím; khi tối, nút là màu đèn spotlight hổ phách.
- **Giấy nhạc**: giấy kem, mực khắc bản, bút chì đỏ.

Ảnh so sánh ba bảng (sáng và tối, 5 trang) ở `docs/soi-loi-frontend/theme/`. Nhóm chọn Sân khấu.

## Quyết định

1. **Sân khấu là mặc định.** `VITE_BRAND` mặc định là `san-khau` (`frontend/vite.config.ts`). Script nhỏ trong `index.html` đặt `<html data-brand>` trước khi vẽ trang, nên không nháy màu cũ.
2. **Chỉ đổi token màu.** Toàn bộ nằm trong `frontend/src/theme/brands.css`: token `--color-*` của app, biến `--w-*` của trang chủ, biến `--hm-logo-*` của logo. Bố cục, font, chữ giao diện không đổi.
3. **Bảng màu Sân khấu** (tương phản WCAG 2.1, đo bằng `docs/soi-loi-frontend/script/tuong-phan-theme.py`):

   | Vai trò | Sáng | Tối |
   | --- | --- | --- |
   | Nền | `#F4F2F8` | `#0E0C1B` |
   | Thẻ | `#FFFFFF` | `#18152B` |
   | Chữ | `#17142B` (16,1:1) | `#ECEBF5` (16,3:1) |
   | Chữ phụ | `#57536E` (6,6:1) | `#A9A5C2` (8,1:1) |
   | Primary | `#4B33B8` (7,7:1), chữ trắng trên nút 8,5:1 | `#F2B33D` (10,4:1), chữ `#1A1405` trên nút 9,9:1 |
   | Thanh bên khu học | `#120F24` | `#08070F` |
   | Sai / đúng | `#B02A37` (5,8:1) / `#1D6B40` (5,9:1) | `#FF9A94` / `#74D39C` |

   Mọi cặp chữ/nền đều ≥ 5,8:1. axe 0 lỗi ở 11 trang × sáng/tối (`docs/soi-loi-frontend/audit-san-khau.json`).
4. **Logo (sửa ADR-007 mục 3 "Màu").** Hình logo không đổi. Không sửa `HarmonyMentorLogo.tsx` hay SVG sinh tự động; `brands.css` chỉ đổi biến:
   - Ô cuộn giấy: `#17142B` (nền sáng), `#1A1630` kèm viền hổ phách `#F2B33D` (nền tối, 10,1:1 trên `#120F24`; ô tối đứng một mình chỉ 1,07:1 nên viền là bắt buộc, giống lý do viền gỉ của ADR-007).
   - Chữ: `#17142B` trên nền sáng, `#ECEBF5` trên nền tối.
   - **Màu các lỗ giữ nguyên** (luật số 2 của `BRAND_NOTE.md`: mỗi lỗ là một nốt, màu nốt không đổi theo chế độ). Lỗ thấp nhất `#D48FD1` trên ô `#17142B` = 7,4:1.
   - Favicon `frontend/public/favicon-san-khau.svg` (cùng hình, chỉ đổi biến ô và viền), `theme-color` `#17142B`, `site.webmanifest` theo Sân khấu.
5. **Đồng & Gỉ được giữ lại**, không xóa: build với `VITE_BRAND=dong-gi`, hoặc mở `?brand=dong-gi` một lần (trình duyệt nhớ trong `localStorage` `hm-brand`). Giấy nhạc cũng giữ làm **phương án dự phòng** (Phúc chọn 17/11/2026: giữ, không xóa): bật bằng `?brand=giay-nhac` hoặc `VITE_BRAND=giay-nhac`; chỉ tốn khoảng 3 KB CSS và là minh chứng nhóm đã cân nhắc hai phương án. Giấy nhạc có đủ bộ riêng như Sân khấu (18 SVG + PNG ở `docs/thuong-hieu/logo/giay-nhac/`, favicon SVG/ICO, icon app `*-giay-nhac.png`), dựng bằng cùng script `python3 docs/thuong-hieu/_nguon/san_khau.py giay-nhac` rồi `node docs/thuong-hieu/_nguon/xuat_png_ban_mau.mjs giay-nhac`; lỗ nốt cũng giữ nguyên màu. `index.html` tự đổi favicon, `theme-color` và icon iPhone theo `?brand=`; `site.webmanifest` là file tĩnh nên vẫn theo Sân khấu.
6. **Màu 12 nốt** (`--color-note-*`) và phím đàn, khuông nhạc không đổi: chúng là ký hiệu học, không phải nhận diện.

## Hệ quả

- Ảnh chụp, slide, báo cáo cũ (màu xanh Đồng & Gỉ) sẽ khác app. Cần chụp lại cho slide bảo vệ.
- Bộ file logo Sân khấu (17 SVG + PNG cho slide) ở `docs/thuong-hieu/logo/san-khau/`, dựng bằng `docs/thuong-hieu/_nguon/san_khau.py` (chỉ thay màu vỏ/chữ/viền, script tự kiểm màu nốt không đổi). Bộ Đồng & Gỉ trong `logo/*.svg` giữ nguyên.
- Icon PNG cho app (`icon-192/512-san-khau.png`, `apple-touch-icon-san-khau.png`) đã có; manifest trỏ bản Sân khấu kể cả khi chạy `?brand=dong-gi` (manifest là file tĩnh). `favicon-san-khau.ico` (16/32/48 px) cho trình duyệt không đọc favicon SVG; `favicon.ico` cũ giữ cho bản Đồng & Gỉ.
- Nếu `VITE_BRAND=dong-gi` thì `site.webmanifest` vẫn mang màu Sân khấu (file tĩnh); chỉ ảnh hưởng màu thanh tiêu đề khi cài app lên màn hình chính.
- Đổi lại về Đồng & Gỉ cho cả nhóm chỉ cần sửa một dòng trong `vite.config.ts`.
