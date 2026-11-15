# G7: tổng kết góp ý thầy T1–T6

Ngày làm: 15/11/2026. Nhánh `gop-y-thay/g7-tong-ket` (xếp trên G6, đã gộp G1 để nhánh có đủ T1–T6).

## Đã làm
- `docs/AI_TEACHER_FEEDBACK_MAP.md`: bản đồ T1–T6 → cổng, PR, cách kiểm, phần còn thiếu.
- `docs/DEMO_5_PHUT.md`: kịch bản demo 5 phút và câu thầy dễ hỏi.
- `docs/AI_USAGE.md`: thêm dòng nhật ký; `README.md`: mục lệnh chạy và liên kết tài liệu.
- Gộp G1 vào chuỗi (G1 và G2 cùng tách từ `phuc-music`, nên các PR chưa chứa nhau); xung đột `ci.yml`, `docs/giai-doan/README.md` đã giải, `--min-passed` nâng 1397.

## Kiểm chứng
`pytest -q` (backend) trên nhánh đã gộp G1–G7: 1396 passed, 44 skipped. Frontend không đổi ở G2–G7; `npm test` và `npm run build` của G1 chạy ở báo cáo G1 (chưa chạy lại trên nhánh gộp).

## Thứ tự gộp đề xuất
G1 → G2 → G3 → G4 → G5 → G6 → G7 (mỗi PR đích là PR trước). Nếu gộp riêng lẻ vào `phuc-music`, `ci.yml --min-passed` xung đột: giữ số lớn nhất, và nhớ sửa số theo tổng test thật.

## Việc còn mở (cần Phúc/nhóm)
1. ADR-027: lạc đề giờ tốn một lượt Gemini; `OFFTOPIC_MODE=refuse` quay lại cách cũ. Có bật `RAG_STRICT_GROUNDING` không?
2. Đạt kiểm nhãn: bộ 115 ca G5 và dữ liệu G6.
3. Chạy thật trên máy Phúc: Docker + Qdrant (`ingest`, `eval`), Gemini thật.
