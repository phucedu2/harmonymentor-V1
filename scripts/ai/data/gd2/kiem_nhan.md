# Kiểm nhãn tự động GĐ2

Sinh bởi `scripts/ai/gop_y/tao_du_lieu_gd2.py`. Claude viết 07/11/2026, đóng vai người học (quyết định GĐ2 2A), không dùng Gemini (4A). KHÔNG phải tập test chính thức: số chính thức lấy trên phiếu do Đạt/Thắng/Phúc viết (1A).

| Tập | Câu | Nhóm | Theo luồng | Theo kiểu |
|---|---|---|---|---|
| train | 667 | 71 | {'A': 407, 'B': 112, 'C': 70, 'D': 60, 'G': 18} | {'chu_thuong': 48, 'go_tat': 48, 'goc': 249, 'khong_dau': 82, 'khong_dau_go_tat': 71, 'loi_go': 77, 'loi_goi': 92} |
| dev | 170 | 28 | {'A': 95, 'B': 31, 'C': 17, 'D': 23, 'G': 4} | {'chu_thuong': 16, 'go_tat': 24, 'goc': 43, 'khong_dau': 25, 'khong_dau_go_tat': 25, 'loi_go': 15, 'loi_goi': 22} |
| test_tam | 174 | 27 | {'A': 86, 'B': 39, 'C': 21, 'D': 21, 'G': 7} | {'chu_thuong': 15, 'go_tat': 11, 'goc': 52, 'khong_dau': 20, 'khong_dau_go_tat': 33, 'loi_go': 22, 'loi_goi': 21} |

Lệch nhãn cần người xem: 0


Câu gốc bị bỏ vì trùng/gần trùng tập khác: 63

- train: tại sao E với F chỉ cách nhau nửa cung
- train: hợp âm Em gồm những nốt nào
- train: hợp âm F gồm những nốt nào
- train: hợp âm Gm gồm những nốt nào
- train: hợp âm F#m gồm những nốt nào
- train: giữa B và C có phím đen không
- train: C lên E là quãng mấy
- train: D lên A là quãng mấy
- train: voice leading là gì
- train: âm giai A thứ hòa âm gồm những nốt nào
- train: âm giai E thứ hòa âm gồm những nốt nào
- train: âm giai D thứ hòa âm gồm những nốt nào
- train: âm giai C thứ hòa âm gồm những nốt nào
- train: Csus4 gồm những nốt nào
- train: Dsus4 gồm những nốt nào
- train: Gsus4 gồm những nốt nào
- train: Asus4 gồm những nốt nào
- train: Esus4 gồm những nốt nào
- train: tension 9 11 13 là gì
- train: secondary dominant là gì
- train: modal interchange là gì
- train: mượn hợp âm từ giọng thứ là sao
- train: mode dorian là gì
- train: nhịp 6/8 đếm thế nào
- train: nốt móc đơn dài mấy phách
- train: khóa Fa đọc nốt thế nào
- train: làm sao để ngủ ngon hơn
- train: concert BlackPink ở Hà Nội bao giờ
- train: dịch câu này sang tiếng anh: tôi đi học
- train: làm sao giảm cân nhanh
- train: viết giúp mình email xin nghỉ học
- train: kể chuyện cười đi
- train: bạn có người yêu chưa
- train: lịch sử chiến tranh thế giới thứ hai
- train: mình đăng nhập không được
- train: tải bài sáng tác về máy được không
- train: bài kiểm tra đầu vào là gì
- train: làm lại bài kiểm tra đầu vào được không
- train: mở bài học ở đâu
- train: good morning
- train: cảm ơn đã giải thích
- train: chúc ngủ ngon
- train: tạm biệt
- dev: C# với Db có phải cùng một phím không
- dev: hợp âm ba nốt dựng như thế nào
- dev: hợp âm 7sus4 là gì
- dev: giọng song song là gì
- dev: dấu chấm dôi làm nốt dài thêm bao nhiêu
- dev: bài hát nào đang hot trên tiktok
- dev: tải nhạc mp3 miễn phí ở đâu
- dev: Sơn Tùng sinh năm bao nhiêu
- dev: chào buổi sáng
- dev: chào AI
- dev: hẹn gặp lại
- test_tam: A5 có mấy nửa cung
- test_tam: hợp âm chủ của một giọng là gì
- test_tam: tritone substitution là gì
- test_tam: piano điện yamaha giá bao nhiêu
- test_tam: trợ lý AI này trả lời được những gì
- test_tam: xin chào
- test_tam: chào bạn nha
- test_tam: hello
- test_tam: hi
