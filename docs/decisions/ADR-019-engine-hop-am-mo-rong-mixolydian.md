# ADR-019 · Music Engine: hợp âm mở rộng (maj9, m9, 9, 13) và âm giai mixolydian

Trạng thái: **Có hiệu lực 11/11/2026**. Phúc báo Thắng chốt "làm cả hai" (hợp âm mở rộng và mixolydian) để mở bài L07. Nhánh `ai/l07-engine-mo-rong`.

## Bối cảnh

- L07 (Jazz Tensions, Modes và Chord-Scale Context) nói về nốt 9, 11, 13 và về mode (Dorian, Mixolydian, Ionian). Engine chỉ có hợp âm đến bảy và các âm giai trưởng, thứ, Dorian, nên bài bị khóa ("Sắp có") từ 09/11 chờ quyết định này.
- Nguyên tắc 1: Engine là nguồn sự thật về nốt. Muốn AI Tutor và bài tập nói về Cmaj9, G13, G Mixolydian thì Engine phải dựng được, không để LLM tự tính.

## Quyết định

Thêm dữ liệu, không đổi cách tính hiện có:

- Loại hợp âm (`chord.py`): `maj9` (1 3 5 7 9), `m9` (1 b3 5 b7 9), `9` (1 3 5 b7 9), `13` (1 3 5 b7 9 13, bỏ nốt 11 như quy ước thường dùng trên hợp âm bảy át). Ví dụ Cmaj9 = C E G B D; G13 = G B D F A E.
- Bí danh nhập: `maj9`/`M9`/`Δ9`, `m9`/`min9`/`-9`, `9`, `13`.
- Âm giai (`scale.py`): `mixolydian` = 2 2 1 2 2 1 2 (trưởng với bậc 7 thứ).
- Nốt 9 và 13 là tension, không tạo thể đảo: bass là nốt 9 hay 13 thì `inversion = None`. `chord_member` trả "ninth", "thirteenth".
- Chưa làm: hợp âm 11 (C11, m11), add9, 7#9, 7b9, alt. Câu hỏi về các hợp âm này vẫn đi luồng B "Engine chưa biết", không đoán.

## Trạng thái nguồn

Hai claim mới `MUS-EXT-001` và `MUS-SCALE-009` ở trạng thái `pending` (chưa duyệt, vị trí trang OMT chưa khóa), nên các loại hợp âm mới gắn `verified=False` như sus2, sus4. Tên nốt vẫn suy từ quãng, tất định. Người duyệt (Đạt, Thắng) khóa claim sau.

## Ảnh hưởng

- `identify_chord` có thêm 4 loại để thử; các hợp âm ba và bảy cũ nhận diện y như trước (có test).
- L07 mở cho người học và vào kho AI Tutor. L07-Q06 là câu tự luận chấm từ khóa, trái quy tắc bài 1–4 nên để `draft` chờ Đạt viết lại thành câu chọn (giống L08-Q06).
- Không bài nào đang phát hành đổi nội dung hay phiên bản câu hỏi (ADR-006).

## Kiểm chứng

`backend/tests/test_engine_extended_l07.py`: nốt của Cmaj9, G13, G9, Dm9, Dbmaj9, F#13, Ebm9; bí danh; thể đảo và vai trò nốt 9, 13; nhận diện ngược; hợp âm cũ không đổi; mixolydian ở G và Eb; claim còn `pending`.
