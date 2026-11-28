# Thử nghiệm "wow UI" cho trang chủ (nhánh `wow-ui-thu-nghiem`)

Ngày 31/10/2026. Bài tập kiểm chứng bộ công cụ Claude Code (skill `wow-ui`, GSAP skills, Context7, Playwright). **Draft, chưa gộp.** Chỉ đổi trang chủ `/`; khu vực học `/app` chưa đụng tới.

## Concept

- Ý tưởng lớn: **cuộn trang = chơi nhạc**. Mỗi đoạn cuộn thêm một nốt, rồi một hợp âm, rồi một vòng hợp âm.
- Cảm xúc: tò mò, vui, chuyên nghiệp.
- Khoảnh khắc chữ ký: rê chuột qua tiêu đề thì mỗi chữ cái phát một nốt (khi đã bật âm thanh); cuộn tới khuông nhạc thì nốt rơi xuống và vang lên.

## Storyboard cuộn

| Cảnh | Khoảng cuộn | Chuyển động | Âm thanh | Nội dung |
|---|---|---|---|---|
| 1. Hero (nền tối Đồng & Gỉ) | 0–100vh | Chữ tiêu đề bật lên từng ký tự; 7 nốt nhạc trang trí bay lên theo độ sâu (parallax); tiêu đề thu nhỏ, mờ dần | Rê chuột qua chữ: nốt ngũ cung Đô | "Hiểu nhạc lý bằng cách chơi nó." + nút bật âm thanh |
| 2. Khuông nhạc (ghim) | +220% | Nốt C, E, G lần lượt rơi xuống khuông; lời giải thích đổi theo bước | Mỗi bước phát số nốt đang có (1, 2, rồi 3 nốt) | Từ một nốt đến một hợp âm |
| 3. Vòng hợp âm (ghim, cuộn ngang) | theo chiều rộng dải thẻ | Dải 4 thẻ C–G–Am–F trượt ngang; thẻ đang giữa được tô viền đồng | Phát hợp âm của thẻ đang chọn | I – V – vi – IV, chức năng lấy từ Engine |
| 4. Tự tay thử | bình thường | Hiện dần | Chọn hợp âm thì nghe luôn | Khối "Bấm thử một hợp âm" cũ, đổi màu |
| 5. Chương trình, Tính năng, lời mời cuối | bình thường | Hiện dần theo nhóm | Không | Nội dung cũ, đổi màu và font |

Mọi nốt, chức năng (`roman`, `function`) đều lấy từ `GET /api/v1/music/chords/inspect` (Music Engine), đúng nguyên tắc bất biến 1. Riêng 6 nốt hiệu ứng khi rê chuột qua chữ là âm trang trí, viết sẵn trong `WowScenes.tsx` và có ghi chú.

## Thay đổi

- `frontend/src/pages/public/wow/WowScenes.tsx`: Hero, cảnh khuông nhạc, cảnh vòng hợp âm, cuộn mượt Lenis + ScrollTrigger, hook giảm chuyển động.
- `frontend/src/pages/public/wow/sound.tsx`: bật/tắt âm thanh (mặc định tắt, nhớ bằng localStorage), giới hạn tần suất, **tải Tone.js chỉ khi bật**.
- `frontend/src/pages/public/wow/wow.css`: bảng màu Đồng & Gỉ chỉ áp trong `.wow` (không đổi `@theme` chung), font Fraunces (có bộ chữ tiếng Việt).
- `frontend/src/pages/public/HomePage.tsx`: ghép các cảnh, giữ nguyên `ChordDemo`, `Curriculum`, `FEATURES`.
- Thư viện mới (ghim phiên bản): `gsap 3.13.0`, `@gsap/react 2.1.2`, `lenis 1.3.4`, `@fontsource/fraunces 5.2.6`.

## Kiểm chứng

- `npm run build`: đạt. Gói `index` tăng từ 297.9 kB lên 449.1 kB (gzip 97.4 → 154.7 kB) vì GSAP, Lenis, font. Tone.js tách thành `AudioEngine-*.js` (235 kB) chỉ tải khi người dùng bật âm thanh.
- Playwright (Chromium, backend thật trên SQLite): chụp 7 vị trí cuộn ở 1440px và 390px, không có lỗi JavaScript (chỉ có 401 của `/auth/me` khi chưa đăng nhập, có sẵn từ trước).
- Giảm chuyển động (`reducedMotion: 'reduce'`): không ghim, không cuộn mượt, cả 3 bước khuông nhạc hiện cùng lúc, thẻ hợp âm có nút "Nghe", toàn bộ nội dung đọc được (ảnh `anh/giam-chuyen-dong-toan-trang.png`).
- **Chưa đo**: Lighthouse, FPS bằng Chrome DevTools, nghe âm thanh thật (máy chủ không có loa). Phúc cần mở `npm run dev` trên máy, bật âm thanh và cuộn thử.

## Tự chấm rubric (skill wow-ui, 0–3 mỗi mục)

| # | Tiêu chí | Điểm | Ghi chú |
|---|---|---|---|
| 1 | Ấn tượng 5 giây đầu | 3 | Tiêu đề serif cỡ lớn, nền tối, nốt bay |
| 2 | Kịch bản cuộn mạch lạc | 3 | Nốt → hợp âm → vòng hợp âm, đúng mạch bài học |
| 3 | Motion có ý nghĩa | 2 | Ổn; dải thẻ ngang còn hơi đơn điệu |
| 4 | Âm thanh vui, không phiền | 2 | Chưa nghe thật trên loa |
| 5 | Tắt tiếng, chỉ phát sau tương tác | 3 | Mặc định tắt, nút ở hero và ở "Tự tay thử" |
| 6 | Bản giảm chuyển động | 3 | Đã chụp kiểm tra |
| 7 | Mượt | 2 | Chỉ animate transform/opacity; chưa đo FPS |
| 8 | Hiệu năng | 1 | Gói tăng ~57 kB gzip; chưa chạy Lighthouse |
| 9 | Truy cập | 2 | `aria-pressed`, `aria-label` cho khuông/piano; chưa kiểm tra bàn phím đầy đủ |
| 10 | Mobile | 2 | Dùng được ở 390px; nốt trang trí đã làm mờ để không che chữ |
| 11 | Nhất quán thương hiệu | 2 | Trang chủ dùng Đồng & Gỉ, nhưng header và logo vẫn màu xanh cũ |
| 12 | Không cản trở mục tiêu | 3 | Nút "Bắt đầu miễn phí" luôn ở hero và cuối trang |
| | **Tổng** | **28/36** | Đạt ngưỡng 27 của skill |

## Việc còn lại

1. Đổi header, logo, `@theme` sang Đồng & Gỉ cho cả web (cần nhóm đồng ý).
2. Đo Lighthouse và FPS; nếu thấp, tách GSAP ra khỏi gói chính bằng `lazy()`.
3. Áp dụng nhẹ cho khu vực học (âm thanh khi trả lời đúng, chuyển bước mượt), ưu tiên dễ dùng.
