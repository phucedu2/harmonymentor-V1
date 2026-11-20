# Chấm độ đúng nhạc lý câu trả lời AI Tutor

Câu đã có trả lời: 300/300. Tự động: {'dat': 267, 'can_xem': 33}. Người chấm: {'dung': 277, 'sai': 14, 'tranh_luan': 2, 'khong_tra_loi': 7}.

| Nhóm | Số câu | Sai (người chấm) | Tranh luận | Tự động cần xem |
|---|---|---|---|---|
| bai | 240 | 10 | 1 | 23 |
| ngoai | 60 | 4 | 1 | 10 |

## Câu sai hoặc cần xem

### T003 [thanh_phan_hop_am] luồng A · người chấm: sai
- Hỏi: hop am F#m co nhung not gi
- Đáp án: F# A C#
- AI: Hợp âm F#m dựng bằng quãng ba trưởng nhỏ và năm đúng, gồm các nốt F# A C#.
- Ghi chú người chấm: Nốt đúng (F# A C#) nhưng gọi quãng là "ba trưởng nhỏ"; F#m dùng quãng ba thứ

### T008 [thanh_phan_hop_am] luồng A · người chấm: dung
- Hỏi: Cho mình các nốt của hợp âm F#dim với.
- Đáp án: F# A C
- AI: Hợp âm giảm F#dim gồm các nốt F#, A và C, được dựng bằng nốt gốc F# cộng với quãng ba thứ và quãng năm giảm.
- Tự động: thuật ngữ sai: 'nam giam'
- Ghi chú người chấm: Bộ chấm tự động bắt nhầm "quãng năm giảm" là thuật ngữ sai

### T011 [thanh_phan_hop_am] luồng A · người chấm: sai
- Hỏi: Hợp âm Db được cấu tạo từ những nốt nào?
- Đáp án: Db F Ab
- AI: Hợp âm Db là hợp âm trưởng lấy Db làm nốt gốc. Khung chữ cái dùng Db–F–Ab theo công thức M3 + P5, trong đó Db đến F là quãng ba trưởng và F đến Ab là quãng năm đúng.
- Ghi chú người chấm: Nốt đúng (Db F Ab) nhưng ghi "F đến Ab là quãng năm đúng"; F–Ab là m3, Db–Ab mới là P5

### T017 [thanh_phan_hop_am] luồng A · người chấm: dung
- Hỏi: Hợp âm Bm7b5 được cấu tạo từ những nốt nào?
- Đáp án: B D F A
- AI: Hợp âm Bm7b5 được cấu tạo từ các nốt B, D, F và A. Đây là hợp âm bảy bán giảm gồm một nốt gốc, quãng ba thứ, quãng năm giảm và quãng bảy thứ.
- Tự động: thuật ngữ sai: 'nam giam'
- Ghi chú người chấm: Bộ chấm tự động bắt nhầm "quãng năm giảm"

### T020 [thanh_phan_hop_am] luồng A · người chấm: dung
- Hỏi: Cho mình các nốt của hợp âm Bbm7 với.
- Đáp án: Bb Db F Ab
- AI: Hợp âm Bbm7 (Bbm7) được cấu tạo từ bốn nốt theo ENGINE_FACTS là Bb Db F Ab.
- Tự động: từ chối/lộ chữ nội bộ: lộ ENGINE_FACTS
- Ghi chú người chấm: Nốt đúng; lộ chữ nội bộ ENGINE_FACTS (lỗi trình bày)

### T039 [thanh_phan_hop_am] luồng B · người chấm: tranh_luan
- Hỏi: hop am Am9 co nhung not gi
- Đáp án: A C E G B
- AI: Hợp âm Am9 của bạn gồm các nốt A C E G B. Đây là hợp âm trưởng-thứ mở rộng rất hay trong jazz và pop. Bài gần nhất với câu hỏi: L07 “Jazz Tensions, Modes và Chord-Scale Context”.
- Ghi chú người chấm: Nốt đúng (A C E G B); gọi Am9 là "hợp âm trưởng-thứ" không chuẩn (hợp âm chín thứ)

### T084 [am_giai] luồng B · người chấm: khong_tra_loi
- Hỏi: F Lydian gồm những nốt nào?
- Đáp án: F G A B C D E
- AI: Music Engine chưa tính được mục này. Âm giai Lydian là một điệu thức trưởng, tương tự âm giai trưởng tự nhiên nhưng có bậc 4 được thăng lên nửa cung. Bài gần nhất với câu hỏi: L07 “Jazz Tensions, Modes và Chord-Scale Context”.
- Tự động: thiếu nốt ['F', 'G', 'A', 'B', 'C', 'D', 'E']
- Ghi chú người chấm: Engine chưa có Lydian; mô tả công thức đúng nhưng không liệt kê nốt

### T085 [am_giai] luồng B · người chấm: khong_tra_loi
- Hỏi: E Phrygian gồm những nốt nào?
- Đáp án: E F G A B C D
- AI: Music Engine chưa tính được mục này. Âm giai Phrygian (Phrygian mode) là mode thứ ba của âm giai trưởng, có công thức dựa trên âm giai trưởng tự nhiên nhưng bắt đầu từ bậc III, với đặc trưng là nốt bậc 2 giáng (b2). Bạn có thể thử áp dụng công thức khoảng cách cung và nửa cung để tìm ra các nốt nhé. Bài gần nhất với câu hỏi: L01 “Từ bàn phím đến hợp âm ba nốt”.
- Tự động: thiếu nốt ['E', 'F', 'G', 'A', 'B', 'C', 'D']
- Ghi chú người chấm: Engine chưa có Phrygian; không liệt kê nốt, gợi ý bài L01 không liên quan

### T086 [am_giai] luồng B · người chấm: khong_tra_loi
- Hỏi: B Locrian gồm những nốt nào?
- Đáp án: B C D E F G A
- AI: Music Engine chưa tính được mục này. Âm giai Locrian (thang âm Locrian) là âm giai thứ tự nhiên có bậc 2 và bậc 5 giáng, tạo nên quãng 5 giảm đặc trưng ở bậc I. Bạn có thể tra cứu công thức cấu tạo âm giai này trên các tài liệu nhạc lý hoặc thử nghiệm trong Harmony Lab nhé. Bài gần nhất với câu hỏi: L07 “Jazz Tensions, Modes và Chord-Scale Context”.
- Tự động: thiếu nốt ['B', 'C', 'D', 'E', 'F', 'G', 'A']
- Ghi chú người chấm: Engine chưa có Locrian; công thức (thứ tự nhiên giáng 2 và 5) đúng nhưng không liệt kê nốt

### T087 [am_giai] luồng B · người chấm: khong_tra_loi
- Hỏi: Âm giai ngũ cung C trưởng (C major pentatonic) gồm những nốt nào?
- Đáp án: C D E G A
- AI: Music Engine chưa tính được mục này. Âm giai ngũ cung trưởng bao gồm bậc 1, 2, 3, 5 và 6 của âm giai trưởng tương ứng. Bài gần nhất với câu hỏi: L02 “Âm giai trưởng và hợp âm bảy điệu tính”.
- Tự động: thiếu nốt ['C', 'D', 'E', 'G', 'A']
- Ghi chú người chấm: Engine chưa có ngũ cung; công thức 1-2-3-5-6 đúng nhưng không liệt kê nốt

### T088 [am_giai] luồng B · người chấm: khong_tra_loi
- Hỏi: Âm giai ngũ cung A thứ (A minor pentatonic) gồm những nốt nào?
- Đáp án: A C D E G
- AI: Music Engine chưa tính được mục này. Âm giai ngũ cung A thứ (A minor pentatonic) được xây dựng dựa trên các bậc 1, 3, 4, 5, 7 của âm giai thứ tự nhiên, mang lại màu sắc âm nhạc quen thuộc trong nhiều thể loại như blues, rock và pop. Bài gần nhất với câu hỏi: L02 “Âm giai trưởng và hợp âm bảy điệu tính”.
- Tự động: thiếu nốt ['C', 'D', 'E', 'G']
- Ghi chú người chấm: Engine chưa có ngũ cung; công thức đúng nhưng chỉ có A, không liệt kê đủ nốt

### T089 [am_giai] luồng B · người chấm: khong_tra_loi
- Hỏi: Âm giai blues C gồm những nốt nào?
- Đáp án: C Eb F Gb G Bb
- AI: Music Engine chưa tính được mục này cho âm giai blues C. Bạn có thể tìm hiểu công thức của âm giai blues gồm các bậc 1, b3, 4, #4/b5, 5 và b7 nhé! Bài gần nhất với câu hỏi: L02 “Âm giai trưởng và hợp âm bảy điệu tính”.
- Tự động: thiếu nốt ['Eb', 'F', 'Gb', 'G', 'Bb']
- Ghi chú người chấm: Engine chưa có blues; công thức đúng nhưng không liệt kê nốt

### T097 [quang] luồng A · người chấm: dung
- Hỏi: Nốt E và nốt Bb phía trên cách nhau quãng gì?
- Đáp án: d5 (6 nửa cung)
- AI: Nốt E và nốt Bb phía trên cách nhau quãng d5, tức là quãng năm giảm có độ rộng 6 nửa cung theo bàn phím piano.
- Tự động: thuật ngữ sai: 'nam giam'
- Ghi chú người chấm: Bộ chấm tự động bắt nhầm "quãng năm giảm"

### T100 [quang] luồng A · người chấm: sai
- Hỏi: Quãng từ A lên C# là quãng gì?
- Đáp án: M3 (4 nửa cung)
- AI: Từ A lên C# là quãng 3 trưởng (M3), vì A lên C là quãng 3 chứa 4 nửa cung và C# được nâng lên thành 3 nửa cung lớn, đồng thời giữ đúng tên chữ cái bước quãng.
- Ghi chú người chấm: Kết luận M3 đúng nhưng giải thích sai: "A lên C ... chứa 4 nửa cung" (A–C là 3 nửa cung)

### T107 [quang] luồng A · người chấm: sai
- Hỏi: Nốt D và nốt C# phía trên cách nhau quãng gì?
- Đáp án: M7 (11 nửa cung)
- AI: Nốt D và nốt C# phía trên tạo thành quãng 7 trưởng (M7). Trên bàn phím, D cách C# một nửa cung.
- Ghi chú người chấm: Kết luận M7 đúng nhưng thêm "D cách C# một nửa cung", mâu thuẫn với quãng bảy trưởng 11 nửa cung

### T110 [quang] luồng A · người chấm: sai
- Hỏi: Quãng từ Ab lên F là quãng gì?
- Đáp án: M6 (9 nửa cung)
- AI: Từ Ab lên F là quãng M6, tức là quãng sáu trưởng, có độ rộng bằng 8 nửa cung trên bàn phím.
- Ghi chú người chấm: Gọi đúng M6 nhưng ghi "8 nửa cung" (M6 = 9)

### T111 [quang] luồng A · người chấm: tranh_luan
- Hỏi: C# lên E là quãng mấy?
- Đáp án: m3 (3 nửa cung)
- AI: C# lên E là quãng ba thứ (m3), gồm 3 nửa cung, vì E nằm ở họ chữ cái cách C một bậc và thỏa mãn khoảng cách cao độ.
- Ghi chú người chấm: Kết luận m3 đúng; giải thích "E cách C một bậc" lủng củng

### T141 [hoa_bieu] luồng A · người chấm: dung
- Hỏi: Giọng F# thứ có mấy dấu hóa?
- Đáp án: 3 dấu thăng: F# C# G#
- AI: Trợ lý AI chưa trả lời được lúc này, nên mình trả lời bằng phần bài học liên quan nhất. Theo Music Engine: Giọng F# thứ có 3 dấu thăng: F# C# G#. Trong bài “Âm giai trưởng và hợp âm bảy điệu tính”, phần “2. G major trên khuông”: Mỗi bậc dùng một chữ cái khác nhau; vì vậy G major dùng F#, không viết Gb.
- Tự động: không phải câu AI trả lời bình thường: status=fallback lý do=engine_contradiction
- Tự động: từ chối/lộ chữ nội bộ: AI lỗi, câu dự phòng
- Ghi chú người chấm: Câu dự phòng (engine_contradiction) do máy chủ trả, nội dung đúng

### T146 [giong_tuong_quan] luồng A · người chấm: dung
- Hỏi: Giọng thứ tương quan của G trưởng là gì?
- Đáp án: E thứ
- AI: Trợ lý AI chưa trả lời được lúc này, nên mình trả lời bằng phần bài học liên quan nhất. Theo Music Engine: Giọng tương quan của G trưởng là E thứ. Trong bài “Âm giai trưởng và hợp âm bảy điệu tính”, phần “1. Âm giai trưởng là một chuỗi 7 bậc”: Major scale có bảy tên nốt khác nhau trước khi lặp lại tonic ở quãng tám. Ta gọi chúng là bậc 1 đến bậc 7. Tonic là bậc 1 và là nốt làm điểm quy chiếu của scale/key. Whole step (cung nguyên) = 2 nửa cung; half step (nửa cung) = 1 nửa cung. Mẫu khoảng cách đi lên của major scale là: whole–whole–half–whole–whole–whole–half, hay 2–2–1–2–2–2–1 nửa cung. Viết
- Tự động: không phải câu AI trả lời bình thường: status=fallback lý do=engine_contradiction
- Tự động: từ chối/lộ chữ nội bộ: AI lỗi, câu dự phòng
- Ghi chú người chấm: Câu dự phòng (engine_contradiction) do máy chủ trả, nội dung đúng

### T147 [giong_tuong_quan] luồng A · người chấm: dung
- Hỏi: Giọng thứ tương quan của D trưởng là gì?
- Đáp án: B thứ
- AI: Trợ lý AI chưa trả lời được lúc này, nên mình trả lời bằng phần bài học liên quan nhất. Theo Music Engine: Giọng tương quan của D trưởng là B thứ. Trong bài “Âm giai trưởng và hợp âm bảy điệu tính”, phần “1. Âm giai trưởng là một chuỗi 7 bậc”: Major scale có bảy tên nốt khác nhau trước khi lặp lại tonic ở quãng tám. Ta gọi chúng là bậc 1 đến bậc 7. Tonic là bậc 1 và là nốt làm điểm quy chiếu của scale/key. Whole step (cung nguyên) = 2 nửa cung; half step (nửa cung) = 1 nửa cung. Mẫu khoảng cách đi lên của major scale là: whole–whole–half–whole–whole–whole–half, hay 2–2–1–2–2–2–1 nửa cung. Viết
- Tự động: không phải câu AI trả lời bình thường: status=fallback lý do=engine_contradiction
- Tự động: từ chối/lộ chữ nội bộ: AI lỗi, câu dự phòng
- Ghi chú người chấm: Câu dự phòng (engine_contradiction) do máy chủ trả, nội dung đúng

### T159 [hoa_bieu] luồng A · người chấm: dung
- Hỏi: Thứ tự các dấu thăng trong hóa biểu là gì?
- Đáp án: F C G D A E B
- AI: Thứ tự các dấu thăng trong hóa biểu là F#, C#, G#, D#, A#, E#, B#.
- Tự động: không thấy cụm nào trong ['F C G D A E B', 'F, C, G, D, A, E, B', 'F–C–G–D–A–E–B', 'F-C-G-D-A-E-B']…

### T169 [so_la_ma] luồng A · người chấm: dung
- Hỏi: Trong giọng F trưởng, Em7b5 là hợp âm bậc mấy?
- Đáp án: viiø7
- AI: Mình trả lời theo Music Engine và bài học nhé. Theo Music Engine: Trong giọng F trưởng, Em7b5 là viiø7. Trong bài “Âm giai trưởng và hợp âm bảy điệu tính”, phần “1. Âm giai trưởng là một chuỗi 7 bậc”: F phải được nâng thành F# để giữ mẫu khoảng cách major scale.
- Tự động: không phải câu AI trả lời bình thường: status=fallback lý do=fact_missing
- Ghi chú người chấm: Câu dự phòng (fact_missing) do máy chủ trả, nội dung đúng

### T175 [so_la_ma] luồng A · người chấm: dung
- Hỏi: Trong giọng E trưởng, D#m7b5 là hợp âm bậc mấy?
- Đáp án: viiø7
- AI: Mình trả lời theo Music Engine và bài học nhé. Theo Music Engine: Trong giọng E trưởng, D#m7b5 là viiø7. Trong bài “Âm giai trưởng và hợp âm bảy điệu tính”, phần “Ghi nhớ”: Major scale dùng 7 bậc và giữ đúng thứ tự chữ cái. Seventh chord mở rộng triad thành 1–3–5–7. Trong major key: Imaj7, ii7, iii7, IVmaj7, V7, vi7, viiø7. Trong C major: Dm7 = ii7, G7 = V7, Bm7♭5 = viiø7. Đổi giọng thì đổi hợp âm: trong G major, bậc V là D nên V7 = D7 (D–F#–A–C).
- Tự động: không phải câu AI trả lời bình thường: status=fallback lý do=fact_missing
- Ghi chú người chấm: Câu dự phòng (fact_missing) do máy chủ trả, nội dung đúng

### T181 [so_la_ma] luồng A · người chấm: dung
- Hỏi: Hợp âm viiø7 trong giọng F trưởng là hợp âm gì?
- Đáp án: Em7b5
- AI: Mình trả lời theo Music Engine và bài học nhé. Theo Music Engine: Trong giọng F trưởng, Em7b5 là viiø7. Em7b5 = E G Bb D. Trong bài “Âm giai trưởng và hợp âm bảy điệu tính”, phần “Ghi nhớ”: Major scale dùng 7 bậc và giữ đúng thứ tự chữ cái. Seventh chord mở rộng triad thành 1–3–5–7. Trong major key: Imaj7, ii7, iii7, IVmaj7, V7, vi7, viiø7. Trong C major: Dm7 = ii7, G7 = V7, Bm7♭5 = viiø7. Đổi giọng thì đổi hợp âm: trong G major, bậc V là D nên V7 = D7 (D–F#–A–C).
- Tự động: không phải câu AI trả lời bình thường: status=fallback lý do=fact_missing
- Ghi chú người chấm: Câu dự phòng (fact_missing) do máy chủ trả, nội dung đúng

### T184 [so_la_ma] luồng A · người chấm: dung
- Hỏi: Hợp âm viiø7 trong giọng Ab trưởng là hợp âm gì?
- Đáp án: Gm7b5
- AI: Mình trả lời theo Music Engine và bài học nhé. Theo Music Engine: Trong giọng Ab trưởng, Gm7b5 là viiø7. Gm7b5 = G Bb Db F. Trong bài “Âm giai trưởng và hợp âm bảy điệu tính”, phần “Ghi nhớ”: Major scale dùng 7 bậc và giữ đúng thứ tự chữ cái. Seventh chord mở rộng triad thành 1–3–5–7. Trong major key: Imaj7, ii7, iii7, IVmaj7, V7, vi7, viiø7. Trong C major: Dm7 = ii7, G7 = V7, Bm7♭5 = viiø7. Đổi giọng thì đổi hợp âm: trong G major, bậc V là D nên V7 = D7 (D–F#–A–C).
- Tự động: không phải câu AI trả lời bình thường: status=fallback lý do=fact_missing
- Ghi chú người chấm: Câu dự phòng (fact_missing) do máy chủ trả, nội dung đúng

### T185 [bay_so_la_ma, bẫy] luồng A · người chấm: dung
- Hỏi: Trong C trưởng, G7 là hợp âm IV đúng không?
- Đáp án: Không, G7 là V7
- AI: Không phải bạn nhé. Trong C major, G7 là hợp âm bậc V, được cấu tạo từ các nốt G B D F, chứ không phải hợp âm bậc IV.
- Tự động: không thấy số La Mã ['V7']

### T210 [guide_tone] luồng A · người chấm: dung
- Hỏi: Guide tone (nốt 3 và nốt 7) của Fmaj7 là những nốt nào?
- Đáp án: A và E
- AI: Trợ lý AI chưa trả lời được lúc này, nên mình trả lời bằng phần bài học liên quan nhất. Theo Music Engine: Guide tone của Fmaj7: nốt 3 là A, nốt 7 là E. Trong bài “ii–V–I và guide-tone voice leading trên piano”, phần “5. Vì sao 3rd và 7th quan trọng?”: Trong G7, B là 3rd và F là ♭7. Hai nốt này giúp tai nhận ra màu dominant seventh rất rõ. Khi sang Cmaj7, B có thể giữ nguyên vì Cmaj7 cũng chứa B; F đi xuống E bằng một nửa cung. Đây là ví dụ cụ thể của common tone + stepwise motion. Đây là một voicing/voice-leading choice phục vụ lesson, không phải cách duy nhất phải dùng trong mọi phong cách.
- Tự động: không phải câu AI trả lời bình thường: status=fallback lý do=engine_contradiction
- Tự động: từ chối/lộ chữ nội bộ: AI lỗi, câu dự phòng
- Ghi chú người chấm: Câu dự phòng (engine_contradiction) do máy chủ trả, nội dung đúng

### T211 [guide_tone] luồng A · người chấm: dung
- Hỏi: Guide tone (nốt 3 và nốt 7) của Bb7 là những nốt nào?
- Đáp án: D và Ab
- AI: Mình trả lời theo Music Engine và bài học nhé. Theo Music Engine: Guide tone của Bb7: nốt 3 là D, nốt 7 là Ab. Trong bài “ii–V–I và guide-tone voice leading trên piano”, phần “5. Vì sao 3rd và 7th quan trọng?”: Trong G7, B là 3rd và F là ♭7. Hai nốt này giúp tai nhận ra màu dominant seventh rất rõ. Khi sang Cmaj7, B có thể giữ nguyên vì Cmaj7 cũng chứa B; F đi xuống E bằng một nửa cung. Đây là ví dụ cụ thể của common tone + stepwise motion. Đây là một voicing/voice-leading choice phục vụ lesson, không phải cách duy nhất phải dùng trong mọi phong cách.
- Tự động: không phải câu AI trả lời bình thường: status=fallback lý do=fact_missing
- Ghi chú người chấm: Câu dự phòng (fact_missing) do máy chủ trả, nội dung đúng

### T217 [guide_tone] luồng A · người chấm: dung
- Hỏi: Vì sao nốt 3 và nốt 7 quan trọng trong hợp âm bảy?
- Đáp án: Quyết định chất lượng hợp âm (trưởng/thứ, loại 7) và dẫn giọng mượt
- AI: Nốt 3rd và 7th đóng vai trò guide tones rất quan trọng. Nốt 3rd giúp xác định màu trưởng hoặc thứ của hợp âm, còn nốt 7th cùng với 3rd tạo nên sức căng và định hướng chuyển động rất mạnh khi đi sang hợp âm tiếp theo.
- Tự động: không thấy cụm nào trong ['chất lượng', 'tính chất', 'loại hợp âm', 'màu sắc']…

### T218 [shell_voicing] luồng A · người chấm: sai
- Hỏi: Shell voicing root–3–7 của Dm7 gồm những nốt nào?
- Đáp án: D F C
- AI: Shell voicing gồm nốt gốc, quãng 3 và quãng 7, lược quãng 5. Với Dm7, các nốt là D, F, A và C.
- Ghi chú người chấm: Nói lược quãng 5 nhưng liệt kê D F A C (vẫn có A); shell Dm7 = D F C

### T219 [shell_voicing] luồng A · người chấm: dung
- Hỏi: Shell voicing root–3–7 của G7 gồm những nốt nào?
- Đáp án: G B F
- AI: Trợ lý AI chưa trả lời được lúc này, nên mình trả lời bằng phần bài học liên quan nhất. Theo Music Engine: Shell voicing root–3–7 của G7: G, B, F. Trong bài “Jazz Piano Voicing: shell voicing và guide-tone connection”, phần “2. Shell root–3–7 của ii–V–I ở C major”: Dm7: D–F–C. G7: G–B–F. Cmaj7: C–E–B.
- Tự động: không phải câu AI trả lời bình thường: status=fallback lý do=engine_contradiction
- Tự động: Engine bác: get_chord_tones {'symbol': 'G7'} AI ghi 'G B F', Engine: 'G B D F'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Dm7'} AI ghi 'D F C', Engine: 'D F A C'
- Tự động: Engine bác: get_chord_tones {'symbol': 'G7'} AI ghi 'G B F', Engine: 'G B D F'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Cmaj7'} AI ghi 'C E B', Engine: 'C E G B'
- Tự động: Engine bác: get_chord_tones {'symbol': 'G7'} AI ghi 'G B F', Engine: 'G B D F'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Dm7'} AI ghi 'D F C', Engine: 'D F A C'
- Tự động: Engine bác: get_chord_tones {'symbol': 'G7'} AI ghi 'G B F', Engine: 'G B D F'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Cmaj7'} AI ghi 'C E B', Engine: 'C E G B'
- Tự động: từ chối/lộ chữ nội bộ: AI lỗi, câu dự phòng
- Ghi chú người chấm: Câu dự phòng (engine_contradiction) do máy chủ trả, nội dung đúng; Gemini trả lời đúng có thể đã bị guardrail chặn nhầm (shell voicing)

### T221 [shell_voicing] luồng A · người chấm: sai
- Hỏi: Shell voicing root–3–7 của Fmaj7 gồm những nốt nào?
- Đáp án: F A E
- AI: Shell voicing chỉ giữ ba nốt gồm root, quãng 3 và quãng 7, đồng thời lược quãng 5. Với Fmaj7, shell voicing gồm các nốt F, A, C và E.
- Ghi chú người chấm: Nói lược quãng 5 nhưng liệt kê F A C E (vẫn có C); shell Fmaj7 = F A E

### T222 [shell_voicing] luồng A · người chấm: dung
- Hỏi: Shell voicing root–3–7 của Bb7 gồm những nốt nào?
- Đáp án: Bb D Ab
- AI: Trợ lý AI chưa trả lời được lúc này, nên mình trả lời bằng phần bài học liên quan nhất. Theo Music Engine: Shell voicing root–3–7 của Bb7: Bb, D, Ab. Trong bài “Jazz Piano Voicing: shell voicing và guide-tone connection”, phần “2. Shell root–3–7 của ii–V–I ở C major”: Dm7: D–F–C. G7: G–B–F. Cmaj7: C–E–B.
- Tự động: không phải câu AI trả lời bình thường: status=fallback lý do=engine_contradiction
- Tự động: Engine bác: get_chord_tones {'symbol': 'Bb7'} AI ghi 'Bb D Ab', Engine: 'Bb D F Ab'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Dm7'} AI ghi 'D F C', Engine: 'D F A C'
- Tự động: Engine bác: get_chord_tones {'symbol': 'G7'} AI ghi 'G B F', Engine: 'G B D F'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Cmaj7'} AI ghi 'C E B', Engine: 'C E G B'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Bb7'} AI ghi 'Bb D Ab', Engine: 'Bb D F Ab'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Dm7'} AI ghi 'D F C', Engine: 'D F A C'
- Tự động: Engine bác: get_chord_tones {'symbol': 'G7'} AI ghi 'G B F', Engine: 'G B D F'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Cmaj7'} AI ghi 'C E B', Engine: 'C E G B'
- Tự động: từ chối/lộ chữ nội bộ: AI lỗi, câu dự phòng
- Ghi chú người chấm: Câu dự phòng (engine_contradiction) do máy chủ trả, nội dung đúng; Gemini trả lời đúng có thể đã bị guardrail chặn nhầm (shell voicing)

### T224 [shell_voicing] luồng A · người chấm: dung
- Hỏi: Shell voicing root–3–7 của A7 gồm những nốt nào?
- Đáp án: A C# G
- AI: Trợ lý AI chưa trả lời được lúc này, nên mình trả lời bằng phần bài học liên quan nhất. Theo Music Engine: Shell voicing root–3–7 của A7: A, C#, G. Trong bài “Jazz Piano Voicing: shell voicing và guide-tone connection”, phần “2. Shell root–3–7 của ii–V–I ở C major”: Dm7: D–F–C. G7: G–B–F. Cmaj7: C–E–B.
- Tự động: không phải câu AI trả lời bình thường: status=fallback lý do=engine_contradiction
- Tự động: Engine bác: get_chord_tones {'symbol': 'A7'} AI ghi 'A C# G', Engine: 'A C# E G'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Dm7'} AI ghi 'D F C', Engine: 'D F A C'
- Tự động: Engine bác: get_chord_tones {'symbol': 'G7'} AI ghi 'G B F', Engine: 'G B D F'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Cmaj7'} AI ghi 'C E B', Engine: 'C E G B'
- Tự động: Engine bác: get_chord_tones {'symbol': 'A7'} AI ghi 'A C# G', Engine: 'A C# E G'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Dm7'} AI ghi 'D F C', Engine: 'D F A C'
- Tự động: Engine bác: get_chord_tones {'symbol': 'G7'} AI ghi 'G B F', Engine: 'G B D F'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Cmaj7'} AI ghi 'C E B', Engine: 'C E G B'
- Tự động: từ chối/lộ chữ nội bộ: AI lỗi, câu dự phòng
- Ghi chú người chấm: Câu dự phòng (engine_contradiction) do máy chủ trả, nội dung đúng; Gemini trả lời đúng có thể đã bị guardrail chặn nhầm (shell voicing)

### T225 [shell_voicing] luồng A · người chấm: dung
- Hỏi: Shell voicing root–3–7 của Ebmaj7 gồm những nốt nào?
- Đáp án: Eb G D
- AI: Trợ lý AI chưa trả lời được lúc này, nên mình trả lời bằng phần bài học liên quan nhất. Theo Music Engine: Shell voicing root–3–7 của Ebmaj7: Eb, G, D. Trong bài “Jazz Piano Voicing: shell voicing và guide-tone connection”, phần “2. Shell root–3–7 của ii–V–I ở C major”: Dm7: D–F–C. G7: G–B–F. Cmaj7: C–E–B.
- Tự động: không phải câu AI trả lời bình thường: status=fallback lý do=engine_contradiction
- Tự động: Engine bác: get_chord_tones {'symbol': 'Ebmaj7'} AI ghi 'Eb G D', Engine: 'Eb G Bb D'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Dm7'} AI ghi 'D F C', Engine: 'D F A C'
- Tự động: Engine bác: get_chord_tones {'symbol': 'G7'} AI ghi 'G B F', Engine: 'G B D F'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Cmaj7'} AI ghi 'C E B', Engine: 'C E G B'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Ebmaj7'} AI ghi 'Eb G D', Engine: 'Eb G Bb D'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Dm7'} AI ghi 'D F C', Engine: 'D F A C'
- Tự động: Engine bác: get_chord_tones {'symbol': 'G7'} AI ghi 'G B F', Engine: 'G B D F'
- Tự động: Engine bác: get_chord_tones {'symbol': 'Cmaj7'} AI ghi 'C E B', Engine: 'C E G B'
- Tự động: từ chối/lộ chữ nội bộ: AI lỗi, câu dự phòng
- Ghi chú người chấm: Câu dự phòng (engine_contradiction) do máy chủ trả, nội dung đúng; Gemini trả lời đúng có thể đã bị guardrail chặn nhầm (shell voicing)

### T230 [at_phu] luồng A · người chấm: dung
- Hỏi: V7/vi trong giọng C trưởng là hợp âm gì?
- Đáp án: E7 (E G# B D)
- AI: Trong giọng C trưởng, V7/vi là hợp âm át phụ hướng về bậc vi (Am). Bậc V7/vi có cấu trúc gồm các nốt E G# B D.
- Tự động: không thấy cụm nào trong ['E7']

### T240 [at_phu] luồng B · người chấm: sai
- Hỏi: Vì sao không có V7/vii° trong giọng trưởng?
- Đáp án: vii° là hợp âm giảm, không làm chủ tạm thời
- AI: Trong giọng trưởng, bậc vii° là hợp âm ba giảm (ví dụ Bdim trong C trưởng), có nốt gốc chịu sức hút mạnh về chủ âm. Khi áp dụng dạng hợp âm bảy vào bậc vii°, ta thường dùng hợp âm bảy giảm (vii°7) hoặc bảy nửa giảm (vii°ø7) chứ không dựng V7 trên vii°, vì âm nền của V7 yêu cầu một quãng 5 đúng phía trên nốt gốc, điều này không phù hợp với cấu trúc tự nhiên của bậc vii° trong hệ thống điệu tính. Bài gần nhất với câu hỏi: L02 “Âm giai trưởng và hợp âm bảy điệu tính”.
- Ghi chú người chấm: Hiểu nhầm V7/vii° là "dựng V7 trên vii°"; lý do đúng: vii° là hợp âm giảm nên không làm chủ tạm được

### T266 [nen_tang] luồng B · người chấm: sai
- Hỏi: Bbb là nốt gì? Nó có trùng phím với nốt nào?
- Đáp án: Si giáng kép, cùng phím với A
- AI: Nốt Bbb (Si giáng kép) là nốt Si được giảm xuống hai nửa cung, bằng cách lấy nốt La làm gốc nâng lên hai nửa cung thì không phải, mà nốt Bbb giáng hai lần từ Si (B). Trên đàn piano, nốt Bbb trùng phím với nốt La (A) hoặc Sol# (nếu xét theo cấu tạo quãng, nhưng thực tế đồng âm với La tự nhiên). Music Engine chưa tính được chi tiết mục này. Bài gần nhất với câu hỏi: L01 “Từ bàn phím đến hợp âm ba nốt”.
- Ghi chú người chấm: Bbb trùng phím A nhưng ghi thêm "hoặc Sol#" (sai) và câu đầu lủng củng

### T274 [ngoai_bai] luồng A · người chấm: khong_tra_loi
- Hỏi: Cadence V–I gọi là gì?
- Đáp án: Kết hoàn toàn (authentic cadence)
- AI: Mình không biết câu này vì các bài học hiện có chưa dạy, nên mình không đoán.
- Tự động: từ chối/lộ chữ nội bộ: nói không biết vì bài chưa dạy
- Tự động: không thấy cụm nào trong ['authentic', 'hoàn toàn', 'kết trọn', 'kết chính']…
- Ghi chú người chấm: Từ chối "bài chưa dạy" dù cùng loạt hỏi IV–I, V–vi đều được trả lời

### T290 [ngoai_bai] luồng B · người chấm: sai
- Hỏi: Hợp âm bảy giảm (dim7) có đặc điểm gì về quãng?
- Đáp án: Chồng các quãng 3 thứ; chia quãng tám thành 4 phần bằng nhau
- AI: Hợp âm bảy giảm (dim7) được cấu tạo từ bốn nốt với các khoảng cách quãng ba thứ chồng lên nhau từ nốt gốc, tạo thành ba quãng ba thứ liên tiếp. Cụ thể, từ nốt gốc lên âm bậc ba là quãng ba thứ, lên âm bậc năm là quãng năm giảm, và lên âm bậc bảy là quãng bảy giảm (hoặc tương đương quãng ba trưởng từ âm bậc năm). Đặc điểm nổi bật của hợp âm bảy giảm là khoảng cách từ nốt bậc bảy giảm này lên quãng tám của nốt gốc cũng đúng bằng một quãng ba thứ. Nhờ tính đối xứng cao này, hợp âm dim7 rất bất ổn và có sức căng lớn, thường dùng để chuyển điệu linh hoạt. Bài gần nhất với câu hỏi: L02 “Âm giai trưở
- Tự động: thuật ngữ sai: 'nam giam'
- Ghi chú người chấm: Ghi d7 "tương đương quãng ba trưởng từ âm bậc năm"; từ d5 lên d7 là m3

### T291 [ngoai_bai] luồng B · người chấm: sai
- Hỏi: Hợp âm 13 thường bỏ nốt nào khi chơi trên piano?
- Đáp án: Thường bỏ nốt 11 (và có thể bỏ 5)
- AI: Khi chơi hợp âm 13 trên piano, do có quá nhiều nốt, người chơi thường lược bỏ nốt 5 và nốt 9 để tay bấm gọn hơn và âm thanh không bị đục. Nốt 3 và nốt 7 là hai nốt quan trọng nhất định phải giữ lại vì chúng xác định tính chất trưởng/thứ và màu sắc của hợp âm, trong khi nốt 13 tạo điểm nhấn ở bè trên. Bài gần nhất với câu hỏi: L01 “Từ bàn phím đến hợp âm ba nốt”.
- Tự động: không thấy cụm nào trong ['11']
- Ghi chú người chấm: Nói thường bỏ 5 và 9; thông lệ là bỏ 11 (chỏi với 3), có thể bỏ 5; 9 thường giữ

### T293 [ngoai_bai] luồng B · người chấm: dung
- Hỏi: Đàn guitar tiêu chuẩn có mấy dây và lên dây thế nào?
- Đáp án: 6 dây: E A D G B E
- AI: Đàn guitar tiêu chuẩn có 6 dây. Các dây được lên theo thứ tự từ dây trầm (dây dày nhất, ở trên cùng khi bạn nhìn từ vị trí chơi) đến dây cao (dây mảnh nhất) là: E2, A2, D3, G3, B3 và E4. Bạn có thể nhớ nhanh qua câu tiếng Anh: Elephants And Donkeys Grow Big Ears. Bài gần nhất với câu hỏi: L01 “Từ bàn phím đến hợp âm ba nốt”.
- Tự động: thiếu nốt ['E', 'A', 'D', 'G', 'B']
- Ghi chú người chấm: Đúng E2 A2 D3 G3 B3 E4; bộ chấm tự động không đọc nốt có số quãng tám

### T296 [bay_ngoai_bai, bẫy] luồng B · người chấm: sai
- Hỏi: Hợp âm Cdim7 có nốt Bb đúng không?
- Đáp án: Không; Cdim7 = C Eb Gb Bbb
- AI: Chào bạn, hợp âm Cdim7 (bảy giảm) bao gồm các nốt C, Eb, Gb và Bbb (La giáng), chứ không phải Bb. Nốt Bbb là âm bậc 7 giảm, bằng về cao độ với nốt La (A). Bài gần nhất với câu hỏi: L05 “Secondary Dominants”.
- Ghi chú người chấm: Nốt đúng (C Eb Gb Bbb) nhưng gọi Bbb là "La giáng"; Bbb là Si giáng kép, cùng phím La

### T297 [bay_ngoai_bai, bẫy] luồng B · người chấm: sai
- Hỏi: Tritone substitution của G7 là C#7 hay Db7, cái nào đúng hơn? Hay là E7?
- Đáp án: Db7 (C#7 cùng phím); không phải E7
- AI: Cả C#7 và Db7 đều đúng về mặt âm thanh vì chúng cùng là một tập hợp nốt trên đàn phím (enharmonic). Tuy nhiên, khi xét về lý thuyết hòa âm và cách chuyển giọng (voice leading), C#7 đúng hơn trong giọng C trưởng vì nó giải quyết vào Cmaj7 tốt hơn (C# chuyển nửa cung xuống C). E7 không phải là tritone substitution của G7, mà E7 là át âm (V7) của giọng La thứ (Am). Bài gần nhất với câu hỏi: L02 “Âm giai trưởng và hợp âm bảy điệu tính”.
- Ghi chú người chấm: Cho rằng C#7 "đúng hơn" Db7; quy ước viết Db7 (bII7) vì Db đi xuống C, còn C# gợi hướng đi lên D

### T298 [ten_not_viet] luồng A · người chấm: dung
- Hỏi: Viết hợp âm Cmaj7 nhưng dùng tên Đô Rê Mi giúp mình.
- Đáp án: Đô Mi Sol Si
- AI: Hợp âm Cmaj7 trong ký hiệu tên nốt tiếng Việt (Đô Rê Mi) là Đô – Mi – Sol – Si.
- Tự động: không thấy cụm nào trong ['Đô']
- Tự động: không thấy cụm nào trong ['Mi']
- Tự động: không thấy cụm nào trong ['Sol']
- Tự động: không thấy cụm nào trong ['Si']
- Ghi chú người chấm: Đúng Đô Mi Sol Si; bộ chấm tự động không nhận tên Việt

### T299 [ten_not_viet] luồng A · người chấm: sai
- Hỏi: Hợp âm Rê thứ bảy (Dm7) gồm những nốt nào theo tên Đô Rê Mi?
- Đáp án: Rê Fa La Đô
- AI: Hợp âm Dm7 được cấu tạo từ hợp âm ba thứ kết hợp với quãng bảy thứ, gồm các nốt D F A C.
- Tự động: không thấy cụm nào trong ['Rê']
- Tự động: không thấy cụm nào trong ['Fa']
- Tự động: không thấy cụm nào trong ['La']
- Tự động: không thấy cụm nào trong ['Đô']
- Ghi chú người chấm: Nốt đúng nhưng không dùng tên Đô Rê Mi như câu hỏi yêu cầu (Rê Fa La Đô)

