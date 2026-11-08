### bm25

Đúng luồng 82.0% · B/C bị trả lời như bài học 5.9% (mục tiêu ≤ 2%) · A bị từ chối sai 22.7% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 0.0%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 17 | 5 | 0 | 0 | 0 | 77% |
| **B** | 1 | 9 | 0 | 0 | 0 | 90% |
| **C** | 0 | 0 | 7 | 0 | 0 | 100% |
| **D** | 0 | 0 | 1 | 5 | 0 | 83% |
| **G** | 0 | 0 | 2 | 0 | 3 | 60% |
| precision | 94% | 64% | 70% | 100% | 100% | |

Câu sai luồng:

- A→B (gray_zone_conservative): subdominant la hop am bac may trong C
- G→C (not_music_low_score): chao buoi sang, hom nay hoc gi day
- A→B (no_lesson_hit): ham tonic la gi, cho vi du
- A→B (gray_zone_conservative): V7/vi trong C la hop am nao
- A→B (gray_zone_conservative): dominant keo ve dau vay
- A→B (gray_zone_conservative): at phu la gi vay
- B→A (engine_in_kb): Dm7b5 gom nhung not nao
- D→C (not_music_low_score): xuat file nhac ra mp3 o dau
- G→C (label_out_of_scope): cam on nha, hom nay hoc vui qua

### embedding:multilingual-e5-small

Đúng luồng 86.0% · B/C bị trả lời như bài học 5.9% (mục tiêu ≤ 2%) · A bị từ chối sai 13.6% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 0.0%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 19 | 3 | 0 | 0 | 0 | 86% |
| **B** | 1 | 9 | 0 | 0 | 0 | 90% |
| **C** | 0 | 0 | 7 | 0 | 0 | 100% |
| **D** | 0 | 0 | 1 | 5 | 0 | 83% |
| **G** | 0 | 0 | 2 | 0 | 3 | 60% |
| precision | 95% | 75% | 70% | 100% | 100% | |

Câu sai luồng:

- A→B (gray_zone_conservative): Fb va E co giong nhau ko, sao lai co 2 ten
- G→C (not_music_low_score): chao buoi sang, hom nay hoc gi day
- A→B (no_lesson_hit): chuc nang cua hop am la gi, sao ko chi nhin ten hop am
- A→B (no_lesson_hit): at phu la gi vay
- B→A (lesson_hit): Dm7b5 gom nhung not nao
- D→C (not_music_low_score): xuat file nhac ra mp3 o dau
- G→C (label_out_of_scope): cam on nha, hom nay hoc vui qua

### embedding:multilingual-e5-small-hm-gd2b

Đúng luồng 80.0% · B/C bị trả lời như bài học 5.9% (mục tiêu ≤ 2%) · A bị từ chối sai 22.7% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 4.5%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 16 | 6 | 0 | 0 | 0 | 73% |
| **B** | 1 | 9 | 0 | 0 | 0 | 90% |
| **C** | 0 | 0 | 7 | 0 | 0 | 100% |
| **D** | 0 | 0 | 1 | 5 | 0 | 83% |
| **G** | 0 | 0 | 2 | 0 | 3 | 60% |
| precision | 94% | 60% | 70% | 100% | 100% | |

Câu sai luồng:

- A→B (below_threshold_engine): dem quang tu E len B la quang may, chat luong gi
- A→B (no_lesson_hit): Fb va E co giong nhau ko, sao lai co 2 ten
- G→C (not_music_low_score): chao buoi sang, hom nay hoc gi day
- A→B (no_lesson_hit): ham tonic la gi, cho vi du
- A→B (no_lesson_hit): 1 nua cung tren piano la tu phim nao sang phim nao
- A→B (no_lesson_hit): quang 3 truong tu C len la nốt nào ạ
- A→B (no_lesson_hit): at phu la gi vay
- B→A (lesson_hit): Dm7b5 gom nhung not nao
- D→C (not_music_low_score): xuat file nhac ra mp3 o dau
- G→C (label_out_of_scope): cam on nha, hom nay hoc vui qua

### embedding:multilingual-e5-small-hm-gd2c

Đúng luồng 82.0% · B/C bị trả lời như bài học 5.9% (mục tiêu ≤ 2%) · A bị từ chối sai 18.2% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 4.5%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 17 | 5 | 0 | 0 | 0 | 77% |
| **B** | 1 | 9 | 0 | 0 | 0 | 90% |
| **C** | 0 | 0 | 7 | 0 | 0 | 100% |
| **D** | 0 | 0 | 1 | 5 | 0 | 83% |
| **G** | 0 | 0 | 2 | 0 | 3 | 60% |
| precision | 94% | 64% | 70% | 100% | 100% | |

Câu sai luồng:

- A→B (below_threshold_engine): dem quang tu E len B la quang may, chat luong gi
- A→B (no_lesson_hit): Fb va E co giong nhau ko, sao lai co 2 ten
- G→C (not_music_low_score): chao buoi sang, hom nay hoc gi day
- A→B (no_lesson_hit): quang 3 truong tu C len la nốt nào ạ
- A→B (gray_zone_conservative): chuc nang cua hop am la gi, sao ko chi nhin ten hop am
- A→B (no_lesson_hit): dominant keo ve dau vay
- B→A (lesson_hit): Dm7b5 gom nhung not nao
- D→C (not_music_low_score): xuat file nhac ra mp3 o dau
- G→C (label_out_of_scope): cam on nha, hom nay hoc vui qua
