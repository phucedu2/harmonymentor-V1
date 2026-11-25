# Làm lại trang chủ công khai (25/11/2026)

Nhánh `homepage-lam-lai`, Draft PR vào `phuc-music`. Người yêu cầu: Phúc. Chỉ đụng trang công khai.

## 1. Đã làm gì

| Mục | Neo | File |
| --- | --- | --- |
| Footer đầy đủ 4 cột | mọi trang công khai | `frontend/src/pages/public/home/SiteFooter.tsx`, `components/layout/PublicLayout.tsx` |
| Lộ trình học | `#lo-trinh` | `home/RoadmapSection.tsx` |
| Bạn sẽ học gì và làm được gì | `#hoc-gi` | `home/OutcomesSection.tsx` |
| Tính năng dạng bento 8 ô, có ảnh thật | `#tinh-nang` | `home/FeatureBento.tsx`, `frontend/public/home/*.webp` |
| Chương trình học chi tiết, mở khi rê chuột | `#chuong-trinh` | `home/CurriculumDetail.tsx` |
| Chữ của các mục mới | | `home/copy.ts` |
| Số liệu suy từ API | | `home/curriculum.ts`, `home/data.ts` |
| Kiểu dáng và chuyển động | | `home/home.css` |
| Chụp ảnh khu học | | `scripts/chup-anh-trang-chu.cjs` (sinh `home/shots.ts`) |

Giữ nguyên từng dòng: Hero, StaffScene, ProgressionScene, ChordDemo, khu học `/app`, Admin, backend, logo,
bảng màu, trang đăng nhập/đăng ký. Thay đổi duy nhất ngoài danh sách trên là nút "Xem chương trình" ở Hero
giờ cuộn tới `#lo-trinh` (chỉ đổi tham số truyền vào, không sửa `WowScenes.tsx`).

## 2. Số liệu lấy ở đâu

Không có số nào viết tay trong giao diện (FR-VIS-02). Tất cả từ `GET /api/v1/lessons`; dạng câu hỏi lấy
thêm từ `GET /api/v1/lessons/{id}` và chỉ gọi khi mục "Chương trình học" sắp vào khung nhìn.

Thời lượng là **ước lượng**, công thức trong `home/curriculum.ts`:

```
phút = làm tròn 5( 1,5 × số phần lý thuyết + 1 × số câu hỏi )
```

Ví dụ M1 Nền tảng (25 phần lý thuyết, 24 câu hỏi): 25 × 1,5 + 24 = 61,5 → "khoảng 60 phút".
Đây là ước lượng để người đọc hình dung, **chưa đo trên người học thật**.

Câu "Xong chặng này bạn sẽ…" ghép từ mục tiêu đầu tiên của từng bài trong chặng, không viết tay.
Nhãn "Đang soạn" chỉ hiện khi `block_count = 0` hoặc `exercise_count = 0`; hiện tại 9 bài đều đủ nên
không bài nào mang nhãn này.

Ảnh trong các ô tính năng là ảnh chụp thật của khu học, chụp bằng Playwright trên tài khoản thử tạo lúc
chạy script (làm thật bài 1 để có thẻ ôn và mức thành thạo). AI Tutor chụp khi `AI_ENABLED=false` nên
câu trả lời là bản dự phòng lấy từ bài học, vẫn có trích dẫn `[L06]` và dấu "Đã kiểm bằng Music Engine".

## 3. Lệnh đã chạy (25/11/2026, trên cloud)

```bash
cd frontend && npx tsc -b                 # không lỗi
npm run build                             # built in 3.60s
npx vitest run                            # 20 tệp, 313 test đạt
cd backend && python ../scripts/e2e/dap_an_demo_1011.py > /tmp/dap_an.json
ANS=/tmp/dap_an.json OUT=frontend/public/home node scripts/chup-anh-trang-chu.cjs   # 16 ảnh, 844 KB
```

Kiểm tra giao diện (Playwright, Chromium 1440×900 và 390×844):

- Bàn phím: Tab vào thẻ bài → thẻ mở ra, Tab tiếp vào đúng nút "Xem bài".
- Điện thoại: chạm vào thẻ thì mở ra; tràn ngang 0 px.
- `prefers-reduced-motion: reduce`: thẻ không dịch chuyển khi rê chuột (`transform: none`), vẫn mở ra đọc
  được; bật chuyển động thì nhấc 5 px.
- Không có lỗi JavaScript nào trên trang.

axe-core (WCAG 2.0 A + AA, cả trang chủ, cuộn hết):

| Phương án | Số lỗi |
| --- | --- |
| Sân khấu sáng | 1 (có sẵn từ trước) |
| Sân khấu tối | 0 |
| Đồng & Gỉ sáng | 0 lỗi mới, cùng 1 lỗi có sẵn |

Lỗi còn lại là `color-contrast` ở ba chữ nhỏ `wow-kicker` trong cảnh khuông nhạc (`WowScenes.tsx` dòng 236,
bản dành cho người tắt hiệu ứng). Cảnh này nằm trong danh sách không được sửa nên để nguyên; nếu nhóm
muốn sửa thì làm ở một PR riêng.

Lighthouse (bản build thật, Chromium không giao diện, mỗi bên chạy 2–3 lần):

| | Hiệu năng | Trợ năng | Thói quen tốt | SEO | LCP | CLS |
| --- | --- | --- | --- | --- | --- | --- |
| Trước (`phuc-music`) | 81 / 76 | 100 | 100 | 91 | 5,0 s | 0,004 |
| Sau | 79 / 81 / 81 | 100 | 100 | 92 | 5,0–5,2 s | 0,004 |

Chênh lệch nằm trong khoảng dao động giữa các lần chạy; LCP và CLS không đổi dù trang dài gấp đôi, vì ảnh
đều `loading="lazy"` và có `width`/`height` thật.

## 4. Giải thích cho nhóm

- **Bento** là kiểu lưới ô to nhỏ xen kẽ như hộp cơm Nhật: ô quan trọng (Harmony Lab, AI Tutor) chiếm hai
  cột, ô phụ chiếm một cột. Người đọc nhìn một lượt là biết cái gì quan trọng.
- **Mở thẻ bằng `grid-template-rows: 0fr → 1fr`**: cách này cho phần mở thêm chạy mượt mà không cần đo
  chiều cao bằng JavaScript. Khi thẻ đóng, phần đó để `visibility: hidden` nên phím Tab không lọt vào nút
  đang vô hình.
- **Ảnh theo chế độ sáng/tối**: component nghe sự kiện `hm-theme` mà `ThemeToggle` phát ra, rồi đổi đuôi
  tệp ảnh `-light` / `-dark`. Không cần tải cả hai.
- **Vì sao không viết cứng danh sách bài**: thêm hay sửa bài ở backend là trang chủ tự đổi theo, không ai
  phải nhớ sửa hai chỗ.

## 5. Nhóm cần kiểm

- **Phúc**: nhìn trang ở cả ba phương án màu × sáng/tối trên máy mình, thử rê chuột và chạm trên điện thoại.
- **Đạt**: đọc lại chữ trong `home/copy.ts`, nhất là danh sách đầu ra ở mục "Học gì" — mỗi câu phải khớp
  với bài và câu hỏi thật.
- **Thắng**: xem lại `home/curriculum.ts` (công thức thời lượng, cách gộp mục tiêu) và việc gọi thêm
  `GET /lessons/{id}` cho 9 bài khi cuộn tới mục chương trình.

Người kiểm: Thắng ☐ · Phúc ☐ · Đạt ☐

## 6. Rủi ro và câu cần nhóm quyết

1. Thời lượng "khoảng X phút" là ước lượng, chưa đo người thật. Đề xuất: giữ chữ "khoảng" và ghi rõ trong
   báo cáo cuối kỳ.
2. Email `HarmonyMentor@gmail.com` ở footer: nhóm phải chắc chắn hộp thư này có người đọc trước 04/12.
3. Ảnh chụp đang theo phương án Sân khấu; nếu nhóm đổi phương án mặc định thì chạy lại
   `scripts/chup-anh-trang-chu.cjs` để ảnh khớp màu.
