# Báo cáo soi lỗi frontend HarmonyMentor

- Nhánh soi: `phuc-music` @ `4245967` (16/11/2026). Nhánh sửa: `frontend-soi-loi`.
- Môi trường: cloud Linux, `uvicorn` + SQLite dev + `vite preview` (bản build production), Chromium 1.63 (Playwright), AI tắt. Không chạy Docker trên cloud (image API tải model e5 ~470 MB, không cần cho việc soi giao diện); hướng dẫn chạy Docker trên Windows ở `docs/HUONG_DAN_CHAY_WINDOWS.md`.
- Phạm vi theo trả lời của Phúc (16/11): soi đều mọi trang (1B); thiếu giờ cắt theme mới và P3 (2A); tự sửa P0/P1, P2/P3 và thay đổi diện mạo lớn thì hỏi (3A); trang chủ chỉ nâng cấp trên bố cục cũ (4A); Harmony Lab chỉ sửa lỗi giao diện (5A); không thêm thư viện (6A); được sửa chữ giao diện, Đạt đã đồng ý (7A); thêm AI Tutor và ôn thẻ, bỏ Admin (8A); tránh file luồng "Góp ý thầy T1–T6" (9A).
- Ảnh: `docs/soi-loi-frontend/truoc/` và `sau/` (12 trang × 5 cỡ × sáng/tối, deviceScaleFactor 2, JPEG 72), `luong-truoc/` và `luong-sau/` (đi luồng 2 vai, chụp khung nhìn). Số liệu thô: `*/_report.json`, `audit-truoc.json`, `audit-sau.json`.
- Ghi chú trung thực: điểm 10 góc là đánh giá của người soi, không phải số đo. Âm thanh chỉ đo được thời gian tải và lỗi console, chưa ai nghe bằng tai.

## 1. Tóm tắt

### Điểm 10 góc (0–4)

| # | Góc soi | Trước | Sau (cuối đợt 5) | Lý do chính |
|---|---|---|---|---|
| 1 | Thứ bậc thị giác & bố cục | 3 | 3 | Máy tính gọn, nhịp chữ Fraunces/Be Vietnam Pro tốt. Điện thoại: nội dung bước bắt đầu ở 256 px thay vì 455 px (FE-004); phần đầu bài vẫn chiếm khá nhiều chỗ. |
| 2 | Hệ thống thiết kế | 3 | 4 | Token nhất quán, chế độ tối là bộ token phụ (FE-014), 2 phương án nhận diện chỉ đổi token (theme/brands.css), quầng sáng trang chủ hết rgba ghi cứng. Còn 2 component bàn phím (FE-021 một phần). |
| 3 | Kiến trúc thông tin & điều hướng | 2 | 3 | Menu điện thoại một hàng, dính đầu trang (FE-009); Tổng quan hết lặp Bài 1, CTA chính lên đầu (FE-011); thanh tiến độ đo theo bước (FE-010). Tên bài còn tiếng Anh (FE-019, nội dung). |
| 4 | Trạng thái giao diện | 3 | 4 | Kết quả chấm tự hiện trong khung nhìn (FE-005); khung giữ chỗ khi chờ dữ liệu (FE-017). |
| 5 | Chuyển động & vi tương tác | 3 | 4 | Có khoảnh khắc thưởng CSS khi đúng/hoàn thành bài (FE-016), nút AI thu vào mép khi cuộn và kéo được (FE-002, FE-023); mọi thứ tắt khi reduced-motion. |
| 6 | UX âm thanh & ký hiệu | 2 | 3 | Lần phát đầu Harmony Lab 3,3 s → 0,29 s khi đã rảnh vài giây (FE-012); khuông lớn hơn (FE-013); Tone nạp khi cần (FE-015). Chưa ai nghe bằng tai; bấm Phát ngay khi mở trang vẫn phải chờ tải. |
| 7 | Responsive & cảm ứng | 2 | 4 | Không cuộn ngang 320–1920 px; header công khai một dòng ở 390 px (FE-008); nút AI không còn đè nội dung (FE-001/002/006). Kéo bằng cảm ứng thật chưa thử trên máy. |
| 8 | Accessibility WCAG 2.2 AA | 3 | 4 | axe 0 lỗi ở sáng và tối (và ở 2 phương án nhận diện); Lighthouse A11y điện thoại 100 cả 11 trang; kéo-thả có cách khác bằng phím (WCAG 2.5.7). |
| 9 | Hiệu năng | 3 | 4 | Đo lại cuối (`audit-cuoi.json`, 11 trang): Lighthouse desktop Perf 100 cả 11 trang; điện thoại 98–100, CLS ≤ 0,014 (Tổng quan 0,24 → 0). VexFlow 1129 → 723 kB. Bundle chính chưa tách (thử thì LCP/CLS xấu hơn). |
| 10 | Chất lượng code | 3 | 3 | 0 `any`, TypeScript strict; hết cảnh báo AudioContext ở 3/4 trang. Còn trùng component bàn phím; bundle chính chưa tách. |

### Top 10 việc quan trọng nhất

1. **FE-001 (đã sửa)** Nút AI đè nút "Gửi" khi mở AI Tutor trên điện thoại.
2. **FE-004 (đã sửa)** Mỗi lần "Bước tiếp" trên điện thoại phải cuộn tìm nội dung bước.
3. **FE-005 (đã sửa)** Bấm "Kiểm tra" trên điện thoại không thấy kết quả chấm.
4. **FE-006 (đã sửa)** Thanh Phát/Lưu ở Harmony Lab 390 px xuống 3 dòng, bị nút AI che.
5. **FE-003 (đã sửa)** Chữ màu đồng trên nền ngà 1,95:1 ở trang chủ.
6. **FE-007 (đã sửa)** Vòng focus không đủ tương phản trên nền tối.
7. **FE-012 (đã sửa, đợt 2)** Phát lần đầu chờ ~3–4 s; giờ tải trước mẫu âm khi trang rảnh.
8. **FE-009 (đã sửa, đợt 2)** Menu khu học trên điện thoại: 7 mục chen một hàng, không dính khi cuộn.
9. **FE-014 (đã sửa, đợt 2)** Không có chế độ tối; giờ có chế độ tối + nút sáng/tối.
10. **FE-016 (đã sửa, đợt 2)** Chưa có khoảnh khắc thưởng khi đúng câu/hoàn thành bài.

## 1b. Đợt 2 (17/11/2026): Phúc chọn FE-009, FE-012, FE-016 và làm chế độ tối có nút sáng/tối

| ID | Đã làm | Số đo / kiểm | Ảnh |
|---|---|---|---|
| FE-014 | Bộ token tối trong `index.css` dưới `:root[data-theme="dark"]` (Đồng & Gỉ sáng vẫn mặc định). Nút ☾/☀ ở header công khai và cạnh logo khu học, lưu `localStorage` (`hm-theme`), script nhỏ trong `index.html` đặt theme trước khi vẽ nên không nháy sáng. Chữ trên nút primary dùng token mới `on-primary`. Phím piano và khuông VexFlow giữ giấy sáng (`data-force-light`). Trang chủ chỉ lật phần "giấy", hero và dải tối giữ nguyên. Logo dùng sẵn bản tối của ADR-007. | Tương phản tối: chữ/nền 15,1:1, chữ phụ 7,3:1, primary trên thẻ 7,2:1, chữ trên nút 7,8:1, đỏ trên nền đỏ nhạt 7,4:1. axe sáng 0 / tối 0 nút lỗi ở 11 trang. | [Tổng quan](soi-loi-frontend/anh-loi/FE-014_sau_tong-quan.jpg), [Harmony Lab](soi-loi-frontend/anh-loi/FE-014_sau_harmony-lab.jpg), [Trang chủ 390](soi-loi-frontend/anh-loi/FE-014_sau_trang-chu-390.jpg) |
| FE-009 | Menu khu học dưới 1024 px: một dòng cuộn ngang, dính đầu màn hình (57 px), tự kéo mục đang mở vào tầm nhìn. Không làm thanh tab đáy vì đáy đã có thanh "Bước tiếp" và thanh Phát. `scroll-padding-top` để FE-004/FE-005 không bị menu che. | "Quiz kỹ năng" 3 dòng → 1 dòng. Bài học 390 px sau "Bước tiếp": nội dung bước ở y = 320 px (đợt 1: 256 px, trước khi sửa: 455 px); đổi lấy menu luôn nhìn thấy. | [FE-009_sau.jpg](soi-loi-frontend/anh-loi/FE-009_sau.jpg) |
| FE-012 | Khi trang Harmony Lab rảnh (`requestIdleCallback`), tải file nén của phong cách đang chọn vào Cache Storage, 2 luồng; bỏ qua khi bật tiết kiệm dữ liệu hoặc mạng 2G. Máy mạnh giải nén luôn; điện thoại/máy ≤ 4 GB chỉ tải, không giữ bản giải nén trong RAM. | Cloud localhost (`script/am.js`, `WAIT=8000`): bấm Phát lần đầu 3 333 ms → 290 ms. Bấm ngay khi vừa mở trang thì vẫn ~3,3 s. Phần lớn thời gian cũ là giải nén (~2,6 s), không phải tải. | (số đo) |
| FE-016 | Trả lời đúng: dấu ✓ nảy và 4 nốt nhạc bay lên rồi tan trong 760 ms; hoàn thành bài: 7 nốt. Chỉ CSS (transform/opacity, 0 byte thư viện, không gây CLS), `aria-hidden`, tắt hẳn khi giảm chuyển động, không có âm. | Vitest 277 đạt (có test biến CSS). | [Sáng](soi-loi-frontend/anh-loi/FE-016_sau.jpg), [Tối](soi-loi-frontend/anh-loi/FE-016_sau_toi.jpg) |

Lighthouse đợt 2 (`audit-dot2.json`, một lần chạy, mobile): Accessibility 100 ở cả 11 trang; Performance 89–100; LCP mobile lệch so với đợt 1 trong khoảng nhiễu giữa các lần chạy (Hồ sơ đo lần đầu 1 507 ms, chạy lại hai lần đều 1 357 ms). CLS Tổng quan vẫn 0,218 (FE-017 chưa làm). Ảnh đầy đủ 120 ảnh đợt 2 ở thư mục dự án `soi-loi-frontend/sau-dot2/`; ở đó "tối" là theme thật của app.

## 1c. Đợt 3 (17/11/2026, đêm): làm nốt các lỗi còn lại theo lệnh của Phúc

| ID | Đã làm | Số đo / kiểm | Ảnh |
|---|---|---|---|
| FE-008 | Nguyên nhân thật: nút "Đăng ký" khai báo `hidden sm:inline-flex` nhưng lớp `inline-flex` của chính `Button` đè `hidden`, nên nó vẫn hiện trên điện thoại và xuống 2 dòng. Đổi thành `max-sm:hidden`; "Đăng nhập" `whitespace-nowrap`; nút sáng/tối `size-10` ở màn nhỏ. | Header 81 → 65 px, không cuộn ngang từ 320 đến 412 px. | Đã sửa (e901f9f, b36984f), đợt 3 |
| FE-010 | Thanh trong thẻ tiến độ đo **bước đã đi** (bước 6/18 = 33%); phần trăm câu đúng vẫn hiện, ghi rõ "0% đúng". | Vitest 277 đạt. | Đã sửa (e901f9f), đợt 3 |
| FE-011 | Lời mời kiểm tra đầu vào xuống dưới nút "Bắt đầu bài học". Bài đã nằm ở thẻ "Bắt đầu học" không hiện lại ở "Bài nên học tiếp". | Ảnh bên. | Đã sửa (e901f9f), đợt 3 |
| FE-013 | Khuông trong Harmony Lab to hơn (có prop `large`). Nguyên nhân: VexFlow gắn sẵn `width:220px` vào SVG nên `w-full` không có tác dụng; nay ép `w-full!`. Chữ chú thích `text-sm`. | Khuông 220 → 384 px. | Đã sửa (e901f9f), đợt 3 |
| FE-015 | `AudioEngine` nạp Tone.js bằng `import()` ở cú bấm đầu tiên (Tone tạo AudioContext ngay khi được import). | Cảnh báo "AudioContext was not allowed to start": Học, Luyện tập, Tiến độ 2 → 0. Harmony Lab vẫn còn, vì FE-012 chuẩn bị mẫu âm trước khi bấm (vô hại, chỉ là cảnh báo). | Đã sửa một phần (e901f9f), đợt 3: hết ở Học/Luyện tập/Tiến độ, Harmony Lab còn |
| FE-017 | Thẻ "Học tiếp" luôn chừa chỗ 2 dòng tiêu đề và thanh tiến độ, nút xếp dọc ở màn nhỏ để chữ nút đổi không đổi chiều cao; chỗ thẻ kiểm tra đầu vào được giữ trước; danh sách gợi ý chờ có dữ liệu tổng quan mới vẽ. | CLS mobile Tổng quan (Lighthouse) 0,217 → 0; Performance 89 → 100. | Đã sửa (1497b6d), đợt 3 |
| FE-018 | VexFlow đổi sang `vexflow/bravura` (cùng font Bravura mặc định, bỏ các font không dùng). | `NotationStaff` 1 129 → 723 kB (gzip 692 → 390 kB). | Sửa một phần (1497b6d), đợt 3: VexFlow nhẹ đi, bundle chính giữ nguyên |
| FE-021 | **Cố ý không làm.** Gộp `Piano.tsx` (SVG, trang chủ) vào `VirtualPiano` sẽ đổi diện mạo trang chủ, trái quyết định 4A (trang chủ chỉ nâng cấp trên bố cục cũ), và không giúp người học điều gì. Giữ là nợ kỹ thuật P3. | Không làm (xem mục 1c) |

Thử và hoàn lại: tách `HomePage` thành chunk riêng (FE-018). Entry giảm 484 → 317 kB, nhưng trang chủ chậm hơn (LCP mobile +3–8%, TBT tăng, CLS 0,003 → 0,11 cho tới khi thêm fallback). Vì trang chủ là bộ mặt của sản phẩm và ràng buộc là LCP không xấu quá 10%, mình bỏ phương án này; bundle chính vẫn 484 kB.

Lighthouse đợt 3 (`audit-dot3.json`, mobile, một lần chạy; trang chủ chạy lại 3 lần cho ra 97–98, LCP 1 828–1 852 ms, bằng đợt 1): Accessibility 100 ở cả 11 trang, axe 0 nút lỗi sáng và tối, CLS ≤ 0,014 mọi trang, không cuộn ngang ở 5 cỡ. Ảnh đầy đủ ở thư mục dự án `soi-loi-frontend/sau-dot3/`.

## 1d. Đợt 4 (17/11/2026, sáng): làm nốt FE-002, FE-021 và một lỗi mới của chế độ tối

| ID | Đã làm | Kiểm chứng |
|---|---|---|
| FE-002 | Trên điện thoại (< 768 px) nút AI tròn thu vào mép phải khi đang cuộn xuống đọc bài, hiện lại khi cuộn lên, khi lên đầu trang hoặc tới cuối trang. Nhận focus bằng bàn phím thì luôn hiện đủ. Nội dung khu học có thêm khoảng trống dưới đáy (`max-md:pb-28`) để dòng cuối không bị nút che. Máy tính không đổi. Có `motion-reduce:transition-none`. | Playwright 390 px: x = 330 → 386 (thu) → 330 (cuộn lên / focus / cuối trang). [FE-002_sau_cuon-xuong.png](soi-loi-frontend/anh-loi/FE-002_sau_cuon-xuong.png) |
| FE-021 | Không gộp hai component (lý do 4A vẫn đúng: trang chủ giữ diện mạo cũ, không cần âm thanh). Thay vào đó bỏ bộ phân tích tên nốt riêng của `Piano.tsx`, dùng chung `normalizePitchClass` với `VirtualPiano`, nên hai bàn phím hiểu tên nốt giống nhau ("Bbb", "Fx", "♯"). Phần nợ kỹ thuật thật sự (hai bộ tô màu phím) còn lại, nhỏ. | Vitest 277 đạt, tsc sạch. |
| FE-022 (mới) | Do chính FE-014 gây ra: ở chế độ tối, bàn phím SVG trang chủ bị **lật ngược màu** (phím trắng tô #142723, phím đen #E7EFEA) vì nó dùng token `surface`/`ink`. Thêm `data-force-light` cho SVG, giống `VirtualPiano`. | Đo màu tô phím: trước `rgb(20,39,35)` cho phím trắng, sau `rgb(255,255,255)`. [trước](soi-loi-frontend/anh-loi/FE-021_truoc_toi.png) → [sau](soi-loi-frontend/anh-loi/FE-021_sau_toi.png) |

Đo lại (`audit-dot4.json`): axe 0 lỗi sáng và tối ở Trang chủ, Tổng quan, Học. Lighthouse điện thoại: Trang chủ 99/100 (Perf/A11y), Tổng quan 100/100 CLS 0, Học 100/100 CLS 0.

## 1e. Đợt 5 (17/11/2026, sáng): AI Tutor kéo được + việc còn sót từ đề ban đầu

| ID | Đã làm | Kiểm chứng |
|---|---|---|
| FE-023 (Phúc yêu cầu) | Nút AI tròn kéo được ở mọi cỡ màn hình (thả ra dạt vào mép trái/phải gần nhất, giữ trong màn hình kể cả khi xoay máy). Khung chat kéo được ở thanh tiêu đề từ 640 px (điện thoại khung phủ gần hết màn hình nên không kéo). Vị trí nhớ theo máy (localStorage `hm-ai-nut`, `hm-ai-khung`). Nút ↺ trong khung đưa cả hai về góc phải dưới. Bàn phím: nút ⠿ hoặc nút AI + phím mũi tên (WCAG 2.5.7). Khi nút ở mép trái, khung mở ở bên trái. Bấm ×/↺ trong thanh tiêu đề không bị nhận nhầm là kéo. `src/components/learning/useDraggable.ts`, 3 test mới cho `clampPos`. | Playwright 1440: nút 1364,824 → kéo → 12,624; khung kéo 20,428 → 420,516; 2 lần ↑ → 420,468; tải lại giữ vị trí; ↺ → 1364,824. 390: 330,700 → 12,500. [ảnh 1440](soi-loi-frontend/anh-loi/FE-023_keo-khung_1440.png), [ảnh 390](soi-loi-frontend/anh-loi/FE-023_keo-nut_390.png). Chưa thử kéo bằng ngón tay trên điện thoại thật. |
| Theme mới (đề: "1–2 phương án nhận diện dạng theme token, bật bằng 1 biến") | Hai phương án trong `src/theme/brands.css`, mỗi cái có sáng và tối: **Sân khấu** (tím đêm #17142B, primary tím #4B33B8, khi tối primary là đèn spotlight hổ phách #F2B33D) và **Giấy nhạc** (giấy kem #FBF8F1, mực khắc bản #1D1B18, bút chì đỏ #9E2A2B). Chỉ đổi màu; font, bố cục, logo giữ nguyên. Đồng & Gỉ vẫn mặc định. Bật bằng `VITE_BRAND=san-khau` (hoặc `giay-nhac`) khi build; thử nhanh bằng `?brand=san-khau` trên URL (`?brand=dong-gi` để về). | Tương phản mọi cặp chữ/nền ≥ 5,8:1 (`script/tuong-phan-theme.py`); axe 0 lỗi ở 3 phương án × sáng/tối × 5 trang (`theme/axe.json`). Ảnh so sánh (hàng trên sáng, hàng dưới tối; trái → phải: Đồng & Gỉ, Sân khấu, Giấy nhạc): [Tổng quan](soi-loi-frontend/theme/grid_tong-quan.jpg), [Trang chủ](soi-loi-frontend/theme/grid_trang-chu.jpg), [Harmony Lab](soi-loi-frontend/theme/grid_composition.jpg), [Học](soi-loi-frontend/theme/grid_hoc.jpg), [Luyện tập](soi-loi-frontend/theme/grid_luyen-tap.jpg), [Trang chủ 390](soi-loi-frontend/theme/grid_trang-chu-390.jpg). |

Đo lại cuối đợt 5 (`audit-cuoi.json`): 11 trang, axe 0 lỗi sáng và tối; Lighthouse desktop 100/100/100 (Perf/A11y/BP) cả 11 trang; điện thoại Perf 98–100, A11y 100, BP 100. Bộ ảnh "sau" cuối: 12 trang × 5 cỡ × sáng/tối = 120 ảnh ở `/mnt/project-files/soi-loi-frontend/sau-cuoi/`, 0 trang cuộn ngang; console chỉ còn 2 cảnh báo AudioContext ở Harmony Lab (FE-015 đã biết).

Logo cũ không bị xóa (đề: "không xóa logo cũ"). Bản logo Sân khấu ở mục 1f.

## 1f. Đợt 6 (17/11/2026): nhóm chọn "Sân khấu" làm nhận diện mặc định

- `VITE_BRAND` mặc định đổi thành `san-khau` (`frontend/vite.config.ts`). Đồng & Gỉ không bị xóa: build với `VITE_BRAND=dong-gi`, hoặc mở `?brand=dong-gi` một lần (trình duyệt nhớ lựa chọn trong `hm-brand`).
- Logo "Cuộn I–IV–V–I" theo màu Sân khấu: file logo sinh tự động (ADR-007) không sửa; `brands.css` đổi biến `--hm-logo-*` (ô nền tím đêm #17142B, bản tối có viền spotlight #F2B33D). Màu các lỗ giữ nguyên vì mỗi lỗ là một nốt (luật số 2 của BRAND_NOTE). Bản đầu tiên của đợt 6 có đổi 2 màu lỗ; đã hoàn lại khi viết ADR-026. [So sánh logo](soi-loi-frontend/theme/logo-dong-gi-vs-san-khau.png) (trái Đồng & Gỉ, phải Sân khấu; trên: header sáng, giữa: header tối, dưới: thanh bên khu học).
- `favicon-san-khau.svg`, `theme-color` #17142B, `site.webmanifest` theo Sân khấu. Nút "Bật âm thanh" trang chủ hết `rgba` ghi cứng.
- Ảnh mặc định mới: [Tổng quan](soi-loi-frontend/theme/mac-dinh_tong-quan.jpg), [Trang chủ](soi-loi-frontend/theme/mac-dinh_trang-chu.jpg). Đo lại 11 trang với Sân khấu mặc định (`audit-san-khau.json`): axe 0 lỗi sáng và tối; Lighthouse desktop 100/100/100 cả 11 trang, điện thoại Perf 98–100, A11y 100, BP 100. 120 ảnh (12 trang × 5 cỡ × sáng/tối) ở `/mnt/project-files/soi-loi-frontend/sau-san-khau/`, 0 trang cuộn ngang; console chỉ còn cảnh báo AudioContext ở Harmony Lab (đã biết).

**Ghi chính thức:** `docs/decisions/ADR-026-nhan-dien-san-khau.md`; `docs/thuong-hieu/BRAND_NOTE.md` thêm mục 3b. Ảnh trong slide/báo cáo cũ (màu xanh Đồng & Gỉ) sẽ khác app.

## 2. Mẫu tham chiếu

Từ cloud, trình duyệt Playwright bị proxy chặn mọi site ngoài (`ERR_TUNNEL_CONNECTION_FAILED`), nên các link dưới được mở qua Firecrawl (HTTP 200, đọc văn bản/tóm tắt), **không xem ảnh trực tiếp**. Phần "học được gì" về chữ/màu/chuyển động là hiểu biết sẵn có của người soi về các sản phẩm này, chưa đối chiếu ảnh chụp mới: coi là phỏng đoán có cơ sở.

| # | Mẫu | Link (đã mở được) | Học được gì cho HarmonyMentor |
|---|---|---|---|
| R1 | Ableton Learning Music | https://learningmusic.ableton.com/ | Dạy bằng "hộp nhạc" bấm được ngay, không cần tài khoản; mỗi khái niệm một màn, nút đi tiếp rõ. Áp vào FE-004: nội dung bước phải chiếm màn hình, không phải khung bài. |
| R2 | Chrome Music Lab | https://musiclab.chromeexperiments.com/ | Dùng Web Audio + Tone.js giống ta; thử nghiệm tối giản, mở là chơi được. Gợi ý cho FE-012 (âm thanh sẵn sàng trước khi người dùng bấm). |
| R3 | Duolingo | https://www.duolingo.com/ | Bài ngắn, phản hồi đúng/sai ngay trong khung nhìn ở đáy màn hình, khoảnh khắc thưởng. Áp vào FE-005, FE-016. |
| R4 | Yousician | https://yousician.com/ | Phản hồi tức thì khi chơi, theo dõi tiến độ. Áp vào FE-010 (tách "tiến độ bước" và "câu đúng"). |
| R5 | Awwwards: New York's New Maestro (Honorable Mention 03/10/2026) | https://www.awwwards.com/sites/new-yorks-new-maestro | Scroll trigger mở màn, "chapter menu" cho trang kể chuyện dài. Gợi ý nâng trang chủ: chỉ mục chương nhỏ cạnh các cảnh pin (không đổi bố cục, 4A). |
| R6 | Awwwards: Music & Sound | https://www.awwwards.com/websites/music-sound/ | Danh mục SOTD nhạc, dùng để chọn R5 và đối chiếu nhịp cuộn ngang (trang chủ đã có cảnh vòng hợp âm cuộn ngang tương tự). |
| R7 | Dribbble: music learning app | https://dribbble.com/search/music-learning-app | Mở được trang tìm kiếm, nhưng danh sách shot tải bằng JS nên chỉ đọc được tóm tắt. Không dùng làm căn cứ cụ thể. |
| R8 | Mobbin explore | https://mobbin.com/explore | Trang khám phá mở được; xem màn hình chi tiết cần đăng nhập → **không truy cập được** phần cần dùng. |
| R9 | MotionSites | https://motionsites.ai/ | Thư viện prompt/template chuyển động; không có mẫu học nhạc cụ thể, không dùng làm căn cứ. |

Webflow Made-in-Webflow (https://webflow.com/made-in-webflow/ux-ui) chưa mở thử qua Firecrawl, không dùng.

## 3. Số đo trước/sau

Lighthouse 12.2.1 (desktop preset và mobile mặc định có throttle mô phỏng), axe-core 4.10.2 (wcag2a/aa, wcag21a/aa, wcag22aa, best-practice), cùng máy cloud, localhost. Trang Đăng nhập/Đăng ký khi đã đăng nhập tự chuyển về `/app`, nên số của chúng thực chất là của Tổng quan (ghi chú để không hiểu nhầm).

| Trang | Perf desktop | Perf mobile | A11y desktop | LCP mobile (ms) | CLS mobile | TBT mobile (ms) | axe sáng/tối (số nút lỗi) |
|---|---|---|---|---|---|---|---|
| trang-chu | 100 → 100 | 94 → 98 | 96 → 100 | 1875 → 1828 | 0.004 → 0.004 | 248 → 145 | 2/2 → 0/0 |
| dang-nhap | 100 → 100 | 100 → 100 | 100 → 100 | 1284 → 1208 | 0 → 0 | 0 → 0 | 0/0 → 0/0 |
| dang-ky | 100 → 100 | 100 → 100 | 100 → 100 | 1204 → 1207 | 0.013 → 0.016 | 1 → 0 | 0/0 → 0/0 |
| tong-quan | 97 → 94 | 90 → 90 | 100 → 100 | 1528 → 1522 | 0.214 → 0.214 | 0 → 0 | 0/0 → 0/0 |
| hoc | 100 → 100 | 98 → 94 | 100 → 100 | 1360 → 1361 | 0 → 0 | 161 → 293 | 0/0 → 0/0 |
| luyen-tap | 100 → 100 | 100 → 100 | 100 → 100 | 1540 → 1386 | 0 → 0 | 2 → 0 | 0/0 → 0/0 |
| quiz | 100 → 100 | 100 → 100 | 100 → 100 | 1510 → 1510 | 0 → 0 | 0 → 0 | 0/0 → 0/0 |
| tien-do | 100 → 100 | 97 → 98 | 100 → 100 | 1507 → 1405 | 0 → 0 | 206 → 173 | 0/0 → 0/0 |
| composition | 100 → 100 | 96 → 96 | 100 → 100 | 1679 → 1679 | 0 → 0 | 213 → 211 | 0/0 → 0/0 |
| ho-so | 100 → 100 | 100 → 100 | 100 → 100 | 1356 → 1355 | 0 → 0 | 0 → 0 | 0/0 → 0/0 |
| kiem-tra-dau-vao | 100 → 100 | 100 → 100 | 100 → 100 | 1509 → 1509 | 0 → 0 | 0 → 0 | 0/0 → 0/0 |

Bản "trước" là `4245967` build lại phục vụ ở cổng 4174, bản "sau" là `frontend-soi-loi` ở cổng 4173, đo cùng lúc trên cùng máy (16/11/2026). Mỗi ô là **một lần chạy**: TBT/Perf mobile dao động ±100 ms/±4 điểm giữa các lần chạy (vd Học 98 → 94 không do code đổi, file đổi ở trang đó chỉ là CSS/scroll). Không trang nào có cuộn ngang ở 5 cỡ (`chup-truoc.json`, `chup-sau.json`, trường `hscroll`).

Đo riêng FE-004 (`script/chk4.js`, 390 × 844, sau 8 lần "Bước tiếp"): mép trên nội dung bước y = 455 px → 256 px.


## 4. Bảng lỗi (sắp theo mức)

Cột "Ảnh" trỏ tới file trong `docs/soi-loi-frontend/`. "Đã sửa" ghi mã commit trên `frontend-soi-loi`.

| ID | Mức | Góc | Vai | Trang + thành phần | file:dòng | Ảnh | Vì sao sai | Cách sửa | Công | Trạng thái |
|---|---|---|---|---|---|---|---|---|---|---|
| FE-001 | P1 | 7, 8 | 1 | Khung AI Tutor, điện thoại 390 px | frontend/src/components/learning/FloatingTutorDrawer.tsx:164, :201 | [FE-001_truoc.jpg](soi-loi-frontend/anh-loi/FE-001_truoc.jpg) → [FE-001_sau.jpg](soi-loi-frontend/anh-loi/FE-001_sau.jpg) | Nút tròn `bottom-24 right-4` (z-40) nằm đè đúng chỗ nút **Gửi** của khung chat `bottom-20`; trên cảm ứng không bấm được Gửi. Nút × đóng khung chỉ ~28×28 px. WCAG 2.5.8 (vùng bấm), nguyên tắc không che điều khiển chính. Duolingo (R3) đặt hành động chính ở đáy, không có phần tử nổi đè. | Ẩn nút tròn khi khung mở (`${open ? "hidden" : "flex"}`), khung điện thoại `bottom-2 max-h-[85vh] z-50`, nút × `size-11`. | S | Đã sửa (6fc9e12) |
| FE-002 | P1 | 7 | 1 | Nút AI nổi ở mọi trang khu học, 390 px | FloatingTutorDrawer.tsx:201 | [FE-002_truoc.jpg](soi-loi-frontend/anh-loi/FE-002_truoc.jpg) → [FE-002_sau.jpg](soi-loi-frontend/anh-loi/FE-002_sau.jpg) | Nút 56 px đè lên chữ bài học, đáp án trắc nghiệm, phím piano. Không có cách thu gọn. | Nút còn 48 px, viền `ring-bg`; đợt 4: thu vào mép khi cuộn xuống trên điện thoại, chừa khoảng trống đáy trang. | S | Đã sửa (6fc9e12 + đợt 4) |
| FE-003 | P1 | 8 | 1, 2 | Trang chủ, tiêu đề "Bấm một hợp âm, *nghe* và *thấy* nó." | frontend/src/pages/public/wow/wow.css:30 | [FE-003_truoc.jpg](soi-loi-frontend/anh-loi/FE-003_truoc.jpg) → [FE-003_sau.jpg](soi-loi-frontend/anh-loi/FE-003_sau.jpg) | axe `color-contrast` serious: #E0A53E trên #F2F3EA = 1,95:1; chữ lớn cần ≥ 3:1 (WCAG 1.4.3). Lighthouse A11y 96. | Biến `--w-brass-deep: #9a6400` (4,48:1) cho `.display em` ở section nền sáng; hero/dải tối giữ đồng sáng. | S | Đã sửa (2d477bf). axe 2 → 0, Lighthouse A11y 96 → 100 |
| FE-004 | P1 | 1, 3, 7 | 1 | Bài học "Từng bước", 390 px | frontend/src/components/learning/LessonRunner.tsx:282–298, :326–331 | [FE-004_truoc.jpg](soi-loi-frontend/anh-loi/FE-004_truoc.jpg) → [FE-004_sau.jpg](soi-loi-frontend/anh-loi/FE-004_sau.jpg) | Bấm "Bước tiếp" cuộn về đầu `<section>`: nút quay lại + tiêu đề 2 dòng + thẻ tiến độ 3 hàng + nút chế độ + mục lục. Đo sau 8 lần bấm: nội dung bước bắt đầu ở y = 455 px trên màn 844 px (còn ~319 px nhìn được trên thanh đáy). Ableton Learning Music (R1): mỗi màn dành cho nội dung. | Điện thoại (< 640 px) cuộn tới thẻ tiến độ (`progressRef`, `scroll-mt-3`); thẻ tiến độ 2 hàng (`grid-cols-[1fr_auto]`, thanh `col-span-2`). Máy tính giữ hành vi cũ. Sau: nội dung bắt đầu ở y = 256 px (+62% chỗ cho nội dung). | S | Đã sửa (56a876a) |
| FE-005 | P1 | 4, 7 | 1 | Kết quả chấm (Luyện tập, câu kiểm tra trong bài, Quiz) | frontend/src/components/ui/Page.tsx:86 | [FE-005_truoc.jpg](soi-loi-frontend/anh-loi/FE-005_truoc.jpg) → [FE-005_sau.jpg](soi-loi-frontend/anh-loi/FE-005_sau.jpg) | Ở 390 px, bấm "Kiểm tra" xong ô "✗ Chưa đúng" hiện dưới mép màn hình hoặc sau thanh nút dính đáy: người học tưởng nút không chạy. Duolingo (R3) hiện phản hồi ngay trong khung nhìn. | `ResultBox` tự `scrollIntoView({block:"nearest"})` khi hiện/đổi đúng-sai, `scroll-mb-28` chừa thanh đáy, tôn trọng reduced-motion. Một chỗ sửa áp cho 14 nơi dùng. | S | Đã sửa (b90f3ed) |
| FE-006 | P1 | 7 | 1, 2 | Harmony Lab, thanh Phát/Tạo bản khác/Lưu, 390 px | frontend/src/pages/app/CompositionLabPage.tsx:46, :384–395 | [FE-006_truoc.jpg](soi-loi-frontend/anh-loi/FE-006_truoc.jpg) → [FE-006_sau.jpg](soi-loi-frontend/anh-loi/FE-006_sau.jpg) | Ba nút `size=lg` chia đều 390 px: "Tạo bản khác" xuống 3 dòng, "Lưu vòng này" 2 dòng, thanh cao ~100 px và nút AI đè lên nút Lưu. | Điện thoại: `whitespace-nowrap max-sm:!px-2 max-sm:!text-sm`, ẩn 🎲, thanh `pr-[4.25rem]` chừa nút AI. Chữ nút giữ nguyên. | S | Đã sửa (9c3ae6e) |
| FE-007 | P1 | 8 | 1, 2 | Vòng focus bàn phím trên nền tối (thanh bên khu học, hero/dải tối trang chủ) | frontend/src/index.css:61–69; AppLayout.tsx:51; wow.css:35 | [FE-007_truoc.jpg](soi-loi-frontend/anh-loi/FE-007_truoc.jpg) → [FE-007_sau.jpg](soi-loi-frontend/anh-loi/FE-007_sau.jpg) | Outline #006D61 trên #081613 = 2,96:1, trên #0C231F = 2,63:1; WCAG 1.4.11 (non-text contrast) cần ≥ 3:1. | `[data-surface="dark"] :focus-visible { outline-signature }` (8,42:1) và verdigris trong các section tối của trang chủ. | S | Đã sửa (2d477bf, 9de3baa) |
| FE-008 | P2 | 7 | 1 | Header trang công khai, 390 px | frontend/src/components/layout/PublicLayout.tsx:25–26 | [FE-008_hien-trang.jpg](soi-loi-frontend/anh-loi/FE-008_hien-trang.jpg) | "Đăng nhập" và "Đăng ký" xuống 2 dòng ở màn đầu tiên người mới thấy; trông vỡ. | Thêm `whitespace-nowrap` cho 2 link, giảm `px` ở `<sm`; hoặc thu "Harmony Mentor" thành logo biểu tượng ở `<sm`. | S | Đã sửa (e901f9f, b36984f), đợt 3 |
| FE-009 | P2 | 3, 7 | 1 | Menu khu học, 390 px | frontend/src/components/layout/AppLayout.tsx:57 | [FE-009_hien-trang.jpg](soi-loi-frontend/anh-loi/FE-009_hien-trang.jpg) | 7 mục `grid-flow-col auto-cols-fr` trong 390 px: "Quiz kỹ năng" 3 dòng; menu không dính khi cuộn nên ở cuối trang dài phải cuộn lên. | Thanh tab dính đáy 5 mục (Tổng quan, Học, Luyện tập, Sáng tác, Thêm ▸ Quiz/Tiến độ/Hồ sơ), hoặc tối thiểu `overflow-x-auto whitespace-nowrap`. Đổi điều hướng = diện mạo lớn. | M | Đã sửa (0126881), đợt 2 |
| FE-010 | P2 | 3 | 1 | Thẻ tiến độ trong bài | LessonRunner.tsx:326–331 | [FE-010_hien-trang.jpg](soi-loi-frontend/anh-loi/FE-010_hien-trang.jpg) | "Bước 6/18" đứng cạnh thanh 0% (thanh đo % câu đúng, không phải % bước) → người mới hiểu là "chưa tiến bộ". Yousician (R4) tách tiến độ và kết quả. | Thêm thanh mỏng tiến độ bước (6/18) hoặc đổi nhãn "0% câu đúng". Đổi chữ giao diện → kèm danh sách cho Đạt. | S | Đã sửa (e901f9f), đợt 3 |
| FE-011 | P3 | 3 | 1 | Tổng quan | frontend/src/pages/Dashboard.tsx:38, :50 | [FE-011_hien-trang.jpg](soi-loi-frontend/anh-loi/FE-011_hien-trang.jpg) | Người mới thấy "Bài 1" hai lần (thẻ Bắt đầu học + Gợi ý cho bạn) và lời mời kiểm tra đầu vào nằm trên CTA chính. | Ẩn mục "Bài nên học tiếp" khi trùng bài ở thẻ Bắt đầu học; đưa lời mời kiểm tra đầu vào xuống dưới CTA. | S | Đã sửa (e901f9f), đợt 3 |
| FE-012 | P2 | 6 | 1, 2 | Harmony Lab, bấm Phát lần đầu | frontend/src/audio/band/samples.ts | (số đo, không ảnh) | Đo trên cloud, localhost, không throttle: 4 141 ms từ bấm Phát tới khi hết "Đang tải nhạc cụ"; tải 221 file mẫu, 9 768 KB. Mạng 4G sẽ lâu hơn nhiều (phỏng đoán, chưa đo). Chrome Music Lab (R2) phát được ngay. | Tải trước nhóm mẫu của phong cách mặc định bằng `requestIdleCallback` khi mở trang; phát piano synth ngay rồi chuyển sang mẫu khi xong. | M | Đã sửa (d0b2c26), đợt 2 |
| FE-013 | P2 | 6 | 2 | Harmony Lab, khuông "Đang chọn C", 1440 px | frontend/src/components/music/NotationStaff.tsx | [FE-013_hien-trang.jpg](soi-loi-frontend/anh-loi/FE-013_hien-trang.jpg) | Khuông VexFlow chỉ ~190 px rộng trong khung 420 px; chữ "C: C – E – G" ~11 px. | Cho `NotationStaff` co theo khung (`width = container`), cỡ chữ chú thích ≥ 14 px. | S | Đã sửa (e901f9f), đợt 3 |
| FE-014 | P2 | 2, 8 | 1, 2 | Toàn app: chế độ tối | frontend/src/index.css | [FE-014_hien-trang.jpg](soi-loi-frontend/anh-loi/FE-014_hien-trang.jpg) | 0 biến thể `dark:`, 1 chỗ `prefers-color-scheme`; ảnh sáng và tối giống hệt ở 12 trang × 5 cỡ. Yêu cầu soi sáng/tối không thực hiện được vì app chỉ có một chế độ. | Thêm bộ token tối trong `@theme` dưới `@media (prefers-color-scheme: dark)` + công tắc; cần Phúc duyệt hướng màu (gộp với việc theme mới). | L | Đã sửa (bc027a5), đợt 2 |
| FE-015 | P2 | 6, 10 | 1, 2 | Học, Luyện tập, Tiến độ, Harmony Lab | frontend/src/audio/AudioEngine.ts:1; audio/band/*.ts | (console) | Console warning "The AudioContext was not allowed to start" ở 4 trang ngay khi mở: `import * as Tone` tạo AudioContext trước cú bấm. Không gây lỗi nhưng sinh cảnh báo và tốn tài nguyên. | Chỉ `import("tone")` động trong hàm phát (như trang chủ đã làm ở `wow/sound.tsx`). | M | Đã sửa một phần (e901f9f), đợt 3: hết ở Học/Luyện tập/Tiến độ, Harmony Lab còn |
| FE-016 | P2 | 5 | 1 | Câu đúng / hoàn thành bài | Page.tsx `ResultBox`; LessonRunner.tsx:259 | [FE-005_sau.jpg](soi-loi-frontend/anh-loi/FE-005_sau.jpg) | Đúng câu hay hoàn thành bài chỉ hiện ô xanh tĩnh. Prompt yêu cầu dồn wow vào khoảnh khắc thưởng; Duolingo (R3) dùng chuyển động + âm ngắn. | Hiệu ứng GSAP nhẹ (nốt nhạc bay lên 600 ms) khi `correct`, tắt khi reduced-motion; âm thưởng mặc định tắt. | M | Đã sửa (979d606), đợt 2 |
| FE-017 | P2 | 9 | 1 | Tổng quan, Lighthouse mobile | frontend/src/pages/Dashboard.tsx; components/learning/RecommendedLessons.tsx | (số đo) | CLS 0,214 (mức "cần cải thiện" 0,1–0,25): các thẻ hiện dần khi API trả về và đẩy nội dung xuống. | Skeleton có chiều cao cố định cho thẻ Bắt đầu học/Gợi ý/4 chỉ số. | S | Đã sửa (1497b6d), đợt 3 |
| FE-018 | P2 | 9 | 1, 2 | Bundle | frontend/src/App.tsx:6; vite build | (số đo) | `index.js` 482 kB (163 kB gzip) gồm GSAP + Lenis + trang chủ, tải cả khi vào thẳng `/app`; `NotationStaff` 1 123 kB (692 kB gzip) do VexFlow kèm font. | Tách `HomePage` thành chunk riêng cho route `/app`; dùng bản `vexflow/bravura` thay bản đủ font. | M | Sửa một phần (1497b6d), đợt 3: VexFlow nhẹ đi, bundle chính giữ nguyên |
| FE-019 | P3 | 3 | 1 | Danh sách bài, Quiz kỹ năng | dữ liệu bài từ API | [FE-019_hien-trang.jpg](soi-loi-frontend/anh-loi/FE-019_hien-trang.jpg) | Tên bài/kỹ năng còn tiếng Anh ("Secondary Dominants", "Modal Interchange…", "enharmonic spelling"). Là nội dung, không phải chữ giao diện. | Chuyển Đạt quyết; frontend không sửa. | — | Không thuộc frontend |
| FE-020 | — | — | 1 | AI Tutor khi AI tắt | backend (route dự phòng) | [FE-020_hien-trang.jpg](soi-loi-frontend/anh-loi/FE-020_hien-trang.jpg) | Hỏi "Hợp âm C gồm những nốt nào?" ở Bài 1 thì câu trả lời dự phòng trích bài L07 (Jazz tensions). Nốt C E G đúng nhưng trích dẫn lạc bài. | Chuyển luồng T1–T6 (đang sửa định tuyến AI). | — | Ngoài phạm vi |
| FE-021 | P3 | 2, 10 | — | Bàn phím piano | frontend/src/Piano.tsx; components/music/VirtualPiano.tsx | — | Hai component bàn phím khác kiểu (trang chủ dùng `Piano.tsx` SVG, khu học dùng `VirtualPiano`). | Dùng chung bộ đọc tên nốt; giữ SVG riêng cho trang chủ (4A). | S | Sửa một phần, đợt 4 (xem mục 1d) |

## 5. Chưa sửa và vì sao

- FE-021 (hai bàn phím piano): không gộp component, chỉ dùng chung bộ đọc tên nốt (mục 1d). FE-018: bundle chính 484 kB giữ nguyên, tách trang chủ đã thử và hoàn lại.
- Theme mới: đã làm ở đợt 5 (mục 1e); nhóm chọn Sân khấu, đợt 6 đặt làm mặc định và làm logo theo màu (mục 1f).
- FE-019 (tên bài/kỹ năng tiếng Anh) là nội dung bài, thuộc Đạt. FE-020 là backend AI, thuộc luồng T1–T6.
- FE-012 chỉ giúp khi người dùng ở trang vài giây trước khi bấm Phát; muốn nhanh hơn nữa cần gộp/nén mẫu phía máy chủ (Thắng).
- Âm thanh chưa ai nghe bằng tai.

## 6. Việc cho từng thành viên

- **Phúc:** chạy `docs/HUONG_DAN_CHAY_WINDOWS.md` mục 4 trên điện thoại thật hoặc DevTools 390 px (có thêm dòng FE-009/012/014/016); nghe Harmony Lab và trang chủ; xem chế độ tối có hợp mắt không.
- **Thắng:** xem FE-020 (route dự phòng AI Tutor) cùng luồng T1–T6; FE-012 nếu muốn tải trước mẫu âm từ phía máy chủ (nén/gộp file).
- **Đạt:** kiểm danh sách chữ giao diện ở mục 7 (đợt này chỉ đổi nhãn nút đóng thành vùng bấm lớn hơn, không đổi chữ); xem FE-019 (tên bài/kỹ năng còn tiếng Anh: "Secondary Dominants", "enharmonic spelling") vì đó là nội dung bài, không thuộc quyền sửa của frontend.

## 7. Chữ giao diện đã đổi (để Đạt kiểm)

Đợt 1 **không đổi câu chữ nào** hiển thị cho người học. Thay đổi duy nhất liên quan chữ: biểu tượng 🎲 trên nút "Tạo bản khác" bị ẩn ở màn hình < 640 px (FE-006); chữ nút giữ nguyên.

Đợt 2 thêm chữ mới cho nút sáng/tối (FE-014), chỉ đọc bằng trình đọc màn hình hoặc khi rê chuột:

| Chỗ | Chữ |
|---|---|
| Nhãn đọc màn hình, đang sáng | "Đang dùng giao diện sáng. Bấm để chuyển sang tối" |
| Nhãn đọc màn hình, đang tối | "Đang dùng giao diện tối. Bấm để chuyển sang sáng" |
| Chú thích khi rê chuột | "Chuyển sang giao diện tối" / "Chuyển sang giao diện sáng" |

Đợt 3 đổi chữ ở hai chỗ (Đạt duyệt rồi, 7A):

| Chỗ | Trước | Sau |
|---|---|---|
| Thẻ tiến độ trong bài | "0%" | "0% đúng" |
| Tổng quan, mục "Bài nên học tiếp" khi bài gợi ý đã nằm ở thẻ "Bắt đầu học" | (hiện lại bài đó) | "Bài gợi ý nằm ở thẻ "Bắt đầu học" phía trên. Học xong bài đó, mình sẽ gợi ý bài kế tiếp." |

Đợt 5 thêm chữ ở AI Tutor (FE-023):

| Chỗ | Chữ mới |
|---|---|
| Rê chuột lên nút AI tròn | "Bấm để hỏi AI Tutor. Kéo để đổi chỗ (hoặc phím mũi tên)." |
| Nút ⠿ đầu khung chat (máy tính) | aria-label "Di chuyển khung AI Tutor bằng phím mũi tên"; rê chuột: "Kéo thanh này để di chuyển khung; hoặc bấm vào đây rồi dùng phím mũi tên" |
| Nút ↺ (chỉ hiện khi đã kéo) | aria-label "Đưa AI Tutor về góc phải dưới"; rê chuột: "Đưa về góc phải dưới" |

## 8. Lệnh đã chạy

Chạy 16/11/2026 trên cloud:

```
cd frontend && npx tsc -b                 # không lỗi
npm test                                  # Test Files 14 passed (14), Tests 277 passed (277)
npm run build                             # ✓ built in 5.49s (cảnh báo chunk > 500 kB có sẵn từ trước, xem FE-018)
cd backend && python -m pytest -q         # 1317 passed, 44 skipped (44 test PostgreSQL cần TEST_DATABASE_URL); nhánh không đổi backend
git merge-tree --write-tree HEAD origin/gop-y-thay/g8-cham-nhac-ly   # merge sạch, không xung đột
node docs/soi-loi-frontend/script/shoot.js <thư mục>                 # 120 ảnh/lượt
node docs/soi-loi-frontend/script/flow.js <thư mục> vai1|vai2         # luồng 2 vai
BASE=… PORT=… node docs/soi-loi-frontend/script/audit.mjs <thư mục>   # Lighthouse 12.2.1 + axe-core 4.10.2
```

Script đang trỏ tới đường dẫn công cụ trên máy cloud (`/tmp/claude-0/tools`); chạy trên máy khác thì sửa dòng `import` đầu file.

Ảnh đầy đủ 2 × 120 ảnh (58 MB) không đưa vào git, nằm ở thư mục dự án `soi-loi-frontend/truoc/` và `soi-loi-frontend/sau/`. Trong repo chỉ giữ ảnh luồng (thu nhỏ còn rộng tối đa 1440 px) và ảnh từng lỗi.

## 9. Chỗ trùng với luồng "Góp ý thầy T1–T6"

Các nhánh `gop-y-thay/g1…g8` sửa `api.ts`, `AiDraftTab.tsx`, `FloatingTutorDrawer.tsx` (dòng 121–128: mã lỗi `AI_RATE_LIMITED`), `KeyedProgression.tsx`, `LessonRunner.tsx` (import và khối `progression`/`audio` dòng ~398–500), `progressionText.ts`. Nhánh này có sửa `FloatingTutorDrawer.tsx` (dòng ~163–205, nút đóng và nút tròn) và `LessonRunner.tsx` (hàm `goTo` và thẻ tiến độ, dòng ~152–330). Các đoạn không chồng nhau; đã thử `git merge-tree` với `gop-y-thay/g8-cham-nhac-ly`, kết quả ghi ở mục 8.
