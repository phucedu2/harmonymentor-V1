# ADR-013 (đề xuất) · Chế độ Bài hát: cấu trúc đoạn, đường năng lượng, chuyển đoạn

Trạng thái: **Đề xuất 02/11/2026**, chờ **Thắng** duyệt. Nhánh `phuc-music` (Draft PR #18). Phúc đã quyết trong prompt (1A, 2A, 5A, 6A, 7B, 8A–12A) và trả lời 7 câu làm rõ (1A–7A, 02/11). Phúc chọn phương án không thay cho Thắng duyệt.

Sổ tay nghiệp vụ đi kèm: [`docs/backing-track/CAU_TRUC_BAI_HAT.md`](../backing-track/CAU_TRUC_BAI_HAT.md).

## Bối cảnh

ADR-012 cho Harmony Lab một ban nhạc mẫu thật, nhưng chỉ lặp một vòng hợp âm (4–8 ô). Nghe lâu thấy đơn điệu, vì không có Intro, Verse, Chorus và không có chỗ "dâng lên" hay "thả xuống". Học sinh cần nghe vòng hợp âm của mình được sắp thành một bài hát thật, như cách producer dựng backing track.

Ràng buộc giữ nguyên:

- Music Engine tính mọi cao độ.
- `AI_ENABLED=false` vẫn chạy được.
- Chỉ nhịp 4/4.
- Không có audio do AI sinh.
- Người dùng không xuất được WAV hay MIDI.
- Không có giai điệu hát hay lời.

## Quyết định đề xuất

### 1. Mô hình `SongForm` (lưu trong cột JSON `form`)

```json
{
  "length": "short | medium | full",
  "hook": true,
  "modulate": {"enabled": false, "semitones": 1},
  "ending": "auto | fade | ritardando_fermata | big_hit | tag_x3",
  "progressions": {"A": ["C","G","Am","F"], "B": null, "C": null},
  "sections": [
    {"id": "s1", "type": "intro", "label": null, "bars": 4, "progression": "A", "energy": 1,
     "feel": "auto", "hook": true, "transition": "auto", "seed": null}
  ]
}
```

- Có 9 loại đoạn: intro, verse, pre, chorus, post, bridge, breakdown, solo, outro.
- Năng lượng đi từ 1 đến 5 cho mỗi đoạn. Năng lượng tổng (1–3) dời cả đường cong.
- Vòng A luôn lấy từ lưới hợp âm của dự án (QĐ 1A). Vòng B/C để trống thì backend đề xuất vòng hợp lý theo chức năng, kèm lý do, và học sinh nghe thử rồi chấp nhận (QĐ 2A).
- Giới hạn tối đa: 160 ô và 32 đoạn. Số ô của mỗi đoạn được làm tròn theo bội số độ dài vòng (QĐ 7A).
- `sections` không gửi lên thì dùng form mặc định của phong cách, theo độ dài đã chọn.

### 2. API

- `POST /api/v1/composition/song {key, style, seed, energy, bpm?, form}` trả về bản phối dài, công khai giống `/composition/arrangement`.
- Kết quả có:
  - các trường cũ: `bars`, `tracks` (gồm cả `hook`);
  - `sections[]`: mốc phách, năng lượng thiết kế và năng lượng thực, chuyển đoạn, `note_vi` là ghi chú producer;
  - `automation[]`, `tempo_map[]`, `key_map[]`, `fx_events[]`, `surprises[]`, `ending`, `suggestions`.
- `GET /composition/options` có thêm khối `song`, chứa các loại đoạn, chuyển đoạn, kết bài và độ dài.
- `ProjectIn.form` không bắt buộc. Có `form` thì `arrangement_version = SONG_VERSION = 2`. Dự án vòng lặp giữ `ARRANGEMENT_VERSION = 1`, và bản phối vòng lặp không đổi một byte (test so hash sha256).

### 3. Lược đồ: chỉ thêm cột `composition_projects.form`

- Kiểu JSON, cho phép null. Migration `b8d5e6f7a9c1` nối sau `a7c4d5e6f8b9` và dùng `batch_alter_table` để chạy được trên SQLite.
- Dự án cũ có `form = NULL` nên vẫn mở như vòng lặp.
- CSDL dev cũ thiếu cột thì `session.py` báo rõ lệnh nâng cấp thay vì để lỗi 500.

### 4. Luật producer viết thành code, có test

| Luật (sổ tay mục) | Hàm | Test |
|---|---|---|
| Chorus dày hơn Verse ít nhất 1 lớp | `ENERGY_RECIPE`, `_drums_bar`, `_keys_bar` | `test_chorus_day_hon_verse` |
| Verse chừa chỗ cho giọng hát (phím ≤ 3 nốt, không lên cao) | `_keys_bar` | `test_verse_chua_cho_giong` |
| Lặp lại phải khác (Verse 2 ≠ Verse 1, Chorus cuối ≠ Chorus 1) | `add_layer` | `test_verse2_khac_verse1` |
| Ít nhất 8 ô có một thay đổi | crash ô 8, fill ô 7 | `test_moi_8_o_co_thay_doi` |
| Ô trước Chorus thưa hơn (hút hơi) | `thin_bars` | `test_o_truoc_chorus_thua_hon` |
| 1–3 "bất ngờ" theo seed, chỉ ở ranh giới đoạn | `_pick_surprises` | `test_dot_bien_1_den_3_o_ranh_gioi` |
| Hook: phách mạnh là nốt hợp âm, tầm MIDI 72–88, đúng chỗ | `_hook_bars`, `_hook_bar` | `test_hook_*` |
| Chuyển giọng nửa cung hoặc một cung, có 1 ô V7 của giọng mới (QĐ 5A, mặc định tắt) | `_transpose_symbol` | `test_len_giong_*` |
| Fade thật sự nhỏ dần tới cuối bài | sắp xếp `automation` | `test_fade_that_su_nho_dan` |

### 5. Phát ở frontend

- `songSchedule.ts` gồm các hàm thuần, có Vitest:
  - lên lịch theo khối 16 phách, luôn đi trước một khối;
  - `tempoAt`/`beatToSeconds` cho đoạn ritardando;
  - `automationAt` để nhảy tới giữa bài mà mức âm lượng và bộ lọc vẫn đúng.
- Thêm vào `mixer.ts`:
  - bộ lọc thấp tổng, âm lượng đoạn, cửa gửi và đường về reverb để tự động hóa;
  - kênh **Hook** riêng có fader. Limiter vẫn đứng cuối chuỗi.
- `songFx.ts` dựng FX ngay trong code, không thêm mẫu mới:
  - cymbal ngược là mẫu crash CC0 đang dùng, đảo buffer;
  - riser là ồn trắng qua bộ lọc dải quét lên (QĐ 6A).
- Dòng thời gian `SongTimeline.tsx` có:
  - kéo thả khối đoạn, hoặc Alt + mũi tên;
  - đường năng lượng, dấu ▲ ở chỗ bất ngờ, ghi chú producer;
  - phát từ một đoạn, lặp riêng một đoạn, xúc xắc seed cho từng đoạn.

### 6. Thu offline cho bản nghe thử (chỉ nội bộ)

`renderOffline` không còn dùng Tone.Offline với Transport, mà dùng `OfflineAudioContext.suspend()` để tạo giọng theo từng khối 2 giây. Có 2 lý do, cả hai đều đo được ngày 02/11:

1. Tone chạy hết đồng hồ trước rồi mới thu âm thật. Hàm dọn giọng trong `SampledInstrument.sweep()` vì thế hủy nút trước khi nút kịp kêu, nên **mọi bản "sau" của ADR-012 gần như im lặng** (chỉ còn khoảng 2 giây cuối). Bản sửa: khi `context.isOffline` thì không hủy nút.
2. Tạo sẵn 6 000–8 000 giọng làm Chrome xử lý mọi nút ở mỗi khối 128 mẫu, nên thời gian thu tăng theo bình phương (bài 155 giây mất 9 phút). Khi tạo giọng theo khối, bài 58 giây thu trong 37 giây.

Phát trực tiếp trong app không bị ảnh hưởng, vì giọng được xếp lịch trước khoảng 0,1 giây theo thời gian thật.

## Hệ quả

- Ước tính số sự kiện trống: tối đa 4 150 cho bossa Đầy đủ 160 ô, dưới ngưỡng 5 000 (test). Backend dựng một bài trong 7–105 ms.
- Có thêm khoảng 1 000 dòng Python và khoảng 1 200 dòng TS. Không thêm thư viện nào.
- Nhóm cần nâng CSDL dev: `cd backend && alembic -c alembic.ini upgrade head` (sao lưu file `.db` trước).
- Rủi ro: "đạt kỹ thuật" chỉ là số đo LUFS từng đoạn cộng với test. "Đạt tai" phải chờ nhóm nghe mù.

## Chưa làm (ngoài phạm vi, theo prompt)

- Nhịp khác 4/4.
- Xuất WAV/MIDI cho người dùng.
- Giai điệu hát, lời.
- Audio do AI sinh.
- Đổi giọng giữa bài ở đoạn khác điệp khúc cuối.
