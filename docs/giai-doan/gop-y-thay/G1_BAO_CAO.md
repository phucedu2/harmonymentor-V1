# G1 (T4): bài 2–9 chỉ thấy hợp âm C / Cmaj7

Ngày làm: 14/11/2026. Nhánh `gop-y-thay/g1-doi-giong` (đích `phuc-music`). Nội dung do Claude soạn thêm: chỉ là khai báo số La Mã, chờ Đạt duyệt.

## Nguyên nhân gốc
Không có lỗi hiển thị. Ví dụ hợp âm trong bài ghi cứng ký hiệu ở giọng C (`"progression": ["Cmaj7","Dm7","G7"]`, `"key": "C"`) và frontend chỉ phát lại đúng chuỗi đó. Cộng thêm `LessonRunner.tsx` ghi cứng C/Cm/Cdim/Caug ở khối "triad". "Bài 2–9" trên màn hình là thứ tự trong Bảng 7 (L02, L09, L10, L03, L05, L11, L06, L04), không phải mã bài.

## Đã đổi (sửa gốc, không vá từng bài)
- `backend/app/content/progression.py`: số La Mã + giọng thành ký hiệu hợp âm, bằng Music Engine (hỗ trợ bậc thuận giọng, V7/ii, iv, bVII...). Không sửa Engine.
- `GET /api/v1/music/progression?key=&numerals=`: sai giọng hay số La Mã trả 422, không lặng lẽ quay về C.
- Các khối ví dụ (L02, L03, L04, L05, L06, L07, L08, L11 và 5 khối "nghe thêm" nháp) khai báo thêm `numerals`. Ký hiệu cũ giữ nguyên ở giọng mặc định, nên lời văn và câu hỏi hiện có không đổi.
- Frontend: `KeyedProgression.tsx` có ô chọn giọng (12 giọng), ký hiệu lấy từ API; khối triad dùng nốt gốc người học đang chọn.
- Test: `backend/tests/test_g1_doi_giong.py` (11 test, chạy đỏ trước khi sửa: thiếu module và thiếu `numerals`), `frontend/src/lib/progressionText.test.ts`.

## Bảng kiểm từng bài (giao diện thật, Playwright, 14/11/2026)
Cột "mặc định" là giọng gốc của bài; cột "Eb" sau khi chọn giọng Eb trên giao diện.

| Thứ tự | Bài | Mặc định (giọng C) | Sau khi chọn Eb |
| --- | --- | --- | --- |
| 2 | L02 | Cmaj7 G7 | Ebmaj7 Bb7 |
| 3, 4 | L09, L10 | không có khối hợp âm (bản nháp chỉ có "Dùng vào sáng tác") | không áp dụng |
| 5 | L03 | Cmaj7 Dm7 G7 Cmaj7 | Ebmaj7 Fm7 Bb7 Ebmaj7 |
| 6 | L05 | Cmaj7 A7 Dm7 G7 Cmaj7 | Ebmaj7 C7 Fm7 Bb7 Ebmaj7 |
| 7 | L11 | C G Am F | Eb Bb Cm Ab |
| 8 | L06 | C F Fm C | Eb Ab Abm Eb |
| 9 | L04 | Dm7 G7 Cmaj7 | Fm7 Bb7 Ebmaj7 |

L07 và L08 (vòng ii–V–I dạng nút nghe, không có nhãn chữ) cũng đổi giọng được; kiểm bằng test API ở cả 12 giọng. Ảnh: `docs/giai-doan/gop-y-thay/anh/L0x-giong-Eb.png`.

## Kết quả chạy (14/11/2026)
- `cd backend && python3 -m pytest -q`: 1328 passed, 44 skipped (trước: ngưỡng CI 1317). `--min-passed` nâng lên 1328.
- `cd frontend && npm test`: 279 passed. `npm run build`: đạt.
- CHƯA chạy: PostgreSQL (CI sẽ chạy), Docker thật.

## Còn nhắc / cần Phúc quyết
1. Giọng mặc định mỗi bài vẫn là C, vì lời văn và câu hỏi của L02–L04 đã phát hành viết theo C ("Chú ý G7…"). Đổi mặc định sang giọng khác phải sửa chữ trong bài đã duyệt, cần Đạt/Astra duyệt. Đề xuất: chỉ đổi giọng mặc định ở các ví dụ nghe thêm nháp (đã có L04 giọng F).
2. Lời văn cạnh ví dụ vẫn nhắc tên hợp âm giọng C. Khi chọn giọng khác, người học thấy hợp âm mới nhưng đoạn chữ không đổi. Muốn đổi chữ theo giọng thì cần thêm mẫu câu có chỗ trống; mình đề xuất làm ở bước sau nếu thầy yêu cầu.
3. Các hợp âm trong câu hỏi (mastery) vẫn ở giọng C, đúng ADR-006, không đụng.
