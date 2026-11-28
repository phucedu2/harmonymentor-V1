"""Cổng nhạc lý cho tài liệu Admin tải lên (góp ý thầy T1).

Luồng: kiểm byte thật (mime) -> trích chữ (PDF/DOCX/ảnh OCR/MusicXML/MIDI/dán chữ) -> làm sạch và lọc chỉ dẫn lạ
-> chấm điểm liên quan nhạc lý -> quyết định nhận / chờ duyệt / từ chối. Chỉ nội dung được nhận mới tới bộ sinh bài."""
