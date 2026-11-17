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
5. **Đồng & Gỉ được giữ lại**, không xóa: build với `VITE_BRAND=dong-gi`, hoặc mở `?brand=dong-gi` một lần (trình duyệt nhớ trong `localStorage` `hm-brand`). Giấy nhạc cũng giữ để so sánh (`?brand=giay-nhac`).
6. **Màu 12 nốt** (`--color-note-*`) và phím đàn, khuông nhạc không đổi: chúng là ký hiệu học, không phải nhận diện.

## Hệ quả

- Ảnh chụp, slide, báo cáo cũ (màu xanh Đồng & Gỉ) sẽ khác app. Cần chụp lại cho slide bảo vệ.
- File logo trong `docs/thuong-hieu/logo/*.svg` vẫn là bản Đồng & Gỉ. Muốn có file SVG/PNG Sân khấu để in hay đưa vào slide thì thêm bảng màu Sân khấu vào script `docs/thuong-hieu/_nguon/` rồi dựng lại; chưa làm.
- `favicon.ico`, `apple-touch-icon.png`, `icon-192/512.png` (ảnh raster) vẫn là bản Đồng & Gỉ; chỉ favicon SVG đổi. Trình duyệt hiện đại dùng SVG.
- Nếu `VITE_BRAND=dong-gi` thì `site.webmanifest` vẫn mang màu Sân khấu (file tĩnh); chỉ ảnh hưởng màu thanh tiêu đề khi cài app lên màn hình chính.
- Đổi lại về Đồng & Gỉ cho cả nhóm chỉ cần sửa một dòng trong `vite.config.ts`.
