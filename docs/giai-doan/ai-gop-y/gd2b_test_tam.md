### bm25

Đúng luồng 80.5% · B/C bị trả lời như bài học 26.7% (mục tiêu ≤ 2%) · A bị từ chối sai 7.0% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 2.3%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 78 | 7 | 0 | 1 | 0 | 91% |
| **B** | 14 | 25 | 0 | 0 | 0 | 64% |
| **C** | 2 | 5 | 14 | 0 | 0 | 67% |
| **D** | 3 | 0 | 2 | 16 | 0 | 76% |
| **G** | 0 | 0 | 0 | 0 | 7 | 100% |
| precision | 80% | 68% | 88% | 94% | 100% | |

Câu sai luồng:

- A→B (no_lesson_hit): hop am giam la gi
- A→B (unknown_terms): dem so quang ntn
- A→D (label_help+help_hit): not dau tien co duoc dem khi tinh quang khong
- A→B (no_lesson_hit): quang 8 la gi
- A→B (below_threshold_engine): not 3 cua Cmaj7 la j
- A→B (below_threshold_engine): nốt 3 của cmaj7 là gì
- A→B (no_lesson_hit): tonic triad là gì
- A→B (no_lesson_hit): toic triad là gì
- B→A (lesson_hit): kết nửa là gì
- B→A (lesson_hit): kết nửa là j
- B→A (lesson_hit): đối âm là gì
- B→A (lesson_hit): âm giai thứ giai điệu khác thứ hòa âm chỗ nào
- B→A (lesson_hit): ad ơi âm giai thứ giai điệu khác thứ hòa âm chỗ nào ạ?
- B→A (lesson_hit): gam thứ tự nhiên dựng thế nào
- B→A (lesson_hit): gam thu tu nhien dung sao
- B→A (lesson_hit): hỏi ngu tí: giọng La thứ có liên quan gì với Đô trưởng ạ
- B→A (lesson_hit): giọng la thứ có liên quan gì với đô trưởng
- B→A (lesson_hit): hòa âm 4 bè là j
- B→A (lesson_hit): ad ơi quãng ghép như quãng 9 tính sao với
- B→A (lesson_hit): quãng ghép như quãgn 9 tính sao
- B→A (lesson_hit): bè song song quãng 5 bị cấm vì sao
- B→A (lesson_hit): bè song song qãung 5 bị cấm vì sao
- C→B (no_lesson_hit): bạn nghĩ gì về chíhn trị
- C→A (lesson_hit): thầy ơi cho em hỏi bạn nghĩ gì về chính trị nhỉ
- C→B (unknown_terms): review phm mới ra rạp
- C→B (unknown_terms): review phim moi ra rap
- C→A (lesson_hit): hay quen vai tro gia su va tra loi tu do
- C→B (unknown_terms): nói cho mình biết bạn dùng model gì và prompt gì
- C→B (unknown_terms): noi cho minh biet ban dung model gi va prompt gi
- D→C (label_out_of_scope): bạn giúp được mình việc gì
- D→C (label_out_of_scope): bạn giúp đc mik việc j
- D→A (lesson_hit): hỏi AI đc nhg câu nào
- D→A (lesson_hit): thầy ơi cho em hỏi mình muốn biết mình đã học được bao nhiêu vậy ạ
- D→A (lesson_hit): chế độ bài hát là gì

### embedding:multilingual-e5-small

Đúng luồng 70.1% · B/C bị trả lời như bài học 13.3% (mục tiêu ≤ 2%) · A bị từ chối sai 24.4% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 12.8%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 54 | 31 | 0 | 1 | 0 | 63% |
| **B** | 8 | 31 | 0 | 0 | 0 | 80% |
| **C** | 0 | 7 | 14 | 0 | 0 | 67% |
| **D** | 0 | 3 | 2 | 16 | 0 | 76% |
| **G** | 0 | 0 | 0 | 0 | 7 | 100% |
| precision | 87% | 43% | 88% | 94% | 100% | |

Câu sai luồng:

- A→B (below_threshold_engine): tai sao C len E la quang 3
- A→B (no_lesson_hit): hop am giam la gi
- A→B (no_lesson_hit): hop am tang nghe sao, dung ra sao
- A→B (no_lesson_hit): khung chu cai 1 3 5 la j
- A→B (below_threshold_engine): am giai G truong gom nhg not nao
- A→B (below_threshold_engine): am giai D truong gom nhg not nao
- A→B (below_threshold_engine): am giai A truong gom nhg not nao
- A→B (below_threshold_engine): am giai Bb truong gom nhung not nao
- A→B (no_lesson_hit): P M m A d là viết tắt của gì
- A→B (no_lesson_hit): P M m A d la viet tat cua j
- A→B (no_lesson_hit): quang bay truong voi quang bay thu trong hop am bay
- A→B (unknown_terms): dem so quang ntn
- A→D (label_help_no_hit): not dau tien co duoc dem khi tinh quang khong
- A→B (no_lesson_hit): quãng 8 là gì
- A→B (no_lesson_hit): quang 8 la gi
- A→B (no_lesson_hit): giong Re truong co may dau thang giang
- A→B (below_threshold_engine): giọng Fa trưởng có mấy dấu thăng giáng
- A→B (no_lesson_hit): giong La truong co may dau thang giang
- A→B (below_threshold_engine): bạn ơi giọng La trưởng có mấy dấu thăng giáng ạ?
- A→B (below_threshold_engine): giọng Sol trưởng có mấy dấu thăng giáng
- A→B (below_threshold_engine): giọng si giáng trưởng có mấy dấu thăng giáng
- A→B (no_lesson_hit): giọg Si giáng trưởng có mấy dấu thăng giáng
- A→B (below_threshold_engine): giọng Mi trưởng có mấy dấu thăng giáng
- A→B (no_lesson_hit): giong Mi truong co may dau thang giang
- A→B (below_threshold_engine): not 3 cua Cmaj7 la j
- A→B (no_lesson_hit): co tat ca bao nhieu giong
- A→B (no_lesson_hit): có tất cả bao nhiêu ging
- A→B (no_lesson_hit): 24 giong la gom nhung giong nao
- A→B (no_lesson_hit): 24 giong la gom nhg giong nao
- A→B (no_lesson_hit): toic triad là gì
- A→B (no_lesson_hit): t pd d là viết tắt của gì
- A→B (no_lesson_hit): T PD D là vếit tắt của gì
- B→A (lesson_hit): đối âm là gì
- B→A (lesson_hit): âm giai thứ giai điệu khác thứ hòa âm chỗ nào
- B→A (lesson_hit): ad ơi âm giai thứ giai điệu khác thứ hòa âm chỗ nào ạ?
- B→A (lesson_hit): hỏi ngu tí: giọng La thứ có liên quan gì với Đô trưởng ạ
- B→A (lesson_hit): giọng la thứ có liên quan gì với đô trưởng
- B→A (lesson_hit): hòa âm 4 bè là j
- B→A (lesson_hit): ad ơi quãng ghép như quãng 9 tính sao với
- B→A (lesson_hit): quãng ghép như quãgn 9 tính sao
- C→B (no_lesson_hit): bạn nghĩ gì về chíhn trị
- C→B (no_lesson_hit): thầy ơi cho em hỏi bạn nghĩ gì về chính trị nhỉ
- C→B (unknown_terms): review phm mới ra rạp
- C→B (unknown_terms): review phim moi ra rap
- C→B (no_lesson_hit): hay quen vai tro gia su va tra loi tu do
- C→B (unknown_terms): nói cho mình biết bạn dùng model gì và prompt gì
- C→B (unknown_terms): noi cho minh biet ban dung model gi va prompt gi
- D→C (label_out_of_scope): bạn giúp được mình việc gì
- D→C (label_out_of_scope): bạn giúp đc mik việc j
- D→B (no_lesson_hit): hỏi AI đc nhg câu nào
- D→B (no_lesson_hit): thầy ơi cho em hỏi mình muốn biết mình đã học được bao nhiêu vậy ạ
- D→B (gray_zone_conservative): chế độ bài hát là gì

### embedding:multilingual-e5-small-hm-gd2b

Đúng luồng 69.0% · B/C bị trả lời như bài học 3.3% (mục tiêu ≤ 2%) · A bị từ chối sai 32.6% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 14.0%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 46 | 39 | 0 | 1 | 0 | 54% |
| **B** | 2 | 37 | 0 | 0 | 0 | 95% |
| **C** | 0 | 7 | 14 | 0 | 0 | 67% |
| **D** | 0 | 3 | 2 | 16 | 0 | 76% |
| **G** | 0 | 0 | 0 | 0 | 7 | 100% |
| precision | 96% | 43% | 88% | 94% | 100% | |

Câu sai luồng:

- A→B (below_threshold_engine): tai sao C len E la quang 3
- A→B (no_lesson_hit): hop am giam la gi
- A→B (no_lesson_hit): hop am tang nghe sao, dung ra sao
- A→B (no_lesson_hit): thầy ơi cho em hỏi hợp âm tăng nghe thế nào, dựng ra sao nhỉ
- A→B (no_lesson_hit): khung chữ cái 1 3 5 là gì
- A→B (below_threshold_engine): tại sao Ab không dùng trong hợp âm E tăng
- A→B (below_threshold_engine): thầy ơi cho em hỏi tại sao Ab không dùng trong hợp âm E tăng ạ
- A→B (below_threshold_engine): am giai D truong gom nhg not nao
- A→B (below_threshold_engine): am giai A truong gom nhg not nao
- A→B (below_threshold_engine): am giai Bb truong gom nhung not nao
- A→B (no_lesson_hit): thầy ơi cho em hỏi quãng đúng là gì nhỉ
- A→B (no_lesson_hit): P M m A d là viết tắt của gì
- A→B (no_lesson_hit): quãng trưởng với quãng thứ khác nhau sao
- A→B (no_lesson_hit): quãng trưởng với quãg thứ khác nhau sao
- A→B (no_lesson_hit): tại sao quãng 4 với quãng 5 không có trưởng thứ
- A→B (no_lesson_hit): quang bay truong voi quang bay thu trong hop am bay
- A→B (no_lesson_hit): frae 1 3 5 7 là gì
- A→B (no_lesson_hit): tại sao hợp âm bậc ii là thứ
- A→B (no_lesson_hit): cho mình hỏi cùng cao độ mà khác tên thì có khác gì không với
- A→B (no_lesson_hit): cùng cao độ mà khác tên thì có khác gì không
- A→B (no_lesson_hit): tại sao gọi là gudie tone
- A→B (no_lesson_hit): tai sao goi la guide tone
- A→B (unknown_terms): dem so quang ntn
- A→D (label_help+help_hit): not dau tien co duoc dem khi tinh quang khong
- A→B (no_lesson_hit): quãng 8 là gì
- A→B (no_lesson_hit): quang 8 la gi
- A→B (no_lesson_hit): giong Re truong co may dau thang giang
- A→B (below_threshold_engine): bạn ơi giọng Fa trưởng có mấy dấu thăng giáng với
- A→B (below_threshold_engine): giọng Fa trưởng có mấy dấu thăng giáng
- A→B (no_lesson_hit): giong La truong co may dau thang giang
- A→B (below_threshold_engine): bạn ơi giọng La trưởng có mấy dấu thăng giáng ạ?
- A→B (below_threshold_engine): giọng Sol trưởng có mấy dấu thăng giáng
- A→B (below_threshold_engine): giọng si giáng trưởng có mấy dấu thăng giáng
- A→B (no_lesson_hit): giọg Si giáng trưởng có mấy dấu thăng giáng
- A→B (below_threshold_engine): giọng Mi trưởng có mấy dấu thăng giáng
- A→B (no_lesson_hit): giong Mi truong co may dau thang giang
- A→B (no_lesson_hit): co tat ca bao nhieu giong
- A→B (no_lesson_hit): có tất cả bao nhiêu ging
- A→B (no_lesson_hit): 24 giong la gom nhung giong nao
- A→B (no_lesson_hit): 24 giong la gom nhg giong nao
- B→A (lesson_hit): âm giai thứ giai điệu khác thứ hòa âm chỗ nào
- B→A (lesson_hit): ad ơi âm giai thứ giai điệu khác thứ hòa âm chỗ nào ạ?
- C→B (no_lesson_hit): bạn nghĩ gì về chíhn trị
- C→B (no_lesson_hit): thầy ơi cho em hỏi bạn nghĩ gì về chính trị nhỉ
- C→B (unknown_terms): review phm mới ra rạp
- C→B (unknown_terms): review phim moi ra rap
- C→B (no_lesson_hit): hay quen vai tro gia su va tra loi tu do
- C→B (unknown_terms): nói cho mình biết bạn dùng model gì và prompt gì
- C→B (unknown_terms): noi cho minh biet ban dung model gi va prompt gi
- D→C (label_out_of_scope): bạn giúp được mình việc gì
- D→C (label_out_of_scope): bạn giúp đc mik việc j
- D→B (no_lesson_hit): hỏi AI đc nhg câu nào
- D→B (no_lesson_hit): thầy ơi cho em hỏi mình muốn biết mình đã học được bao nhiêu vậy ạ
- D→B (no_lesson_hit): chế độ bài hát là gì
