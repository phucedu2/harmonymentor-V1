# ADR-012 (đề xuất) · Bộ phối khí và nhạc cụ mẫu

Trạng thái: **Đề xuất 02/11/2026**, chờ **Thắng** duyệt. Nhánh `phuc-music` (Draft PR #18). Phúc đã trả lời 13 câu làm rõ (1A…13A, ngày 02/11). Phúc chọn phương án không thay cho Thắng duyệt. Nguồn Rhodes/clavi: VCSL TX81Z (FM), Phúc chọn trên thẻ quyết định 02/11/2026.

## Bối cảnh

Backing track của Harmony Lab (ADR-010) phát bằng synth Tone.js, nghe như nhạc game 8-bit. Số đo bản cũ trên 36 bản thu: −9,7 đến −11,3 LUFS, đỉnh thật tới +0,3 dBTP, mỗi bản 162–2 190 mẫu chạm trần (vỡ tiếng). Mục tiêu là nghe như ban nhạc thu phòng thu, nhưng vẫn giữ các nguyên tắc sau:

- Music Engine tính mọi cao độ.
- Frontend không tự nghĩ ra nốt.
- Chạy được khi `AI_ENABLED=false`.

## Quyết định đề xuất

### 1. Bộ phối ở backend, frontend chỉ "chơi"

- `POST /api/v1/composition/arrangement {key, bpm, style, chords[], seed, energy}` trả về bản phối đã trải sẵn: nốt MIDI từng nhát cho phím, bass và guitar, cùng sự kiện trống theo mã.
- Gói phong cách nằm ở `backend/app/composition/styles/`, gồm 9 phong cách, `ARRANGEMENT_VERSION = 1`.
- Mọi nốt đi qua `build_chord`/`transpose`/`get_chord_tones` của Engine.
- Màu 7/9/13 chỉ thêm ở lớp phát (QĐ 7A), không thêm loại hợp âm mới vào Engine.
- Frontend (`frontend/src/audio/band/humanize.ts`) chỉ dời thời điểm (tối đa ±30 ms) và lực đánh theo seed, không đổi cao độ.

### 2. Nhạc cụ mẫu thu thật, nhiều lớp lực, round-robin

- Thư viện tự viết, khoảng 400 dòng, chạy trên Tone.js đã có. Không thêm thư viện JS mới.
- Không dùng `Tone.Sampler` vì công cụ này chỉ có một lớp mẫu cho mỗi nốt.
- Mẫu được commit thẳng vào `frontend/public/samples` (QĐ 1A, không dùng LFS): 610 file `.ogg`, 21 MB.
- Mẫu được dựng lại bằng `scripts/samples/build_samples.py`. Script này kiểm cao độ bằng YIN và loại mẫu sai.

| Nhạc cụ | Nguồn | Tác giả | Giấy phép | Lớp lực | Số mẫu | MB |
|---|---|---|---|---|---|---|
| Piano (Yamaha C5) | Salamander Grand Piano V3 | Alexander Holm | CC BY 3.0 | 4 | 100 | 6,85 |
| Electric piano (TX81Z FM) | VCSL | Versilian Studios / Sam Gossner | CC0 1.0 | 3 | 42 | 1,91 |
| Clavi (TX81Z FM) | VCSL | Versilian Studios / Sam Gossner | CC0 1.0 | 3 | 30 | 0,74 |
| Bass điện (Squier Jazz) | Growlybass | Karoryfer Lecolds | CC0 1.0 | 3 | 71 | 2,16 |
| Upright bass (pizz) | Otto Rubner double bass | D. Smolken | CC0 1.0 | 3 | 66 | 1,16 |
| Guitar điện clean (Gretsch) | Black And Green Guitars | Karoryfer Lecolds / Brian Wood | CC0 1.0 | 3 | 120 | 3,74 |
| Guitar chặn tiếng | Black And Green Guitars | Karoryfer Lecolds / Brian Wood | CC0 1.0 | 1 | 28 | 0,26 |
| Trống (16 bộ phận) | Big Rusty Drums | Karoryfer Lecolds | CC0 1.0 | 4 | 133 | 3,05 |
| Bộ gõ (conga, shaker, tambourine, triangle, clap) | VCSL | Versilian Studios / Sam Gossner | CC0 1.0 | 3 | 20 | 0,34 |

Ghi công đầy đủ (repo, commit nguồn) nằm ở `frontend/public/samples/CREDITS.md`. Không có âm thanh do AI tạo.

### 3. Tải lười và dự phòng

- Chỉ tải khi bấm Phát, và chỉ tải các nhạc cụ của phong cách đang chọn.
- Có thanh tiến độ %. File nén được giữ trong Cache Storage `hm-samples-v1`.
- Điện thoại hoặc máy có ≤ 4 GB RAM chỉ dùng `lite_layers` (QĐ 9A).
- Mẫu lỗi (mạng, giải mã) thì tự chuyển sang synth cũ và hiện thông báo. Đã thử chặn toàn bộ `/samples/**`: chế độ chuyển sang `synth`, đỉnh −4,4 dBFS, không im lặng.

### 4. Bàn trộn kiểu phòng thu

- Mỗi kênh đi qua EQ3, Compressor, Panner rồi fader.
- Reverb và delay dùng chung qua send (bus).
- Bus chính gồm glue compressor, limiter −2 dB và bộ cắt mềm.
- Mức nền của mỗi phong cách được cân theo số đo LUFS từng kênh thu solo (`STYLE_TRIM` trong `mixer.ts`).

### 5. Thay đổi schema (cần Thắng duyệt)

Migration `a7c4d5e6f8b9` nối sau `f6a2b3c4d5e7` thêm vào `composition_projects` (QĐ 5A, 13A):

| Cột | Kiểu | Mặc định | Ghi chú |
|---|---|---|---|
| `seed` | INTEGER | 1 | Dự án cũ nhận seed 1 |
| `energy` | INTEGER (API từ chối giá trị ngoài 1–3) | 2 | Dự án cũ nhận năng lượng 2 |
| `mix` | JSON | NULL | Âm lượng và tắt tiếng 4 kênh (`chords`, `bass`, `guitar`, `drums`) |
| `arrangement_version` | INTEGER | 0 | 0 nghĩa là dự án lưu trước bộ phối mới; giao diện báo "bản phối đã đổi" |

Ràng buộc `ck_drum_kind` của `drum_events` được nới từ 3 mã (`kick`/`snare`/`hat`) lên 23 mã ngắn ≤ 8 ký tự (QĐ 6A, giữ kiểu cột). Mã `hat` cũ vẫn hợp lệ. `drum_events` vẫn lưu đầy đủ sự kiện đã trải ra (QĐ 5A). Khi hạ phiên bản (downgrade), migration xóa các sự kiện dùng mã mới trước khi trả ràng buộc cũ.

**Điểm có thể lệch tài liệu 04:** ERD Bảng 8 chỉ có `kick/snare/hat` và không có `seed/energy/mix`. Đây là phần mở rộng cần Thắng ký. `alembic check` trên SQLite báo không lệch model. Phần PostgreSQL chờ CI chạy.

## Hệ quả

- `npm run build` không thêm thư viện. Mẫu âm thanh làm repo nặng thêm 21 MB, file nghe thử trong `docs/backing-track/nghe-thu` thêm 9 MB.
- Hiệu năng đo bằng Chrome headless trên máy ảo (`scripts/backing-track/do_hieu_nang.mjs`):

  | Chỉ số | Kết quả |
  |---|---|
  | Tải lần đầu (pop: piano, bass, guitar, trống, bộ gõ) | 2,5 s |
  | Đổi phong cách (một phần mẫu đã có) | 46–331 ms |
  | CPU luồng chính khi phát | 1,6–3,2 % |
  | Heap JS | 9–16 MB |
  | Lỗi console | 0 |

  CPU của luồng âm thanh (audio thread) chưa đo được trong headless.
- Bản thu mới trên 36 bản: −14,7 đến −19,6 LUFS, đỉnh thật ≤ −0,3 dBTP, **0 mẫu chạm trần**.

## Rủi ro và câu hỏi mở

1. **Safari/iOS cũ không giải mã `.ogg`.** Trên các máy đó app sẽ dùng synth dự phòng. Muốn nghe mẫu thật trên Safari thì cần thêm bộ `.m4a` (khoảng +21 MB).
2. **Jazz chưa lên được 180 BPM**, vì tempo dự án bị chặn ở 60–160 (CHECK của ADR-010). Muốn nới thì cần migration riêng.
3. **DB SQLite dev cũ** (`backend/harmonymentor_dev.db`) cần chạy `alembic upgrade head` hoặc xóa đi rồi tạo lại. Nếu không, lưu dự án sẽ vướng ràng buộc trống cũ.
4. **Rhodes và clavi là mẫu FM (TX81Z)**, không phải Rhodes điện cơ thật. Chưa tìm được bộ Rhodes thật nào có giấy phép CC0/CC BY đủ lớp lực (QĐ 3C: hỏi từng trường hợp).
5. **Claude không nghe được âm thanh.** "Đạt" chỉ có nghĩa là đạt về kỹ thuật và số đo. Chất lượng nghe phải chờ 3 bạn chấm ở trang nghe mù (đích ≥ 4/5, không phong cách nào < 3).
