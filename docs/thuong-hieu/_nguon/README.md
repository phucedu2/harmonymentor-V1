# Dựng lại bộ logo Harmony Mentor

Script này dựng lại cả 26 phác thảo và 12 phương án đã đề xuất ngày 27/10/2026. Trong repo chỉ giữ bản nhóm chọn ở `../logo/` (ADR-007). Chạy `build.sh` sẽ ghi thêm các thư mục `svg/`, `png/`, `favicon/`, `react/`, `mockup/` vào `docs/thuong-hieu/`; đừng commit các thư mục đó, chỉ chép file cần thiết vào `../logo/`, `frontend/public/` và `frontend/src/components/brand/`.

Mọi hình đều sinh bằng code: vị trí phím đen, tỉ lệ dây 2^(-n/12), độ rộng vòm 4:3… đều là công thức trong `symbols.js`, chữ được đổi thành path bằng opentype.js trong `wordmarks.js`.

Cần: Node 22, Python 3 với `fonttools`, `cairosvg`, `pillow`; Playwright (để chụp mockup).

```bash
cd _nguon
npm install
pip install fonttools cairosvg pillow
bash build.sh        # tải font nếu chưa có, dựng svg/, png/, favicon/, react/, mockup/, xem-truoc.html
```

| File | Việc |
| --- | --- |
| `symbols.js` | 26 biểu tượng trong khung 100×100, kèm CSS chuyển động |
| `wordmarks.js` | 12 wordmark "Harmony Mentor" phá cách |
| `palette.js` | bảng màu Đồng & Gỉ (sáng, tối, 1 màu, 12 màu nốt cho bản táo bạo) |
| `compose.js` | ghép logo ngang, dọc, app icon, favicon.svg |
| `meta.js` | câu chuyện, lãnh thổ, bảng điểm, Top 3 |
| `export_png.py` | PNG các cỡ, favicon.ico, apple-touch-icon |
| `gen_react.js` | Logo.tsx + logo.css cho Top 3 |
| `gen_page.js`, `shots.js` | trang xem trước và ảnh mockup |
| `sheet.js` | bảng thử nhanh 26 phác thảo (sáng, tối, 1 màu, 32px, 16px, nheo mắt) |

Sinh lại đúng hai file logo đang dùng trong app:

```bash
REPO_OUT=../../../frontend/src/components/brand node gen_react.js
```
