# Logo Harmony Mentor · Ghi chú nhận diện

Logo chính thức: **Cuộn I–IV–V–I**. Nhóm chốt ngày 30/10/2026 (ADR-007), chọn trong 12 phương án đề xuất ngày 27/10/2026.

## 1. Câu chuyện

Logo là một ô **cuộn giấy pianola**. Pianola là cây đàn piano tự chơi theo cuộn giấy đục lỗ: mỗi cột là một phím, mỗi lỗ là một nốt, lỗ càng dài thì nốt giữ càng lâu.

Ô này có 13 cột, từ nốt C đến C cao hơn một quãng tám, và 4 hàng lỗ. Bốn hàng là bốn hợp âm thật:

| Hàng | Hợp âm | Ba nốt (cột) |
| --- | --- | --- |
| 1 | I (Đô trưởng) | C, E, G |
| 2 | IV (Fa trưởng) | F, A, C cao |
| 3 | V (Sol trưởng) | D, G, B |
| 4 | I (Đô trưởng, thêm C cao) | C, E, G, C cao |

I–IV–V–I là tiến trình hợp âm đầu tiên trong hầu hết giáo trình hòa âm. Nếu đem ô này đặt vào một cây pianola, nó sẽ chơi đúng tiến trình đó. Mỗi lỗ tô bằng màu của nốt trong bảng 12 màu nốt của app, nên cùng một nốt luôn cùng một màu (cột C ở hàng 1, 4 cùng xanh gỉ).

Lớp nghĩa nhẹ về AI: pianola là "máy đọc bài rồi chơi", tổ tiên của nhạc lập trình, nhưng logo không cần robot hay mạch điện.

Wordmark "Harmony Mentor" dùng chữ máy IBM Plex Mono (như các cột lỗ đều nhau trên cuộn giấy). Dấu cách thay bằng ba lỗ nhỏ màu C, E, G: một hợp âm Đô trưởng nằm giữa hai chữ.

Nguồn cảm hứng: Conlon Nancarrow, "Studies for Player Piano" (ông tự tay đục lỗ cuộn giấy để đàn tự chơi). Không sao chép hình của tác phẩm, chỉ mượn cách nghĩ.

## 2. Các file

Thư mục `docs/thuong-hieu/logo/`:

| File | Dùng khi |
| --- | --- |
| `ngang-sang.svg`, `ngang-toi.svg` | Logo ngang trên nền sáng / nền tối |
| `doc-sang.svg`, `doc-toi.svg` | Logo dọc (slide bìa, trang chào) |
| `bieu-tuong-sang.svg`, `bieu-tuong-toi.svg` | Chỉ biểu tượng |
| `*-den.svg`, `*-trang.svg` | Bản 1 màu (in, khắc, đóng dấu) |
| `wordmark-sang.svg`, `wordmark-toi.svg` | Chỉ chữ |
| `app-icon.svg` | Icon ứng dụng (ô sơn mài phủ kín) |
| `favicon.svg` | Favicon tự đổi màu theo trình duyệt |
| `chuyen-dong.svg` | Bản có chuyển động cuộn giấy |

Trong app: `frontend/src/components/brand/HarmonyMentorLogo.tsx` (+ `logo.css`) và các icon trong `frontend/public/`. Script dựng lại ở `docs/thuong-hieu/_nguon/` (xem README trong đó).

## 3. Màu

- Ô cuộn giấy: sơn mài `#0C231F` (nền tối dùng `#101F1C` và viền gỉ `#45C2AB` để ô không chìm vào nền `#081613`).
- Lỗ: 12 màu nốt của app, **giống nhau ở mọi chế độ**, không được đổi (luật số 5 của bảng màu Đồng & Gỉ). Phúc đồng ý dùng màu nốt cho bản logo này ngày 27/10/2026.
- Chữ: sơn mài `#0C231F` trên nền sáng, ngà `#F2F3EA` trên nền tối.

Độ tương phản (WCAG 2.1, tính từ mã HEX):

| Cặp màu | Tỉ số | Kết quả |
| --- | --- | --- |
| Chữ `#0C231F` trên nền `#F2F3EA` | 14,72 : 1 | Đạt AAA |
| Chữ `#F2F3EA` trên nền `#081613` | 16,56 : 1 | Đạt AAA |
| Lỗ màu nốt trên ô `#0C231F` (thấp nhất là B `#D48FD1`) | 6,78 : 1 trở lên | Đạt |
| Ô `#0C231F` trên nền `#F2F3EA` | 14,72 : 1 | Đạt |
| Ô tối `#101F1C` trên nền `#081613` | 1,09 : 1 | Không đủ, nên bản tối có viền `#45C2AB` (8,42 : 1) |
| Ba lỗ màu trong wordmark trên nền `#F2F3EA` | khoảng 2 : 1 | Chỉ trang trí; chữ vẫn đọc đủ khi bỏ ba lỗ này |

## 4. Quy tắc dùng

**Khoảng trống tối thiểu.** Chừa quanh logo một khoảng bằng 1/4 chiều cao biểu tượng.

**Kích thước nhỏ nhất.**

| Bản | Màn hình | In |
| --- | --- | --- |
| Icon app / favicon | 16 px (chỉ còn nhận ra ô tối có vạch màu) | 6 mm |
| Biểu tượng mà vẫn đọc được 4 hàng hợp âm | 48 px | 15 mm |
| Logo ngang | cao 28 px | rộng 30 mm |
| Logo dọc | cao 64 px | cao 18 mm |

Trong app, logo ngang đang dùng cao 36 px (`h-9`).

**Chuyển động.** Cuộn giấy chạy qua trong 2,4 giây, chạy một lần. Bật bằng prop `animate`. Tự tắt khi người dùng bật "giảm chuyển động". Chỉ dùng ở màn hình chào, lúc tải, hoặc lúc AI Tutor đang trả lời.

**Chế độ tối.** App hiện chưa có chế độ tối, nên logo chỉ đổi sang bản tối khi `<html data-theme="dark">`. Nó không tự đổi theo cài đặt hệ điều hành, vì như thế chữ ngà sẽ chìm trên nền sáng của app.

## 5. Không được làm

1. Không đổi vị trí lỗ. Mỗi lỗ là một nốt thật; dời lỗ là logo chơi sai hợp âm.
2. Không đổi màu lỗ, không dùng màu nốt khác cho cùng một nốt.
3. Không kéo dãn, nghiêng, xoay, thêm bóng đổ hay gradient.
4. Không gõ lại "Harmony Mentor" bằng font khác; dùng file có sẵn (chữ đã thành path).
5. Không viết liền "HarmonyMentor" trong logo.
6. Không đặt bản sáng lên nền tối hoặc ngược lại.
7. Không thêm robot, mạch điện, tia lấp lánh để "cho có AI".
8. Không dùng logo ngang dưới 28 px chiều cao; khi đó dùng icon app.

## 6. Rủi ro đã biết

- Bản này được chấm 2/5 ở tiêu chí "nhận ra ở 16px" và 2/5 ở "hợp người mới học" trong vòng đề xuất: ở favicon chỉ còn thấy một ô tối có vạch màu, và người mới cần được kể câu chuyện một lần mới hiểu các lỗ là hợp âm. Nên có một câu giới thiệu ngắn trên trang chủ hoặc trong slide.
- Điểm số là đánh giá của người thiết kế, chưa thử với người dùng thật.
- Màu chủ đạo của app vẫn là bảng màu cũ (xanh lam). Logo đã theo bảng Đồng & Gỉ, nên khi nhóm chốt bảng màu mới cho cả app thì hai bên mới khớp hẳn.
