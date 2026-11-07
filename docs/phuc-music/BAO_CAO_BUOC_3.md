# Báo cáo Bước 3: giao diện "Đồng & Gỉ"

Ngày 31/10/2026. Nhánh `phuc-music`, Draft PR #18. Bước 3 chỉ sửa frontend, script kiểm tra và tài liệu. Backend, Music Engine, nội dung bài và CSDL không đổi.

## 1. Đã làm gì

**Hệ thiết kế** (`frontend/src/index.css`, khối `@theme` của Tailwind v4)
- Bảng màu "Đồng & Gỉ": nền ngà `#F2F3EA`, chữ `#0C231F`, màu chính `#006D61`, chữ ký `#45C2AB`, đồng thau `#E0A53E`, sai `#B4343B`, nền tối `#081613`. Thêm vài sắc phụ để đủ tương phản: `primary-strong #00574D`, `muted #4A5E59`, `success #1F6F43`, `warning #7A4F00` và các nền nhạt `*-soft`.
- Đồng thau `#E0A53E` và chữ ký `#45C2AB` chỉ dùng để trang trí (viền, vạch), vì trên nền ngà chúng không đạt 4.5:1 khi làm màu chữ.
- Font: Fraunces cho tiêu đề, Be Vietnam Pro cho chữ thường, IBM Plex Mono cho tên nốt và số. Gỡ JetBrains Mono.
- 12 màu nốt theo vòng quãng năm (C, G, D, A, E, B, F#, Db, Ab, Eb, Bb, F), đặt trong `@theme static` để Tailwind không lược bỏ. Piano dùng màu này làm vạch dưới phím đang tô sáng.

**Chuyển trang sang Tailwind**
- Bỏ lớp `legacy-page` và xóa `styles.css`. Tổng quan, Học, Luyện tập, Tiến độ, bài học và các widget nhạc (piano, khuông nhạc, nghe, hợp âm, thuật ngữ) đều dùng Tailwind.
- Component dùng chung mới ở `components/ui/Page.tsx`: `PageHeading`, `Card`, `ProgressBar`, `Badge`, `Metric`, `ToggleGroup`, `ChipButton`, `ResultBox`. Lớp chung cho khối bài học nằm ở `components/learning/lessonStyles.ts`. Bài học vẫn dùng `Button`, `Alert`, `TextField` sẵn có.

**Nguyên tắc cho người mới**
- Một màn hình một việc chính. Tổng quan đặt thẻ "Học tiếp" lên đầu, rồi mới tới số liệu. Tiến độ đặt thẻ cần ôn hôm nay lên trước danh sách bài.
- Nút chính luôn thấy trên điện thoại. Ở màn hẹp, thanh "Bước trước / Bước tiếp" của bài học dính đáy màn hình. Nút cao tối thiểu 44px.
- Chú giải thuật ngữ: lần đầu "nửa cung", "quãng tám", "hợp âm trưởng/thứ/giảm/tăng", M3, m3, P5, d5 xuất hiện trong bài thì chữ đó thành nút. Bấm vào sẽ mở lời giải nghĩa và nút "Nghe ví dụ". Âm thanh lấy nốt từ Music Engine qua `api.transpose` và `api.inspectChord`, frontend không tự tính nốt.
- Phản hồi sai nói rõ chỗ sai: khung kết quả luôn có dấu ✓/✗ và chữ "Chính xác"/"Chưa đúng", không chỉ dựa vào màu. Trên piano, phím sai có dấu ✗ và nhãn đọc "nốt sai".
- Không còn thuật ngữ dev trên giao diện. Ví dụ "Đang gọi API…" đổi thành "Đang lấy nốt từ máy chủ…".

**WCAG 2.1 AA**
- Tương phản: test `frontend/tests/contrast.test.ts` tính tỷ lệ cho mọi cặp chữ/nền dùng trong giao diện, đều ≥ 4.5:1. Chữ trên 12 màu nốt cũng ≥ 4.5:1.
- Bàn phím: mọi điều khiển là `button`/`input` thật, viền focus 2px màu chính. Escape đóng khung hợp âm và khung thuật ngữ. Nút chọn có `aria-pressed`.
- Piano: mỗi phím có `aria-label` (ví dụ "Phím C4, đang chọn"), và dòng "đang chọn" dùng `aria-live`. Khuông nhạc là `role="img"` với `aria-label` liệt kê các nốt.
- Thanh tiến độ có `role="progressbar"` kèm nhãn.

## 2. Commit

| Commit | Nội dung |
|---|---|
| `09a3d64` | feat(ui): bảng màu, font, 12 màu nốt, test tương phản |
| `7a1fc22` | refactor(ui): Tổng quan, Học, Luyện tập, Tiến độ sang Tailwind |
| `5072083` | refactor(ui): bài học và widget nhạc sang Tailwind, bỏ `styles.css` và `legacy-page` |
| `00e506b` | feat(lesson): chú giải thuật ngữ lần đầu xuất hiện, nút nghe |
| `8d0dbd0` | test(phuc-music): script chụp ảnh mọi trang và kiểm tra WCAG |
| `655d4f2` | fix(lesson): chú giải không mất khi StrictMode render lại, khung nổi vừa màn 390px |
| `455b114` | docs(phuc-music): ảnh trước/sau và kết quả WCAG |
| `fd67d8f` | fix(ui): giữ mốc `data-part` để test hotfix ký âm cũ vẫn kiểm được |

**Hai lỗi tự bắt được khi kiểm tra:**
- Bản đầu ghi nhận "đã chú giải" ngay bên trong lúc component con render. Ở chế độ dev, React StrictMode render hai lần, nên lần thứ hai bỏ mất chú giải. Cách sửa: chuyển sang hàm thuần `annotateTerms` và thêm test render lại hai lần.
- 2 test backend cũ (`test_phase2_notation_hotfix.py`) dò tên lớp CSS cũ trong `NotationStaff.tsx`. Đã thêm thuộc tính `data-part` cùng tên để test vẫn kiểm đúng ý cũ (có khung dự phòng, nhãn nằm trong từng thẻ ví dụ). Không sửa test.

## 3. Kiểm tra (chạy thật ngày 31/10/2026)

| Lệnh | Kết quả |
|---|---|
| `cd backend && python -m pytest -q` | **371 passed, 21 skipped** (không đổi so với Bước 2) |
| `cd frontend && npm test` | **219 passed** (Bước 2: 195; thêm test tương phản và 5 test chú giải) |
| `cd frontend && npm run build` | Đạt |
| `node scripts/phuc-music/kiem_tra_wcag.cjs` (axe-core, chuẩn wcag2a/2aa/21a/21aa) | **0 vi phạm** trên 15 màn × 2 cỡ (1440px, 390px): trang chủ, đăng nhập, đăng ký, tổng quan, học, Bài 1 (mở đầu, bước 2, 7, 8, 10), luyện tập (trước và sau khi chấm), tiến độ, sáng tác, hồ sơ. Kết quả: `kiem_tra_wcag_buoc3.txt` |
| Bàn phím (cùng script) | Enter mở Bài 1; Tab tới "Phím C3, nốt cần tìm"; viền focus hiện rõ |
| Chú giải trên trình duyệt | Bài 1 bước 2: "nửa cung" được chú giải; bấm vào mở khung giải nghĩa ở cả 1440px và 390px |
| CI trên PR #18 | Xem check trên PR |

## 4. Ảnh (`anh/buoc-3/`)

- `01`…`10-<trang>-<1440|390>-<truoc|sau>.png`: 10 trang, mỗi trang có ảnh trước/sau ở 2 cỡ màn. Ảnh "trước" chụp ở `d9e28cc` (cuối Bước 2).
- `11-bai-1-buoc-{5,7,8,9}-*-sau.png`: các bước có piano, khuông nhạc, câu hỏi và phản hồi sai.
- `12-thuat-ngu-*-sau.png`: khung chú giải "Nửa cung".

## 5. Còn lại và vì sao

| Việc | Lý do |
|---|---|
| Lời giải nghĩa 10 thuật ngữ trong `TermText.tsx` | Claude viết bản đầu. Theo phân công, Astra kiểm nhạc lý và Đạt duyệt. Nội dung bài đã phát hành không bị sửa. |
| Trang Sáng tác, Hồ sơ, Đăng nhập | Các trang này vốn đã dùng Tailwind. Ở bước này chỉ đổi màu theo token mới; xưởng sáng tác làm ở Bước 4. |
| Thanh bên tối không kéo hết chiều cao trong ảnh `fullPage` 1440px | Lỗi có từ trước (layout Bước 1), chỉ lộ ra khi chụp cả trang dài. Trên màn hình thật thì không thấy. Để Bước 4 sửa cùng layout xưởng. |
| Khung chú giải ở 1440px có thể che nút "Bước tiếp" | Người dùng đóng được bằng Escape hoặc nút "Đóng". Nếu nhóm muốn, có thể đổi khung mở sang bên trái. |
| Kiểm tra bằng trình đọc màn hình thật (NVDA/VoiceOver) | Chưa làm. Mới kiểm tự động bằng axe và bằng bàn phím. |

## 6. Câu hỏi cho nhóm

- **Q1 (Phúc):** đồng thau `#E0A53E` không đủ tương phản để làm màu chữ trên nền ngà, nên mình chỉ dùng cho viền và vạch. Màu chữ cảnh báo là `#7A4F00` (cùng họ, đậm hơn). Phúc thấy được không?
- **Q2 (Đạt/Astra):** duyệt lời giải nghĩa 10 thuật ngữ trong `frontend/src/components/learning/TermText.tsx` (mảng `TERMS`).
- **Q3 (Phúc):** có muốn chú giải cả những bài sau (mỗi bài chú giải lại lần đầu) như hiện tại không, hay chỉ chú giải ở bài đầu tiên người học gặp thuật ngữ đó?

## 7. Xung đột có thể gặp

- PR #15 (HM-011): `VirtualPiano.tsx` đã viết lại phần lớn bằng Tailwind. Nếu #15 lên main trước thì phải gộp tay phần nhãn phím.
- PR #17 (CP2): có thể đụng `ci.yml` (`--min-passed`). Bước 3 không đổi mức này.
- Nhánh nào còn import `styles.css` hoặc dùng lớp CSS cũ (`legacy-page`, `lesson-block`, `piano-key`…) sẽ mất định dạng sau khi gộp.
