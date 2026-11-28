# ADR-007 · Logo chính thức "Cuộn I–IV–V–I"

Trạng thái: **Chấp nhận 30/10/2026**. Phúc báo nhóm đã chọn logo này.

## Bối cảnh

Logo cũ là một ô vuông màu với ký tự "♪" và chữ "HarmonyMentor" gõ bằng font của trang. Nó giống logo của rất nhiều app âm nhạc khác và không có favicon. Ngày 27/10/2026 nhóm nhận 12 phương án (26 phác thảo, 6 hướng sáng tạo, bảng điểm 7 tiêu chí), mỗi phương án dựng từ một sự thật của cây đàn piano. Nhóm chọn **Cuộn I–IV–V–I** (bản "táo bạo", 27/35 điểm).

## Quyết định

1. Logo là ô cuộn giấy pianola 13 cột (C đến C cao), 4 hàng lỗ là 4 hợp âm I–IV–V–I của Đô trưởng. Vị trí lỗ tính bằng code (`docs/thuong-hieu/_nguon/symbols.js`), không vẽ tay.
2. Lỗ tô bằng 12 màu nốt của app. Đây là ngoại lệ có chủ ý so với luật "chỉ dùng họ Đồng & Gỉ cho logo"; Phúc đồng ý dùng màu nốt cho bản táo bạo ngày 27/10/2026.
3. Tên trong logo là "Harmony Mentor" (có dấu cách). Chữ là path sinh từ IBM Plex Mono, nên không cần tải font Plex vào app.
4. Component `HarmonyMentorLogo` đọc màu từ biến `--hm-logo-*`. Logo **không** tự đổi theo `prefers-color-scheme`, vì app chưa có chế độ tối: nếu logo tự chuyển sang chữ ngà khi máy để chế độ tối, chữ sẽ chìm trên nền sáng của app. Bản tối chỉ bật khi `<html data-theme="dark">`.
5. Thêm favicon (SVG tự đổi sáng/tối, ICO 16/32/48), apple-touch-icon 180, icon 192/512, `site.webmanifest`; tiêu đề tab đổi thành "Harmony Mentor".

## Hệ quả

- Ở 16px favicon chỉ còn là ô tối có vạch màu; muốn đọc được 4 hàng hợp âm cần từ 48px. Đã ghi kích thước nhỏ nhất trong `docs/thuong-hieu/BRAND_NOTE.md`.
- Người mới cần được kể một lần mới hiểu lỗ là hợp âm; nên có một câu giới thiệu trên trang chủ hoặc slide.
- Màu chính của app vẫn là bảng cũ (xanh lam) cho tới khi nhóm chốt bảng Đồng & Gỉ cho toàn app.
- Các chữ "HarmonyMentor" khác trong giao diện (chân trang, thông báo lỗi) chưa đổi; việc thống nhất tên hiển thị để nhóm quyết riêng.
- Sửa logo thì sửa script trong `_nguon/` rồi dựng lại, không sửa SVG hay `HarmonyMentorLogo.tsx` bằng tay.
