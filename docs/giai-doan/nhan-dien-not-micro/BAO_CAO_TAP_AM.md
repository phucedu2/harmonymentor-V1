# Báo cáo ADR-039: nghe nốt khi có tạp âm

Ngày đo: 2026-11-25. Yêu cầu của Phúc: nghe được nốt khi có tạp âm, cả piano thật lẫn piano ảo qua micro laptop; mục tiêu SNR ≥ ~6 dB, đúng ≥ 90%, nốt ma ≤ 2%.

## Cách đo (và giới hạn)
- `scripts/ai/pitch/luong_thu_on.py` dựng 65 luồng 15 giây: 10 nốt/luồng (piano, epiano, guitar, upright) trộn tạp âm tổng hợp (quạt, người nói, nhạc nền, gõ bàn) ở SNR 20/12/6/0 dB; luồng "loa" = piano ảo qua loa laptop + vang phòng; luồng chỉ có tạp âm để đếm nốt ma. Nốt lấy từ các bản thu **giữ riêng** (crc32(file) % 5 == 0): cả model trước lẫn sau đều không được thấy khi train.
- `frontend/scripts/danh_gia_micro.ts` chạy đúng `pipeline.ts` + model JSON của trình duyệt qua các luồng đó (`npx vite-node`).
- **Tạp âm là mô phỏng, không phải thu phòng thật; micro laptop thật chưa thử.** Số đo cho biết xu hướng, chưa phải cam kết với phòng học thật.
- "Nốt ma" = số nốt máy báo thêm (ngoài nốt đúng đầu tiên của mỗi nốt đàn, cộng cả nốt báo khi không ai đàn) chia cho số nốt đàn thật.

## Thay đổi
1. Lọc trầm 70 Hz (2 tầng) trước khi phân tích: bớt tiếng ù/rung quạt.
2. Ngưỡng im lặng thích nghi theo nền ồn (đáy RMS 5 giây gần nhất, trần tự đo 0,02) + nút **Đo nền ồn** (1,5 giây) + vạch nền trên thanh âm lượng + cảnh báo "phòng hơi ồn" (máy bỏ qua tiếng không rõ, không chấm sai).
3. Bỏ phiếu 5/7 khung thay cho 5 khung liên tiếp (không bị một khung nhiễu làm mất nốt, không báo hai lần).
4. Train lại MLP có tạp âm (SNR −3…25 dB, 4 loại) + piano qua loa; lớp "không có nốt" thêm tiếng quạt, người nói, gõ bàn. Model 207 KB (< 500 KB).
5. Bộ nhận diện mặc định đổi sang "Model AI" (YIN đứng trước dễ nhận giọng người nói là nốt).

## Trước và sau
**Trước** (model cũ train lại không có bản giữ riêng, cách xử lý ADR-032: ngưỡng cố định, 5 khung liên tiếp, YIN + model):

| Tình huống | Số nốt | Đúng tên nốt | Đúng cả quãng tám | Sai | Bỏ sót | Nốt ma / số nốt | Độ trễ TB |
|---|---|---|---|---|---|---|---|
| sach | sạch | 30 | 96.7% | 96.7% | 0.0% | 3.3% | 0.0% | 209 ms |
| quat | 20 dB | 30 | 100.0% | 100.0% | 0.0% | 0.0% | 3.3% | 210 ms |
| quat | 12 dB | 30 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 221 ms |
| quat | 6 dB | 30 | 93.3% | 93.3% | 0.0% | 6.7% | 0.0% | 216 ms |
| quat | 0 dB | 30 | 86.7% | 86.7% | 0.0% | 13.3% | 3.3% | 208 ms |
| giong_noi | 20 dB | 30 | 93.3% | 93.3% | 0.0% | 6.7% | 10.0% | 210 ms |
| giong_noi | 12 dB | 30 | 83.3% | 80.0% | 3.3% | 13.3% | 20.0% | 323 ms |
| giong_noi | 6 dB | 30 | 76.7% | 73.3% | 6.7% | 16.7% | 66.7% | 242 ms |
| giong_noi | 0 dB | 30 | 46.7% | 43.3% | 23.3% | 30.0% | 50.0% | 251 ms |
| nhac_nen | 20 dB | 30 | 90.0% | 83.3% | 3.3% | 6.7% | 50.0% | 230 ms |
| nhac_nen | 12 dB | 30 | 80.0% | 70.0% | 16.7% | 3.3% | 80.0% | 208 ms |
| nhac_nen | 6 dB | 30 | 63.3% | 60.0% | 36.7% | 0.0% | 143.3% | 208 ms |
| nhac_nen | 0 dB | 30 | 50.0% | 43.3% | 43.3% | 6.7% | 106.7% | 277 ms |
| tieng_dong | 20 dB | 30 | 96.7% | 96.7% | 0.0% | 3.3% | 0.0% | 217 ms |
| tieng_dong | 12 dB | 30 | 96.7% | 96.7% | 0.0% | 3.3% | 10.0% | 220 ms |
| tieng_dong | 6 dB | 30 | 96.7% | 96.7% | 0.0% | 3.3% | 13.3% | 232 ms |
| tieng_dong | 0 dB | 30 | 96.7% | 96.7% | 0.0% | 3.3% | 30.0% | 219 ms |
| loa | sạch | 30 | 96.7% | 96.7% | 0.0% | 3.3% | 0.0% | 219 ms |
| loa+quat | 12 dB | 30 | 93.3% | 93.3% | 0.0% | 6.7% | 13.3% | 208 ms |
| chỉ ồn | quat | 6 dB | 0 | – | – | – | – | 0 nốt ma / 0.5 phút = 0.0/phút | – |
| chỉ ồn | quat | 0 dB | 0 | – | – | – | – | 0 nốt ma / 0.5 phút = 0.0/phút | – |
| chỉ ồn | giong_noi | 6 dB | 0 | – | – | – | – | 14 nốt ma / 0.5 phút = 28.0/phút | – |
| chỉ ồn | giong_noi | 0 dB | 0 | – | – | – | – | 6 nốt ma / 0.5 phút = 12.0/phút | – |
| chỉ ồn | nhac_nen | 6 dB | 0 | – | – | – | – | 34 nốt ma / 0.5 phút = 68.0/phút | – |
| chỉ ồn | nhac_nen | 0 dB | 0 | – | – | – | – | 30 nốt ma / 0.5 phút = 60.0/phút | – |
| chỉ ồn | tieng_dong | 6 dB | 0 | – | – | – | – | 0 nốt ma / 0.5 phút = 0.0/phút | – |
| chỉ ồn | tieng_dong | 0 dB | 0 | – | – | – | – | 1 nốt ma / 0.5 phút = 2.0/phút | – |

| Tổng hợp | Số nốt | Đúng tên nốt | Nốt ma / số nốt | Nốt ma khi chỉ có ồn |
|---|---|---|---|---|
| Sạch (chưa thêm tạp âm, gồm piano ảo qua loa) | 60 | 96.7% | 0.0% | |
| **SNR ≥ 6 dB** (mục tiêu) | 390 | **89.5%** | **31.5%** | |
| SNR 0 dB (rất ồn, ngoài mục tiêu) | 120 | 70.0% | 47.5% | |
| Chỉ có tạp âm (4.0 phút) | 0 | | | 85 nốt = 21.3/phút |

**Sau** (model mới, pipeline mới, bộ nhận diện "Model AI"):

| Tình huống | Số nốt | Đúng tên nốt | Đúng cả quãng tám | Sai | Bỏ sót | Nốt ma / số nốt | Độ trễ TB |
|---|---|---|---|---|---|---|---|
| sach | sạch | 30 | 96.7% | 96.7% | 0.0% | 3.3% | 0.0% | 214 ms |
| quat | 20 dB | 30 | 96.7% | 96.7% | 0.0% | 3.3% | 0.0% | 214 ms |
| quat | 12 dB | 30 | 96.7% | 96.7% | 0.0% | 3.3% | 0.0% | 216 ms |
| quat | 6 dB | 30 | 86.7% | 86.7% | 0.0% | 13.3% | 0.0% | 214 ms |
| quat | 0 dB | 30 | 83.3% | 83.3% | 0.0% | 16.7% | 3.3% | 215 ms |
| giong_noi | 20 dB | 30 | 96.7% | 96.7% | 0.0% | 3.3% | 0.0% | 216 ms |
| giong_noi | 12 dB | 30 | 80.0% | 80.0% | 0.0% | 20.0% | 10.0% | 223 ms |
| giong_noi | 6 dB | 30 | 76.7% | 76.7% | 0.0% | 23.3% | 6.7% | 224 ms |
| giong_noi | 0 dB | 30 | 60.0% | 60.0% | 0.0% | 40.0% | 13.3% | 249 ms |
| nhac_nen | 20 dB | 30 | 93.3% | 93.3% | 0.0% | 6.7% | 36.7% | 212 ms |
| nhac_nen | 12 dB | 30 | 86.7% | 83.3% | 10.0% | 3.3% | 93.3% | 216 ms |
| nhac_nen | 6 dB | 30 | 73.3% | 70.0% | 20.0% | 6.7% | 80.0% | 211 ms |
| nhac_nen | 0 dB | 30 | 53.3% | 50.0% | 33.3% | 13.3% | 90.0% | 203 ms |
| tieng_dong | 20 dB | 30 | 96.7% | 96.7% | 0.0% | 3.3% | 0.0% | 214 ms |
| tieng_dong | 12 dB | 30 | 96.7% | 96.7% | 0.0% | 3.3% | 0.0% | 216 ms |
| tieng_dong | 6 dB | 30 | 96.7% | 96.7% | 0.0% | 3.3% | 0.0% | 230 ms |
| tieng_dong | 0 dB | 30 | 96.7% | 96.7% | 0.0% | 3.3% | 0.0% | 219 ms |
| loa | sạch | 30 | 96.7% | 96.7% | 0.0% | 3.3% | 0.0% | 214 ms |
| loa+quat | 12 dB | 30 | 93.3% | 93.3% | 0.0% | 6.7% | 0.0% | 214 ms |
| chỉ ồn | quat | 6 dB | 0 | – | – | – | – | 0 nốt ma / 0.5 phút = 0.0/phút | – |
| chỉ ồn | quat | 0 dB | 0 | – | – | – | – | 0 nốt ma / 0.5 phút = 0.0/phút | – |
| chỉ ồn | giong_noi | 6 dB | 0 | – | – | – | – | 6 nốt ma / 0.5 phút = 12.0/phút | – |
| chỉ ồn | giong_noi | 0 dB | 0 | – | – | – | – | 0 nốt ma / 0.5 phút = 0.0/phút | – |
| chỉ ồn | nhac_nen | 6 dB | 0 | – | – | – | – | 23 nốt ma / 0.5 phút = 46.0/phút | – |
| chỉ ồn | nhac_nen | 0 dB | 0 | – | – | – | – | 21 nốt ma / 0.5 phút = 42.0/phút | – |
| chỉ ồn | tieng_dong | 6 dB | 0 | – | – | – | – | 0 nốt ma / 0.5 phút = 0.0/phút | – |
| chỉ ồn | tieng_dong | 0 dB | 0 | – | – | – | – | 0 nốt ma / 0.5 phút = 0.0/phút | – |

| Tổng hợp | Số nốt | Đúng tên nốt | Nốt ma / số nốt | Nốt ma khi chỉ có ồn |
|---|---|---|---|---|
| Sạch (chưa thêm tạp âm, gồm piano ảo qua loa) | 60 | 96.7% | 0.0% | |
| **SNR ≥ 6 dB** (mục tiêu) | 390 | **90.0%** | **17.4%** | |
| SNR 0 dB (rất ồn, ngoài mục tiêu) | 120 | 73.3% | 26.7% | |
| Chỉ có tạp âm (4.0 phút) | 0 | | | 50 nốt = 12.5/phút |

## Tóm tắt theo mục tiêu (SNR ≥ 6 dB, 390 nốt)
| | Đúng tên nốt | Nốt ma / số nốt |
|---|---|---|
| Trước (ADR-032) | 89,5% | 31,5% |
| Sau, mọi loại tạp âm | 90,0% | 17,4% |
| Sau, **trừ nhạc nền** (quạt, người nói, gõ bàn) | **91,7%** | **1,7%** |
| Sau, chỉ nhạc nền | 84,4% | 70,0% |

Khi chỉ có tạp âm (không ai đàn), trừ nhạc nền: 7,0 → 2,0 nốt ma/phút.

## Kết luận trung thực
- **Đạt** (trong mô phỏng): quạt/điều hòa, người nói chuyện, gõ bàn ở SNR ≥ 6 dB: đúng 91,7%, nốt ma 1,7%; piano ảo qua loa laptop sạch và có quạt 12 dB: 96,7%.
- **Chưa đạt: nhạc nền.** Nhạc nền là các nốt đàn thật phát liên tục; một bộ nghe từng nốt (monophonic) không phân biệt được "nốt của mình" với "nốt của bài nhạc" nếu cao độ không khác nhau về âm lượng. Khi người học nghe nhạc cùng lúc, nốt ma còn rất nhiều. Cách thực tế: tắt nhạc/đeo tai nghe khi trả lời bằng micro. Muốn làm tốt hơn phải đổi hướng (nghe đa âm hoặc chọn "nốt to nhất, gần micro nhất"), cần nhóm quyết.
- Giọng nói ở SNR 6 dB vẫn làm sai khoảng 1/4 nốt (dải 90–250 Hz trùng nốt trầm).
- SNR 0 dB (tạp âm to bằng tiếng đàn) nằm ngoài mục tiêu: đúng ~69%.
- Độ trễ ≈ 210 ms (5 khung × 40 ms); CPU Node 1–2 ms/khung (ngân sách 40 ms), chưa đo trong trình duyệt thật.
- `noiseSuppression`/`echoCancellation` của trình duyệt: **chưa đo** (cần micro thật); giữ tắt như ADR-032 vì bộ khử ồn làm méo cao độ. Phúc có thể thử bật trên máy thật rồi gửi kết quả.
- Chưa có bản thu phòng thật. Việc cần làm tiếp (không bắt buộc): thu 20–30 nốt piano thật có tiếng quạt/nói chuyện rồi chạy lại `danh_gia_micro.ts`.

## Chạy lại
```
python scripts/ai/pitch/luong_thu_on.py --out /tmp/luong_on
python scripts/ai/pitch/du_lieu.py --on --out /tmp/pitch_on.npz        # bỏ qua bản giữ riêng
python scripts/ai/pitch/train.py --data /tmp/pitch_on.npz --export frontend/public/models/pitch_mlp.json \
    --fixture frontend/src/audio/pitch/__fixtures__/parity.json --report docs/giai-doan/nhan-dien-not-micro/KET_QUA_MODEL.md
cd frontend && npx vite-node scripts/danh_gia_micro.ts -- --data /tmp/luong_on --model public/models/pitch_mlp.json --pipeline robust --detector model
# so với bản cũ: --pipeline legacy --detector hybrid (kèm model train bằng du_lieu.py không có --on)
```
Model gửi lên là bản train **không** có các bản thu giữ riêng (để số đo ở trên kiểm chứng được), nên kém hơn chút so với train bằng `--tat-ca`.
