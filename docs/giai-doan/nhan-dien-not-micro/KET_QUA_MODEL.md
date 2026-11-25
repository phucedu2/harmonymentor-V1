# Kết quả model nhận diện nốt so với YIN (ADR-032 bước 2)

Ngày chạy: 2026-11-25. Lệnh: `python scripts/ai/pitch/du_lieu.py` rồi `python scripts/ai/pitch/train.py --seed 42` (xem đầu file train.py). Máy: container cloud, CPU, scikit-learn.

> Đo trên mẫu nhạc cụ thu sẵn (thư viện CC0/CC BY) và giọng hát tổng hợp, có thêm nhiễu. **Chưa chứng minh chất lượng với micro thật của người học**: phòng ồn, micro laptop, đàn lệch dây sẽ khác.

## Dữ liệu

- 54030 khung 2048 mẫu (≈ 43 ms ở 48 kHz), 1220 nhóm bản thu, nốt MIDI 40–88 (49 nốt) + lớp 0 "không có nốt" (7700 khung ù/ồn).
- Train: 43203 khung / 976 nhóm. Test (khung có nốt): 9237 khung / 85 nhóm (chia theo bản thu: mọi bản dịch cao độ/thêm nhiễu của một bản thu nằm cùng một phía).
- Nhạc cụ: bass 4997, cello 7630, clav 3160, epiano 3900, guitar 11478, guitar_mute 1330, nen 7700, piano 6910, upright 3925, voice 3000.
- Mỗi khung có 5 phiên bản điều kiện thu: Sạch, Nhiễu trắng 15 dB, Nhiễu trắng 5 dB (rất ồn), Micro laptop (mất trầm < 250 Hz + nhiễu hồng), Tiếng ù điện 50 Hz, Piano ảo qua loa laptop (vang phòng), Quạt/điều hòa, SNR −3…25 dB, Người nói chuyện/TV, SNR −3…25 dB, Nhạc nền, SNR −3…25 dB, Gõ bàn/đóng cửa, SNR −3…25 dB.

## Chọn tham số (GridSearchCV, GroupKFold 4 phần, chỉ trên tập train)

| Lớp ẩn | alpha (L2) | Điểm train | Điểm kiểm định |
|---|---|---|---|
| (128,) | 0.0001 | 99,6% | 94,8% |
| (128,) | 0.01 | 99,6% | 94,7% |
| (192, 96) | 0.0001 | 99,5% | 94,7% |
| (192, 96) | 0.01 | 99,5% | 94,7% |
| (64,) | 0.01 | 99,3% | 94,6% |
| (64,) | 0.0001 | 99,5% | 94,6% |
| (128, 64) | 0.01 | 99,4% | 94,3% |
| (128, 64) | 0.0001 | 99,3% | 94,2% |

Chọn: `{'mlp__alpha': 0.0001, 'mlp__hidden_layer_sizes': (128,)}`. Thời gian tìm + train: 92 giây.

## Kết quả trên bộ test

| Chỉ số | Model MLP | YIN (thuật toán) | Kết hợp (YIN, YIN bỏ qua thì hỏi model) |
|---|---|---|---|
| Đúng nốt (đúng cả quãng tám) | 95,2% | 65,6% | 93,3% |
| Có trả lời (không bỏ qua) | 97,5% | 69,4% | 98,8% |
| Đúng khi có trả lời | 97,6% | 94,4% | 94,4% |
| Đúng tên nốt, bỏ qua quãng tám (cách chấm pitch_class_only) | 96,2% | 67,6% | 95,9% |
| Nhầm quãng tám | 1,0% | 2,0% | 2,6% |
| Báo nhầm khi KHÔNG có nốt (1590 khung ù/ồn) | 2,5% | 13,1% | 14,0% |

Học vẹt (Ch.4): đúng trên train 99,6% so với test 95,2%.

### Theo điều kiện thu (đúng nốt)

| Điều kiện | Số khung test | Model | YIN | Kết hợp |
|---|---|---|---|---|
| Sạch | 976 | 94,1% | 96,5% | 97,5% |
| Nhiễu trắng 15 dB | 976 | 95,3% | 96,2% | 97,4% |
| Nhiễu trắng 5 dB (rất ồn) | 976 | 97,0% | 0,0% | 97,0% |
| Micro laptop (mất trầm < 250 Hz + nhiễu hồng) | 976 | 96,3% | 94,1% | 96,6% |
| Tiếng ù điện 50 Hz | 976 | 92,4% | 8,6% | 92,3% |
| Piano ảo qua loa laptop (vang phòng) | 853 | 98,6% | 95,3% | 96,7% |
| Quạt/điều hòa, SNR −3…25 dB | 876 | 95,8% | 58,6% | 92,5% |
| Người nói chuyện/TV, SNR −3…25 dB | 876 | 90,8% | 62,3% | 82,3% |
| Nhạc nền, SNR −3…25 dB | 876 | 93,3% | 62,2% | 84,6% |
| Gõ bàn/đóng cửa, SNR −3…25 dB | 876 | 98,4% | 86,4% | 94,5% |

### Theo nhạc cụ (đúng nốt)

| Nhạc cụ | Số khung test | Model | YIN |
|---|---|---|---|
| bass | 450 | 97,1% | 64,9% |
| cello | 2190 | 95,0% | 61,7% |
| clav | 650 | 98,6% | 69,5% |
| epiano | 600 | 98,3% | 68,7% |
| guitar | 2807 | 98,5% | 69,4% |
| guitar_mute | 300 | 98,0% | 63,7% |
| piano | 890 | 98,0% | 69,9% |
| upright | 850 | 91,4% | 57,3% |
| voice | 500 | 66,8% | 60,2% |

### Phép thử khó: giấu hẳn cello khỏi train

Model chưa từng nghe cello: đúng 74,3% (trả lời 96,0%). YIN trên cùng các khung: đúng 65,2%.

### Ma trận nhầm lẫn 12 lớp cao độ: Model (hàng = nốt thật, cột = nốt đoán, — = không trả lời)

| thật \ đoán | C | C# | D | D# | E | F | F# | G | G# | A | A# | B | — |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **C** | 641 | · | · | · | · | 1 | · | 1 | · | · | · | · | 6 |
| **C#** | · | 752 | · | · | 1 | · | 1 | · | 3 | · | · | · | 17 |
| **D** | · | 2 | 387 | 1 | · | 9 | · | 4 | · | 3 | · | · | 14 |
| **D#** | 1 | 2 | · | 841 | · | 9 | · | 3 | 2 | 1 | 1 | 1 | 33 |
| **E** | · | · | · | · | 730 | · | 1 | 1 | 3 | 1 | · | 1 | 12 |
| **F** | · | 3 | · | · | 1 | 1176 | · | · | · | 2 | 1 | · | 11 |
| **F#** | · | 2 | 1 | 1 | 1 | 1 | 752 | 4 | · | · | 3 | 2 | 32 |
| **G** | 1 | · | · | · | 2 | 1 | · | 985 | 8 | · | 1 | · | 50 |
| **G#** | · | · | · | · | 1 | · | · | 2 | 634 | 3 | 1 | · | 24 |
| **A** | · | 1 | · | · | 1 | · | · | · | 1 | 744 | 3 | · | 6 |
| **A#** | · | 1 | · | · | 1 | 1 | · | · | · | 2 | 464 | · | 7 |
| **B** | · | · | · | · | 2 | · | 11 | · | · | · | 3 | 779 | 18 |

### Ma trận nhầm lẫn 12 lớp cao độ: YIN (hàng = nốt thật, cột = nốt đoán, — = không trả lời)

| thật \ đoán | C | C# | D | D# | E | F | F# | G | G# | A | A# | B | — |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **C** | 422 | 1 | 2 | · | · | 3 | · | 22 | 3 | · | · | · | 196 |
| **C#** | · | 501 | · | 4 | 1 | · | 5 | · | 24 | 1 | · | · | 238 |
| **D** | · | · | 278 | · | · | · | · | 1 | · | · | · | · | 141 |
| **D#** | · | · | · | 606 | · | · | · | · | 6 | · | · | 1 | 281 |
| **E** | 1 | · | 1 | · | 508 | · | 2 | · | · | 5 | · | · | 232 |
| **F** | · | 2 | · | · | · | 810 | 2 | 1 | 1 | · | 9 | · | 369 |
| **F#** | · | · | 1 | · | 1 | · | 558 | 1 | 1 | · | · | 5 | 232 |
| **G** | 2 | 1 | · | 1 | · | 1 | · | 736 | 8 | · | · | · | 299 |
| **G#** | · | 3 | · | · | · | · | · | 2 | 434 | 1 | 2 | · | 223 |
| **A** | · | · | 3 | · | · | 1 | · | · | 2 | 526 | · | · | 224 |
| **A#** | · | · | · | 3 | · | · | 3 | · | · | · | 312 | 1 | 157 |
| **B** | · | · | · | · | 4 | 1 | 22 | 4 | · | · | 1 | 549 | 232 |

