# Kết quả model nhận diện nốt so với YIN (ADR-030 bước 2)

Ngày chạy: 2026-11-19. Lệnh: `python scripts/ai/pitch/du_lieu.py` rồi `python scripts/ai/pitch/train.py --seed 42` (xem đầu file train.py). Máy: container cloud, CPU, scikit-learn.

> Đo trên mẫu nhạc cụ thu sẵn (thư viện CC0/CC BY) và giọng hát tổng hợp, có thêm nhiễu. **Chưa chứng minh chất lượng với micro thật của người học**: phòng ồn, micro laptop, đàn lệch dây sẽ khác.

## Dữ liệu

- 33935 khung 2048 mẫu (≈ 43 ms ở 48 kHz), 843 nhóm bản thu, nốt MIDI 40–88 (49 nốt) + lớp 0 "không có nốt" (3000 khung ù/ồn).
- Train: 27040 khung / 674 nhóm. Test (khung có nốt): 6335 khung / 113 nhóm (chia theo bản thu: mọi bản dịch cao độ/thêm nhiễu của một bản thu nằm cùng một phía).
- Nhạc cụ: bass 3225, cello 4915, clav 1975, epiano 2775, guitar 7470, guitar_mute 780, nen 3000, piano 4500, upright 2295, voice 3000.
- Mỗi khung có 5 phiên bản điều kiện thu: Sạch, Nhiễu trắng 15 dB, Nhiễu trắng 5 dB (rất ồn), Micro laptop (mất trầm < 250 Hz + nhiễu hồng), Tiếng ù điện 50 Hz.

## Chọn tham số (GridSearchCV, GroupKFold 4 phần, chỉ trên tập train)

| Lớp ẩn | alpha (L2) | Điểm train | Điểm kiểm định |
|---|---|---|---|
| (128,) | 0.0001 | 99,9% | 97,5% |
| (128,) | 0.01 | 99,9% | 97,5% |
| (128, 64) | 0.01 | 99,8% | 97,3% |
| (64,) | 0.01 | 99,8% | 97,2% |
| (128, 64) | 0.0001 | 99,8% | 97,2% |
| (64,) | 0.0001 | 99,8% | 97,1% |

Chọn: `{'mlp__alpha': 0.0001, 'mlp__hidden_layer_sizes': (128,)}`. Thời gian tìm + train: 31 giây.

## Kết quả trên bộ test

| Chỉ số | Model MLP | YIN (thuật toán) | Kết hợp (YIN, YIN bỏ qua thì hỏi model) |
|---|---|---|---|
| Đúng nốt (đúng cả quãng tám) | 96,5% | 59,8% | 96,9% |
| Có trả lời (không bỏ qua) | 98,2% | 60,6% | 98,7% |
| Đúng khi có trả lời | 98,3% | 98,7% | 98,2% |
| Đúng tên nốt, bỏ qua quãng tám (cách chấm pitch_class_only) | 97,2% | 60,0% | 97,5% |
| Nhầm quãng tám | 0,7% | 0,2% | 0,5% |
| Báo nhầm khi KHÔNG có nốt (560 khung ù/ồn) | 0,0% | 0,0% | 0,0% |

Học vẹt (Ch.4): đúng trên train 99,9% so với test 96,5%.

### Theo điều kiện thu (đúng nốt)

| Điều kiện | Số khung test | Model | YIN | Kết hợp |
|---|---|---|---|---|
| Sạch | 1267 | 98,8% | 98,5% | 99,0% |
| Nhiễu trắng 15 dB | 1267 | 98,5% | 98,4% | 99,0% |
| Nhiễu trắng 5 dB (rất ồn) | 1267 | 97,3% | 0,0% | 97,3% |
| Micro laptop (mất trầm < 250 Hz + nhiễu hồng) | 1267 | 96,3% | 95,1% | 97,5% |
| Tiếng ù điện 50 Hz | 1267 | 91,8% | 6,9% | 91,9% |

### Theo nhạc cụ (đúng nốt)

| Nhạc cụ | Số khung test | Model | YIN |
|---|---|---|---|
| bass | 650 | 91,2% | 54,6% |
| cello | 1270 | 99,5% | 58,1% |
| clav | 295 | 100,0% | 62,4% |
| epiano | 225 | 100,0% | 60,9% |
| guitar | 1675 | 99,6% | 60,5% |
| guitar_mute | 120 | 97,5% | 61,7% |
| piano | 950 | 99,5% | 62,3% |
| upright | 375 | 96,3% | 56,8% |
| voice | 775 | 83,5% | 62,1% |

### Phép thử khó: giấu hẳn cello khỏi train

Model chưa từng nghe cello: đúng 91,9% (trả lời 97,6%). YIN trên cùng các khung: đúng 58,9%.

### Ma trận nhầm lẫn 12 lớp cao độ: Model (hàng = nốt thật, cột = nốt đoán, — = không trả lời)

| thật \ đoán | C | C# | D | D# | E | F | F# | G | G# | A | A# | B | — |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **C** | 331 | · | · | 3 | · | 2 | 1 | 5 | · | · | · | · | 3 |
| **C#** | 3 | 392 | · | · | 1 | · | 2 | · | 2 | · | · | · | 20 |
| **D** | · | · | 371 | · | · | · | · | · | · | · | · | · | 9 |
| **D#** | · | · | · | 495 | · | · | · | · | · | · | · | · | · |
| **E** | · | · | · | · | 615 | · | · | 1 | · | · | · | · | 4 |
| **F** | · | · | · | · | · | 690 | 2 | 3 | · | · | · | · | 15 |
| **F#** | · | · | 15 | · | · | · | 630 | 1 | · | · | · | 1 | 28 |
| **G** | · | · | · | · | · | · | · | 719 | 1 | · | · | · | 10 |
| **G#** | · | 1 | · | · | 1 | · | · | 2 | 594 | · | · | · | 2 |
| **A** | 1 | · | · | · | 1 | · | · | · | 1 | 541 | · | · | 6 |
| **A#** | · | · | · | · | · | · | 1 | · | 3 | · | 415 | · | 11 |
| **B** | · | · | · | · | · | · | 10 | · | · | · | · | 366 | 4 |

### Ma trận nhầm lẫn 12 lớp cao độ: YIN (hàng = nốt thật, cột = nốt đoán, — = không trả lời)

| thật \ đoán | C | C# | D | D# | E | F | F# | G | G# | A | A# | B | — |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **C** | 199 | · | · | · | · | · | · | 11 | · | · | · | · | 135 |
| **C#** | · | 246 | · | · | · | · | · | · | 9 | · | · | · | 165 |
| **D** | · | · | 234 | · | · | · | · | · | · | · | · | · | 146 |
| **D#** | · | · | · | 304 | · | · | · | · | · | · | · | · | 191 |
| **E** | · | · | · | · | 371 | · | · | · | · | · | · | · | 249 |
| **F** | · | · | · | · | · | 424 | · | · | · | · | · | · | 286 |
| **F#** | · | · | · | · | · | · | 401 | 1 | · | · | · | · | 273 |
| **G** | · | · | · | · | · | · | · | 442 | 2 | · | · | · | 286 |
| **G#** | · | · | · | · | · | · | · | · | 365 | 1 | · | · | 234 |
| **A** | · | · | · | · | · | · | · | · | · | 339 | · | · | 211 |
| **A#** | · | · | · | · | · | · | · | · | · | · | 258 | · | 172 |
| **B** | · | · | · | · | · | · | 12 | · | · | · | · | 218 | 150 |

