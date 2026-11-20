# Sổ tay phong cách backing track (9 phong cách)

Ngày 02/11/2026, nhánh `phuc-music`, đi kèm ADR-012 (đề xuất, chờ Thắng duyệt).

Sổ tay này ghi **luật chơi** của từng phong cách mà code đang làm theo, để cả nhóm kiểm được bằng tai và bằng mắt. Mỗi luật trỏ tới chỗ trong code. Nguồn là sách giáo trình và sách kỹ thuật phòng thu đã xuất bản; nhóm chỉ học quy ước chơi (chung cho cả thể loại), không chép bản nhạc có bản quyền.

Code liên quan:

- Gói phong cách (backend, nguồn sự thật về nốt): `backend/app/composition/styles/<id>.py`
- Bộ phối (dẫn giọng, walking bass, fill, crash): `backend/app/composition/arranger.py`
- Humanize, swing, pocket (frontend, chỉ dời thời gian và lực, **không đổi nốt**): `frontend/src/audio/band/humanize.ts`
- Âm thanh từng kênh (EQ, nén, reverb, méo): `frontend/src/audio/band/mixer.ts`

## Quy ước chung cho cả 9 phong cách

| Quy ước | Giá trị | Ở đâu trong code |
|---|---|---|
| Nhịp | 4/4. Ballad và Jazz dùng lưới chia ba (12 ô một ô nhịp) để ra cảm giác 12/8 và swing (QĐ 11A) | `grid` trong gói |
| Cấu trúc | 4 vòng: vòng 1 mộc, vòng 2–3 đầy đủ, vòng 4 có fill lớn. Bấm "Lặp lại" thì quay về vòng 2 (QĐ 10A) | `arranger.py`, mức `[max(1, e-1), e, e, e]` |
| Fill | Fill nhỏ ở ô cuối mỗi vòng khi năng lượng ≥ 2; fill lớn ở vòng 4 | `arranger.py`, test `fill (tom) chỉ nằm ở ô cuối mỗi vòng` |
| Crash | Ô đầu vòng 2, 3, 4 khi năng lượng ≥ 2 | `arranger.py` |
| Dẫn giọng | Chọn thế bấm (voicing) có tổng quãng di chuyển nhỏ nhất; giữa vài thế gần tốt nhất thì chọn theo seed | `lead`, `movement` |
| Vùng trầm | Không xếp hai nốt cách nhau dưới quãng 4 đúng ở dưới E3 (MIDI 52), vì dưới đó quãng hẹp nghe đục | `harmonize` |
| Tô màu | Chỉ ở lớp phát (7, 9, 13 lấy qua `transpose`/`build_chord` của Engine, QĐ 7A). Giao diện ghi "Bản phối tô thêm màu: …" | `color` trong gói, `colors` trong kết quả |
| Lệch thời gian | Tối đa ±30 ms mỗi nhát; độ lệch chuẩn riêng từng nhạc cụ (`sigma_ms`), độ trễ cố ý (`pocket_ms`) | `humanize.ts`, `MAX_OFFSET_SEC` |

Năng lượng: 1 Mộc (ít nhạc cụ, nhát thưa), 2 Vừa, 3 Đầy (thêm guitar hoặc bộ gõ, hat dày hơn).

## Pop · 100 BPM (80–130)

- **Trống:** kick ở phách 1 và "và" của phách 3, snare phách 2 và 4, hi-hat móc đơn; hat hơi sớm (−2 ms) để nhịp "đẩy" về trước.
- **Bass:** nốt gốc móc đơn, nối sang hợp âm sau bằng nốt dẫn (approach) ở nhát cuối ô.
- **Phím:** piano thế bấm hẹp, đỉnh quanh A4 (69), rải nhẹ 4–14 ms từ trầm lên.
- **Guitar:** từ năng lượng 2, quạt thế mở (open), quạt lên nhẹ hơn quạt xuống và dây cao vang trước.
- **Màu:** add9.
- **Nguồn:** Mark Harrison, *The Pop Piano Book* (Hal Leonard, 1997), phần đệm pop và thế bấm tay phải; Bruce Buckingham & Eric Paschal, *Rhythm Guitar: The Complete Guide* (Hal Leonard/Musicians Institute, 1997), phần quạt móc kép; Bobby Owsinski, *The Mixing Engineer's Handbook* (cân trống và bass trong mix pop).

## Ballad · 70 BPM (60–84)

- **Cảm giác 12/8** trên lưới 12: piano tay trái rải 1-5-8-10 (gốc, năm, quãng tám, mười), tay phải giữ hợp âm.
- **Trống:** side-stick (`xstick`) nhẹ ở phách 2 và 4, ride hoặc hat thưa; snare trễ 6 ms.
- **Bass:** nốt dài, đổi theo hợp âm.
- **Guitar:** chỉ ở năng lượng 3.
- **Hiệu ứng:** reverb hall dài nhất trong 9 phong cách.
- **Nguồn:** Mark Harrison, *The Pop Piano Book*, chương ballad và mẫu rải tay trái; Mike Senior, *Mixing Secrets for the Small Studio* (Focal Press, 2011), phần reverb và độ sâu.

## Bossa nova · 130 BPM (110–150)

- **Cảm giác 2** (hai phách lớn mỗi ô).
- **Trống:** rim click theo mẫu clave bossa, kick 1-và-3 kiểu surdo, hat móc kép nhẹ; shaker từ năng lượng 2, thêm conga ở năng lượng 3.
- **Bass:** upright, gốc và năm luân phiên.
- **Phím:** Rhodes FM, thế bấm không gốc (rootless), đánh nảy lệch phách.
- **Guitar:** thế shell, có từ năng lượng 1.
- **Màu:** 9 trên mọi hợp âm.
- **Nguồn:** Nelson Faria, *The Brazilian Guitar Book* (Sher Music, 1995), các mẫu bossa của guitar và bass; Antonio Adolfo, *Brazilian Music Workshop* (Advance Music, 1993), clave bossa và phần trống.

## Lo-fi · 80 BPM (68–92)

- **Swing móc kép 58%.**
- **Trống:** snare trễ trung bình 15–30 ms (pocket "lười", có test riêng).
- **Phím:** Rhodes FM maj7/9 ngân dài.
- **Âm thanh:** lọc thấp ~4,2 kHz, bão hòa nhẹ, rung cao độ ±5 cent (wow) như băng cũ, tiếng đĩa than tùy chọn.
- **Nguồn:** Dan Charnas, *Dilla Time* (MCD, 2022), giải thích nhịp "trễ" và swing của J Dilla mà lo-fi kế thừa; Rick Snoman, *The Dance Music Manual* (Focal Press, 3rd ed. 2014), phần bão hòa và lọc để tạo màu cũ.

## Jazz · 120 BPM (90–160)

- **Swing** trên lưới 12.
- **Trống:** ride "ding, ding-da, ding" sớm 6 ms để kéo nhịp; hi-hat đạp phách 2 và 4; bộ chổi (brush).
- **Bass:** walking bass 4 nốt mỗi ô, chọn bằng tìm kiếm chi phí. Nốt gốc ở phách 1, nốt dẫn nửa cung vào hợp âm sau qua `transpose` của Engine.
- **Phím:** rootless kiểu A/B, đỉnh quanh F#4 (66).
- **Guitar:** 4 nhát mỗi ô ở năng lượng 3.
- **Giới hạn:** tempo dự án tối đa 160 BPM, nên chưa lên được swing nhanh 180.
- **Nguồn:** Mark Levine, *The Jazz Piano Book* (Sher Music, 1989), thế rootless; Ed Friedland, *Building Walking Bass Lines* (Hal Leonard, 1995); John Riley, *The Art of Bop Drumming* (Manhattan Music, 1994), mẫu ride và hat.

## Rock · 116 BPM (96–150), 2 biến thể

- **Trống:** mạnh, kick và snare đúng phách, lệch rất ít (σ 4 ms).
- **Bass:** móc đơn đều trên nốt gốc.
- **Guitar:** power chord. Chặn tiếng (mute) ở vòng thường, mở tiếng ở cao trào. Méo + lọc loa thùng 4×12.
- **Phím:** lùi lại sau guitar.
- **Nguồn:** Buckingham & Paschal, *Rhythm Guitar: The Complete Guide*, power chord và chặn tiếng bằng lòng bàn tay; Owsinski, *The Mixing Engineer's Handbook*, phần guitar méo và lọc loa.

## Indie · 112 BPM (96–132), 2 biến thể

- **Trống:** hat móc kép, tambourine từ năng lượng 2 (dày hơn ở năng lượng 3).
- **Guitar:** clean qua chorus và delay, rải nốt treo ở thế cao.
- **Hiệu ứng:** reverb hall rộng, delay chấm (dotted eighth) trên phím và guitar.
- **Nguồn:** Mike Senior, *Mixing Secrets for the Small Studio*, phần chorus và delay qua send; Buckingham & Paschal, *Rhythm Guitar*, phần rải nốt (arpeggio) và nốt treo.

## Funk · 104 BPM (92–118), 2 biến thể

- **Swing móc kép nhẹ 53%.**
- **Trống:** hat móc kép có nhấn, snare ghost rất nhỏ.
- **Bass:** nốt chết (dead note) xen kẽ.
- **Guitar:** chicken scratch: mẫu `guitar_mute` xen nhát mở.
- **Phím:** clavi, nhát ngắn.
- **Nguồn:** David Garibaldi, *Future Sounds* (Alfred, 1990), ghost note và hat có nhấn; Jon Liebman, *Funk Bass* (Hal Leonard, 1992), nốt chết và móc kép; Buckingham & Paschal, *Rhythm Guitar*, chương funk.

## R&B · 78 BPM (64–92), 2 biến thể

- **Swing móc kép 55%.**
- **Trống:** snare và clap trễ 14 ms; conga và shaker.
- **Phím:** Rhodes FM rải chậm (12–30 ms).
- **Màu:** 9 và 13 trên hợp âm át (thêm 13 chỉ khi hợp âm có chức năng át).
- **Nguồn:** Dan Charnas, *Dilla Time*, nhịp neo-soul trễ phách; Mark Levine, *The Jazz Theory Book* (Sher Music, 1995), hợp âm 9/13 và chức năng át.

## Những gì sổ tay này chưa đảm bảo

- Claude không nghe được âm thanh. Các luật trên được kiểm bằng test và số đo (độ to, đỉnh, độ lệch thời gian), còn "nghe có giống ban nhạc thật không" phải chờ ba bạn chấm ở trang nghe mù.
- Năm phong cách làm sâu (Pop, Ballad, Lo-fi, Bossa, Jazz) có nhiều mẫu hơn. Rock, Indie, Funk, R&B mới có 2 biến thể (QĐ 8A).
