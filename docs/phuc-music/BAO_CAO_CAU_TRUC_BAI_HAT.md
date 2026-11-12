# Báo cáo: Harmony Lab chế độ Bài hát (cấu trúc đoạn, năng lượng, chuyển đoạn)

Ngày 02/11/2026, nhánh `phuc-music` (Draft PR #18). Quyết định: ADR-013 (đề xuất, chờ Thắng). Sổ tay: `docs/backing-track/CAU_TRUC_BAI_HAT.md`.

Trang nghe có mốc đoạn và nghe mù: https://claude.ai/artifact/N3pQphRxJiQ2SLkyWYcWD9 (bản trong repo: `docs/backing-track/bai-hat/index.html`).

## 1. Đã làm theo từng bước

| Bước | Việc | File chính |
|---|---|---|
| 0 | Khảo sát code ADR-012, sổ tay producer: nguồn [1]–[7], bảng kỹ thuật → hàm, 5 luật vàng → test | `docs/backing-track/CAU_TRUC_BAI_HAT.md` |
| 1 | `SongForm`, `arrange_song`, `POST /api/v1/composition/song`, đề xuất vòng B/C, hook, chuyển giọng, 4 kiểu kết, cột `form` + migration | `backend/app/composition/song.py`, `router.py`, `styles/*.py`, migration `b8d5e6f7a9c1` |
| 2 | Phát bài dài theo khối 16 phách, automation (âm lượng, bộ lọc, reverb), tempo chậm dần, FX cymbal ngược và riser dựng trong code, kênh Hook | `frontend/src/audio/band/{songSchedule,songFx,player,mixer}.ts` |
| 3 | Dòng thời gian: kéo thả đoạn, Alt + mũi tên, đường năng lượng, dấu bất ngờ, ghi chú producer, phát từ đoạn, lặp đoạn, xúc xắc seed từng đoạn | `frontend/src/components/compose/{SongTimeline.tsx,songForm.ts}`, `CompositionLabPage.tsx` |
| 4 | Lưu và mở dự án có `form`. Dự án cũ (`form = NULL`) vẫn mở như vòng lặp | `router.py`, `api.ts` |
| 5 | Thu 10 bài trọn vẹn, đo LUFS từng đoạn, biểu đồ năng lượng, trang nghe mù. Sửa 4 lỗi tìm ra khi thu (mục 3) | `scripts/backing-track/thu_bai_hat.mjs`, `tao_trang_bai_hat.py`, `docs/backing-track/bai-hat/` |

## 2. Lệnh và kết quả

```bash
cd backend && pytest -q            # 592 passed, 21 skipped (21 test PostgreSQL cần TEST_DATABASE_URL)
cd frontend && npm test            # Vitest 258 passed (thêm 18 test song.test.ts)
cd frontend && npm run build       # đạt
# Thu: backend uvicorn :8000 + frontend npm run dev, rồi
node scripts/backing-track/thu_bai_hat.mjs && python3 scripts/backing-track/tao_trang_bai_hat.py
```

Có 130 test backend cho chế độ Bài hát. Chúng kiểm tra:

- Chorus dày hơn Verse ít nhất một lớp.
- Verse chừa chỗ cho giọng hát.
- Verse 2 khác Verse 1.
- Ít nhất 8 ô lại có một thay đổi.
- Ô ngay trước Chorus thưa hơn.
- Có 1–3 chỗ bất ngờ, và chỉ nằm ở ranh giới đoạn.
- Snare dồn có lực tăng dần; drop im lặng thật.
- Hook đặt đúng chỗ; phách mạnh của hook là nốt trong hợp âm.
- Chuyển giọng nửa cung hoặc một cung.
- Fade thật sự nhỏ dần.
- Bản phối vòng lặp v1 giữ nguyên từng byte (so sha256).
- Ước tính sự kiện trống dưới 5 000.

CI: mức `--min-passed` của job SQLite nâng lên 592.

## 3. Lỗi tìm ra khi thu, đã sửa

1. **Mọi bản "sau" ở `docs/backing-track/nghe-thu/` (ADR-012) gần như im lặng.** Chỉ còn khoảng 2 giây cuối có tiếng. Tone.Offline chạy hết đồng hồ trước rồi mới thu âm thật, nên `SampledInstrument.sweep()` hủy giọng trước khi giọng kịp kêu. Số LUFS cũ trông vẫn bình thường vì phép đo EBU R128 bỏ qua đoạn im. Phát trực tiếp trong app không bị ảnh hưởng. Đã sửa (`instruments.ts`) và thu lại 18 cặp trước/sau.
2. **Intro im khoảng 10 giây.** `param.getValueAtTime` trả 0 trong offline, nên bộ lọc mở dần từ 0 Hz. Giờ `mixer.automate` tự tính giá trị xuất phát.
3. **Outro không nhỏ dần.** Điểm "đặt mức đoạn" đứng sau điểm "dốc fade" ở cùng phách nên hủy mất dốc. Backend giờ sắp điểm đặt ngay lên trước. Có test phát lại automation theo thứ tự.
4. **Thu chậm theo bình phương.** Bài 155 giây mất 9 phút, vì tạo sẵn mọi giọng từ đầu. `renderOffline` giờ dùng `OfflineAudioContext.suspend()` để tạo giọng theo từng khối 2 giây: bài 155 giây còn 101 giây.

## 4. Số đo 10 bài (bản Vừa, seed 1, năng lượng tổng 2; ffmpeg ebur128)

| Bài | Ô | Dài | Kết | LUFS cả bài | Chorus − Verse (LU) | Intro | Outro | Đoạn giữa nhỏ nhất | Đỉnh thật (dBTP) | Mẫu vỡ | Thu (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pop | 64 | 2:34 | fade | −16,3 | **2,60** | −31,8 | −24,3 | −18,8 | −1,4 | 0 | 101 |
| ballad | 52 | 3:03 | ritardando + ngân | −17,6 | **2,55** | −28,0 | −25,5 | −20,5 | −1,3 | 0 | 82 |
| rock | 72 | 2:30 | big hit | −17,6 | **3,32** | −22,3 | (không có) | −20,1 | −1,2 | 0 | 88 |
| indie | 64 | 2:18 | fade | −15,4 | **2,85** | −28,0 | −21,6 | −18,1 | −1,4 | 0 | 89 |
| funk | 58 | 2:15 | big hit | −16,8 | **3,23** | −25,2 | −18,4 ⚠ | −18,9 | −1,3 | 0 | 75 |
| jazz | 68 | 2:19 | tag ii–V × 3 | −19,5 | (không có Verse/Chorus) | −23,0 | −20,7 ⚠ | −21,4 | −1,5 | 0 | 67 |
| bossa | 68 | 2:06 | fade | −19,0 | **2,75** | −30,0 | −21,3 | −21,3 | −1,5 | 0 | 74 |
| lofi | 40 | 2:01 | fade | −19,6 | **3,60** | −23,2 | −24,1 | −21,6 | −1,4 | 0 | 41 |
| rnb | 60 | 3:09 | ritardando + ngân | −21,3 | **2,32** | −27,2 | −23,6 | −23,1 | −1,5 | 0 | 80 |
| pop vòng A/B + chuyển giọng | 100 | 4:01 | fade | −16,3 | **2,50** | −31,7 | −21,2 | −18,5 | −1,3 | 0 | 162 |

- **Chorus − Verse:** 9/9 bài có Verse và Chorus nằm trong +2…+4 LU. Lần đo đầu, bài pop ra +7,2 LU. Sau đó đã thu nhỏ chênh dB của `ENERGY_RECIPE` và thêm `chorus_trim_db` riêng cho từng phong cách, đo trên bản Ngắn.
- **Đỉnh thật:** 10/10 bài ≤ −1 dBTP. Lần đầu đo được −0,3 dBTP. Đã hạ trần sau bộ cắt mềm 1,1 dB. Cả 10 bài có 0 mẫu chạm trần.
- **Intro/Outro nhỏ nhất (không tính Breakdown):** 8/10 bài đạt. Hai bài lệch là funk và jazz, đều có kết lớn (big hit, tag ii–V × 3). Đoạn cuối của hai bài này cố ý giữ năng lượng cao để dồn vào nhát kết. Phúc chọn: giữ như vậy, hay hạ năng lượng Outro của funk/jazz xuống 2 để đạt đúng tiêu chí.
- **Biểu đồ năng lượng thiết kế và độ to đo được** có trên trang nghe, mỗi bài một biểu đồ. Dải trên là năng lượng 1–5 theo thiết kế. Dải dưới là đường LUFS ngắn hạn, kèm vạch đồng là LUFS của từng đoạn.

## 5. Giải thích cho nhóm

Giây ghi theo file `docs/backing-track/bai-hat/pop.ogg` (P) và `ballad.ogg` (B). Mở trang nghe, bấm vào khối đoạn để nhảy tới.

**Cấu trúc bài (song form).** Bài pop có thứ tự: Intro → Verse → Pre-Chorus → Chorus → Verse 2 → Pre 2 → Chorus 2 → Bridge → Chorus cuối → Outro. Các mốc trong P: 0:00, 0:10, 0:29, 0:38, 0:58, 1:17, 1:26, 1:46, 2:05, 2:24.

- Verse kể chuyện, Chorus là câu ai cũng nhớ, Bridge đổi màu để Chorus cuối nghe "mới" lại.
- Code: `default_form()` và khối `PACK["song"]["forms"]` trong `backend/app/composition/styles/pop.py`.
- Học sinh kéo thả khối đoạn trong `SongTimeline.tsx`.

**Đường năng lượng (energy curve).** Mỗi đoạn có mức 1–5. Pop đi theo dãy 1 → 2 → 3 → 4 → 2 → 3 → 4 → 3 → 5 → 2: sóng lên dần, mỗi lần dâng cao hơn lần trước.

- Mức năng lượng quyết định 5 thứ:
  - mẫu trống mức mấy;
  - bass chơi dày hay thưa;
  - guitar vào hay nghỉ;
  - phím mấy nốt;
  - âm lượng đoạn.
- Code: `ENERGY_RECIPE` trong `song.py`.
- Nghe P 0:38 (Chorus 1, mức 4) rồi 0:58 (Verse 2, mức 2): ban nhạc thưa hẳn lại để chừa chỗ cho giọng hát.

**Build và drop.**

- *Build* là dồn trước khi bùng nổ. Ví dụ là snare dồn: 8 nốt móc đơn, rồi 8 nốt móc kép, rồi 16 nốt móc ba, lực tăng dần, hi-hat tắt. Nghe ở P 0:34–0:38 (2 ô cuối Pre-Chorus 1). Code: `_snare_build()`.
- *Drop* là im đột ngột 2 phách, kể cả tiếng vang reverb, rồi Chorus vào. Nghe ở B 0:39–0:41. Code: nhánh `drop_bar` trong `arrange_song()` và điểm automation `reverb_return`.
- Cymbal ngược (P 1:25) và riser (bài rock 1:10) cũng là kiểu build, dựng trong `frontend/src/audio/band/songFx.ts`.

**Half-time.** Trống vẫn giữ tempo cũ, nhưng snare chuyển từ phách 2 và 4 sang chỉ phách 3. Nghe như chậm đi một nửa, nặng và rộng hơn. Nghe P 1:46 (Bridge, cũng là một chỗ bất ngờ theo seed). Code: `_half_time()` trong `song.py`.

**Pedal point.** Trong Pre-Chorus, bass giữ nguyên một nốt là bậc V của giọng (nốt G ở giọng C), trong khi hợp âm phía trên vẫn đổi. Hai lớp "cọ" vào nhau tạo căng, khiến tai mong Chorus về. Nghe P 0:29–0:38: bass đứng yên ở G. Code: biến `pedal` trong `arrange_song()` truyền vào `_bass_bar()`.

**Automation.** Đây là các núm được vặn tự động theo thời gian, giống producer kéo fader trong lúc mix.

- Intro mở dần bộ lọc thấp từ 2,5 kHz lên 20 kHz (P 0:00–0:10, nghe từ "đục" sang "sáng").
- Mỗi đoạn có mức âm lượng riêng.
- Pre-Chorus dâng âm lượng dần.
- Outro nhỏ dần về −40 dB (P 2:24–2:34).
- Bridge có reverb dày hơn.
- Code: backend sinh danh sách `automation` (mục 10 trong `arrange_song()`). Frontend áp qua `BandMixer.automate()` trong `mixer.ts`, và `automationAt()` trong `songSchedule.ts` để nhảy vào giữa bài mà mức vẫn đúng.

## 6. Chưa xong và rủi ro

- **Chưa có người nghe.** Claude không nghe được âm thanh. "Đạt kỹ thuật" là số đo ở mục 4 cộng với test. "Đạt tai" phải chờ Phúc, Thắng và Đạt chấm ở tab Nghe mù, với đích ≥ 4/5 điểm và đoán đúng Chorus ≥ 80%. Thắng và Đạt cần được Phúc chia sẻ trang với quyền "Có thể tương tác" thì mới lưu được điểm.
- **Phòng nghe mù cũ (ADR-012) cần chấm lại** trên bản thu mới, vì bản cũ gần như im lặng.
- ADR-013 chờ Thắng duyệt: thêm cột `form` và API mới.
- Chưa kiểm tra phát trực tiếp (realtime) bằng tai trên máy thật. Bản thu offline và bản phát trực tiếp dùng chung lịch nốt và automation, nhưng khác đường xếp lịch: Transport khi phát trực tiếp, `suspend()` khi thu.
- Không làm theo prompt: nhịp khác 4/4, xuất WAV/MIDI, giai điệu hát, audio do AI sinh.

## 7. Nâng CSDL trên máy Phúc

Code mới thêm cột `composition_projects.form`. Ở `D:\aptech\Music Tutor v1\hm-phuc-music`, chạy:

```powershell
cd backend
copy harmonymentor_dev.db harmonymentor_dev.db.bak   # sao lưu trước
alembic -c alembic.ini upgrade head                  # a7c4d5e6f8b9 → b8d5e6f7a9c1
```

Nếu quên bước này, app sẽ báo rõ lệnh cần chạy thay vì lỗi 500.
