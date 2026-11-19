### bm25

Đúng luồng 94.6% · B/C bị trả lời như bài học 3.5% (mục tiêu ≤ 2%) · A bị từ chối sai 5.4% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 2.7%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 34 | 1 | 2 | 0 | 0 | 92% |
| **B** | 1 | 4 | 0 | 0 | 0 | 80% |
| **C** | 0 | 0 | 24 | 0 | 0 | 100% |
| **D** | 0 | 0 | 0 | 6 | 0 | 100% |
| **G** | 0 | 0 | 0 | 0 | 2 | 100% |
| precision | 97% | 80% | 92% | 100% | 100% | |

Câu sai luồng:

- A→C (label_out_of_scope): Tiền át (predominant) có vai trò gì?
- A→C (label_out_of_scope): Tập vòng ii-V-I nhanh hơn thì nên làm thế nào?
- B→A (lesson_hit): Bài hát buồn thường dùng hợp âm gì?
- A→B (below_threshold_engine): cmaj7 la gi

### embedding:multilingual-e5-small

Đúng luồng 96.0% · B/C bị trả lời như bài học 3.5% (mục tiêu ≤ 2%) · A bị từ chối sai 5.4% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 0.0%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 35 | 0 | 2 | 0 | 0 | 95% |
| **B** | 1 | 4 | 0 | 0 | 0 | 80% |
| **C** | 0 | 0 | 24 | 0 | 0 | 100% |
| **D** | 0 | 0 | 0 | 6 | 0 | 100% |
| **G** | 0 | 0 | 0 | 0 | 2 | 100% |
| precision | 97% | 100% | 92% | 100% | 100% | |

Câu sai luồng:

- A→C (label_out_of_scope): Tiền át (predominant) có vai trò gì?
- A→C (label_out_of_scope): Tập vòng ii-V-I nhanh hơn thì nên làm thế nào?
- B→A (lesson_hit): Bài hát buồn thường dùng hợp âm gì?
