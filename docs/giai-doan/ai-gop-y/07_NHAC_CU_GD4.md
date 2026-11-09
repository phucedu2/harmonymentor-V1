# GĐ4: thêm nhạc cụ cho backing track Harmony Lab

Ngày 08/11/2026 · nhánh `ai/gd4-nhac-cu` (từ `phuc-music`).

## Đã làm

| Việc | Chi tiết |
|---|---|
| Kênh mới "Dây (cello)" | Thêm vào bàn trộn như một kênh riêng (fader, tắt tiếng, reverb gửi riêng). **Mặc định tắt** nên mọi bản phối cũ nghe y hệt; bật thì mới tải mẫu cello (3,8 MB) |
| Mẫu cello | Karoryfer × Bigcat Cello, lớp kéo cung (sus), giấy phép **CC0** (đã đọc LICENSE trong kho). 76 mẫu, 3 lớp lực, dây D và G, nốt cách quãng 3 thứ từ G2 đến C5. Tên tệp có nốt lệch 1 quãng tám so với tiếng thật, script đo bằng YIN và dịch lại, nốt nào không khớp thì bỏ (C1, Eb1 lớp nhẹ) |
| Nốt cello | `stringsPad()` lấy hai nốt thấp nhất (khác tên nốt) của mỗi hợp âm phím do Engine dựng, dời quãng tám vào tầm G2–E4, giữ suốt ô. Không tự tính hợp âm ở frontend. Không dùng số ngẫu nhiên nên bật kênh Dây không làm đổi nhát của kênh khác (có test) |
| Ba âm sắc guitar | Sạch / Rè nhẹ / Rè mạnh, cộng chế độ "Theo phong cách". Làm bằng Web Audio (lọc → méo → loa thùng) trên mẫu guitar có sẵn, **không thêm mẫu**. "Rè mạnh" giữ đúng giá trị overdrive cũ của rock/indie nên chế độ tự động không đổi tiếng bản cũ. Đổi được khi đang nghe |
| Backend | `MIX_CHANNELS` thêm `strings` (cột `mix` là JSON, không cần migration) |
| Script mẫu | `build_samples.py` thêm nguồn `cello`, chỉ clone kho thật sự dùng; `CREDITS.md` và `manifest.json` sinh lại |

## Không làm và lý do

- **Violin**: chưa tìm được thư viện CC0 chất lượng. Các thư viện violin tìm được đều thương mại.
- **Guitar mộc (acoustic)**: ứng viên Emilyguitar thực ra là **Epiphone Emily the Strange**, guitar điện thu trực tiếp (readme trong kho), không phải guitar mộc. Không dùng để tránh gọi sai tên. Cần tìm nguồn CC0 khác.

## Kiểm chứng

- `npm test`: 271 đạt (8 test mới trong `frontend/tests/bandStrings.test.ts`).
- `npm run build`: đạt.
- `pytest`: 1005 đạt, 43 bỏ qua (thêm 1 test lưu kênh `strings`). CI nâng `--min-passed` lên 1005.
- **Chưa nghe thử bằng tai**: môi trường cloud không phát âm thanh. Cần Phúc nghe cello ở vài phong cách và 3 âm sắc guitar, nhất là mức âm lượng kênh Dây (`BASE_DB.strings = -9`) và độ méo "rè nhẹ".
- Thu offline (`renderOffline`) chưa nhận kênh Dây và âm sắc, vẫn như cũ.
