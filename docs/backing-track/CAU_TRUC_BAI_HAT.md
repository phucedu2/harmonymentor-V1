# Sổ tay producer: dựng backing track thành một bài hát

Ngày 02/11/2026, nhánh `phuc-music`, đi kèm ADR-013 (đề xuất, chờ Thắng duyệt). Sổ tay này nối tiếp
`PHONG_CACH.md` (luật chơi của từng phong cách): ở đó là "chơi một ô nhịp thế nào", ở đây là "xếp 60–120 ô nhịp
thành một bài có đầu có đuôi".

Code thực hiện sổ tay này:

| Phần | File |
|---|---|
| Mô hình bài (đoạn, chuyển đoạn, kết bài) và khuôn theo phong cách | `backend/app/composition/song_forms.py` |
| Công thức năng lượng 1–5, luật thêm/bớt, đột biến, hook, ghi chú producer | `backend/app/composition/song.py` |
| Phát bài dài theo khối, tự động hóa (automation), FX chuyển đoạn | `frontend/src/audio/band/player.ts`, `songFx.ts`, `mixer.ts` |
| Dòng thời gian "Cấu trúc bài" | `frontend/src/components/compose/SongTimeline.tsx` |

Nguồn lý thuyết dùng chung (đánh số để trích ở dưới):

1. Bobby Owsinski, *The Music Producer's Handbook* (Hal Leonard, 2010; bản 2, 2016): chương về sắp xếp (arrangement),
   các "thành phần" của bản phối (nền, đệm, nhịp, câu dẫn, fill) và luật "luôn có gì đó thay đổi".
2. Mike Senior, *Mixing Secrets for the Small Studio* (Focal Press, 2011): phần dựng độ to theo đoạn, tương phản
   trước cao trào, tự động hóa âm lượng và reverb.
3. Jimmy Kachulis, *The Songwriter's Workshop: Harmony* (Berklee Press, 2005): chức năng hòa âm của từng đoạn,
   Pre-Chorus kết trên V/IV, Bridge bắt đầu ở hợp âm khác giọng chủ.
4. Jack Perricone, *Melody in Songwriting* (Berklee Press, 2000): hook, câu hỏi–đáp, độ dài câu 4/8 ô.
5. Pat Pattison, *Writing Better Lyrics* (Writer's Digest, bản 2, 2009): vai trò kể chuyện của Verse,
   "đích đến" của Chorus, tương phản của Bridge.
6. Mark Levine, *The Jazz Theory Book* (Sher Music, 1995): khuôn AABA, head–solo–head, tag ending ii–V lặp lại.
7. Mark Harrison, *The Pop Piano Book* (Hal Leonard, 1997): đệm piano theo đoạn, tay trái quãng tám ở cao trào.

Nhóm chỉ học **quy ước** của thể loại (chung cho hàng nghìn bài). Không chép bản ghi, giai điệu hay lời bài nào.

---

## A. Các loại đoạn và vai trò

| Đoạn | Mã | Vai trò | Độ dài thường gặp | Năng lượng (1–5) | Nguồn |
|---|---|---|---|---|---|
| Intro | `intro` | Giới thiệu "màu" bài, 1–2 nhạc cụ hoặc hook | 2–8 ô | 1–2 | [1] |
| Verse | `verse` | Kể chuyện, chừa chỗ cho giọng hát: thưa, tầm trung–thấp | 8–16 ô | 2 (Verse 2: thêm 1 lớp) | [1], [5] |
| Pre-Chorus | `pre` | Dồn căng: trống build, bass giữ nốt (pedal) | 4–8 ô | 3 | [3] |
| Chorus | `chorus` | Cao trào: đủ ban nhạc, tầm rộng, crash đầu đoạn | 8–16 ô | 4 (Chorus cuối 5) | [1], [2] |
| Post-Chorus / Tag | `post` | Lặp hook, hạ nhẹ trước Verse sau | 2–4 ô | 3 | [4] |
| Bridge | `bridge` | Tương phản: vòng khác, half-time hoặc rút trống, reverb dài | 4–8 ô | 2–3 | [3], [5] |
| Breakdown | `breakdown` | Rút gần hết (chỉ phím hoặc chỉ bass + trống) rồi bùng lại | 2–4 ô | 1–2 | [1] |
| Solo / Instrumental | `solo` | Ban nhạc đệm đầy hơn để học sinh tự ứng tác (QĐ 5A của bài này) | 8–16 ô | 3–4 | [6] |
| Outro | `outro` | Kết: nhỏ dần, hoặc tag + nốt ngân (fermata) + chậm dần | 2–8 ô | 2 → 1 | [1], [6] |

## B. Khuôn cấu trúc theo phong cách

Khuôn ghi theo độ dài **Vừa**. Ngắn = Intro · Verse · Chorus · Outro. Đầy đủ thêm Verse 3 hoặc Solo/Breakdown,
Chorus cuối nhân đôi. Số trong ngoặc là số ô *trước khi làm tròn*: theo QĐ 7A, số ô mỗi đoạn tự làm tròn về bội số
độ dài vòng hợp âm mà đoạn trỏ tới (vòng 6 ô thì đoạn 8 ô thành 6 hoặc 12). Đoạn ngắn (Intro, Pre, Tag, Breakdown,
Outro) ngắn hơn một vòng thì giữ nguyên và chỉ lấy các ô đầu của vòng. Khuôn đầy đủ của cả 3 độ dài nằm trong
`song_forms.py` (`TEMPLATES`).

| Phong cách | Khuôn "Vừa" | Kết bài |
|---|---|---|
| Pop | Intro(4) · Verse(8) · Pre(4) · Chorus(8) · Verse(8) · Pre(4) · Chorus(8) · Bridge(8) · Chorus cuối(8) · Outro(4) | nhỏ dần |
| Ballad | Intro piano(4) · Verse(8) · Chorus(8) · Verse(8) · Chorus(8) · Bridge(4) · Chorus cuối(8) · Outro(4) | chậm dần + ngân |
| Rock | Intro riff(4) · Verse(8) · Pre(4) · Chorus(8) · Verse(8) · Pre(4) · Chorus(8) · Solo(8) · Breakdown(4) · Chorus(8) · Chorus(8) | một nhát đồng loạt |
| Indie | Intro(8) · Verse(8) · Chorus(8) · Verse(8) · Chorus(8) · Bridge build(8) · Chorus(8) · Outro(8) | nhỏ dần |
| Jazz | Intro(4) · Head A A B A · Solo(2 vòng) · Head(A A B A) · Outro tag ii–V × 3 | tag ii–V × 3 |
| Bossa | Intro(4) · A(8) · B(8) · A(8) · Instrumental(8) · A(8) · Outro(8) | nhỏ dần |
| Lo-fi | Intro lọc thấp(4) · A(8) · B(8) · A thêm lớp(8) · B(8) · Outro lọc dần(4) | nhỏ dần, còn tiếng đĩa |
| Funk | Intro trống(2) · Vamp A(8) · Vamp B(8) · Breakdown bass+trống(4) · Vamp A(8) · Outro stop-time(4) | một nhát đồng loạt |
| R&B | Intro Rhodes(4) · Verse(8) · Pre(4) · Chorus(8) · Verse(8) · Pre(4) · Chorus(8) · Bridge(4) · Chorus(8) · Outro(4) | chậm dần + ngân |

Vòng hợp âm (QĐ 1A): mỗi đoạn trỏ tới một vòng A/B/C. Mặc định Verse/Intro/Outro = A, Chorus = B, Bridge = C.
Vòng nào trống thì đoạn **tạm dùng vòng A** (QĐ 3A) và giao diện hiện thẻ gợi ý vòng B/C để nghe thử rồi mới
chấp nhận. Rất nhiều bài pop dùng chung 4 hợp âm cho cả bài; tương phản lúc đó đến từ phối khí [1].

## C. Hộp đồ nghề chuyển đoạn và "đột biến"

| Kỹ thuật | Mã | Làm gì | Vì sao nghe hiệu quả | Code |
|---|---|---|---|---|
| Fill nhỏ / lớn | `fill_small`, `fill_big` | Tom/snare ở ô cuối đoạn | Báo trước "sắp sang đoạn mới" như dấu phẩy, dấu chấm | `_transition_bar` |
| Snare build | `snare_build` | 2 ô cuối: móc đơn → móc kép → móc ba (32nd) ở 2 phách cuối, lực tăng dần | Mật độ và lực tăng đều làm tai "chờ" cú nổ [2] | `_snare_build` |
| Drop | `drop_bar` | 2 phách cuối đoạn im hẳn, cắt cả đuôi reverb | Tương phản trước cao trào: im lặng làm Chorus nổ to hơn thực tế [2] | `_silence_window`, automation `reverb_return` |
| Stop-time | `stop_time` | Cả ban đánh 1 nhát ở phách 1 rồi nghỉ hết ô | Chỗ trống cho câu hát "đinh" | `_stop_bar` |
| Pickup | `pickup` | Snare + bass đi lên ở phách 4 | Nối mềm, không ồn | `_transition_bar` |
| Riser | `riser` | Tiếng ồn trắng qua bộ lọc quét lên trong 2 ô (QĐ 6A) | Tai nghe "dâng lên" | `songFx.ts` `riser` |
| Reverse cymbal | `reverse_cymbal` | Mẫu crash CC0 đảo ngược, kết đúng phách 1 đoạn mới | Hút người nghe vào đoạn mới | `songFx.ts` `reverseCymbal` |
| Crash + kick đồng loạt | (tự động) | Phách 1 mỗi đoạn có năng lượng ≥ 3 | "Mở cửa" đoạn mới | `_section_start_hits` |
| Hat đóng → mở/ride | (công thức năng lượng) | Verse hat đóng, Chorus ride/hat mở | Cymbal mở kéo dài nốt, lấp đầy dải cao [1] | `_drums_for` |
| Side-stick → snare | (công thức năng lượng) | Verse side-stick, Chorus snare thật | Side-stick "khô" chừa chỗ cho giọng | `_drums_for` |
| Half-time | `feel: half` | Snare chỉ ở phách 3, kick phách 1 | Cảm giác chậm một nửa mà tempo không đổi, hợp với Bridge | `_half_time` |
| Double-time | `feel: double` | Kick móc đơn xuôi, snare móc đơn ngược | Chorus cuối Rock "chạy" gấp đôi | `_double_time` |
| Pedal point | (Pre-Chorus) | Bass giữ nốt bậc V trong khi hợp âm đổi | Nốt bass không chịu về chủ → căng, đòi giải quyết [3] | `_pedal_bass` |
| Bass nghỉ trước drop | (drop) | Bass dừng trước cửa sổ im lặng | Đáy tần số biến mất làm drop "hụt chân" hơn | `_silence_window` |
| Lên giọng | `modulate` | Chorus cuối lên nửa cung hoặc 1 cung, ô trước là át (V7) của giọng mới (QĐ 5A, tắt mặc định) | Cùng giai điệu nhưng cao hơn → cảm giác "lên đỉnh" | `_modulate` |
| Tag ending | `tag_x3` | Jazz: lặp ii–V 3 lần rồi về I ngân | Kết kiểu jazz câu lạc bộ [6] | `_tag_ending` |
| Chậm dần + ngân | `ritardando_fermata` | 2 ô cuối giảm tempo 15%, hợp âm I ngân 6 phách | Kết như người chơi thật thở ra | `tempo_map`, `_fermata` |
| Nhỏ dần | `fade` | 4 ô cuối, âm lượng tổng xuống −40 dB, lo-fi đóng bộ lọc | Kết kiểu bản thu phòng thu | automation `master`, `filter` |
| Một nhát đồng loạt | `big_hit` | Cả ban 1 nhát ở phách 1 ô cuối, crash ngân | Kết rock/funk dứt khoát | `_big_hit` |

### Năm nguyên tắc vàng (code kiểm bằng test)

1. **Luật thêm/bớt:** không quá 8 ô liền có cùng "bộ lớp" (tập nhạc cụ và bộ phận trống đang chơi). Đoạn dài hơn 8 ô
   tự thêm một lớp ở ô thứ 9 và có fill nhỏ ở ô 8 [1]. Test: `test_moi_8_o_co_thay_doi`.
2. **Tương phản trước cao trào:** ô ngay trước Chorus thưa hơn chính Chorus (drop, stop, rút kick, snare build bỏ hat) [2].
   Test: `test_o_truoc_chorus_thua_hon`.
3. **Không lặp y hệt:** Verse 2 ≠ Verse 1, Chorus cuối ≠ Chorus 1 (thêm lớp, đổi biến thể, double-time hoặc lên giọng).
   Test: `test_verse2_khac_verse1`, `test_chorus_cuoi_khac_chorus_dau`.
4. **Chừa chỗ cho giọng hát:** ở Verse, phím chỉ 3 nốt và đỉnh thế bấm thấp hơn; số nốt trong tầm C4–C5 (MIDI 60–72)
   mỗi ô của Verse ít hơn Chorus. Hook không vào giữa câu hát của Verse [4], [5]. Test: `test_verse_chua_cho_giong`.
5. **Đột biến có liều lượng:** 1–3 điểm bất ngờ mỗi bài, chỉ đặt ở ranh giới đoạn, chọn theo seed trong danh sách cho phép
   của từng phong cách (`SURPRISES`). Test: `test_dot_bien_1_den_3`.

## D. Thang năng lượng 1–5

| Mức | Ý nghĩa | Công thức chung (`ENERGY_RECIPE`) | Ví dụ Pop |
|---|---|---|---|
| 1 | Mộc | mẫu mức 1, không guitar (trừ phong cách guitar dẫn), trống thưa hoặc tắt, âm lượng tổng −6 dB | Intro piano, ô cuối Outro |
| 2 | Thưa | mẫu mức 2 nhưng bass mức 1 (nốt dài), snare → side-stick (pop, R&B), phím 3 nốt, −4 dB | Verse 1 |
| 3 | Dồn | mẫu mức 2, bass mức 2, guitar vào nếu phong cách cho phép, −2,5 dB | Verse 2, Pre-Chorus |
| 4 | Cao trào | mẫu mức 3 (hat mở/ride), crash đầu đoạn, phím tay trái quãng tám, tầm rộng hơn, 0 dB | Chorus |
| 5 | Đỉnh | như 4 + bộ gõ thêm (tambourine), double-time (rock) hoặc lên giọng nếu bật, +0,5 dB | Chorus cuối |

Tương thích: cột `energy` cũ (1/2/3) giữ nguyên nghĩa ở chế độ Vòng lặp. Ở chế độ Bài hát nó thành **Năng lượng tổng**:
dời cả đường cong −1/0/+1 mức và kẹp trong 1–5 (2 = giữ nguyên khuôn). Không thêm cột.

## E. Hook nhạc cụ (QĐ 7B)

Hook là câu 2–4 nốt dài 1 ô, lặp lại để người nghe "nhận ra bài" [4]. Luật đặt (code: `_hook_bars`):

- **Nên:** Intro, Chorus (ô 2 và 4 của mỗi câu 4 ô, kiểu hỏi–đáp), Post-Chorus, Solo (2 ô đầu, 2 ô cuối), Outro.
- **Hạn chế:** Verse chỉ một mảnh ngắn (2 nốt đầu của hook) ở ô cuối câu 4 ô, tối đa 2 lần mỗi Verse.
- **Không:** Pre-Chorus, Bridge, Breakdown, ô có drop/stop-time/snare build, ô ngân kết bài.
- **Tầm:** C5–E6 (MIDI 72–88), trên tầm giọng hát.
- **Cao độ:** do Engine dựng: nốt phách mạnh là nốt hợp âm gần nhất, nốt phách yếu là nốt trong gam giọng
  (`build_scale`). Nhịp hook giữ nguyên khi đổi hợp âm, chỉ dời nốt cho khớp hợp âm.
- **Nhạc cụ:** Pop/Ballad/Jazz/Bossa = piano; Rock/Indie = guitar; Lo-fi/R&B = Rhodes FM; Funk = clavi.
- Công tắc "Hook" (bật mặc định) và kênh "Hook" riêng trên bàn trộn. "Tạo bản khác" đổi seed nên đổi cả hook.

## F. Độ dài bài

Ngắn (~24–32 ô), Vừa (~56–72 ô), Đầy đủ (~96–128 ô). Thời lượng = số ô × 4 × 60 / BPM, hiện phút:giây thật trên
dòng thời gian. Giới hạn cứng **160 ô**: (1) thời gian dựng ở backend tăng tuyến tính, 160 ô ở mức đo được vẫn dưới
1 giây; (2) mỗi ô sinh 20–60 dòng `drum_events`, 160 ô có thể tới ~8 000 dòng mỗi lần lưu (rủi ro ghi trong ADR-013).

---

## Ba bài hát nổi tiếng, phân tích theo đoạn (chỉ mô tả cấu trúc, không chép bản ghi)

### 1. "Smells Like Teen Spirit" — Nirvana (1991): tương phản to–nhỏ

- **Intro:** guitar đánh riff 4 hợp âm một mình, rồi cả ban nhạc "đổ" vào cùng lúc với trống fill: ví dụ kinh điển của
  "crash + kick đồng loạt ở phách 1 đoạn mới".
- **Verse:** rút gần hết: bass và trống giữ nhịp, guitar chỉ vài nốt lặp. Đây là "Verse thưa để chừa chỗ cho giọng".
- **Pre-Chorus:** một câu lặp lại, năng lượng dâng dần.
- **Chorus:** guitar méo đầy, trống mạnh nhất. Khoảng cách to–nhỏ giữa Verse và Chorus lớn có chủ đích.
- **Bài học cho code:** công thức năng lượng 2 → 4 ở Rock đổi hẳn guitar từ chặn tiếng (P) sang mở tiếng (O), hat → ride.

### 2. "Billie Jean" — Michael Jackson (1982): dựng lớp dần

- **Intro dài:** trống một mình vài ô, rồi bass vào, rồi lớp synth/phím: mỗi vài ô thêm một lớp.
- **Verse:** giữ nguyên groove, hầu như chỉ thay đổi bằng cách thêm/bớt lớp.
- **Pre-Chorus:** hợp âm đổi, căng hơn trước khi về điệp khúc.
- **Bài học cho code:** "luật thêm/bớt" (mỗi 8 ô có thay đổi nghe được) và Intro Funk bắt đầu bằng trống.

### 3. "The Girl from Ipanema" — Antônio Carlos Jobim (1962): khuôn AABA

- **A (8 ô) · A (8 ô) · B (16 ô, bridge) · A (8 ô):** bridge dài gấp đôi và đổi sang vùng hợp âm khác hẳn rồi quay về A.
- Phối khí bossa giữ mềm suốt bài; tương phản chủ yếu đến từ hòa âm của B và từ đoạn instrumental (kèn/piano chơi lại A).
- **Bài học cho code:** khuôn Bossa A · B · A · Instrumental · A, vòng C dùng cho B; không dùng riser ồn ào (QĐ 6A).

## Phạm vi và giới hạn

- Chỉ 4/4, không thêm giai điệu hát/lời, không dùng AI sinh âm thanh, không xuất WAV/MIDI cho người dùng.
- Mọi cao độ (kể cả hook, hợp âm lên giọng, tag ii–V, hợp âm I kết bài) dựng bằng Music Engine ở backend.
- Claude không nghe được âm thanh: "đạt" về kỹ thuật = số đo LUFS + test; "đạt" về cảm nhận = bài nghe mù của nhóm.
