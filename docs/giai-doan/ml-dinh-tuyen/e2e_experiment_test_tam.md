### bm25

Đúng luồng 86.5% · B/C bị trả lời như bài học 7.8% (mục tiêu ≤ 2%) · A bị từ chối sai 9.0% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 0.0%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 101 | 8 | 1 | 1 | 0 | 91% |
| **B** | 4 | 32 | 2 | 0 | 0 | 84% |
| **C** | 0 | 0 | 11 | 2 | 0 | 85% |
| **D** | 1 | 1 | 1 | 19 | 1 | 83% |
| **G** | 0 | 0 | 5 | 0 | 10 | 67% |
| precision | 95% | 78% | 55% | 86% | 91% | |

Câu sai luồng:

- A→B (gray_zone_conservative): 7 ten not co ban la nhung not nao
- A→D (label_help+help_hit): phim trang tren piano ten gi
- A→C (not_music_low_score): phim den co ten rieng ko hay fai goi theo phim trang
- A→B (gray_zone_conservative): hỏi ngu tí: F là ♭7 của hợp âm nào ạ
- A→B (no_lesson_hit): ad ơi dominant là gì với
- A→B (no_lesson_hit): dominatn là gì
- A→B (gray_zone_conservative): quang giam la j
- A→B (gray_zone_conservative): muon biet mot hop am la truong hay thu thi dem sao
- A→B (gray_zone_conservative): root của hợp âm là gì
- A→B (gray_zone_conservative): root cua hop am la gi
- B→C (not_music_low_score): counterpoint học có khó không
- B→C (unknown_terms_not_music): counterpoint hoc co kho ko
- B→A (lesson_hit): chuyển giọng là j
- B→A (lesson_hit): dịch giọng một bài hát sang tông khác làm sao
- B→A (lesson_hit): cadence là gì, có mấy loại
- B→A (lesson_hit): cadence là j, có mấy loại
- C→D (label_help+help_hit): bài tập vật lý về lực ma sát làm sao
- C→D (label_help+help_hit): cách làm bài nghị lunậ xã hội
- D→C (label_out_of_scope): sao app gợi ý cho mnìh bài này
- D→G (label_greeting): mik muốn biết mik đã học đc bn
- D→A (lesson_hit): có chỗ nào luyện riêng phần quãng ko
- D→B (gray_zone_conservative): có chỗ nào luyn riêng phần quãng không
- G→C (label_out_of_scope): hi, hôm nay mình định ôn lại cúht
- G→C (not_music_low_score): cảm ơn nha, hôm nay học thú vị ghê
- G→C (not_music_low_score): thầy ơi cho em hỏi cảm ơn nha, hôm nay học thú vị ghê với
- G→C (not_music_low_score): thầy ơi cho em hỏi thanks bạn, bài này dễ hiểu quá với
- G→C (not_music_low_score): bạn ơi cám ơn, mai mình học tiếp nhỉ

### embedding:multilingual-e5-small

Đúng luồng 88.0% · B/C bị trả lời như bài học 7.8% (mục tiêu ≤ 2%) · A bị từ chối sai 6.3% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 0.0%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 104 | 5 | 1 | 1 | 0 | 94% |
| **B** | 4 | 32 | 2 | 0 | 0 | 84% |
| **C** | 0 | 0 | 11 | 2 | 0 | 85% |
| **D** | 2 | 0 | 1 | 19 | 1 | 83% |
| **G** | 0 | 0 | 5 | 0 | 10 | 67% |
| precision | 94% | 86% | 55% | 86% | 91% | |

Câu sai luồng:

- A→B (gray_zone_conservative): so quang dem theo chu cai hay theo phim
- A→B (gray_zone_conservative): 7 ten not co ban la nhung not nao
- A→D (label_help+help_hit): phim trang tren piano ten gi
- A→C (not_music_low_score): phim den co ten rieng ko hay fai goi theo phim trang
- A→B (gray_zone_conservative): quang giam la j
- A→B (no_lesson_hit): muon biet mot hop am la truong hay thu thi dem sao
- A→B (gray_zone_conservative): root cua hop am la gi
- B→C (not_music_low_score): counterpoint học có khó không
- B→C (unknown_terms_not_music): counterpoint hoc co kho ko
- B→A (lesson_hit): chuyển giọng là j
- B→A (lesson_hit): dịch giọng một bài hát sang tông khác làm sao
- B→A (lesson_hit): cadence là gì, có mấy loại
- B→A (lesson_hit): cadence là j, có mấy loại
- C→D (label_help+help_hit): bài tập vật lý về lực ma sát làm sao
- C→D (label_help+help_hit): cách làm bài nghị lunậ xã hội
- D→C (label_out_of_scope): sao app gợi ý cho mnìh bài này
- D→G (label_greeting): mik muốn biết mik đã học đc bn
- D→A (lesson_hit): có chỗ nào luyện riêng phần quãng ko
- D→A (lesson_hit): có chỗ nào luyn riêng phần quãng không
- G→C (label_out_of_scope): hi, hôm nay mình định ôn lại cúht
- G→C (not_music_low_score): cảm ơn nha, hôm nay học thú vị ghê
- G→C (not_music_low_score): thầy ơi cho em hỏi cảm ơn nha, hôm nay học thú vị ghê với
- G→C (not_music_low_score): thầy ơi cho em hỏi thanks bạn, bài này dễ hiểu quá với
- G→C (not_music_low_score): bạn ơi cám ơn, mai mình học tiếp nhỉ
