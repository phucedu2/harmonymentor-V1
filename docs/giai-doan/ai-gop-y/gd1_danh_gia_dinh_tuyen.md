### bm25

Đúng luồng 94.6% · B/C bị trả lời như bài học 3.5% (mục tiêu ≤ 2%) · A bị từ chối sai 5.4% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 0.0%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 35 | 0 | 0 | 2 | 0 | 95% |
| **B** | 1 | 4 | 0 | 0 | 0 | 80% |
| **C** | 0 | 1 | 23 | 0 | 0 | 96% |
| **D** | 0 | 0 | 0 | 6 | 0 | 100% |
| **G** | 0 | 0 | 0 | 0 | 2 | 100% |
| precision | 97% | 80% | 100% | 75% | 100% | |

Câu sai luồng:

- A→D (label_help+help_hit): Phím đen trên đàn piano được gọi tên ra sao?
- A→D (label_help+help_hit): Tập vòng ii-V-I nhanh hơn thì nên làm thế nào?
- B→A (lesson_hit): Bài hát buồn thường dùng hợp âm gì?
- C→B (unknown_terms): what is the capital of France

### embedding:multilingual-e5-small

Đúng luồng 91.9% · B/C bị trả lời như bài học 3.5% (mục tiêu ≤ 2%) · A bị từ chối sai 10.8% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 0.0%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 33 | 2 | 0 | 2 | 0 | 89% |
| **B** | 1 | 4 | 0 | 0 | 0 | 80% |
| **C** | 0 | 1 | 23 | 0 | 0 | 96% |
| **D** | 0 | 0 | 0 | 6 | 0 | 100% |
| **G** | 0 | 0 | 0 | 0 | 2 | 100% |
| precision | 97% | 57% | 100% | 75% | 100% | |

Câu sai luồng:

- A→D (label_help+help_hit): Phím đen trên đàn piano được gọi tên ra sao?
- A→B (no_lesson_hit): Quãng tăng và quãng giảm nghĩa là gì?
- A→D (label_help+help_hit): Tập vòng ii-V-I nhanh hơn thì nên làm thế nào?
- B→A (lesson_hit): Bài hát buồn thường dùng hợp âm gì?
- C→B (unknown_terms): what is the capital of France
- A→B (no_lesson_hit): What is a half-diminished chord?
