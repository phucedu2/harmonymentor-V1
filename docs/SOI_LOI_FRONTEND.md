# Báo cáo soi lỗi frontend HarmonyMentor

- Nhánh soi: `phuc-music` @ `4245967` (16/11/2026). Nhánh sửa: `frontend-soi-loi`.
- Môi trường: cloud Linux, `uvicorn` + SQLite dev + `vite preview` (bản build production), Chromium 1.63 (Playwright), AI tắt. Không chạy Docker trên cloud (image API tải model e5 ~470 MB, không cần cho việc soi giao diện); hướng dẫn chạy Docker trên Windows ở `docs/HUONG_DAN_CHAY_WINDOWS.md`.
- Phạm vi theo trả lời của Phúc (16/11): soi đều mọi trang (1B); thiếu giờ cắt theme mới và P3 (2A); tự sửa P0/P1, P2/P3 và thay đổi diện mạo lớn thì hỏi (3A); trang chủ chỉ nâng cấp trên bố cục cũ (4A); Harmony Lab chỉ sửa lỗi giao diện (5A); không thêm thư viện (6A); được sửa chữ giao diện, Đạt đã đồng ý (7A); thêm AI Tutor và ôn thẻ, bỏ Admin (8A); tránh file luồng "Góp ý thầy T1–T6" (9A).
- Ảnh: `docs/soi-loi-frontend/truoc/` và `sau/` (12 trang × 5 cỡ × sáng/tối, deviceScaleFactor 2, JPEG 72), `luong-truoc/` và `luong-sau/` (đi luồng 2 vai, chụp khung nhìn). Số liệu thô: `*/_report.json`, `audit-truoc.json`, `audit-sau.json`.
- Ghi chú trung thực: điểm 10 góc là đánh giá của người soi, không phải số đo. Âm thanh chỉ đo được thời gian tải và lỗi console, chưa ai nghe bằng tai.

## 1. Tóm tắt

### Điểm 10 góc (0–4)

| # | Góc soi | Trước | Sau | Lý do chính |
|---|---|---|---|---|
| 1 | Thứ bậc thị giác & bố cục | 3 | 3 | Máy tính gọn, nhịp chữ Fraunces/Be Vietnam Pro tốt. Điện thoại: phần đầu bài học chiếm ~55% màn hình (đã giảm, chưa đổi bố cục). |
| 2 | Hệ thống thiết kế | 3 | 3 | Token `@theme` dùng nhất quán, 0 `any`. Trang chủ có bảng `--w-*` riêng trùng token; 2 component bàn phím (`Piano.tsx`, `VirtualPiano.tsx`). |
| 3 | Kiến trúc thông tin & điều hướng | 2 | 2 | Thanh menu điện thoại 7 mục chen một hàng; Bài 1 xuất hiện 2 lần ở Tổng quan; thanh % cạnh "Bước x/18" dễ hiểu nhầm là tiến độ bước. Chưa sửa (P2). |
| 4 | Trạng thái giao diện | 3 | 4 | Có loading/rỗng/lỗi/disabled. Trước: kết quả chấm rơi khỏi màn hình điện thoại (đã sửa FE-005). |
| 5 | Chuyển động & vi tương tác | 3 | 3 | Trang chủ có scroll storytelling GSAP + Lenis, tôn trọng reduced-motion. Khu học gần như tĩnh, chưa có khoảnh khắc thưởng khi đúng/hoàn thành bài (P2, cần duyệt diện mạo). |
| 6 | UX âm thanh & ký hiệu | 2 | 2 | Bấm Phát lần đầu ở Harmony Lab chờ 4,1 s (221 mẫu, 9,5 MB, localhost); AudioContext tạo trước cú bấm; khuông VexFlow trong Harmony Lab nhỏ; chunk VexFlow 1,12 MB. Chưa sửa (P2). |
| 7 | Responsive & cảm ứng | 2 | 3 | Không cuộn ngang ở cả 5 cỡ. Trước: nút AI đè nút Gửi, thanh Harmony Lab xuống 3 dòng (đã sửa). Còn header công khai và menu khu học xuống dòng ở 390 px. |
| 8 | Accessibility WCAG 2.2 AA | 3 | 4 | axe trước: 1 lỗi (tương phản 1,95:1), sau: 0. Vòng focus trên nền tối 2,96:1 → 8,4:1. Không có chế độ tối. |
| 9 | Hiệu năng | 3 | 3 | Lighthouse desktop 97–100; mobile 82–100. CLS mobile Tổng quan 0,24. Bundle chính 482 kB (GSAP/Lenis/trang chủ nằm chung). |
| 10 | Chất lượng code | 3 | 3 | 0 `any`, 2 `console.*`, TypeScript strict qua `tsc -b`. Trùng component bàn phím. |

### Top 10 việc quan trọng nhất

1. **FE-001 (đã sửa)** Nút AI đè nút "Gửi" khi mở AI Tutor trên điện thoại.
2. **FE-004 (đã sửa)** Mỗi lần "Bước tiếp" trên điện thoại phải cuộn tìm nội dung bước.
3. **FE-005 (đã sửa)** Bấm "Kiểm tra" trên điện thoại không thấy kết quả chấm.
4. **FE-006 (đã sửa)** Thanh Phát/Lưu ở Harmony Lab 390 px xuống 3 dòng, bị nút AI che.
5. **FE-003 (đã sửa)** Chữ màu đồng trên nền ngà 1,95:1 ở trang chủ.
6. **FE-007 (đã sửa)** Vòng focus không đủ tương phản trên nền tối.
7. **FE-012 (chưa sửa, P2)** Phát lần đầu chờ ~4 s, không báo trước; nên tải trước mẫu âm khi rảnh.
8. **FE-009 (chưa sửa, P2)** Menu khu học trên điện thoại: 7 mục chen một hàng, không dính khi cuộn.
9. **FE-014 (chưa sửa, P2)** Không có chế độ tối dù yêu cầu soi sáng/tối; cần Phúc quyết hướng theme.
10. **FE-016 (chưa sửa, P2)** Chưa có khoảnh khắc thưởng khi đúng câu/hoàn thành bài.

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
| FE-002 | P1 | 7 | 1 | Nút AI nổi ở mọi trang khu học, 390 px | FloatingTutorDrawer.tsx:201 | [FE-002_truoc.jpg](soi-loi-frontend/anh-loi/FE-002_truoc.jpg) → [FE-002_sau.jpg](soi-loi-frontend/anh-loi/FE-002_sau.jpg) | Nút 56 px đè lên chữ bài học, đáp án trắc nghiệm, phím piano. Không có cách thu gọn. | Nút còn 48 px, viền `ring-bg` để tách khỏi nội dung. Hết đè hoàn toàn cần chuyển AI vào thanh bước dưới đáy (đổi bố cục, P2: hỏi Phúc). | S | Sửa một phần (6fc9e12) |
| FE-003 | P1 | 8 | 1, 2 | Trang chủ, tiêu đề "Bấm một hợp âm, *nghe* và *thấy* nó." | frontend/src/pages/public/wow/wow.css:30 | [FE-003_truoc.jpg](soi-loi-frontend/anh-loi/FE-003_truoc.jpg) → [FE-003_sau.jpg](soi-loi-frontend/anh-loi/FE-003_sau.jpg) | axe `color-contrast` serious: #E0A53E trên #F2F3EA = 1,95:1; chữ lớn cần ≥ 3:1 (WCAG 1.4.3). Lighthouse A11y 96. | Biến `--w-brass-deep: #9a6400` (4,48:1) cho `.display em` ở section nền sáng; hero/dải tối giữ đồng sáng. | S | Đã sửa (2d477bf). axe 2 → 0, Lighthouse A11y 96 → 100 |
| FE-004 | P1 | 1, 3, 7 | 1 | Bài học "Từng bước", 390 px | frontend/src/components/learning/LessonRunner.tsx:282–298, :326–331 | [FE-004_truoc.jpg](soi-loi-frontend/anh-loi/FE-004_truoc.jpg) → [FE-004_sau.jpg](soi-loi-frontend/anh-loi/FE-004_sau.jpg) | Bấm "Bước tiếp" cuộn về đầu `<section>`: nút quay lại + tiêu đề 2 dòng + thẻ tiến độ 3 hàng + nút chế độ + mục lục. Đo sau 8 lần bấm: nội dung bước bắt đầu ở y = 455 px trên màn 844 px (còn ~319 px nhìn được trên thanh đáy). Ableton Learning Music (R1): mỗi màn dành cho nội dung. | Điện thoại (< 640 px) cuộn tới thẻ tiến độ (`progressRef`, `scroll-mt-3`); thẻ tiến độ 2 hàng (`grid-cols-[1fr_auto]`, thanh `col-span-2`). Máy tính giữ hành vi cũ. Sau: nội dung bắt đầu ở y = 256 px (+62% chỗ cho nội dung). | S | Đã sửa (56a876a) |
| FE-005 | P1 | 4, 7 | 1 | Kết quả chấm (Luyện tập, câu kiểm tra trong bài, Quiz) | frontend/src/components/ui/Page.tsx:86 | [FE-005_truoc.jpg](soi-loi-frontend/anh-loi/FE-005_truoc.jpg) → [FE-005_sau.jpg](soi-loi-frontend/anh-loi/FE-005_sau.jpg) | Ở 390 px, bấm "Kiểm tra" xong ô "✗ Chưa đúng" hiện dưới mép màn hình hoặc sau thanh nút dính đáy: người học tưởng nút không chạy. Duolingo (R3) hiện phản hồi ngay trong khung nhìn. | `ResultBox` tự `scrollIntoView({block:"nearest"})` khi hiện/đổi đúng-sai, `scroll-mb-28` chừa thanh đáy, tôn trọng reduced-motion. Một chỗ sửa áp cho 14 nơi dùng. | S | Đã sửa (b90f3ed) |
| FE-006 | P1 | 7 | 1, 2 | Harmony Lab, thanh Phát/Tạo bản khác/Lưu, 390 px | frontend/src/pages/app/CompositionLabPage.tsx:46, :384–395 | [FE-006_truoc.jpg](soi-loi-frontend/anh-loi/FE-006_truoc.jpg) → [FE-006_sau.jpg](soi-loi-frontend/anh-loi/FE-006_sau.jpg) | Ba nút `size=lg` chia đều 390 px: "Tạo bản khác" xuống 3 dòng, "Lưu vòng này" 2 dòng, thanh cao ~100 px và nút AI đè lên nút Lưu. | Điện thoại: `whitespace-nowrap max-sm:!px-2 max-sm:!text-sm`, ẩn 🎲, thanh `pr-[4.25rem]` chừa nút AI. Chữ nút giữ nguyên. | S | Đã sửa (9c3ae6e) |
| FE-007 | P1 | 8 | 1, 2 | Vòng focus bàn phím trên nền tối (thanh bên khu học, hero/dải tối trang chủ) | frontend/src/index.css:61–69; AppLayout.tsx:51; wow.css:35 | [FE-007_truoc.jpg](soi-loi-frontend/anh-loi/FE-007_truoc.jpg) → [FE-007_sau.jpg](soi-loi-frontend/anh-loi/FE-007_sau.jpg) | Outline #006D61 trên #081613 = 2,96:1, trên #0C231F = 2,63:1; WCAG 1.4.11 (non-text contrast) cần ≥ 3:1. | `[data-surface="dark"] :focus-visible { outline-signature }` (8,42:1) và verdigris trong các section tối của trang chủ. | S | Đã sửa (2d477bf, 9de3baa) |
| FE-008 | P2 | 7 | 1 | Header trang công khai, 390 px | frontend/src/components/layout/PublicLayout.tsx:25–26 | [FE-008_hien-trang.jpg](soi-loi-frontend/anh-loi/FE-008_hien-trang.jpg) | "Đăng nhập" và "Đăng ký" xuống 2 dòng ở màn đầu tiên người mới thấy; trông vỡ. | Thêm `whitespace-nowrap` cho 2 link, giảm `px` ở `<sm`; hoặc thu "Harmony Mentor" thành logo biểu tượng ở `<sm`. | S | Chưa sửa (P2, chờ Phúc) |
| FE-009 | P2 | 3, 7 | 1 | Menu khu học, 390 px | frontend/src/components/layout/AppLayout.tsx:57 | [FE-009_hien-trang.jpg](soi-loi-frontend/anh-loi/FE-009_hien-trang.jpg) | 7 mục `grid-flow-col auto-cols-fr` trong 390 px: "Quiz kỹ năng" 3 dòng; menu không dính khi cuộn nên ở cuối trang dài phải cuộn lên. | Thanh tab dính đáy 5 mục (Tổng quan, Học, Luyện tập, Sáng tác, Thêm ▸ Quiz/Tiến độ/Hồ sơ), hoặc tối thiểu `overflow-x-auto whitespace-nowrap`. Đổi điều hướng = diện mạo lớn. | M | Chưa sửa (P2, chờ Phúc) |
| FE-010 | P2 | 3 | 1 | Thẻ tiến độ trong bài | LessonRunner.tsx:326–331 | [FE-010_hien-trang.jpg](soi-loi-frontend/anh-loi/FE-010_hien-trang.jpg) | "Bước 6/18" đứng cạnh thanh 0% (thanh đo % câu đúng, không phải % bước) → người mới hiểu là "chưa tiến bộ". Yousician (R4) tách tiến độ và kết quả. | Thêm thanh mỏng tiến độ bước (6/18) hoặc đổi nhãn "0% câu đúng". Đổi chữ giao diện → kèm danh sách cho Đạt. | S | Chưa sửa (P2, chờ Phúc) |
| FE-011 | P3 | 3 | 1 | Tổng quan | frontend/src/pages/Dashboard.tsx:38, :50 | [FE-011_hien-trang.jpg](soi-loi-frontend/anh-loi/FE-011_hien-trang.jpg) | Người mới thấy "Bài 1" hai lần (thẻ Bắt đầu học + Gợi ý cho bạn) và lời mời kiểm tra đầu vào nằm trên CTA chính. | Ẩn mục "Bài nên học tiếp" khi trùng bài ở thẻ Bắt đầu học; đưa lời mời kiểm tra đầu vào xuống dưới CTA. | S | Chưa sửa (P3) |
| FE-012 | P2 | 6 | 1, 2 | Harmony Lab, bấm Phát lần đầu | frontend/src/audio/band/samples.ts | (số đo, không ảnh) | Đo trên cloud, localhost, không throttle: 4 141 ms từ bấm Phát tới khi hết "Đang tải nhạc cụ"; tải 221 file mẫu, 9 768 KB. Mạng 4G sẽ lâu hơn nhiều (phỏng đoán, chưa đo). Chrome Music Lab (R2) phát được ngay. | Tải trước nhóm mẫu của phong cách mặc định bằng `requestIdleCallback` khi mở trang; phát piano synth ngay rồi chuyển sang mẫu khi xong. | M | Chưa sửa (P2) |
| FE-013 | P2 | 6 | 2 | Harmony Lab, khuông "Đang chọn C", 1440 px | frontend/src/components/music/NotationStaff.tsx | [FE-013_hien-trang.jpg](soi-loi-frontend/anh-loi/FE-013_hien-trang.jpg) | Khuông VexFlow chỉ ~190 px rộng trong khung 420 px; chữ "C: C – E – G" ~11 px. | Cho `NotationStaff` co theo khung (`width = container`), cỡ chữ chú thích ≥ 14 px. | S | Chưa sửa (P2) |
| FE-014 | P2 | 2, 8 | 1, 2 | Toàn app: chế độ tối | frontend/src/index.css | [FE-014_hien-trang.jpg](soi-loi-frontend/anh-loi/FE-014_hien-trang.jpg) | 0 biến thể `dark:`, 1 chỗ `prefers-color-scheme`; ảnh sáng và tối giống hệt ở 12 trang × 5 cỡ. Yêu cầu soi sáng/tối không thực hiện được vì app chỉ có một chế độ. | Thêm bộ token tối trong `@theme` dưới `@media (prefers-color-scheme: dark)` + công tắc; cần Phúc duyệt hướng màu (gộp với việc theme mới). | L | Chưa sửa (diện mạo lớn, chờ Phúc) |
| FE-015 | P2 | 6, 10 | 1, 2 | Học, Luyện tập, Tiến độ, Harmony Lab | frontend/src/audio/AudioEngine.ts:1; audio/band/*.ts | (console) | Console warning "The AudioContext was not allowed to start" ở 4 trang ngay khi mở: `import * as Tone` tạo AudioContext trước cú bấm. Không gây lỗi nhưng sinh cảnh báo và tốn tài nguyên. | Chỉ `import("tone")` động trong hàm phát (như trang chủ đã làm ở `wow/sound.tsx`). | M | Chưa sửa (P2) |
| FE-016 | P2 | 5 | 1 | Câu đúng / hoàn thành bài | Page.tsx `ResultBox`; LessonRunner.tsx:259 | [FE-005_sau.jpg](soi-loi-frontend/anh-loi/FE-005_sau.jpg) | Đúng câu hay hoàn thành bài chỉ hiện ô xanh tĩnh. Prompt yêu cầu dồn wow vào khoảnh khắc thưởng; Duolingo (R3) dùng chuyển động + âm ngắn. | Hiệu ứng GSAP nhẹ (nốt nhạc bay lên 600 ms) khi `correct`, tắt khi reduced-motion; âm thưởng mặc định tắt. | M | Chưa sửa (diện mạo, chờ Phúc) |
| FE-017 | P2 | 9 | 1 | Tổng quan, Lighthouse mobile | frontend/src/pages/Dashboard.tsx; components/learning/RecommendedLessons.tsx | (số đo) | CLS 0,214 (mức "cần cải thiện" 0,1–0,25): các thẻ hiện dần khi API trả về và đẩy nội dung xuống. | Skeleton có chiều cao cố định cho thẻ Bắt đầu học/Gợi ý/4 chỉ số. | S | Chưa sửa (P2) |
| FE-018 | P2 | 9 | 1, 2 | Bundle | frontend/src/App.tsx:6; vite build | (số đo) | `index.js` 482 kB (163 kB gzip) gồm GSAP + Lenis + trang chủ, tải cả khi vào thẳng `/app`; `NotationStaff` 1 123 kB (692 kB gzip) do VexFlow kèm font. | Tách `HomePage` thành chunk riêng cho route `/app`; dùng bản `vexflow/bravura` thay bản đủ font. | M | Chưa sửa (P2) |
| FE-019 | P3 | 3 | 1 | Danh sách bài, Quiz kỹ năng | dữ liệu bài từ API | [FE-019_hien-trang.jpg](soi-loi-frontend/anh-loi/FE-019_hien-trang.jpg) | Tên bài/kỹ năng còn tiếng Anh ("Secondary Dominants", "Modal Interchange…", "enharmonic spelling"). Là nội dung, không phải chữ giao diện. | Chuyển Đạt quyết; frontend không sửa. | — | Không thuộc frontend |
| FE-020 | — | — | 1 | AI Tutor khi AI tắt | backend (route dự phòng) | [FE-020_hien-trang.jpg](soi-loi-frontend/anh-loi/FE-020_hien-trang.jpg) | Hỏi "Hợp âm C gồm những nốt nào?" ở Bài 1 thì câu trả lời dự phòng trích bài L07 (Jazz tensions). Nốt C E G đúng nhưng trích dẫn lạc bài. | Chuyển luồng T1–T6 (đang sửa định tuyến AI). | — | Ngoài phạm vi |
| FE-021 | P3 | 2, 10 | — | Bàn phím piano | frontend/src/Piano.tsx; components/music/VirtualPiano.tsx | — | Hai component bàn phím khác kiểu (trang chủ dùng `Piano.tsx` SVG, khu học dùng `VirtualPiano`). | Gộp về `VirtualPiano` với chế độ chỉ hiển thị. | M | Chưa sửa (P3) |

## 5. Chưa sửa và vì sao

- Mọi lỗi P2/P3 chưa sửa vì quy tắc 3A (dừng hỏi Phúc trước). Cách sửa cụ thể đã ghi trong từng dòng; Phúc chọn ID nào thì làm ID đó.
- Theme mới (tối kiểu sân khấu, sáng kiểu giấy nhạc) chưa làm: cắt theo 2A. Ngoài ra app chưa có chế độ tối nào (FE-014), nên làm theme trước khi có chế độ tối sẽ phải làm lại.
- FE-020 là lỗi backend/AI (trả lời dự phòng khi AI tắt trích dẫn bài L07), ngoài phạm vi frontend; chuyển cho luồng T1–T6.

## 6. Việc cho từng thành viên

- **Phúc:** chạy `docs/HUONG_DAN_CHAY_WINDOWS.md` mục 4 trên điện thoại thật hoặc DevTools 390 px; nghe Harmony Lab và trang chủ; chọn P2 nào làm tiếp (gợi ý: FE-009, FE-012, FE-016); quyết FE-014 (có làm chế độ tối không).
- **Thắng:** xem FE-020 (route dự phòng AI Tutor) cùng luồng T1–T6; FE-012 nếu muốn tải trước mẫu âm từ phía máy chủ (nén/gộp file).
- **Đạt:** kiểm danh sách chữ giao diện ở mục 7 (đợt này chỉ đổi nhãn nút đóng thành vùng bấm lớn hơn, không đổi chữ); xem FE-019 (tên bài/kỹ năng còn tiếng Anh: "Secondary Dominants", "enharmonic spelling") vì đó là nội dung bài, không thuộc quyền sửa của frontend.

## 7. Chữ giao diện đã đổi (để Đạt kiểm)

Đợt này **không đổi câu chữ nào** hiển thị cho người học. Thay đổi duy nhất liên quan chữ: biểu tượng 🎲 trên nút "Tạo bản khác" bị ẩn ở màn hình < 640 px (FE-006); chữ nút giữ nguyên.

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
