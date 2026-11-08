### bm25

Đúng luồng 94.6% · B/C bị trả lời như bài học 3.5% (mục tiêu ≤ 2%) · A bị từ chối sai 2.7% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 2.7%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 35 | 1 | 0 | 1 | 0 | 95% |
| **B** | 1 | 4 | 0 | 0 | 0 | 80% |
| **C** | 0 | 1 | 23 | 0 | 0 | 96% |
| **D** | 0 | 0 | 0 | 6 | 0 | 100% |
| **G** | 0 | 0 | 0 | 0 | 2 | 100% |
| precision | 97% | 67% | 100% | 86% | 100% | |

Câu sai luồng:

- A→D (label_help+help_hit): Tập vòng ii-V-I nhanh hơn thì nên làm thế nào?
- B→A (lesson_hit): Bài hát buồn thường dùng hợp âm gì?
- C→B (unknown_terms): what is the capital of France
- A→B (below_threshold_engine): cmaj7 la gi

### embedding:multilingual-e5-small

Đúng luồng 94.6% · B/C bị trả lời như bài học 3.5% (mục tiêu ≤ 2%) · A bị từ chối sai 5.4% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 0.0%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 35 | 1 | 0 | 1 | 0 | 95% |
| **B** | 1 | 4 | 0 | 0 | 0 | 80% |
| **C** | 0 | 1 | 23 | 0 | 0 | 96% |
| **D** | 0 | 0 | 0 | 6 | 0 | 100% |
| **G** | 0 | 0 | 0 | 0 | 2 | 100% |
| precision | 97% | 67% | 100% | 86% | 100% | |

Câu sai luồng:

- A→D (label_help+help_hit): Tập vòng ii-V-I nhanh hơn thì nên làm thế nào?
- B→A (lesson_hit): Bài hát buồn thường dùng hợp âm gì?
- C→B (unknown_terms): what is the capital of France
- A→B (gray_zone_conservative): What is a half-diminished chord?

### embedding:multilingual-e5-small-hm-gd2b

Đúng luồng 96.0% · B/C bị trả lời như bài học 0.0% (mục tiêu ≤ 2%) · A bị từ chối sai 5.4% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 0.0%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 35 | 1 | 0 | 1 | 0 | 95% |
| **B** | 0 | 5 | 0 | 0 | 0 | 100% |
| **C** | 0 | 1 | 23 | 0 | 0 | 96% |
| **D** | 0 | 0 | 0 | 6 | 0 | 100% |
| **G** | 0 | 0 | 0 | 0 | 2 | 100% |
| precision | 100% | 71% | 100% | 86% | 100% | |

Câu sai luồng:

- A→D (label_help+help_hit): Tập vòng ii-V-I nhanh hơn thì nên làm thế nào?
- C→B (unknown_terms): what is the capital of France
- A→B (gray_zone_conservative): What is a half-diminished chord?

### embedding:multilingual-e5-small-hm-gd2c

Đúng luồng 97.3% · B/C bị trả lời như bài học 0.0% (mục tiêu ≤ 2%) · A bị từ chối sai 2.7% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 0.0%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 36 | 0 | 0 | 1 | 0 | 97% |
| **B** | 0 | 5 | 0 | 0 | 0 | 100% |
| **C** | 0 | 1 | 23 | 0 | 0 | 96% |
| **D** | 0 | 0 | 0 | 6 | 0 | 100% |
| **G** | 0 | 0 | 0 | 0 | 2 | 100% |
| precision | 100% | 83% | 100% | 86% | 100% | |

Câu sai luồng:

- A→D (label_help+help_hit): Tập vòng ii-V-I nhanh hơn thì nên làm thế nào?
- C→B (unknown_terms): what is the capital of France
