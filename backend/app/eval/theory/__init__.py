"""Chấm độ đúng nhạc lý câu trả lời của AI Tutor (G8).

build.py  sinh bộ 300 câu hỏi; đáp án lấy từ Music Engine khi Engine tính được (không tự gõ tay).
probe.py  chạy trên máy có khóa Gemini: hỏi từng câu qua pipeline thật, lưu câu trả lời.
grade.py  chấm tự động (Music Engine quét khẳng định + đối chiếu đáp án) để người chấm đọc lại."""
