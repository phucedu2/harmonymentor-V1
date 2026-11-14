# Báo cáo: backing track "ban nhạc thật" (Bước 0 → 5)

Ngày 02/11/2026, nhánh `phuc-music` (Draft PR #18). Quyết định đi kèm: [ADR-012](../decisions/ADR-012-bo-phoi-khi-va-nhac-cu-mau.md) (đề xuất, chờ Thắng duyệt). Luật từng phong cách: [PHONG_CACH.md](../backing-track/PHONG_CACH.md).

> **Đính chính 02/11/2026 (chiều):** các bản "sau" thu lần đầu trong `docs/backing-track/nghe-thu/` gần như im lặng, chỉ có khoảng 2 giây cuối. Lỗi nằm ở công cụ thu offline, không ở phát trực tiếp. Chi tiết ở `BAO_CAO_CAU_TRUC_BAI_HAT.md` mục 3. Đã thu lại 18 cặp và cập nhật trang nghe mù. Số đo mới của bản "sau": −15,7…−20,6 LUFS, đỉnh thật ≤ −1,2 dBTP, 0 mẫu vỡ. Các số LUFS bản "sau" ở dưới là của lần thu lỗi, xem `nghe-thu/ket-qua-thu.json` để lấy số đúng.

**Trạng thái: xong về kỹ thuật và đã đo, CHƯA có người nghe.** Claude không nghe được âm thanh. Bản phối có "nghe như ban nhạc phòng thu" hay không, phải chờ 3 bạn chấm ở trang nghe mù.

## 1. Đã làm gì

| Bước | Nội dung | File chính |
|---|---|---|
| 0 | 610 mẫu thu thật (CC0, CC BY 3.0), kiểm cao độ bằng YIN, ghi công đầy đủ | `scripts/samples/build_samples.py`, `frontend/public/samples/` (manifest + CREDITS) |
| 1 | Nhạc cụ mẫu nhiều lớp lực, round-robin, hi-hat đóng chặn hi-hat mở, giới hạn 48 giọng, synth dự phòng | `frontend/src/audio/band/instruments.ts`, `samples.ts` |
| 2 | 9 gói phong cách, API `POST /api/v1/composition/arrangement`, dẫn giọng, walking bass, fill, crash, tô màu qua Engine | `backend/app/composition/arranger.py`, `styles/*.py`, `router.py` |
| 3 | Humanize theo seed: σ riêng từng nhạc cụ, pocket, swing, rải hợp âm, quạt guitar, chặn ±30 ms | `frontend/src/audio/band/humanize.ts` |
| 4 | Năng lượng 1–3, kênh Guitar (giữ tên kênh "Hợp âm" cho phím), fader từng kênh, Lặp lại, Tạo bản khác, lưu seed/energy/mix, migration `a7c4d5e6f8b9` | `CompositionLabPage.tsx`, `mixer.ts`, `backend/migrations/versions/20261102_pm_composition_arrangement.py` |
| 5 | Thu 9 phong cách × 2 vòng trước/sau, đo độ to/đỉnh/vỡ tiếng, đo hiệu năng, trang nghe mù | `scripts/backing-track/*`, `docs/backing-track/nghe-thu/` |

Trong lúc làm, đã sửa 2 lỗi tự gây ra:

1. **Bản thu offline im lặng hoàn toàn.** Nguyên nhân: gọi `dispose()` trong `onended`. Chia nhỏ từng bước (bisect) mới thấy: kết hợp `stop()` với `dispose` trong `onended` thì RMS = 0, còn từng bước riêng lẻ vẫn kêu. Cách sửa: dọn giọng trễ theo thời điểm kết thúc đã biết.
2. **Cao độ lệch.** Lệch cent trong manifest bị tính như nửa cung. Cách sửa: chia cho 100.

## 2. Số đo (chạy thật, 02/11/2026)

Lệnh: `node scripts/backing-track/thu_nghe_thu.mjs --wav-dir /tmp/wav`. Kết quả nằm ở `docs/backing-track/nghe-thu/ket-qua-thu.json`. Mỗi bản dài 32 giây. Độ to đo bằng `ffmpeg ebur128`.

| Phong cách | Vòng | Trước: LUFS / đỉnh dBTP / mẫu vỡ | Sau: LUFS / đỉnh dBTP / mẫu vỡ |
|---|---|---|---|
| Pop | C–G–Am–F | −10,5 / +0,1 / 1 028 | −15,9 / −0,3 / 0 |
| Pop | Dm7–G7–Cmaj7–A7 | −10,1 / +0,1 / 1 554 | −15,0 / −0,3 / 0 |
| Ballad | C–G–Am–F | −11,3 / 0,0 / 418 | −17,3 / −0,5 / 0 |
| Ballad | Dm7–G7–Cmaj7–A7 | −11,0 / 0,0 / 630 | −15,9 / −0,5 / 0 |
| Bossa | C–G–Am–F | −10,0 / +0,1 / 1 078 | −19,1 / −2,9 / 0 |
| Bossa | Dm7–G7–Cmaj7–A7 | −9,7 / +0,1 / 2 190 | −19,3 / −2,4 / 0 |
| Lo-fi | C–G–Am–F | −11,1 / 0,0 / 162 | −19,2 / −0,3 / 0 |
| Lo-fi | Dm7–G7–Cmaj7–A7 | −11,0 / 0,0 / 910 | −19,6 / −0,3 / 0 |
| Jazz* | C–G–Am–F | −10,6 / 0,0 / 306 | −15,6 / −0,7 / 0 |
| Jazz* | Dm7–G7–Cmaj7–A7 | −10,2 / +0,3 / 1 280 | −14,7 / −0,6 / 0 |
| Rock* | C–G–Am–F | −10,3 / +0,1 / 1 084 | −18,9 / −0,3 / 0 |
| Rock* | Dm7–G7–Cmaj7–A7 | −10,0 / +0,1 / 1 426 | −18,5 / −0,3 / 0 |
| Indie* | C–G–Am–F | −10,3 / 0,0 / 794 | −16,6 / −0,3 / 0 |
| Indie* | Dm7–G7–Cmaj7–A7 | −9,9 / +0,1 / 1 962 | −15,5 / −0,4 / 0 |
| Funk* | C–G–Am–F | −10,5 / +0,1 / 596 | −17,9 / −0,3 / 0 |
| Funk* | Dm7–G7–Cmaj7–A7 | −10,4 / +0,1 / 1 018 | −18,5 / −0,4 / 0 |
| R&B* | C–G–Am–F | −11,2 / 0,0 / 518 | −18,4 / −0,7 / 0 |
| R&B* | Dm7–G7–Cmaj7–A7 | −11,0 / 0,0 / 916 | −18,7 / −0,3 / 0 |

\* Bản cũ không có phong cách này. Cột "Trước" dùng phong cách cũ gần nhất: jazz và R&B so với lo-fi cũ; rock, indie và funk so với pop cũ.

"Mẫu vỡ" là số mẫu âm thanh chạm trần 16-bit, tức tiếng bị rè. Bản cũ to hơn vì nó bị vỡ. Vì vậy trang nghe mù chỉnh cả hai take về cùng −20 LUFS trước khi phát, để bản to hơn không được lợi.

Hiệu năng phát trực tiếp đo bằng `node scripts/backing-track/do_hieu_nang.mjs` (Chrome headless trên máy ảo, năng lượng 3):

| Phong cách | Tải trước khi phát | CPU luồng chính | Heap JS |
|---|---|---|---|
| Pop (tải lần đầu, chưa có cache) | 2 532 ms | 2,0 % | 13 MB |
| Jazz | 331 ms | 1,6 % | 16 MB |
| Rock | 46 ms | 3,2 % | 9 MB |
| Funk | 166 ms | 3,0 % | 10 MB |

- Lỗi console: 0.
- Thử chặn toàn bộ `/samples/**`: app chuyển sang synth, đỉnh −4,4 dBFS, vẫn có tiếng.
- Chưa đo: CPU của luồng âm thanh, và máy thật (điện thoại, laptop yếu).

Test:

| Bộ test | Kết quả |
|---|---|
| `pytest -q` | 459 passed + 21 skipped (21 test PostgreSQL chạy trên CI) |
| `npm test` | 240 passed |
| `npm run build` | Đạt, không thêm thư viện JS |
| `alembic upgrade head && alembic check` (SQLite) | "No new upgrade operations detected" |

## 3. Cách nghe và chấm

- Trên claude.ai: trang **Phòng nghe mù** (link trong PR #18). Mỗi bạn chấm 18 cặp take, mỗi take 3 tiêu chí × 1–5 điểm. Điểm được lưu theo tài khoản, người này không thấy điểm người kia. Chủ trang (Phúc) thấy bảng tổng hợp.
- Ngoài claude.ai: mở `docs/backing-track/nghe-thu/index.html` bằng trình duyệt. Điểm lưu trên máy, bấm "Chép kết quả (JSON)" rồi gửi lại.
- Đích của nhóm: bản mới trung bình ≥ 4/5, không phong cách nào dưới 3.

## 4. Giải thích cho nhóm

### Sampler (máy phát mẫu)

Synth tạo tiếng bằng công thức (sóng tam giác, sóng vuông), nên nghe "điện tử". Sampler phát lại bản thu thật của nhạc cụ. Ta không thu đủ 88 phím, mà thu cách nhau 3 nửa cung, rồi phát nhanh hoặc chậm hơn để ra nốt ở giữa.

Ví dụ: muốn nốt D4 (62) mà gần nhất chỉ có mẫu C4 (60), thì phát mẫu C4 nhanh hơn 2^(2/12) ≈ 1,122 lần. Code ở `instruments.ts`, dòng `const rate = … 2 ** ((hit.midi - zone.midi - zone.cents / 100) / 12)`. `zone.cents` là độ lệch nhỏ đo được khi kiểm cao độ mẫu, chia 100 vì 100 cent = 1 nửa cung (đây chính là lỗi đã sửa).

### Velocity layer (lớp lực)

Đánh piano mạnh không chỉ to hơn mà còn sáng và "gắt" hơn, vì búa đập mạnh làm dây rung nhiều họa âm cao. Nên piano có 4 bản thu cho mỗi nốt: rất nhẹ, nhẹ, vừa, mạnh.

`layerFor(vel)` (`instruments.ts` dòng 45) chia lực 0–1 thành 4 khoảng:

| Lực | Lớp | Âm lượng thêm |
|---|---|---|
| 0,2 | Lớp 0 | Không |
| 0,9 | Lớp 3 | Chỉnh thêm trong khoảng 0,55–1 |

Chỉnh âm lượng trong lớp để hai lực gần nhau không nhảy bậc.

### Round-robin (xoay vòng mẫu)

Hai nhát snare liền nhau mà dùng cùng một file thì nghe như "súng máy", vì tai nhận ra hai âm giống hệt nhau. Bộ trống thu mỗi lực 2–4 lần khác nhau, và `pick()` (dòng 52) xoay vòng: nhát 1 dùng `rr1`, nhát 2 dùng `rr2`, nhát 3 quay lại `rr1`. Test `snare/hat có round-robin` khóa điều này.

### Voice leading (dẫn giọng)

Khi đổi hợp âm, người chơi giỏi giữ ngón ở nốt chung và di chuyển ít nhất. `lead()` (`arranger.py` dòng 140) thử mọi thế bấm trong vùng cho phép, rồi chọn thế có tổng quãng di chuyển nhỏ nhất (`movement`, dòng 125).

Ví dụ Pop C–G–Am–F thật từ code:

| Hợp âm | Thế bấm (MIDI) | Tên nốt | Di chuyển so với hợp âm trước |
|---|---|---|---|
| C | [64, 67, 72] | E4 G4 C5 | |
| G | [62, 67, 71] | D4 G4 B4 | 3 nửa cung (G4 đứng yên) |
| Am | [64, 69, 72] | E4 A4 C5 | 5 |
| F | [65, 69, 72] | F4 A4 C5 | 1 |

Nếu đánh cả bốn hợp âm ở thế gốc (C4-E4-G4 rồi G4-B4-D5 …), tay phải nhảy tới 21 nửa cung. Test `dẫn giọng: đổi hợp âm pop đi ≤ 7 nửa cung` khóa điều này.

Walking bass trong jazz dùng cùng ý tưởng. Ví dụ Dm7–G7–Cmaj7–A7, vòng 2:

- Ô Dm7: D2 E2 F2 G#2. G#2 là nốt dẫn nửa cung từ trên xuống G2.
- Ô G7: bắt đầu từ G2.

Nốt dẫn lấy qua `transpose` của Music Engine (`approach`, dòng 198). Frontend không tự tính nốt nào.

### Humanize (làm cho "người" hơn)

Máy đánh đúng tuyệt đối từng mili giây, nên nghe cứng. Người chơi thật lệch vài mili giây, và lệch có chủ ý: tay trống lo-fi đánh snare trễ để nhịp "lười". `humanize()` (`humanize.ts` dòng 73) cộng hai thứ:

1. **Pocket:** độ trễ cố ý theo phong cách, ví dụ lo-fi `snare: 24` ms.
2. **Nhiễu ngẫu nhiên** theo phân phối chuẩn (`gaussian`) với σ riêng từng nhạc cụ, ví dụ trống 5 ms, guitar 12 ms.

Tổng lệch bị chặn trong ±30 ms (`MAX_OFFSET_SEC`). Nhiễu sinh từ `rng(seed)` (mulberry32), nên cùng seed thì ra đúng bản cũ. Nút "Tạo bản khác" chỉ đổi seed.

Piano còn rải hợp âm từ nốt trầm lên (`roll_ms`). Guitar quạt xuống thì dây trầm kêu trước, quạt lên thì dây cao kêu trước và nhẹ hơn.

### Bus và send (đường gửi hiệu ứng)

Nếu mỗi nhạc cụ có một reverb riêng, CPU tốn gấp 4 và bốn nhạc cụ nghe như đứng ở bốn phòng khác nhau. Phòng thu làm khác: chỉ có **một** reverb trên một đường riêng (bus), mỗi kênh "gửi" (send) vào một lượng.

Trong `mixer.ts` (dòng 13), `SEND = { chords: 1, bass: 0.12, guitar: 0.9, drums: 0.75 }`. Bass gần như khô, vì reverb trên tiếng trầm làm mix đục.

Bus chính có thêm:

- glue compressor (dán các kênh lại với nhau);
- limiter −2 dB;
- bộ cắt mềm `softClip`, để không bao giờ chạm trần (0 mẫu vỡ trên 36 bản thu).

## 5. Rủi ro và câu hỏi cho nhóm

1. **Thắng cần duyệt ADR-012:** 4 cột mới trong `composition_projects`, nới `ck_drum_kind` lên 23 mã. Cả hai lệch ERD Bảng 8 của tài liệu 04.
2. **Rhodes và clavi đang là mẫu FM (TX81Z) của VCSL**, không phải Rhodes thật. Phúc đã chọn nguồn này (02/11).
3. **Safari/iOS cũ** không giải mã `.ogg`, nên sẽ nghe synth dự phòng.
4. **Jazz bị chặn ở 160 BPM** do giới hạn tempo của dự án.
5. **DB SQLite dev cũ** phải `alembic upgrade head` (hoặc xóa đi rồi tạo lại) trước khi lưu dự án.
6. **Repo nặng thêm khoảng 30 MB** (mẫu 21 MB + file nghe thử 9 MB), commit thẳng không qua LFS theo QĐ 1A.
