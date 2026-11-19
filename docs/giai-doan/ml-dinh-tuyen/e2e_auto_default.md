### bm25

Đúng luồng 96.0% · B/C bị trả lời như bài học 3.5% (mục tiêu ≤ 2%) · A bị từ chối sai 2.7% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 2.7%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 35 | 1 | 0 | 1 | 0 | 95% |
| **B** | 1 | 4 | 0 | 0 | 0 | 80% |
| **C** | 0 | 0 | 24 | 0 | 0 | 100% |
| **D** | 0 | 0 | 0 | 6 | 0 | 100% |
| **G** | 0 | 0 | 0 | 0 | 2 | 100% |
| precision | 97% | 80% | 100% | 86% | 100% | |

Câu sai luồng:

- A→D (label_help+help_hit): Tập vòng ii-V-I nhanh hơn thì nên làm thế nào?
- B→A (lesson_hit): Bài hát buồn thường dùng hợp âm gì?
- A→B (below_threshold_engine): cmaj7 la gi

### embedding:multilingual-e5-small

Đúng luồng 97.3% · B/C bị trả lời như bài học 3.5% (mục tiêu ≤ 2%) · A bị từ chối sai 2.7% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 0.0%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 36 | 0 | 0 | 1 | 0 | 97% |
| **B** | 1 | 4 | 0 | 0 | 0 | 80% |
| **C** | 0 | 0 | 24 | 0 | 0 | 100% |
| **D** | 0 | 0 | 0 | 6 | 0 | 100% |
| **G** | 0 | 0 | 0 | 0 | 2 | 100% |
| precision | 97% | 100% | 100% | 86% | 100% | |

Câu sai luồng:

- A→D (label_help+help_hit): Tập vòng ii-V-I nhanh hơn thì nên làm thế nào?
- B→A (lesson_hit): Bài hát buồn thường dùng hợp âm gì?
