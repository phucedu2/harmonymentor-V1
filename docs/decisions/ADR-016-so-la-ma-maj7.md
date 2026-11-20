# ADR-016 · Số La Mã hợp âm maj7: chấm nhận cả "Imaj7" và "IM7"

Trạng thái: **Có hiệu lực 04/11/2026**. Phúc giao Claude chọn ("vậy hãy sửa theo bạn nhé", trả lời câu Q-B1 trong báo cáo demo 10/11). Nhánh `ai/demo-1011`.

## Bối cảnh

- Music Engine (`roman.py`) trả `IM7`, `IVM7` cho hợp âm maj7 trên bậc I, IV. Cách này giống MT21C §8.3 ("Add “M7” for a major seventh chord, e.g. IM7").
- Bài L02 (khối L02-B04, L02-B08), L04-B09 và mô tả kỹ năng `roman.major_seventh` dạy `Imaj7`, `IVmaj7`, khớp ký hiệu hợp âm `Cmaj7` dùng khắp khóa học.
- Học sinh gõ đúng như bài dạy (`Imaj7`) sẽ bị chấm sai. Chưa có câu nào hỏi Imaj7/IVmaj7 nên chưa ai gặp, nhưng câu mới về sau sẽ gặp.

## Quyết định

Phần chấm (`grading._normalize_roman`) đổi `maj7` thành `M7` trước khi so, nên `Imaj7` và `IM7` đều đúng. Đầu ra chuẩn của Engine (`roman_numeral(...).numeral`) giữ `IM7`.

Không nhận `I7`: đó là hợp âm bảy át dựng trên bậc I (C–E–G–Bb), khác Cmaj7. Hoa/thường vẫn kiểm như cũ.

## Phương án đã cân nhắc

1. Sửa câu chữ bài L02/L04 sang `IM7`: đổi nội dung đã phát hành, và lệch với ký hiệu hợp âm `Cmaj7` học sinh dùng.
2. Đổi đầu ra Engine sang `Imaj7`: đổi hành vi Engine, ảnh hưởng mọi nơi dùng `numeral`.
3. **Chấm nhận cả hai** (chọn): không đổi nội dung bài, không đổi đầu ra Engine, chỉ nới phần chấm cho một cách viết cùng nghĩa có nguồn.

## Kiểm chứng

`backend/tests/test_adr016_roman_maj7.py`: `Imaj7`/`IM7`/`IVmaj7`/`IVM7` đúng; `I7`, `imaj7`, `IVmaj7` cho Cmaj7, `Vmaj7` cho G7 vẫn sai đúng mã lỗi; đầu ra Engine không đổi. Toàn bộ pytest đạt.
