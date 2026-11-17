"""Bản dịch tiếng Việt cho những chữ chỉ có tiếng Anh, dùng khi dựng bản thuần tiếng Việt (build_docx.py --vi,
gen_diagrams.py --vi).

Chữ song ngữ (en, vi) nằm sẵn ở noi_dung.py và mo_ta_bang.py; file này chỉ giữ phần còn lại: ô bảng một ngôn ngữ
(ca kiểm thử, Task Sheet, số liệu) và nhãn sơ đồ Graphviz. Tên bảng, tên cột, endpoint, mã lỗi và đường dẫn
file giữ nguyên vì đó là tên trong code.
"""

from __future__ import annotations

import re

# ------------------------------------------------------------------------------------------------ ô bảng, chữ cứng
CHU: dict[str, str] = {
    # Ca kiểm thử thủ công: module
    "Visitor": "Khách", "Auth": "Xác thực", "Placement": "Đầu vào", "Learning": "Học", "Grading": "Chấm bài",
    "Review": "Ôn tập", "Practice": "Luyện tập", "Recommend": "Gợi ý", "Profile": "Hồ sơ", "Security": "Bảo mật",
    "Admin": "Quản trị",
    # Ca kiểm thử thủ công: các bước và dữ liệu
    "Open /": "Mở /",
    "Open /dang-ky, fill form, submit": "Mở /dang-ky, điền form, gửi",
    "minhan@harmony.demo (demo learner)": "minhan@harmony.demo (người học demo)",
    "Fill form with weak password, submit": "Điền form với mật khẩu yếu, gửi",
    "password 'abc'": "mật khẩu 'abc'",
    "Answer 12 questions": "Trả lời 12 câu",
    "8 correct, 4 wrong": "8 đúng, 4 sai",
    "Open /app/hoc": "Mở /app/hoc",
    "Open L01, go to step 13/18": "Mở L01, tới bước 13/18",
    "Type notes for 'build D minor', submit": "Nhập nốt cho câu 'dựng D minor', gửi",
    "Submit a second wrong answer": "Gửi đáp án sai lần thứ hai",
    "Submit correct notes": "Gửi đúng các nốt",
    "Answer all questions correctly, click Complete": "Trả lời đúng mọi câu, bấm Hoàn thành",
    "12/12 correct": "12/12 đúng",
    "After a wrong answer click 'Giải thích lỗi này'": "Sau một câu sai, bấm 'Giải thích lỗi này'",
    "Open /app/tien-do": "Mở /app/tien-do",
    "after L01": "sau L01",
    "Answer 3 cards": "Trả lời 3 thẻ",
    "2 right, 1 wrong": "2 đúng, 1 sai",
    "Open /app/luyen-tap, answer a chord question": "Mở /app/luyen-tap, trả lời một câu hợp âm",
    "Save goal, open /app": "Lưu mục tiêu, mở /app",
    "goal text": "nội dung mục tiêu",
    "Open AI drawer, ask": "Mở ngăn AI, đặt câu hỏi",
    "Ask to ignore rules and print the system prompt": "Yêu cầu bỏ qua quy tắc và in system prompt",
    "injection text": "câu tiêm lệnh",
    "Open /app/quiz, pick 'Dựng hợp âm ba'": "Mở /app/quiz, chọn 'Dựng hợp âm ba'",
    "skill": "kỹ năng",
    "Open /app/composition, enter chords, save": "Mở /app/composition, nhập hợp âm, lưu",
    "Change display name, save": "Đổi tên hiển thị, lưu",
    "Go to /admin as learner": "Vào /admin bằng tài khoản người học",
    "learner token": "token người học",
    "no token": "không có token",
    "Enter wrong password 5 times, then once more": "Nhập sai mật khẩu 5 lần, rồi thêm một lần nữa",
    "Log in as admin, open /admin": "Đăng nhập bằng Admin, mở /admin",
    "Lessons tab, 'Sửa nội dung bài 1'": "Tab Bài học, 'Sửa nội dung bài 1'",
    "Users tab": "Tab Người dùng",
    "AI tab": "Tab AI",
    # Tiêu chí nghiệm thu: cột bằng chứng
    "Run 17/11/2026 (handover §4)": "Lần chạy 17/11/2026 (báo cáo bàn giao mục 4)",
    # Mốc
    "Submission": "Nộp bài",
    # Final Checklist
    "Done": "Xong", "Not yet": "Chưa",
    "1,448 passed + 1 skipped; PostgreSQL 25/25": "1.448 đạt + 1 bỏ qua; PostgreSQL 25/25",
    "Vitest 282/282, build OK": "Vitest 282/282, build đạt",
    "CI PostgreSQL job; schema.json": "Job PostgreSQL trong CI; schema.json",
    "_nguon/so_do/ (Graphviz sources)": "_nguon/so_do/ (nguồn Graphviz)",
    "23 screenshots, _nguon/anh/": "23 ảnh chụp, _nguon/anh/",
    # Bằng chứng phạm vi, đánh giá
    "backend/app/content/, SQL count on the demo DB 17/11/2026": "backend/app/content/, đếm bằng SQL trên CSDL demo 17/11/2026",
    "backend/app/admin/ (ADR-025 status: proposed)": "backend/app/admin/ (ADR-025 trạng thái: đề xuất)",
    "docs/giai-doan/gop-y-thay/G5_BAO_CAO.md (15/11/2026); guarded by tests/test_g5_eval.py":
        "docs/giai-doan/gop-y-thay/G5_BAO_CAO.md (15/11/2026); được giữ bởi tests/test_g5_eval.py",
    # Kho dữ liệu
    "Redis key login_fail:{ip}|{email}, TTL 15 min": "Khóa Redis login_fail:{ip}|{email}, TTL 15 phút",
    "Qdrant collection harmony_knowledge (e5, 82 chunks in the demo run)":
        "Collection Qdrant harmony_knowledge (e5, 82 đoạn trong lần chạy demo)",
    # Kiểm thử tự động
    "282 (16 files)": "282 (16 file)", "1 build": "1 lần build", "OK": "Đạt",
    "1,449": "1.449", "1,448": "1.448", "1,492": "1.492", "1,445": "1.445",
    "125.75 s": "125,75 s", "102.19 s": "102,19 s", "20.92 s": "20,92 s", "3.18 s": "3,18 s", "6.92 s": "6,92 s",
    # Task Sheet
    "Completed": "Hoàn thành", "In review": "Đang duyệt",
    "Phúc (on behalf of group)": "Phúc (thay mặt nhóm)",
    "Draft PR (docs-review123)": "Draft PR (docs-review123)",
    "Phase A plan, FR trace, ADRs, project rules": "Kế hoạch Giai đoạn A, truy vết FR, các ADR, quy tắc dự án",
    "Front end skeleton: router, home, login / register, protected routes":
        "Khung giao diện: router, trang chủ, đăng nhập / đăng ký, route được bảo vệ",
    "Back end auth: register, login, rotating refresh, roles": "Xác thực backend: đăng ký, đăng nhập, refresh xoay vòng, vai trò",
    "Docker Compose and DevOps base": "Docker Compose và nền tảng DevOps",
    "Lesson 1 in many keys; beginner audit (CP1)": "Bài 1 ở nhiều giọng; rà soát cho người mới (CP1)",
    "Replace SRS v1.3 by design documents bản 2.1": "Thay SRS v1.3 bằng bộ tài liệu thiết kế bản 2.1",
    "Fix parallel lesson start (HM-010); GitHub Actions CI": "Sửa lỗi bắt đầu bài song song (HM-010); CI GitHub Actions",
    "Immutable question versions (HM-003, ADR-006)": "Phiên bản câu hỏi bất biến (HM-003, ADR-006)",
    "Notation / MIDI octave fix for lesson 1 (HM-001)": "Sửa ký âm / quãng tám MIDI cho bài 1 (HM-001)",
    "Official logo (ADR-007)": "Logo chính thức (ADR-007)",
    "Animated home page (GSAP + audio)": "Trang chủ có hiệu ứng động (GSAP + âm thanh)",
    "AI pipeline: recommender (CP2) and AI Tutor (CP3), evaluation": "Pipeline AI: hệ gợi ý (CP2) và AI Tutor (CP3), đánh giá",
    "Teacher feedback G1–G7: RAG inventory, routing, e5 fine-tune, lesson L05":
        "Góp ý của thầy G1–G7: kiểm kê RAG, định tuyến, tinh chỉnh e5, bài L05",
    "Instruments, piano practice, evaluation, lessons L06–L08": "Nhạc cụ, luyện bấm piano, đánh giá, bài L06–L08",
    "Lesson L07 Engine extension; AI Tutor answers music questions outside lessons (ADR-020)":
        "Mở rộng Engine cho bài L07; AI Tutor trả lời câu hỏi âm nhạc ngoài bài (ADR-020)",
    "Review fixes, admin pages, skill quiz, AI lesson drafts (ADR-025)":
        "Sửa lỗi rà soát, trang quản trị, quiz kỹ năng, AI soạn bài nháp (ADR-025)",
    "Front end bug sweep FE-001..023, 'Stage' theme": "Soát lỗi giao diện FE-001..023, theme 'Sân khấu'",
    "Teacher feedback T1–T6 (gates G1–G8): Qdrant, evaluation, upload gate":
        "Góp ý của thầy T1–T6 (cổng G1–G8): Qdrant, đánh giá, cổng kiểm tra tải lên",
    "eProject documentation Review 01–03 (this document)": "Tài liệu eProject Đánh giá 01–03 (tài liệu này)",
    # Đường dẫn màn hình
    "/app (AI drawer)": "/app (ngăn AI)", "/admin (Lessons tab)": "/admin (tab Bài học)",
    "/admin (Users tab)": "/admin (tab Người dùng)", "/admin (AI tab)": "/admin (tab AI soạn bài)",
    # Thiết kế bảng
    "Serial": "STT", "Fields": "Trường", "S.N": "STT", "No.": "STT",
}


def T(s):
    """Dịch một chuỗi một ngôn ngữ; chuỗi không có trong bảng (đường dẫn, mã, số) giữ nguyên."""
    if not isinstance(s, str):
        return s
    return CHU.get(s, s)


def so_vi(s: str) -> str:
    """Số kiểu Việt Nam trong chữ tiếng Việt: 1,449 → 1.449; 0.65 → 0,65 (không đụng phiên bản như 3.11 hay 1.0)."""
    s = re.sub(r"(?<![\d.])(\d{1,3}),(\d{3})(?![\d,])", r"\1.\2", s)
    return s


# ------------------------------------------------------------------------------------------------ nhãn sơ đồ
SO_DO: dict[str, str] = {
    # DFD mức 0
    "0\\nHarmonyMentor AI\\nSystem": "0\\nHệ thống\\nHarmonyMentor AI",
    "Guest": "Khách", "Learner": "Người học", "Admin": "Quản trị viên",
    "Google Gemini API\\n(external AI service)": "Google Gemini API\\n(dịch vụ AI bên ngoài)",
    "Register / login data": "Dữ liệu đăng ký / đăng nhập",
    "Home page, curriculum,\\nJWT + refresh cookie": "Trang chủ, chương trình học,\\nJWT + refresh cookie",
    "Answers, piano input, flashcard answers,\\ngoal text, chat questions, chord grids":
        "Đáp án, phím piano, đáp án thẻ ôn,\\nmục tiêu học, câu hỏi chat, lưới hợp âm",
    "Grading result + error code, explanation,\\nmastery, review queue, recommendations,\\ncited AI answers, backing track":
        "Kết quả chấm + mã lỗi, lời giải,\\nmastery, hàng đợi ôn, gợi ý bài,\\ntrả lời AI có trích dẫn, bản đệm",
    "Lesson text edits, publish / hide,\\nuser lock, uploaded documents":
        "Sửa nội dung bài, phát hành / ẩn,\\nkhóa người dùng, tài liệu tải lên",
    "Statistics, audit log,\\nAI lesson drafts with Engine flags":
        "Thống kê, nhật ký thao tác,\\nbài nháp AI kèm cờ kiểm của Engine",
    "Question, last 6 messages, lesson chunks,\\nweak skills, error code (no e-mail / name / id)":
        "Câu hỏi, 6 tin nhắn gần nhất, đoạn bài học,\\nkỹ năng yếu, mã lỗi (không email / tên / id)",
    "JSON answer + citations\\n(checked by Music Engine)": "Trả lời JSON + trích dẫn\\n(Music Engine kiểm tra)",
    # DFD mức 1: tiến trình
    "1.0\nRegister": "1.0\nĐăng ký", "2.0\nLogin +\ntemporary lock": "2.0\nĐăng nhập +\nkhóa tạm",
    "3.0\nRefresh /\nlogout": "3.0\nLàm mới /\nđăng xuất", "4.0\nProfile &\nrole check": "4.0\nHồ sơ &\nkiểm vai trò",
    "5.0\nManage users\n(admin)": "5.0\nQuản lý\nngười dùng\n(Admin)",
    "6.0\nView lessons": "6.0\nXem bài học", "7.0\nSubmit answer\n(Music Engine)": "7.0\nNộp đáp án\n(Music Engine)",
    "8.0\nUpdate EMA\nmastery": "8.0\nCập nhật\nmastery EMA", "9.0\nComplete lesson\n+ Leitner": "9.0\nHoàn thành bài\n+ Leitner",
    "10.0\nReview\nflashcards": "10.0\nÔn\nthẻ ôn", "11.0\nPractice /\nplacement / quiz": "11.0\nLuyện tập /\nđầu vào / quiz",
    "12.0\nSave goal\n+ embed": "12.0\nLưu mục tiêu\n+ embedding", "13.0\nHybrid\nrecommend": "13.0\nGợi ý\nlai",
    "14.0\nAI Tutor\nchat": "14.0\nChat\nAI Tutor", "15.0\nExplain wrong\nanswer (3 levels)": "15.0\nGiải thích\ncâu sai (3 mức)",
    "16.0\nRate answer": "16.0\nChấm sao\ncâu trả lời",
    "17.0\nSuggest &\narrange chords": "17.0\nGợi ý &\nphối hợp âm", "18.0\nSave / open\nproject": "18.0\nLưu / mở\ndự án",
    "19.0\nEdit & publish\nlesson text": "19.0\nSửa & phát hành\nnội dung bài", "20.0\nStatistics": "20.0\nThống kê",
    "21.0\nAI lesson\ndraft": "21.0\nAI soạn\nbài nháp",
    # DFD mức 1: thực thể, kho
    "Guest / Learner": "Khách / Người học", "Google Gemini": "Google Gemini",
    "Redis login_fail:ip|email": "Redis login_fail:ip|email",
    "Qdrant harmony_knowledge (lesson chunks)": "Qdrant harmony_knowledge (đoạn bài học)",
    "attempts (is_test = false)": "attempts (is_test = false)",
    # DFD mức 1: luồng
    "name, e-mail, password": "tên, email, mật khẩu", "new user (bcrypt hash)": "người dùng mới (băm bcrypt)",
    "access JWT": "JWT truy cập", "e-mail, password": "email, mật khẩu", "count failures": "đếm lần sai",
    "locked seconds": "số giây bị khóa", "hashed_password, role": "hashed_password, role",
    "refresh token hash": "băm refresh token", "JWT / 401 / 429": "JWT / 401 / 429", "refresh cookie": "refresh cookie",
    "valid token": "token hợp lệ", "new JWT": "JWT mới", "Bearer JWT": "Bearer JWT", "user row": "dòng user",
    "profile / 403": "hồ sơ / 403", "lock / unlock": "khóa / mở khóa", "is_active": "is_active", "action log": "nhật ký thao tác",
    "open lesson": "mở bài", "blocks": "các khối", "published version": "phiên bản đã phát hành",
    "theory, piano, staff, questions": "lý thuyết, piano, khuông nhạc, câu hỏi", "answer + input method": "đáp án + cách nhập",
    "answer_key, grader_config": "answer_key, grader_config", "attempt + error codes": "lượt làm + mã lỗi",
    "correct?, error code, feedback": "đúng?, mã lỗi, phản hồi", "result 1 / 0.5 / 0": "kết quả 1 / 0,5 / 0",
    "new score": "điểm mới", "complete": "hoàn thành", "all questions correct?": "đúng hết các câu?",
    "completed": "đã hoàn thành", "cards due now (box 1)": "thẻ đến hạn ngay (hộp 1)", "card answer": "đáp án thẻ",
    "due card": "thẻ đến hạn", "box 1..5, due_at": "hộp 1..5, due_at", "review attempt": "lượt ôn",
    "due review result": "kết quả ôn đến hạn", "answer": "đáp án", "history / placement": "lịch sử / đầu vào",
    "placement 0.65": "đầu vào 0,65",
    "goal text": "mục tiêu học", "goal_text, goal_embedding": "goal_text, goal_embedding", "GET /recommend": "GET /recommend",
    "mastery of all learners (KNN)": "mastery của mọi người học (KNN)", "due skills": "kỹ năng đến hạn ôn",
    "prerequisites, thresholds": "tiên quyết, ngưỡng", "goal vector": "vector mục tiêu",
    "list + scores + reasons": "danh sách + điểm + lý do", "continue / next / review lists": "danh sách học tiếp / nên học / nên ôn",
    "question": "câu hỏi", "last 6 messages": "6 tin nhắn gần nhất", "top chunks": "các đoạn liên quan nhất",
    "prompt (no PII)": "prompt (không dữ liệu cá nhân)", "JSON answer": "trả lời JSON",
    "messages, citations, engine claims": "tin nhắn, trích dẫn, khẳng định đã kiểm", "answer + citations": "trả lời + trích dẫn",
    "attempt id": "id lượt làm", "error code, prompt": "mã lỗi, prompt", "hint level 1–3": "gợi ý mức 1–3",
    "1–5 stars": "1–5 sao", "rating": "đánh giá",
    "key, chord grid, style, energy": "giọng, lưới hợp âm, phong cách, cường độ",
    "suggestions, voicings, backing track": "gợi ý, thế bấm, bản đệm", "project": "dự án",
    "header, form, mix": "thông tin chung, cấu trúc bài, phối âm", "events in beats": "sự kiện tính theo phách",
    "own projects only": "chỉ dự án của mình", "block text": "nội dung khối", "draft / published revision": "bản sửa nháp / đã phát hành",
    "original block": "khối gốc", "action": "thao tác", "attempts, reviews": "lượt làm, lượt ôn", "charts, funnel": "biểu đồ, phễu",
    "PDF / DOCX / text + source": "PDF / DOCX / văn bản + nguồn", "pages, relevance": "các trang, độ liên quan",
    "selected pages": "các trang được chọn", "draft JSON": "bài nháp JSON", "draft + Engine report": "bài nháp + báo cáo Engine",
    "publish (admin click)": "phát hành (Admin bấm)",
    # ERD: tên quan hệ
    "owns": "sở hữu", "requires": "cần", "contains": "chứa", "cites": "trích", "used in": "dùng trong", "has": "có",
    "trains": "luyện", "versioned as": "có phiên bản", "makes": "thực hiện", "answers": "trả lời", "diagnoses": "chẩn đoán",
    "tracks": "theo dõi", "progress of": "tiến độ của", "has cards": "có thẻ", "reviews": "ôn", "schedules": "xếp lịch",
    "state of": "trạng thái của", "logs": "ghi lại", "practises": "luyện tập", "masters": "thành thạo", "measured": "được đo",
    "history": "lịch sử", "event of": "sự kiện của", "takes": "làm", "receives": "nhận", "opens": "mở", "holds": "chứa",
    "rates": "đánh giá", "gives": "cho", "creates": "tạo", "chords": "hợp âm", "drums": "trống", "revises": "sửa",
    "acts": "thao tác", "uploads": "tải lên", "summarises": "tóm tắt", "drafts": "soạn",
    # SiteMap
    "/  Home (public)": "/  Trang chủ (công khai)", "/dang-nhap  Login": "/dang-nhap  Đăng nhập",
    "/dang-ky  Register": "/dang-ky  Đăng ký", "*  404 Not found": "*  404 Không tìm thấy",
    "/#chuong-trinh  Curriculum": "/#chuong-trinh  Chương trình học", "/#tinh-nang  Features": "/#tinh-nang  Tính năng",
    "/app  Dashboard\\n[login required]": "/app  Tổng quan\\n[cần đăng nhập]", "/app/hoc  Lessons": "/app/hoc  Bài học",
    "/app/hoc?bai=L01  Lesson runner": "/app/hoc?bai=L01  Học từng bước", "/app/luyen-tap  Practice": "/app/luyen-tap  Luyện tập",
    "/app/tien-do  Progress & flashcards": "/app/tien-do  Tiến độ & thẻ ôn", "/app/quiz  Skill quiz": "/app/quiz  Quiz kỹ năng",
    "/app/composition  Harmony Lab": "/app/composition  Harmony Lab", "/app/ho-so  Profile": "/app/ho-so  Hồ sơ",
    "/app/kiem-tra-dau-vao  Placement test": "/app/kiem-tra-dau-vao  Kiểm tra đầu vào",
    "AI Tutor drawer\\n(on every /app page)": "Ngăn AI Tutor\\n(trên mọi trang /app)",
    "/admin  Administration\\n[role = admin, else 403]": "/admin  Quản trị\\n[role = admin, nếu không thì 403]",
    "Tab: Statistics": "Tab: Thống kê", "Tab: Lessons (edit, preview,\\npublish, history, hide)":
        "Tab: Bài học (sửa, xem trước,\\nphát hành, lịch sử, ẩn)", "Tab: AI lesson drafts": "Tab: AI soạn bài",
    "Tab: Users (lock / unlock)": "Tab: Người dùng (khóa / mở khóa)",
    # Lưu đồ: chung
    "Start": "Bắt đầu", "End": "Kết thúc", "Yes": "Có", "No": "Không",
    # Lưu đồ 1: đăng nhập
    "Input e-mail, password\n(client IP from proxy)": "Nhập email, mật khẩu\n(IP máy khách từ proxy)",
    "key = ip | normalised e-mail": "khóa = ip | email đã chuẩn hóa",
    "failures(key) >= 5\nin 15 minutes?": "số lần sai(khóa) >= 5\ntrong 15 phút?",
    "Return 429 LOGIN_LOCKED\n+ Retry-After": "Trả 429 LOGIN_LOCKED\n+ Retry-After",
    "Find user by e-mail;\nbcrypt verify (dummy hash if none)": "Tìm user theo email;\nkiểm bcrypt (băm giả nếu không có)",
    "Password OK and user\nactive, not synthetic?": "Mật khẩu đúng và user\nđang hoạt động, không mô phỏng?",
    "Redis INCR login_fail:key\n(TTL 15 min on first failure)": "Redis INCR login_fail:khóa\n(TTL 15 phút ở lần sai đầu)",
    "Return 401\nINVALID_CREDENTIALS": "Trả 401\nINVALID_CREDENTIALS",
    "Reset counter;\ncreate refresh token (SHA-256 stored)": "Xóa bộ đếm;\ntạo refresh token (lưu băm SHA-256)",
    "Return access JWT (30 min)\n+ HttpOnly refresh cookie (7 days)": "Trả JWT truy cập (30 phút)\n+ refresh cookie HttpOnly (7 ngày)",
    # Lưu đồ 2: nộp đáp án
    "Input exercise_version_id,\nanswer, input method": "Nhập exercise_version_id,\nđáp án, cách nhập",
    "Version is the current\npublished one?": "Phiên bản là bản\nđang phát hành?",
    "Return 409\nEXERCISE_VERSION_SUPERSEDED": "Trả 409\nEXERCISE_VERSION_SUPERSEDED",
    "Input method allowed\nfor this question?": "Cách nhập được phép\ncho câu này?",
    "Return 422 (no attempt saved)": "Trả 422 (không lưu lượt làm)",
    "Music Engine grades with the version's\nanswer_key + grader_config":
        "Music Engine chấm theo answer_key\n+ grader_config của phiên bản",
    "Save attempt + attempt_errors\n(is_test = true if admin)": "Lưu attempt + attempt_errors\n(is_test = true nếu là Admin)",
    "Admin test attempt?": "Lượt làm thử\ncủa Admin?", "Correct?": "Đúng?",
    "First attempt\nof this question?": "Lượt đầu tiên\ncủa câu này?", "Previous attempt\nwas wrong?": "Lượt trước\nbị sai?",
    "result = 1": "kết quả = 1", "result = 0.5": "kết quả = 0,5", "result = 0": "kết quả = 0",
    "repeat correct:\ncount only, score unchanged": "đúng lặp lại:\nchỉ đếm, điểm giữ nguyên",
    "mastery = old + 0.3 × (result − old)\nlevel: weak < 0.60 (≥5 tries), ready ≥ 0.60, mastered ≥ 0.80":
        "mastery = cũ + 0,3 × (kết quả − cũ)\nmức: yếu < 0,60 (≥ 5 lượt), sẵn sàng ≥ 0,60, thành thạo ≥ 0,80",
    "Return correct?, error code, feedback;\nexplanation if correct or wrong ≥ 2 times":
        "Trả đúng?, mã lỗi, phản hồi;\nlời giải khi đúng hoặc sai ≥ 2 lần",
    "Learner presses\nComplete lesson?": "Người học bấm\nHoàn thành bài?",
    "Every question correct\nat least once?": "Mọi câu đã đúng\nít nhất một lần?",
    "Return 409\nLESSON_NOT_MASTERED": "Trả 409\nLESSON_NOT_MASTERED",
    "Mark completed; create review_states\nbox 1, due_at = now": "Đánh dấu hoàn thành; tạo review_states\nhộp 1, due_at = bây giờ",
    "Review card: correct when due → box+1\n(1-2-4-8-16 days); wrong → box 1, +1 day;\ncorrect before due → keep box":
        "Ôn thẻ: đúng khi đến hạn → hộp+1\n(1-2-4-8-16 ngày); sai → hộp 1, +1 ngày;\nđúng trước hạn → giữ hộp",
    # Lưu đồ 3: gợi ý
    "Input: learner (token), goal text,\nmastery, due cards": "Vào: người học (token), mục tiêu học,\nmastery, thẻ đến hạn",
    "Build 14-dimension vector\n(mean mastery per group_code)": "Dựng vector 14 chiều\n(mastery trung bình theo group_code)",
    "≥ 1 neighbour sharing\n≥ 3 assessed dimensions?": "Có ≥ 1 người học lân cận\nchung ≥ 3 chiều đã đánh giá?",
    "Weights 0.35 content, 0.25 mastery,\n0.20 due, 0.20 collaborative (KNN k = 10)":
        "Trọng số 0,35 nội dung, 0,25 mastery,\n0,20 đến hạn, 0,20 cộng tác (KNN k = 10)",
    "Cold start: content 0.55,\nmastery 0.25, due 0.20, CF 0": "Khởi đầu lạnh: nội dung 0,55,\nmastery 0,25, đến hạn 0,20, CF 0",
    "For each lesson": "Với mỗi bài học",
    "Has a skill below 0.80 and every\nprerequisite ≥ 0.60? (layer 1)": "Có kỹ năng dưới 0,80 và mọi\ntiên quyết ≥ 0,60? (tầng 1)",
    "Exclude lesson\n(reason stored)": "Loại bài\n(lưu lý do)",
    "Skill score = w·content (cosine goal vs skill, layer 2)\n+ w·(1 − mastery) + w·due + w·CF (layer 3)\nLesson score = mean over open skills":
        "Điểm kỹ năng = w·nội dung (cosine mục tiêu – kỹ năng, tầng 2)\n+ w·(1 − mastery) + w·đến hạn + w·CF (tầng 3)\nĐiểm bài = trung bình các kỹ năng đang mở",
    "More lessons?": "Còn bài?",
    "Sort by score, then curriculum order;\ntake top 5; write reason sentence":
        "Sắp theo điểm, rồi theo thứ tự chương trình;\nlấy 5 bài đầu; viết câu lý do",
    "Split: Continue (started) / Next (new) /\nReview (completed, label \"Ôn lại\")":
        "Chia: Học tiếp (đã bắt đầu) / Nên học (mới) /\nNên ôn (đã xong, nhãn \"Ôn lại\")",
    "Save recommendation_logs": "Lưu recommendation_logs", "Output: 3 lists with reasons": "Ra: 3 danh sách kèm lý do",
    # Lưu đồ 4: AI Tutor
    "Input question, session_id": "Nhập câu hỏi, session_id", "> 20 questions\nin 60 s?": "> 20 câu\ntrong 60 s?",
    "Return 429 AI_RATE_LIMITED": "Trả 429 AI_RATE_LIMITED", "Prompt injection\ndetected?": "Phát hiện\ntiêm lệnh?",
    "Fixed refusal": "Câu từ chối cố định",
    "Intent + rewrite follow-up;\nretrieve top chunks (Qdrant e5,\nfallback e5 in memory + BM25)":
        "Ý định + viết lại câu hỏi nối tiếp;\ntruy xuất đoạn liên quan (Qdrant e5,\ndự phòng e5 trong bộ nhớ + BM25)",
    "Route?": "Luồng?", "Greeting / help\n(fixed text)": "Chào hỏi / trợ giúp\n(câu cố định)",
    "Off-topic: ≤ 2 sentences,\nthen lead back": "Ngoài chủ đề: ≤ 2 câu,\nrồi dẫn về bài học",
    "Outside lessons: Gemini general\nanswer, Engine scans notes": "Ngoài bài học: Gemini trả lời\nchung, Engine dò các nốt",
    "AI enabled and\ndaily quota (30) left?": "AI đang bật và còn\nhạn mức ngày (30)?",
    "Answer from lesson text +\nMusic Engine (no AI)": "Trả lời từ bài học +\nMusic Engine (không AI)",
    "Build prompt: question, 6 last messages,\nchunks, weak skills (no PII)":
        "Dựng prompt: câu hỏi, 6 tin gần nhất,\nđoạn bài, kỹ năng yếu (không dữ liệu cá nhân)",
    "Call Gemini → JSON": "Gọi Gemini → JSON",
    "Keep only citations whose block id\nwas in the retrieved context": "Chỉ giữ trích dẫn có id khối\nnằm trong ngữ cảnh đã truy xuất",
    "Music Engine confirms every\nnote / chord / interval?": "Music Engine xác nhận mọi\nnốt / hợp âm / quãng?",
    "Already\nretried once?": "Đã thử lại\nmột lần?", "Rule-based fallback answer": "Trả lời dự phòng theo luật",
    "Save chat_messages (citations,\nengine claims, latency, tokens)": "Lưu chat_messages (trích dẫn,\nkhẳng định đã kiểm, độ trễ, token)",
    "Output answer + citations + verified flag": "Ra câu trả lời + trích dẫn + cờ đã kiểm",
    "G / D": "G / D", "C": "C", "B": "B", "A (in lessons)": "A (trong bài học)", "No (retry)": "Không (thử lại)",
}


def nhan(s: str) -> str:
    """Nhãn sơ đồ bằng tiếng Việt; thiếu bản dịch thì báo lỗi để không lọt chữ Anh vào bản tiếng Việt."""
    if s in SO_DO:
        return SO_DO[s]
    raise KeyError(f"Thiếu bản dịch nhãn sơ đồ: {s!r}")
