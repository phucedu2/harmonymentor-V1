### bm25

Đúng luồng 93.2% · B/C bị trả lời như bài học 3.5% (mục tiêu ≤ 2%) · A bị từ chối sai 2.7% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 2.7%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 35 | 1 | 0 | 1 | 0 | 95% |
| **B** | 1 | 4 | 0 | 0 | 0 | 80% |
| **C** | 0 | 1 | 23 | 0 | 0 | 96% |
| **D** | 1 | 0 | 0 | 5 | 0 | 83% |
| **G** | 0 | 0 | 0 | 0 | 2 | 100% |
| precision | 95% | 67% | 100% | 83% | 100% | |

Câu sai luồng:

- A→D (label_help+help_hit): Tập vòng ii-V-I nhanh hơn thì nên làm thế nào?
- B→A (lesson_hit): Bài hát buồn thường dùng hợp âm gì?
- C→B (unknown_terms): what is the capital of France
- D→A (lesson_hit): Mình bị khóa đăng nhập, phải làm sao?
- A→B (below_threshold_engine): cmaj7 la gi

### embedding:multilingual-e5-small-hm-gd2b

Đúng luồng 94.6% · B/C bị trả lời như bài học 0.0% (mục tiêu ≤ 2%) · A bị từ chối sai 5.4% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 2.7%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 34 | 2 | 0 | 1 | 0 | 92% |
| **B** | 0 | 5 | 0 | 0 | 0 | 100% |
| **C** | 0 | 1 | 23 | 0 | 0 | 96% |
| **D** | 0 | 0 | 0 | 6 | 0 | 100% |
| **G** | 0 | 0 | 0 | 0 | 2 | 100% |
| precision | 100% | 62% | 100% | 86% | 100% | |

Câu sai luồng:

- A→B (below_threshold_engine): Hợp âm Eb trưởng có những nốt nào?
- A→D (label_help+help_hit): Tập vòng ii-V-I nhanh hơn thì nên làm thế nào?
- C→B (unknown_terms): what is the capital of France
- A→B (no_lesson_hit): What is a half-diminished chord?

### embedding:multilingual-e5-small

Đúng luồng 93.2% · B/C bị trả lời như bài học 0.0% (mục tiêu ≤ 2%) · A bị từ chối sai 8.1% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 2.7%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 33 | 3 | 1 | 0 | 0 | 89% |
| **B** | 0 | 5 | 0 | 0 | 0 | 100% |
| **C** | 0 | 1 | 23 | 0 | 0 | 96% |
| **D** | 0 | 0 | 0 | 6 | 0 | 100% |
| **G** | 0 | 0 | 0 | 0 | 2 | 100% |
| precision | 100% | 56% | 96% | 100% | 100% | |

Câu sai luồng:

- A→B (no_lesson_hit): Quãng tăng và quãng giảm nghĩa là gì?
- A→C (not_music_low_score): Tập vòng ii-V-I nhanh hơn thì nên làm thế nào?
- C→B (unknown_terms): what is the capital of France
- A→B (below_threshold_engine): cmaj7 la gi
- A→B (no_lesson_hit): What is a half-diminished chord?
