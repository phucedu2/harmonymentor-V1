"""Chữ song ngữ (English, Tiếng Việt) của từng mục trong tài liệu Review 01–03.

Mọi số liệu ở đây đã đối chiếu với code nhánh phuc-music commit COMMIT; nguồn của từng số ghi ở
BAO_CAO_BAN_GIAO.md mục 3. Chỗ SRS khác code thì viết theo code (danh sách lệch ở báo cáo bàn giao mục 5).
"""

from __future__ import annotations

COMMIT = "1ab6a15"
EFF = {"R01": "20/10/2026", "R02": "03/11/2026", "R03": "17/11/2026"}

GROUPS_FOR_DOC = [
    ("learning_content", "Learning content", "Nội dung học", [
        "skills", "skill_prerequisites", "lessons", "lesson_blocks", "source_works", "lesson_sources",
        "exercises", "exercise_versions", "review_items"]),
    ("learning_activity", "Accounts and learning activity", "Tài khoản và hoạt động học", [
        "users", "refresh_tokens", "attempts", "attempt_errors", "lesson_progress", "review_states",
        "review_attempts", "practice_attempts", "mastery_states", "mastery_events", "placement_results"]),
    ("ai", "AI Tutor and recommendation", "AI Tutor và gợi ý", [
        "recommendation_logs", "chat_sessions", "chat_messages", "chat_feedback"]),
    ("lab", "Harmony Lab", "Harmony Lab", ["composition_projects", "chord_events", "drum_events"]),
    ("admin", "Administration", "Quản trị", ["content_revisions", "admin_audit_log", "source_documents", "ai_lesson_drafts"]),
]

# ------------------------------------------------------------------------------------------------ front matter
ACKNOWLEDGE = [
    ("This project gave our group the chance to put the five subjects of Semester II together in one real product. "
     "Python taught us to write the Music Engine as pure, testable code. AI Fundamental gave us the EMA mastery model, "
     "Leitner spaced review, KNN and the offline metrics HitRate@5 and Precision@5. NLP gave us embeddings, retrieval "
     "with citations and intent routing for the AI Tutor. FastAPI let us build a clear REST API with automatic "
     "OpenAPI documentation, and Docker let the whole system start with one command.",
     "Đồ án giúp nhóm ghép năm môn học của Học kỳ II vào một sản phẩm thật. Python giúp nhóm viết Music Engine thành code "
     "thuần, kiểm thử được. AI Fundamental cho nhóm mô hình mastery EMA, ôn tập ngắt quãng Leitner, KNN và các chỉ số "
     "offline HitRate@5, Precision@5. NLP cho nhóm embedding, truy xuất có trích dẫn và định tuyến ý định cho AI Tutor. "
     "FastAPI giúp xây REST API rõ ràng có tài liệu OpenAPI tự sinh, còn Docker giúp cả hệ thống chạy bằng một lệnh."),
    ("We thank FPT Aptech for the project framework and the review process, which made us write down every "
     "design decision and check it against the running code.",
     "Nhóm cảm ơn FPT Aptech đã tạo khung đồ án và quy trình review, giúp nhóm ghi lại mọi quyết định thiết kế "
     "và đối chiếu với code đang chạy."),
]

SYNOPSIS = [
    ("The primary objective of this program is to provide hands-on experience in working on real-life projects. "
     "Rather than focusing on one tool, the project combines the subjects of Semester II: Python programming, "
     "AI fundamentals, natural language processing, API design with FastAPI and containerisation with Docker.",
     "Mục tiêu chính của chương trình là cho sinh viên kinh nghiệm thực tế với một dự án thật. Thay vì chỉ một công cụ, "
     "đồ án kết hợp các môn của Học kỳ II: lập trình Python, nền tảng AI, xử lý ngôn ngữ tự nhiên, thiết kế API với "
     "FastAPI và đóng gói bằng Docker."),
    ("HarmonyMentor AI is a web platform that helps beginners learn music theory and harmony in a loop: Learn → "
     "Practise → Diagnose → Review → Apply. Every answer is graded by a deterministic Music Engine written in pure "
     "Python, which also names the error (for example THIRD_QUALITY when F# is used instead of F in D minor). "
     "Mastery per skill is updated with an exponential moving average, flashcards follow a 5-box Leitner schedule, "
     "and a three-tier hybrid recommender suggests the next lessons with a reason. An AI Tutor answers questions "
     "with citations to the lesson text; every note and chord in its answer is checked by the Music Engine, and "
     "when AI is switched off the whole learning loop still works with rule-based answers. Harmony Lab lets "
     "learners build 4–8 bar chord loops and play along with backing tracks in 9 styles.",
     "HarmonyMentor AI là nền tảng web giúp người mới học nhạc lý và hòa âm theo vòng: Học → Luyện tập → Chẩn đoán "
     "→ Ôn tập → Vận dụng. Mọi đáp án được chấm bằng Music Engine tất định viết bằng Python thuần; Engine còn gọi tên "
     "lỗi (ví dụ THIRD_QUALITY khi dùng F# thay vì F trong D minor). Mức thành thạo từng kỹ năng cập nhật bằng trung "
     "bình trượt hàm mũ, thẻ ôn theo lịch Leitner 5 hộp, hệ gợi ý lai 3 tầng đề xuất bài tiếp theo kèm lý do. "
     "AI Tutor trả lời có trích dẫn bài học; mọi nốt, hợp âm trong câu trả lời đều được Music Engine kiểm, và khi tắt AI "
     "cả vòng học vẫn chạy bằng câu trả lời theo luật. Harmony Lab cho người học dựng vòng hợp âm 4–8 ô nhịp và chơi "
     "theo bản đệm 9 phong cách."),
    ("The system is built with React 18 + TypeScript (Vite) on the front end, FastAPI + SQLAlchemy 2 on the back end, "
     "PostgreSQL 16 (31 tables, Alembic migrations), Redis for the login limiter, Qdrant for lesson-chunk vectors and "
     "Google Gemini as the optional external AI service. Docker Compose starts all five services with one command. "
     "This document describes the system as it is in the code (branch phuc-music, commit 1ab6a15); items of the SRS "
     "that are not built yet are listed as future scope.",
     "Hệ thống dùng React 18 + TypeScript (Vite) ở giao diện, FastAPI + SQLAlchemy 2 ở backend, PostgreSQL 16 (31 bảng, "
     "migration Alembic), Redis cho bộ giới hạn đăng nhập, Qdrant cho vector đoạn bài học và Google Gemini là dịch vụ AI "
     "bên ngoài, có thể tắt. Docker Compose khởi động cả 5 dịch vụ bằng một lệnh. Tài liệu mô tả hệ thống đúng như "
     "trong code (nhánh phuc-music, commit 1ab6a15); phần SRS chưa làm được ghi ở hướng phát triển."),
]

# ------------------------------------------------------------------------------------------------ Problem Definition
PD_INTRO = [
    ("Many students like to play music but are weak at music theory. They learn from videos, articles or quiz apps. "
     "These sources explain concepts well but leave three problems:",
     "Nhiều học sinh, sinh viên thích chơi nhạc nhưng chưa vững nhạc lý. Các bạn tự học qua video, bài viết hoặc ứng dụng "
     "trắc nghiệm. Những nguồn này giải thích khái niệm khá tốt nhưng còn ba vấn đề:"),
]
PD_PROBLEMS = [
    ("They do not show where the mistake is. A learner who builds G7 as G B D F# only learns that the answer is wrong, "
     "not that the 7th is the wrong interval.",
     "Không chỉ ra chỗ sai. Người học dựng G7 thành G B D F# chỉ biết đáp án sai, chứ không biết lỗi nằm ở quãng 7 bị dựng sai."),
    ("Theory is separated from practice. Passing a quiz does not mean the learner can use the idea to accompany a "
     "chord loop.", "Lý thuyết tách rời thực hành. Làm đúng trắc nghiệm chưa có nghĩa là biết dùng để đệm một vòng hợp âm."),
    ("General chatbots can state wrong music theory, for example list the wrong notes of a chord, and beginners "
     "cannot notice it.", "Chatbot thông dụng có thể nói sai nhạc lý, ví dụ liệt kê sai nốt của hợp âm, người mới học khó nhận ra."),
]
PD_SOLUTION = (
    "HarmonyMentor AI grades every answer with fixed music-theory rules in a Music Engine, tells the learner exactly "
    "what is wrong, schedules the weak skill for review, recommends the next lesson with a reason and offers an AI Tutor "
    "whose musical facts are always checked by the same Music Engine. The rule is: AI explains and suggests; the "
    "Music Engine decides what is right.",
    "Giải pháp: HarmonyMentor AI chấm mọi đáp án bằng luật nhạc lý cố định trong Music Engine, nói rõ sai ở đâu, đưa "
    "kỹ năng yếu vào lịch ôn, gợi ý bài tiếp theo kèm lý do và có AI Tutor mà mọi dữ kiện nhạc lý đều được chính Music "
    "Engine kiểm. Nguyên tắc: AI giải thích và gợi ý; Music Engine quyết định đúng sai.")

OBJECTIVES = [
    ("Diagnostic practice:", "every answer is graded by the Music Engine (strict note spelling or piano keys) and "
     "returns an error code and a feedback sentence; the full explanation appears after a correct answer or two "
     "wrong answers.", "Luyện tập có chẩn đoán:", "mọi đáp án được Music Engine chấm (đúng tên nốt hoặc đúng phím "
     "piano), trả mã lỗi và câu phản hồi; lời giải đầy đủ hiện khi đúng hoặc sau 2 lần sai."),
    ("Mastery and spaced review:", "EMA mastery per skill (alpha 0.3, ready 0.60, mastered 0.80) and a 5-box Leitner "
     "schedule (1, 2, 4, 8, 16 days); cards of a completed lesson are due at once.", "Thành thạo và ôn ngắt quãng:",
     "mastery EMA theo kỹ năng (alpha 0,3, sẵn sàng 0,60, thành thạo 0,80) và lịch Leitner 5 hộp (1, 2, 4, 8, 16 ngày); "
     "thẻ của bài vừa xong đến hạn ngay."),
    ("Personal learning path:", "a three-tier hybrid recommender (rule filter, content match with the learner's goal, "
     "KNN collaborative filtering) returns three lists: continue, next and review, each lesson with a reason.",
     "Lộ trình cá nhân:", "hệ gợi ý lai 3 tầng (lọc luật, so khớp mục tiêu, lọc cộng tác KNN) trả ba danh sách: học "
     "tiếp, nên học, nên ôn, mỗi bài kèm lý do."),
    ("Grounded AI Tutor:", "answers with citations to lesson blocks, keeps the last 6 messages as memory, checks every "
     "note and chord with the Music Engine and falls back to rule-based answers when AI is off or fails.",
     "AI Tutor có căn cứ:", "trả lời có trích dẫn khối bài học, nhớ 6 tin nhắn gần nhất, kiểm mọi nốt và hợp âm bằng "
     "Music Engine, dùng câu trả lời theo luật khi AI tắt hoặc lỗi."),
    ("Secure, one-command deployment:", "bcrypt passwords, 30-minute JWT, rotating 7-day refresh cookie, login lock after "
     "5 failures in 15 minutes, data filtered by user_id from the token; Docker Compose runs all services.",
     "Bảo mật, triển khai một lệnh:", "mật khẩu bcrypt, JWT 30 phút, refresh cookie 7 ngày xoay vòng, khóa đăng nhập "
     "sau 5 lần sai trong 15 phút, dữ liệu lọc theo user_id trong token; Docker Compose chạy mọi dịch vụ."),
]

ROLES_INTRO = ("The code has two account roles (learner, admin) in users.role, plus the guest (no token) and one "
               "external service.", "Code có hai vai trò tài khoản (learner, admin) trong users.role, cộng với khách "
               "(chưa đăng nhập) và một dịch vụ bên ngoài.")
ROLES = [
    [("Guest", "Khách"), ("Visitor without a token.", "Người chưa đăng nhập."),
     ("View the home page and public curriculum; register; log in. Any /app or /admin page redirects to /dang-nhap.",
      "Xem trang chủ và chương trình công khai; đăng ký; đăng nhập. Vào /app hay /admin sẽ bị chuyển về /dang-nhap.")],
    [("Learner", "Người học"), ("Registered student (role = learner).", "Học sinh đã đăng ký (role = learner)."),
     ("Placement test; lessons with piano and staff; answer questions; review flashcards; practice and skill quiz; "
      "progress; recommendations; AI Tutor chat and 'Explain this error'; rate answers; Harmony Lab projects; profile "
      "and goal. Sees only own data; other users' resources return 404; /admin returns 403.",
      "Kiểm tra đầu vào; học bài có piano, khuông nhạc; làm câu hỏi; ôn thẻ; luyện tập và quiz kỹ năng; tiến độ; gợi ý; "
      "chat AI Tutor và 'Giải thích lỗi này'; chấm sao; dự án Harmony Lab; hồ sơ và mục tiêu. Chỉ xem dữ liệu của mình; "
      "tài nguyên người khác trả 404; /admin trả 403.")],
    [("Admin", "Quản trị viên"), ("Content and account manager (role = admin).", "Người quản lý nội dung và tài khoản (role = admin)."),
     ("Statistics dashboard; edit lesson text as draft then publish; show / hide lessons; lock / unlock users; upload "
      "documents and ask Gemini for lesson drafts checked by the Music Engine; every action is written to "
      "admin_audit_log. Admin attempts are stored with is_test = true and excluded from mastery and statistics.",
      "Bảng thống kê; sửa chữ bài học thành bản nháp rồi phát hành; ẩn / hiện bài; khóa / mở khóa người dùng; tải tài "
      "liệu lên và nhờ Gemini soạn bài nháp có Music Engine kiểm; mọi thao tác ghi vào admin_audit_log. Lượt làm của "
      "Admin lưu is_test = true, không tính mastery và thống kê.")],
    [("Google Gemini (external AI service)", "Google Gemini (dịch vụ AI bên ngoài)"),
     ("Called only by the backend AI pipeline when AI_ENABLED = true and a key is set.",
      "Chỉ pipeline AI của backend gọi tới, khi AI_ENABLED = true và đã cấu hình khóa."),
     ("Receives the question, the last 6 messages, lesson chunks, weak skill names and the error code; never e-mail, "
      "name, password or user id. Returns JSON that is parsed, citation-checked and Music-Engine-checked before display. "
      "Default models: gemini-3.5-flash-lite (fallback gemini-3.6-flash) and gemini-embedding-001.",
      "Nhận câu hỏi, 6 tin nhắn gần nhất, đoạn bài học, tên kỹ năng yếu và mã lỗi; không bao giờ nhận email, tên, mật "
      "khẩu hay mã người dùng. Trả JSON được phân tích, kiểm trích dẫn và kiểm bằng Music Engine trước khi hiển thị. "
      "Mô hình mặc định: gemini-3.5-flash-lite (dự phòng gemini-3.6-flash) và gemini-embedding-001.")],
]

IMPACT = [
    ("For learners:", "a wrong answer becomes a lesson, because the learner sees which interval or note is wrong and the "
     "skill comes back in the review queue.", "Với người học:", "câu sai trở thành bài học, vì người học thấy sai ở quãng "
     "hay nốt nào và kỹ năng đó quay lại trong hàng đợi ôn."),
    ("For teachers and content authors:", "lessons, questions and flashcards keep their source (provenance); published "
     "question versions are immutable, so learning history stays meaningful after edits.",
     "Với giáo viên và người soạn nội dung:", "bài học, câu hỏi và thẻ ôn giữ nguồn; phiên bản câu hỏi đã phát hành không "
     "đổi, nên lịch sử học vẫn đúng nghĩa sau khi sửa."),
    ("For safe AI in education:", "the AI can only explain and suggest; facts are verified by deterministic code and the "
     "system keeps working without AI.", "Với AI an toàn trong giáo dục:", "AI chỉ giải thích và gợi ý; dữ kiện được code "
     "tất định kiểm và hệ thống vẫn chạy khi không có AI."),
    ("For the team:", "the project practises all five Semester II subjects with real tests (1,448 backend tests, 282 "
     "frontend tests) and continuous integration on GitHub Actions.", "Với nhóm:", "đồ án luyện cả năm môn Học kỳ II "
     "với kiểm thử thật (1.448 test backend, 282 test frontend) và CI trên GitHub Actions."),
]

SCOPE_INTRO = ("Scope is written from the code on branch phuc-music, commit 1ab6a15 (17/11/2026).",
               "Phạm vi viết theo code nhánh phuc-music, commit 1ab6a15 (17/11/2026).")
SCOPE_BUILT = [
    [("Accounts: register, login with lock, refresh rotation, profile, goal, placement test (12 questions).",
      "Tài khoản: đăng ký, đăng nhập có khóa, xoay refresh, hồ sơ, mục tiêu, kiểm tra đầu vào (12 câu)."),
     "backend/app/auth/, services/placement_service.py"],
    [("Curriculum: 9 visible lessons in modules M1–M5 (plus 3 drafts), 26 skills, 73 published question versions, "
      "70 flashcards in the demo database.",
      "Chương trình: 9 bài hiển thị trong module M1–M5 (thêm 3 bài nháp), 26 kỹ năng, 73 phiên bản câu hỏi đã phát "
      "hành, 70 thẻ ôn trong CSDL demo."), "backend/app/content/, SQL count on the demo DB 17/11/2026"],
    [("Music Engine grading with error codes; piano, staff (VexFlow) and audio (Tone.js).",
      "Music Engine chấm và sinh mã lỗi; piano, khuông nhạc (VexFlow), âm thanh (Tone.js)."),
     "backend/app/music_engine/, frontend/src/components/learning/"],
    [("EMA mastery, Leitner review, practice generator (chord / interval / scale / roman), skill quiz from the bank.",
      "Mastery EMA, ôn Leitner, bộ sinh câu luyện tập (chord / interval / scale / roman), quiz kỹ năng từ ngân hàng câu."),
     "services/mastery_service.py, review_scheduler.py, api/practice"],
    [("Hybrid recommender (rules + content + KNN) with three lists and logs.",
      "Hệ gợi ý lai (luật + nội dung + KNN), ba danh sách và nhật ký."), "backend/app/ai/recommender/"],
    [("AI Tutor pipeline: guard, intent routing, Qdrant / e5 retrieval, citations, Music Engine safety check, "
      "fallback, rating; 'Explain this error' in 3 levels.",
      "Pipeline AI Tutor: chặn, định tuyến ý định, truy xuất Qdrant / e5, trích dẫn, kiểm an toàn bằng Music Engine, "
      "dự phòng, chấm sao; 'Giải thích lỗi này' 3 mức."), "services/ai_pipeline.py, docs/AI_PIPELINE.md"],
    [("Harmony Lab: 4–8 bar loops, 9 backing styles, song form, rule-based chord suggestions, save / open projects.",
      "Harmony Lab: vòng 4–8 ô nhịp, 9 phong cách đệm, chế độ bài hát, gợi ý hợp âm theo luật, lưu / mở dự án."),
     "backend/app/composition/ (ADR-010, 012, 013)"],
    [("Admin: statistics, lesson text revisions, visibility, users, audit log, AI lesson drafts from uploaded documents.",
      "Quản trị: thống kê, bản sửa chữ bài học, ẩn hiện, người dùng, nhật ký, AI soạn bài nháp từ tài liệu tải lên."),
     "backend/app/admin/ (ADR-025 status: proposed)"],
]
FUTURE_INTRO = ("Items below appear in the SRS but are not built (or only partly built) in the code. They are not "
                "claimed as features of this version.",
                "Các mục dưới có trong SRS nhưng chưa làm (hoặc mới làm một phần) trong code, không được coi là tính "
                "năng của bản này.")
FUTURE = [
    [("Harmony assistant chat mode", "Chế độ trợ lý hòa âm"),
     ("Only the value 'harmony_assistant' exists in the chat_sessions.mode CHECK; no behaviour.",
      "Chỉ có giá trị 'harmony_assistant' trong CHECK của chat_sessions.mode; chưa có hành vi.")],
    [("Proactive coaching (FR-16: review reminders, congratulations)", "Kèm cặp chủ động (FR-16: nhắc ôn tập, lời chúc mừng)"),
     ("Not built.", "Chưa làm.")],
    [("AI-generated quiz of 10 questions (FR-14)", "Quiz 10 câu do AI sinh (FR-14)"),
     ("Quiz draws questions from the existing bank (/practice/quiz); no AI generation; endpoint /quiz/generate absent.",
      "Quiz lấy câu từ ngân hàng có sẵn (/practice/quiz); chưa có AI sinh; không có endpoint /quiz/generate.")],
    [("AI ranking and explanation of chord suggestions (FR-18)", "AI xếp hạng và giải thích gợi ý hợp âm (FR-18)"),
     ("Rule-based suggestions exist; AI ranking not built.", "Đã có gợi ý theo luật; chưa có AI xếp hạng.")],
    [("Melody, MIDI / audio export, sharing in Harmony Lab", "Giai điệu, xuất MIDI / âm thanh, chia sẻ"),
     ("Not built.", "Chưa làm.")],
    [("Course / module tables, lesson_chunks table with pgvector, content import endpoint",
      "Bảng courses / modules, bảng lesson_chunks pgvector, endpoint nhập nội dung"),
     ("Not in models.py: modules are a text column lessons.track; chunks live in Qdrant / JSON; "
      "/admin/content/import absent.",
      "Không có trong models.py: module là cột chữ lessons.track; đoạn bài học nằm ở Qdrant / JSON; không có /admin/content/import.")],
    [("Microphone grading, ear training, mobile app, payments, public deployment",
      "Chấm qua micro, luyện tai, ứng dụng di động, thanh toán, triển khai công khai"),
     ("Out of scope in the SRS; not built.", "Ngoài phạm vi trong SRS; chưa làm.")],
]
SCOPE_NOTE = (
    "Note on AI lesson drafts (ADR-025): the brief listed it as future scope, but the code already contains it "
    "(source_documents, ai_lesson_drafts, admin tab 'AI soạn bài'). Following the rule 'write what the code does', it "
    "is described as built. Its ADR status is still 'proposed', it has not been tried end-to-end with a real Gemini key "
    "in this documentation run (AI was off), and every draft needs an admin click to publish.",
    "Ghi chú về AI soạn bài nháp (ADR-025): đề bài xếp vào hướng phát triển, nhưng code đã có (source_documents, "
    "ai_lesson_drafts, tab 'AI soạn bài'). Theo quy tắc 'viết theo code', tài liệu mô tả là đã làm. ADR vẫn ở trạng "
    "thái 'đề xuất', lần chạy để viết tài liệu chưa thử với khóa Gemini thật (AI tắt), và bản nháp nào cũng cần Admin "
    "bấm phát hành.")

# ------------------------------------------------------------------------------------------------ CRS
CRS_INTRO = ("This section states what the customer (learners, admins and the faculty) needs and how each need is "
             "accepted. Inputs, processes and outputs are taken from the real endpoints (85 routes under /api/v1, "
             "file _nguon/du_lieu/endpoints.txt).",
             "Mục này nêu khách hàng (người học, quản trị viên, giảng viên) cần gì và nghiệm thu thế nào. Đầu vào, xử lý, "
             "đầu ra lấy theo endpoint thật (85 route dưới /api/v1, file _nguon/du_lieu/endpoints.txt).")

IPO = [
    (("Guest", "Khách"), [
        [("E-mail, password, display name", "Email, mật khẩu, tên hiển thị"),
         ("POST /auth/register: validate strength, hash with bcrypt, create user, issue tokens",
          "POST /auth/register: kiểm độ mạnh, băm bcrypt, tạo user, cấp token"),
         ("Access JWT + HttpOnly refresh cookie; redirect to placement test", "JWT + refresh cookie HttpOnly; chuyển tới kiểm tra đầu vào")],
        [("E-mail, password", "Email, mật khẩu"),
         ("POST /auth/login: limiter (5 failures / 15 min per IP + e-mail), bcrypt check",
          "POST /auth/login: bộ giới hạn (5 lần sai / 15 phút theo IP + email), kiểm bcrypt"),
         ("Tokens, or 401 INVALID_CREDENTIALS, or 429 LOGIN_LOCKED with Retry-After",
          "Token, hoặc 401 INVALID_CREDENTIALS, hoặc 429 LOGIN_LOCKED kèm Retry-After")],
    ]),
    (("Learner", "Người học"), [
        [("12 placement answers", "12 câu trả lời đầu vào"), ("Grade with the Music Engine; set mastery 0.65 for correct skills",
          "Chấm bằng Music Engine; đặt mastery 0,65 cho kỹ năng làm đúng"), ("Placement result, starting path", "Kết quả đầu vào, lộ trình bắt đầu")],
        [("Answer text / choice / piano keys + input method", "Đáp án chữ / lựa chọn / phím piano + cách nhập"),
         ("POST /attempts: grade the exact published version, save attempt + errors, update EMA in the same transaction",
          "POST /attempts: chấm đúng phiên bản đã phát hành, lưu lượt + lỗi, cập nhật EMA trong cùng giao dịch"),
         ("correct, error code, feedback, explanation (after correct or 2 wrong)", "đúng/sai, mã lỗi, phản hồi, lời giải (khi đúng hoặc sau 2 lần sai)")],
        [("Complete lesson", "Hoàn thành bài"), ("Check every active question answered correctly; create review_states due now",
          "Kiểm mọi câu đang chạy đã đúng; tạo review_states đến hạn ngay"), ("Completed, or 409 LESSON_NOT_MASTERED", "Hoàn thành, hoặc 409 LESSON_NOT_MASTERED")],
        [("Flashcard answer / rating", "Đáp án thẻ / tự đánh giá"), ("Leitner update; due reviews may update mastery once per skill per day",
          "Cập nhật Leitner; lượt ôn đúng hạn cập nhật mastery tối đa 1 lần/kỹ năng/ngày"), ("New box and due date", "Hộp và hạn mới")],
        [("Goal text", "Mục tiêu bằng lời"), ("Embed the goal; rules + content + KNN scoring", "Nhúng mục tiêu; tính điểm luật + nội dung + KNN"),
         ("Lists continue / next / review with reasons", "Danh sách học tiếp / nên học / nên ôn kèm lý do")],
        [("Chat question, session id", "Câu hỏi chat, mã phiên"), ("AI pipeline: guard, route, retrieve, prompt, Gemini, citation and Music Engine checks",
          "Pipeline AI: chặn, định tuyến, truy xuất, prompt, Gemini, kiểm trích dẫn và Music Engine"),
         ("Answer with citations and a verified flag, or fallback answer", "Câu trả lời có trích dẫn và cờ đã kiểm, hoặc câu dự phòng")],
        [("Key, chords, style, tempo", "Giọng, hợp âm, phong cách, tốc độ"), ("Arranger builds a deterministic backing track; project saved in beats",
          "Bộ phối dựng bản đệm tất định; dự án lưu theo phách"), ("Playable loop / song, saved project", "Vòng / bài phát được, dự án đã lưu")],
    ]),
    (("Admin", "Quản trị viên"), [
        [("Block text edits, publish / hide", "Sửa chữ khối, phát hành / ẩn"), ("Save content_revisions draft; publish on click; write audit log",
          "Lưu bản nháp content_revisions; phát hành khi bấm; ghi nhật ký"), ("Updated lesson for learners", "Bài cập nhật cho người học")],
        [("Lock / unlock user", "Khóa / mở khóa người dùng"), ("Set users.is_active; audit log", "Đặt users.is_active; ghi nhật ký"),
         ("User list with status", "Danh sách người dùng kèm trạng thái")],
        [("PDF / DOCX / text + source + consent", "PDF / DOCX / văn bản + nguồn + đồng ý"),
         ("Extract pages, music-theory relevance gate, Gemini draft, Music Engine report", "Trích trang, cổng liên quan nhạc lý, Gemini soạn nháp, Music Engine kiểm"),
         ("Draft with Engine flags; published only by admin click", "Bản nháp kèm cờ Engine; chỉ phát hành khi Admin bấm")],
        [("Open statistics", "Mở thống kê"), ("Aggregate attempts (is_test = false), reviews, activity", "Tổng hợp lượt làm (is_test = false), lượt ôn, hoạt động"),
         ("Cards: learners, 7-day activity, accuracy, due cards, daily chart", "Thẻ số: người học, hoạt động 7 ngày, tỉ lệ đúng, thẻ đến hạn, biểu đồ")],
    ]),
    (("External AI service (Google Gemini)", "Dịch vụ AI bên ngoài (Google Gemini)"), [
        [("Prompt without personal data", "Prompt không có dữ liệu cá nhân"), ("Generate a JSON answer / embedding", "Sinh câu trả lời JSON / embedding"),
         ("JSON text or vector; on error / 429 the backend uses the fallback", "JSON hoặc vector; khi lỗi / 429 backend dùng dự phòng")],
    ]),
]

HW_INTRO = ("Exact versions come from backend/requirements.txt (pip freeze in the API image), frontend/package.json, "
            "Dockerfiles and docker-compose.yml at commit 1ab6a15.",
            "Phiên bản lấy từ backend/requirements.txt (pip freeze trong image API), frontend/package.json, Dockerfile và "
            "docker-compose.yml ở commit 1ab6a15.")
HW = [
    [("Developer / demo PC", "Máy phát triển / demo"), ("64-bit CPU with 4 cores, 8 GB RAM (16 GB recommended with Docker), "
      "15 GB free disk, Windows 10/11, macOS or Linux", "CPU 64-bit 4 nhân, RAM 8 GB (khuyên 16 GB khi dùng Docker), trống 15 GB, Windows 10/11, macOS hoặc Linux"),
     ("Team recommendation; e5 model 470 MB + images", "Khuyến nghị của nhóm; mô hình e5 470 MB + image")],
    [("Run used for this document", "Máy chạy để viết tài liệu"), ("Cloud Linux container, 4 vCPU, 15 GB RAM, Docker 29.9.2, Compose v5.6.1",
      "Container Linux trên cloud, 4 vCPU, RAM 15 GB, Docker 29.9.2, Compose v5.6.1"), ("Measured 17/11/2026", "Đo ngày 17/11/2026")],
    [("Client", "Máy người dùng"), ("Chrome or Edge desktop; learning page works at 390 px width; speakers for audio",
      "Chrome hoặc Edge desktop; trang học dùng được ở 390 px; loa để nghe"), ("SRS Table 9", "SRS Bảng 9")],
    [("Network", "Mạng"), ("Internet only for Gemini when AI_ENABLED = true; the learning loop works offline from AI",
      "Chỉ cần Internet cho Gemini khi AI_ENABLED = true; vòng học chạy không cần AI"), ("Rule 3, CLAUDE.md", "Nguyên tắc 3")],
]
SW = [
    [("Backend runtime", "Môi trường backend"), ("Python 3.11 (image python:3.11-slim), FastAPI 0.163.1, Uvicorn, SQLAlchemy 2.1.9, "
      "Alembic 1.20.1, psycopg 3.3.9, Pydantic 2.14.3", "Python 3.11 (image python:3.11-slim), FastAPI 0.163.1, Uvicorn, SQLAlchemy 2.1.9, Alembic 1.20.1, psycopg 3.3.9, Pydantic 2.14.3"),
     "Dockerfile, pip freeze"],
    [("Security", "Bảo mật"), ("bcrypt 5.0.0, PyJWT 2.15.1, redis-py 8.1.0", "bcrypt 5.0.0, PyJWT 2.15.1, redis-py 8.1.0"), "pip freeze"],
    [("AI / NLP", "AI / NLP"), ("numpy 2.4.6, scikit-learn 1.9.1, onnxruntime 1.32.0, tokenizers 0.23.3 (local e5-small), "
      "google-genai 3.4.0, qdrant-client 1.12.2, pypdf 7.1.0, python-docx 1.2.0", "numpy 2.4.6, scikit-learn 1.9.1, onnxruntime 1.32.0, tokenizers 0.23.3 (e5-small cục bộ), google-genai 3.4.0, qdrant-client 1.12.2, pypdf 7.1.0, python-docx 1.2.0"), "pip freeze"],
    [("Music", "Âm nhạc"), ("Own Music Engine (pure Python); music21 10.5.2 used in tests / tools", "Music Engine tự viết (Python thuần); music21 10.5.2 dùng trong test / công cụ"), "backend/app/music_engine/"],
    [("Frontend", "Giao diện"), ("Node 22, React 18.3.1, react-router 7.18.4, @tanstack/react-query 5.104.4, Vite 6.0.7, "
      "TypeScript 5.6.3, Tailwind CSS 4.3.3, Tone.js 15.1.22, VexFlow 5.0.0, GSAP 3.13.0, Lenis 1.3.4", "Node 22, React 18.3.1, react-router 7.18.4, @tanstack/react-query 5.104.4, Vite 6.0.7, TypeScript 5.6.3, Tailwind CSS 4.3.3, Tone.js 15.1.22, VexFlow 5.0.0, GSAP 3.13.0, Lenis 1.3.4"),
     "frontend/package.json"],
    [("Data services", "Dịch vụ dữ liệu"), ("PostgreSQL 16 (pgvector/pgvector:pg16), Redis 7 (redis:7-alpine), Qdrant v1.12.4",
      "PostgreSQL 16 (pgvector/pgvector:pg16), Redis 7 (redis:7-alpine), Qdrant v1.12.4"), "docker-compose.yml"],
    [("Web server", "Máy chủ web"), ("nginx 1.27-alpine serving the Vite build on port 5173, proxy /api → api:8000",
      "nginx 1.27-alpine phục vụ bản build Vite cổng 5173, chuyển /api → api:8000"), "Dockerfile (web)"],
    [("Testing", "Kiểm thử"), ("pytest 9.2.0, Vitest 3.2.4, Playwright 1.63.0 (manual journey script), GitHub Actions CI",
      "pytest 9.2.0, Vitest 3.2.4, Playwright 1.63.0 (kịch bản thủ công), CI GitHub Actions"), ".github/workflows/ci.yml"],
    [("Tools", "Công cụ"), ("Git, Docker Desktop / Docker Engine with Compose v2, VS Code", "Git, Docker Desktop / Docker Engine có Compose v2, VS Code"), "README"],
]

AC_INTRO = ("Each criterion is written as Given / When / Then. The 'Proof' column names the manual test (MT, section 9.3) "
            "or pytest file that shows it; the full mapping is in BAO_CAO_BAN_GIAO.md.",
            "Mỗi tiêu chí viết theo Cho / Khi / Thì. Cột 'Bằng chứng' ghi ca thủ công (MT, mục 9.3) hoặc file pytest chứng "
            "minh; bảng đầy đủ ở BAO_CAO_BAN_GIAO.md.")
ACCEPTANCE = [
    ("a guest on /dang-ky", "the password is weak (e.g. 'abc')", "the account is not created and the unmet strength rule is shown",
     "khách ở /dang-ky", "mật khẩu yếu (ví dụ 'abc')", "không tạo tài khoản và hiện điều kiện chưa đạt", "MT-03; tests/test_auth.py"),
    ("a guest with valid data", "they register", "they are logged in and sent to the placement test",
     "khách nhập dữ liệu hợp lệ", "đăng ký", "được đăng nhập và chuyển tới kiểm tra đầu vào", "MT-02"),
    ("any user", "the password is wrong 5 times within 15 minutes", "the next login returns 429 LOGIN_LOCKED and the page says to retry in about 15 minutes",
     "bất kỳ người dùng", "sai mật khẩu 5 lần trong 15 phút", "lần sau trả 429 LOGIN_LOCKED và trang báo thử lại sau khoảng 15 phút", "MT-24; tests/test_auth.py"),
    ("a learner", "they open /admin or call /api/v1/admin/*", "the page shows 403 and the API returns 401 / 403",
     "người học", "mở /admin hoặc gọi /api/v1/admin/*", "trang báo 403 và API trả 401 / 403", "MT-22, MT-23; tests/test_admin_quan_tri.py"),
    ("a learner", "they request another learner's chat session or project", "the API returns 404",
     "người học", "gọi phiên chat hay dự án của người khác", "API trả 404", "tests/test_ai_gd3_tutor_api.py"),
    ("a new learner", "they finish the 12-question placement test", "skills answered correctly start at mastery 0.65",
     "người học mới", "làm xong 12 câu đầu vào", "kỹ năng làm đúng bắt đầu ở mastery 0,65", "MT-04"),
    ("the question 'build D minor'", "the learner types D F# A", "it is wrong and the feedback says a major 3rd was used instead of a minor 3rd (F# → F)",
     "câu 'dựng D minor'", "người học gõ D F# A", "bị chấm sai và phản hồi nói dùng quãng 3 trưởng thay vì quãng 3 thứ (F# → F)", "MT-07"),
    ("a question answered wrongly twice", "the second wrong answer is graded", "the full explanation is shown",
     "câu đã sai 2 lần", "lần sai thứ hai được chấm", "lời giải đầy đủ hiện ra", "MT-08"),
    ("'build Ab major' graded with strict spelling", "the answer is G# C D#", "it is wrong with code ENHARMONIC_SPELLING",
     "câu 'dựng Ab trưởng' chấm đúng tên nốt", "đáp án là G# C D#", "bị chấm sai với mã ENHARMONIC_SPELLING", "tests/test_srs_examples.py"),
    ("a skill at mastery m", "a first-time correct answer is submitted", "mastery becomes m + 0.3 × (1 − m); correct after wrong uses 0.5; wrong uses 0",
     "kỹ năng có mastery m", "trả lời đúng lần đầu", "mastery thành m + 0,3 × (1 − m); đúng sau sai dùng 0,5; sai dùng 0", "tests/test_cp2_mastery_ema.py"),
    ("a lesson with an unanswered question", "the learner clicks Complete", "the API returns 409 LESSON_NOT_MASTERED",
     "bài còn câu chưa đúng", "người học bấm Hoàn thành", "API trả 409 LESSON_NOT_MASTERED", "tests/test_audit_nguoi_moi.py"),
    ("a completed lesson", "the learner opens Progress", "its flashcards are due now; a correct card moves to box 2 (2 days), a wrong card to box 1 (1 day)",
     "bài đã hoàn thành", "người học mở Tiến độ", "thẻ của bài đến hạn ngay; thẻ đúng lên hộp 2 (2 ngày), thẻ sai về hộp 1 (1 ngày)", "MT-11, MT-13, MT-14; tests/test_hm012_leitner.py"),
    ("a learner with a goal", "the dashboard loads", "recommendation lists appear and every lesson has a reason",
     "người học đã có mục tiêu", "mở bảng điều khiển", "danh sách gợi ý hiện ra, bài nào cũng có lý do", "MT-16; tests/test_ai_gd2_recommend_api.py"),
    ("AI_ENABLED = false", "the learner asks 'Which notes are in D minor?'", "the answer comes from the lesson and the Music Engine (Dm = D F A) with a citation",
     "AI_ENABLED = false", "người học hỏi 'Hợp âm D minor gồm những nốt nào?'", "câu trả lời lấy từ bài học và Music Engine (Dm = D F A) có trích dẫn", "MT-17"),
    ("a prompt-injection message", "it is sent to the AI Tutor", "the tutor refuses and reveals nothing",
     "tin nhắn tiêm lệnh", "gửi cho AI Tutor", "trợ lý từ chối, không lộ gì", "MT-18; tests/test_ai_gd3_guardrail.py"),
    ("an AI answer that names notes or chords", "a note disagrees with the Music Engine", "the pipeline retries once, then uses the rule-based fallback",
     "câu trả lời AI có nêu nốt, hợp âm", "một nốt khác Music Engine", "pipeline thử lại 1 lần rồi dùng câu dự phòng theo luật", "tests/test_ai_gd3_tutor_api.py"),
    ("Harmony Lab", "the learner saves the loop C–Am–F–G", "the project is saved with chord events in beats and can be reopened",
     "Harmony Lab", "người học lưu vòng C–Am–F–G", "dự án được lưu với sự kiện hợp âm theo phách và mở lại được", "MT-20; tests/test_phuc_music_harmony_lab.py"),
    ("an admin", "they edit lesson text", "a draft revision is stored, published only on click, and logged",
     "Admin", "sửa chữ bài học", "lưu bản nháp, chỉ phát hành khi bấm, có ghi nhật ký", "MT-26; tests/test_admin_quan_tri.py"),
    ("an admin answering a question", "the attempt is saved", "it has is_test = true and does not change mastery or statistics",
     "Admin làm thử câu hỏi", "lượt được lưu", "có is_test = true, không đổi mastery và thống kê", "tests/test_cp2_mastery_scope.py"),
    ("a clean machine with Docker", "docker compose up --build runs", "all five services start and /api/v1/health reports db ok and redis ok",
     "máy mới có Docker", "chạy docker compose up --build", "cả 5 dịch vụ chạy và /api/v1/health báo db ok, redis ok", "Run 17/11/2026 (handover §4)"),
]

PLAN_INTRO = ("Roles follow SRS Table 14. The six parts follow the SRS phases and checkpoints; the status column is "
              "taken from merged pull requests on GitHub.",
              "Vai trò theo SRS Bảng 14. Sáu phần việc theo giai đoạn và mốc trong SRS; cột trạng thái lấy từ các pull "
              "request đã gộp trên GitHub.")
TEAM = [
    ["Thắng", ("Technical lead. Back end, Music Engine, recommender, AI integration, database, merging source code.",
               "Trưởng nhóm kỹ thuật. Backend, Music Engine, hệ gợi ý, tích hợp AI, cơ sở dữ liệu, hợp nhất mã nguồn.")],
    ["Phúc", ("Learning interface, virtual piano, staff, Tone.js audio, chat window, Harmony Lab (reduced).",
              "Giao diện học tập, piano ảo, khuông nhạc, âm thanh Tone.js, khung chat, Harmony Lab bản rút gọn.")],
    ["Đạt", ("Writing the 9 lessons and references, music-theory test set, quality testing, report editing.",
             "Biên soạn 9 bài học và nguồn tham chiếu, bộ câu hỏi kiểm thử nhạc lý, kiểm thử chất lượng, biên tập báo cáo.")],
]
PLAN = [
    ["1", ("Analysis and design documents (SRS 2.1, functional spec, overview and detailed design)", "Tài liệu phân tích và thiết kế (SRS 2.1, đặc tả chức năng, thiết kế tổng quan và thiết kế chi tiết)"),
     "Thắng, Đạt", "19/10 – 26/10/2026", ("Done (PR #1, #7)", "Xong")],
    ["2", ("Music Engine, grading, exercise taxonomy, lesson 1 (CP1)", "Music Engine, chấm bài, phân loại bài tập, bài 1 (CP1)"),
     "Thắng", "19/10 – 20/10/2026 (CP1)", ("Done (PR #2–#6)", "Xong")],
    ["3", ("Mastery, Leitner, hybrid recommender and offline metrics (CP2)", "Mastery, Leitner, hệ gợi ý lai, chỉ số offline (CP2)"),
     "Thắng", "26/10 – 03/11/2026 (CP2)", ("Done; results on simulated data only (PR #11, #20–#25)", "Xong; kết quả chỉ trên dữ liệu mô phỏng")],
    ["4", ("AI Tutor with citations, guardrails, fallback (CP3)", "AI Tutor có trích dẫn, chặn, dự phòng (CP3)"),
     "Thắng", "03/11 – 10/11/2026 (CP3)", ("Done (PR #20–#47)", "Xong")],
    ["5", ("Learning UI, piano, staff, audio, Harmony Lab, admin pages", "Giao diện học, piano, khuông, âm thanh, Harmony Lab, trang quản trị"),
     "Phúc", "19/10 – 17/11/2026", ("Done (PR #12, #16, #19, #49–#53, #61)", "Xong")],
    ["6", ("Lessons and sources, music test set, QA, Docker, documentation and submission",
           "Bài học và nguồn, bộ test nhạc lý, kiểm thử, Docker, tài liệu và nộp"),
     "Đạt", "20/10 – 04/12/2026", ("In progress: this document, demo video, signatures", "Đang làm: tài liệu này, video demo, chữ ký")],
]
MILESTONES = [
    ["CP1", "20/10/2026", ("Music Engine spec, exercise taxonomy, tests passing", "Đặc tả Music Engine, phân loại bài tập, test đạt"),
     ("PR #5, #6 merged 20/10/2026", "PR #5, #6 gộp 20/10/2026")],
    ["CP2", "03/11/2026", ("Recommender running with HitRate@5 and Precision@5 table", "Hệ gợi ý chạy, có bảng HitRate@5, Precision@5"),
     ("docs/giai-doan/ai-gd4/BAO_CAO_THUC_NGHIEM.md (04/11/2026)", "docs/giai-doan/ai-gd4/BAO_CAO_THUC_NGHIEM.md (04/11/2026)")],
    ["CP3", "10/11/2026", ("AI Tutor answers with lesson citations", "AI Tutor trả lời có trích dẫn bài học"),
     ("PR #36 CP3 evidence, merged 09/11/2026", "PR #36 minh chứng CP3, gộp 09/11/2026")],
    ["Submission", "04/12/2026", ("Source code, Docker, documents, report, demo video", "Mã nguồn, Docker, tài liệu, báo cáo, video demo"),
     ("This document (Draft PR); video not made yet", "Tài liệu này (Draft PR); chưa có video")],
]

# ------------------------------------------------------------------------------------------------ DFD
DFD_INTRO = ("Processes are circles, external entities are rectangles and data stores are open boxes labelled Dx. "
             "Store names are the real table names from backend/app/db/models.py; R1 is Redis and V1 is Qdrant.",
             "Tiến trình là hình tròn, tác nhân ngoài là hình chữ nhật, kho dữ liệu là ô có mã Dx. Tên kho là tên bảng thật "
             "trong models.py; R1 là Redis, V1 là Qdrant.")
DFD0_TEXT = ("At level 0 the whole system is one process. Guests send registration data; learners send answers, piano "
             "input, flashcard answers, goals, chat questions and chord grids; admins send content edits and documents. "
             "Gemini receives only a prompt without personal data and returns JSON that the system checks.",
             "Ở mức 0 cả hệ thống là một tiến trình. Khách gửi dữ liệu đăng ký; người học gửi đáp án, phím piano, đáp án "
             "thẻ, mục tiêu, câu hỏi chat và vòng hợp âm; Admin gửi bản sửa nội dung và tài liệu. Gemini chỉ nhận prompt "
             "không có dữ liệu cá nhân và trả JSON để hệ thống kiểm.")
DFD1_INTRO = ("Level 1 is split into four parts so that each diagram stays readable on A4. Process numbers run from 1.0 "
              "to 21.0 across the parts.", "Mức 1 tách thành bốn phần để đọc được trên A4. Số tiến trình chạy từ 1.0 "
              "đến 21.0 qua các phần.")
DFD1_PARTS = [
    ("dfd_l1_auth", "Part 1: Accounts and access", "Phần 1: Tài khoản và truy cập",
     ("Register, login with temporary lock in Redis, refresh / logout, profile and role check, admin user management "
      "(auth/router.py, auth/service.py, auth/login_limiter.py).",
      "Đăng ký, đăng nhập có khóa tạm trong Redis, làm mới token / đăng xuất, hồ sơ và kiểm tra vai trò, Admin quản lý người dùng (auth/router.py, auth/service.py, auth/login_limiter.py).")),
    ("dfd_l1_learning", "Part 2: Learning, grading, mastery and review", "Phần 2: Học, chấm bài, mastery và ôn tập",
     ("Lessons, answer submission graded by the Music Engine, EMA update, lesson completion that creates Leitner cards, "
      "flashcard review, practice / placement / quiz (services/learning_service.py, review_scheduler.py).",
      "Bài học, nộp đáp án do Music Engine chấm, cập nhật mastery EMA, hoàn thành bài tạo thẻ Leitner, ôn thẻ, luyện tập / kiểm tra đầu vào / quiz (services/learning_service.py, review_scheduler.py).")),
    ("dfd_l1_ai", "Part 3: Recommendation and AI Tutor", "Phần 3: Gợi ý và AI Tutor",
     ("Goal embedding, hybrid recommendation, AI Tutor chat with retrieval from Qdrant, 'Explain this error' and "
      "answer rating (ai/recommender/, services/ai_pipeline.py).",
      "Nhúng (embedding) mục tiêu học, gợi ý lai, chat AI Tutor có truy xuất từ Qdrant, 'Giải thích lỗi này' và chấm sao câu trả lời (ai/recommender/, services/ai_pipeline.py).")),
    ("dfd_l1_lab_admin", "Part 4: Harmony Lab and administration", "Phần 4: Harmony Lab và quản trị",
     ("Chord suggestions and backing tracks, project save / open, lesson text revisions, statistics and AI lesson drafts "
      "(composition/, admin/).", "Gợi ý hợp âm và bản đệm, lưu / mở dự án, sửa nội dung bài học, thống kê và AI soạn bài nháp (composition/, admin/).")),
]
STORES_INTRO = ("Data stores used in the level-1 diagrams.", "Các kho dữ liệu dùng trong DFD mức 1.")
STORES = [
    ["D1", ("Users", "Người dùng"), "users", "1.0, 2.0, 4.0, 5.0, 12.0, 13.0"],
    ["D2", ("Refresh tokens", "Refresh token"), "refresh_tokens", "2.0, 3.0"],
    ["D3", ("Lessons", "Bài học"), "lessons, lesson_blocks (+ source_works, lesson_sources)", "6.0, 19.0, 21.0"],
    ["D4", ("Questions", "Câu hỏi"), "exercises, exercise_versions", "6.0, 7.0"],
    ["D5", ("Attempts", "Lượt làm"), "attempts, attempt_errors", "7.0, 9.0, 20.0"],
    ["D6", ("Mastery", "Mức thành thạo"), "mastery_states, mastery_events", "8.0, 11.0, 13.0"],
    ["D7", ("Lesson progress", "Tiến độ bài"), "lesson_progress", "9.0"],
    ["D8", ("Flashcards and schedule", "Thẻ và lịch ôn"), "review_items, review_states", "9.0, 10.0, 13.0"],
    ["D9", ("Review attempts", "Lượt ôn"), "review_attempts", "10.0"],
    ["D10", ("Practice and placement", "Luyện tập và đầu vào"), "practice_attempts, placement_results", "11.0"],
    ["D11", ("Skill graph", "Đồ thị kỹ năng"), "skills, skill_prerequisites", "13.0"],
    ["D12", ("Recommendation log", "Nhật ký gợi ý"), "recommendation_logs", "13.0"],
    ["D13", ("Chat history", "Lịch sử chat"), "chat_sessions, chat_messages", "14.0"],
    ["D14", ("Chat ratings", "Đánh giá chat"), "chat_feedback", "16.0"],
    ["D15", ("Lab projects", "Dự án Lab"), "composition_projects", "18.0"],
    ["D16", ("Lab events", "Sự kiện Lab"), "chord_events, drum_events", "18.0"],
    ["D17", ("Content revisions", "Bản sửa nội dung"), "content_revisions", "19.0"],
    ["D18", ("Uploaded documents", "Tài liệu tải lên"), "source_documents", "21.0"],
    ["D19", ("AI lesson drafts", "Bài nháp AI"), "ai_lesson_drafts", "21.0"],
    ["D20", ("Audit log", "Nhật ký quản trị"), "admin_audit_log", "5.0, 19.0"],
    ["R1", ("Login failure counter", "Bộ đếm đăng nhập sai"), "Redis key login_fail:{ip}|{email}, TTL 15 min", "2.0"],
    ["V1", ("Lesson chunk vectors", "Vector đoạn bài học"), "Qdrant collection harmony_knowledge (e5, 82 chunks in the demo run)", "14.0"],
]

# ------------------------------------------------------------------------------------------------ ERD
ERD_INTRO = ("Entities are rectangles and relationships are diamonds (Chen notation). Every relationship comes from a "
             "real foreign key in models.py; '1' and 'n' are written on the lines. The overall ERD shows 14 core "
             "entities; the group ERDs show all 31 tables.",
             "Thực thể là hình chữ nhật, quan hệ là hình thoi (ký hiệu Chen). Mọi quan hệ lấy từ khóa ngoại thật trong "
             "models.py; '1' và 'n' ghi trên đường nối. ERD tổng quan có 14 thực thể cốt lõi; các ERD nhóm phủ đủ 31 bảng.")
CARDINALITY = [
    ("One user makes many attempts, has many mastery states (one per skill, unique user_id + skill_id), many review "
     "states (one per card), many chat sessions, many recommendation logs and many Harmony Lab projects.",
     "Một người dùng có nhiều lượt làm, nhiều mastery (mỗi kỹ năng một dòng, duy nhất user_id + skill_id), nhiều lịch "
     "ôn (mỗi thẻ một dòng), nhiều phiên chat, nhiều nhật ký gợi ý và nhiều dự án Harmony Lab."),
    ("One lesson has many blocks, many exercises and many flashcards; one exercise has many versions (unique "
     "exercise_id + version) and every attempt points to exactly one version.",
     "Một bài có nhiều khối, nhiều câu hỏi, nhiều thẻ; một câu hỏi có nhiều phiên bản (duy nhất exercise_id + version) "
     "và mỗi lượt làm trỏ đúng một phiên bản."),
    ("One user has at most one placement result (placement_results.user_id is both primary and foreign key: 1 : 1).",
     "Một người dùng có tối đa một kết quả đầu vào (user_id vừa là khóa chính vừa là khóa ngoại: 1 : 1)."),
    ("Skills form a many-to-many prerequisite graph through skill_prerequisites; lessons and sources are many-to-many "
     "through lesson_sources.", "Kỹ năng tạo đồ thị tiên quyết nhiều–nhiều qua skill_prerequisites; bài học và nguồn "
     "nhiều–nhiều qua lesson_sources."),
    ("One chat session holds many messages; one message can have many star ratings (chat_feedback). One project has "
     "many chord events and drum events.", "Một phiên chat có nhiều tin nhắn; một tin nhắn có thể có nhiều đánh giá. "
     "Một dự án có nhiều sự kiện hợp âm và trống."),
]
ERD_GROUPS = [
    ("erd_learning_content", "ERD: learning content", "ERD: nội dung học"),
    ("erd_learning_activity", "ERD: accounts and learning activity", "ERD: tài khoản và hoạt động học"),
    ("erd_ai", "ERD: AI Tutor and recommendation", "ERD: AI Tutor và gợi ý"),
    ("erd_lab", "ERD: Harmony Lab", "ERD: Harmony Lab"),
    ("erd_admin", "ERD: administration", "ERD: quản trị"),
]
ATTR_INTRO = ("Attribute diagrams for all 31 tables, grouped as in the ERD. The primary key is underlined.",
              "Hình sao thuộc tính cho đủ 31 bảng, nhóm như ERD. Khóa chính được gạch dưới.")

TAB_INTRO = ("Generated from the SQLAlchemy models (script _nguon/du_lieu/dump_schema.py → schema.json), so names, types, "
             "keys and constraints match the code exactly. Types are PostgreSQL types (TIMESTAMPTZ = TIMESTAMP WITH TIME "
             "ZONE). PK = primary key, FK = foreign key, UQ = unique. Published question versions are additionally "
             "protected by PostgreSQL triggers created in the Alembic migrations.",
             "Sinh tự động từ các model SQLAlchemy (script _nguon/du_lieu/dump_schema.py → schema.json), nên tên, kiểu, khóa và ràng buộc khớp đúng code. Kiểu dữ liệu là kiểu của PostgreSQL (TIMESTAMPTZ = TIMESTAMP WITH TIME ZONE). PK = khóa chính, FK = khóa ngoại, UQ = duy nhất. Phiên bản câu hỏi đã phát hành còn được bảo vệ thêm bằng trigger PostgreSQL tạo trong migration Alembic.")
REL_INTRO = ("Relationship diagrams show each table with its columns; lines go from the referenced key to the foreign "
             "key (crow's foot = many).", "Sơ đồ quan hệ hiện từng bảng với các cột; đường nối từ khóa được tham chiếu "
             "tới khóa ngoại (chân chim = nhiều).")
REL_DIAGRAMS = [
    ("rel_learning_content", "Relationship diagram: learning content", "Sơ đồ quan hệ: nội dung học"),
    ("rel_learning_activity", "Relationship diagram: accounts and learning activity", "Sơ đồ quan hệ: tài khoản và hoạt động học"),
    ("rel_ai", "Relationship diagram: AI Tutor and recommendation", "Sơ đồ quan hệ: AI Tutor và gợi ý"),
    ("rel_lab", "Relationship diagram: Harmony Lab", "Sơ đồ quan hệ: Harmony Lab"),
    ("rel_admin", "Relationship diagram: administration", "Sơ đồ quan hệ: quản trị"),
]

# ------------------------------------------------------------------------------------------------ Site map
SM_INTRO = ("Routes come from frontend/src/App.tsx. Rounded boxes are pages; dashed boxes are panels opened inside a "
            "page (AI Tutor drawer, admin tabs).", "Route lấy từ frontend/src/App.tsx. Ô bo góc là trang; ô nét đứt là "
            "khung mở trong trang (ngăn AI Tutor, tab quản trị).")
ROUTES = [
    ["/", ("Home", "Trang chủ"), ("Public", "Công khai"), ("Introduction, curriculum, features, call to action", "Giới thiệu, chương trình học, tính năng, lời mời bắt đầu")],
    ["/dang-nhap", ("Login", "Đăng nhập"), ("Public", "Công khai"), ("E-mail + password; lock message after 5 failures", "Email + mật khẩu; báo khóa sau 5 lần sai")],
    ["/dang-ky", ("Register", "Đăng ký"), ("Public", "Công khai"), ("Name, e-mail, password with strength rules", "Tên, email, mật khẩu có điều kiện độ mạnh")],
    ["/app", ("Dashboard", "Tổng quan"), ("Login required", "Cần đăng nhập"), ("Goal, recommendations, due cards, AI button", "Mục tiêu, gợi ý, thẻ đến hạn, nút AI")],
    ["/app/kiem-tra-dau-vao", ("Placement test", "Kiểm tra đầu vào"), ("Login required", "Cần đăng nhập"), ("12 questions, result", "12 câu, kết quả")],
    ["/app/hoc (?bai=L01)", ("Lessons", "Bài học"), ("Login required", "Cần đăng nhập"), ("Path by module; lesson steps, piano, staff, questions", "Lộ trình theo module; các bước, piano, khuông, câu hỏi")],
    ["/app/luyen-tap", ("Practice", "Luyện tập"), ("Login required", "Cần đăng nhập"), ("Generated questions and history", "Câu sinh tự động và lịch sử")],
    ["/app/tien-do", ("Progress & flashcards", "Tiến độ và thẻ ôn"), ("Login required", "Cần đăng nhập"), ("Mastery, Leitner review", "Mastery, ôn Leitner")],
    ["/app/quiz", ("Skill quiz", "Quiz kỹ năng"), ("Login required", "Cần đăng nhập"), ("Quiz from the question bank", "Quiz từ ngân hàng câu")],
    ["/app/composition", ("Harmony Lab", "Harmony Lab"), ("Login required", "Cần đăng nhập"), ("Chord loops, styles, song form, projects", "Vòng hợp âm, phong cách, bài hát, dự án")],
    ["/app/ho-so", ("Profile", "Hồ sơ"), ("Login required", "Cần đăng nhập"), ("Name, instrument, goal", "Tên, nhạc cụ, mục tiêu")],
    ["/admin", ("Administration", "Quản trị"), ("Admin only (learner sees 403)", "Chỉ Admin (người học thấy 403)"),
     ("Tabs: Statistics, Lessons, AI lesson drafts, Users", "Tab: Thống kê, Bài học, AI soạn bài, Người dùng")],
    ["*", ("Not found", "Không tìm thấy"), ("Public", "Công khai"), ("404 page", "Trang 404")],
]

# ------------------------------------------------------------------------------------------------ Algorithms
ALG_INTRO = ("Four algorithms are drawn as flowcharts from the code. Each section names the source file.",
             "Bốn thuật toán vẽ thành lưu đồ theo code. Mỗi mục ghi file nguồn.")
ALG_SYMBOLS = [
    [("Ellipse", "Hình elip"), ("Start / End", "Bắt đầu / Kết thúc")],
    [("Parallelogram", "Hình bình hành"), ("Input / Output", "Vào / Ra")],
    [("Rectangle", "Hình chữ nhật"), ("Process", "Xử lý")],
    [("Diamond", "Hình thoi"), ("Decision", "Rẽ nhánh")],
]
ALGS = [
    ("alg_1_dang_nhap", "Login and temporary lock", "Đăng nhập và khóa tạm",
     "backend/app/auth/service.py, auth/login_limiter.py", [
         ("The key is login_fail:{ip}|{email}; the first failure sets a 15-minute TTL.", "Khóa Redis là login_fail:{ip}|{email}; lần sai đầu đặt TTL 15 phút."),
         ("With 5 failures the request is refused with 429 LOGIN_LOCKED and Retry-After, before the password is checked.",
          "Đủ 5 lần sai thì trả 429 LOGIN_LOCKED kèm Retry-After, trước khi kiểm mật khẩu."),
         ("If the e-mail does not exist a dummy bcrypt hash is still checked, so timing does not reveal accounts.",
          "E-mail không tồn tại vẫn kiểm một chuỗi băm giả, để thời gian phản hồi không lộ tài khoản."),
         ("Success clears the counter and issues a 30-minute JWT and a 7-day refresh cookie (stored as SHA-256).",
          "Đúng thì xóa bộ đếm, cấp JWT 30 phút và refresh cookie 7 ngày (lưu dạng SHA-256)."),
     ]),
    ("alg_2_nop_bai", "Answer submission: Music Engine → diagnosis → EMA → Leitner", "Nộp đáp án: Music Engine → chẩn đoán → EMA → Leitner",
     "backend/app/services/learning_service.py, mastery_service.py, review_scheduler.py", [
         ("A superseded version returns 409 EXERCISE_VERSION_SUPERSEDED; an input method not allowed returns 422.",
          "Phiên bản đã bị thay trả 409 EXERCISE_VERSION_SUPERSEDED; cách nhập không cho phép trả 422."),
         ("Result for EMA: first correct = 1, correct after a wrong answer = 0.5, repeated correct = no change, wrong = 0.",
          "Giá trị EMA: đúng lần đầu = 1, đúng sau sai = 0,5, đúng lặp = không đổi, sai = 0."),
         ("mastery = old + 0.3 × (result − old); weak < 0.60 after ≥ 5 attempts, ready ≥ 0.60, mastered ≥ 0.80.",
          "mastery = cũ + 0,3 × (kết quả − cũ); yếu < 0,60 sau ≥ 5 lượt, sẵn sàng ≥ 0,60, thành thạo ≥ 0,80."),
         ("Admin attempts are saved with is_test = true and skip the mastery update.", "Lượt của Admin lưu is_test = true và bỏ qua cập nhật mastery."),
         ("Completing a lesson needs every active question correct at least once; cards then start in box 1, due now. "
          "Leitner: wrong → box 1 (1 day); 'hard' keeps the box; good / easy → next box (2, 4, 8, 16 days); correct before "
          "due keeps box and date.",
          "Hoàn thành bài cần mọi câu đang chạy đúng ít nhất 1 lần; thẻ vào hộp 1, đến hạn ngay. Leitner: sai → hộp 1 "
          "(1 ngày); 'khó' giữ hộp; tốt / dễ → lên hộp (2, 4, 8, 16 ngày); đúng trước hạn giữ hộp và ngày."),
     ]),
    ("alg_3_goi_y", "Three-tier hybrid recommendation", "Gợi ý lai 3 tầng",
     "backend/app/ai/recommender/engine.py, scoring.py, knn.py", [
         ("Tier 1 rules drop a lesson with no MVP skill, with every skill ≥ 0.80, or with a prerequisite < 0.60.",
          "Tầng 1 loại bài không có kỹ năng MVP, bài mọi kỹ năng ≥ 0,80, hoặc bài có tiên quyết < 0,60."),
         ("Tier 2 content: cosine between the goal embedding and each skill embedding.", "Tầng 2 nội dung: cosine giữa embedding mục tiêu và embedding kỹ năng."),
         ("Tier 3 collaborative: KNN with k = 10 on a 14-dimension mastery vector (one per skill group), at least 3 "
          "shared dimensions, fallback 'a'.", "Tầng 3 cộng tác: KNN k = 10 trên vector mastery 14 chiều (mỗi nhóm kỹ "
          "năng một chiều), tối thiểu 3 chiều chung, dự phòng 'a'."),
         ("skill score = 0.35 content + 0.25 (1 − mastery) + 0.20 due + 0.20 cf; cold start uses content 0.55 and cf 0. "
          "Lesson score = mean of its open skills; top 5, ties by curriculum order; lists continue / next / review are "
          "logged in recommendation_logs.",
          "điểm kỹ năng = 0,35 nội dung + 0,25 (1 − mastery) + 0,20 đến hạn + 0,20 cf; người mới dùng nội dung 0,55, cf 0. "
          "Điểm bài = trung bình kỹ năng còn mở; lấy 5, hòa thì theo thứ tự chương trình; ba danh sách ghi vào recommendation_logs."),
     ]),
    ("alg_4_ai_tutor", "AI Tutor: routing, retrieval, citations and fallback", "AI Tutor: định tuyến, truy xuất, trích dẫn, dự phòng",
     "backend/app/services/ai_pipeline.py, docs/AI_PIPELINE.md", [
         ("Rate limit 20 questions per minute; daily quota 30 per learner counted in the database.",
          "Giới hạn 20 câu mỗi phút; hạn mức 30 câu mỗi người mỗi ngày đếm trong CSDL."),
         ("Routes: A in lessons, B general music outside lessons, C off-topic, D help, G greeting.",
          "Luồng: A trong bài, B âm nhạc ngoài bài, C lạc đề, D trợ giúp, G chào hỏi."),
         ("Memory = last 6 messages read from PostgreSQL; no personal data is sent to Gemini.",
          "Bộ nhớ = 6 tin gần nhất đọc từ PostgreSQL; không gửi dữ liệu cá nhân cho Gemini."),
         ("Citations are kept only if the block id was in the retrieved context; every note / chord is checked by the "
          "Music Engine; a mismatch triggers one retry, then the rule-based fallback.",
          "Chỉ giữ trích dẫn có mã khối trong ngữ cảnh đã truy xuất; mọi nốt / hợp âm được Music Engine kiểm; sai thì "
          "thử lại 1 lần rồi dùng câu dự phòng theo luật."),
     ]),
]

# ------------------------------------------------------------------------------------------------ Screen design
SD_INTRO = ("Screenshots were taken on 17/11/2026 from the Docker build of commit 1ab6a15 (light theme, 1440 × 900 "
            "viewport, scale 2) with Playwright, while a demo learner went through the real learning loop. AI was off "
            "(AI_ENABLED = false), so AI screens show the documented fallback mode.",
            "Ảnh chụp ngày 17/11/2026 từ bản Docker của commit 1ab6a15 (giao diện sáng, khung 1440 × 900, tỉ lệ 2) bằng "
            "Playwright, khi một người học demo đi thật qua vòng học. AI tắt (AI_ENABLED = false), nên màn hình AI là "
            "chế độ dự phòng đã thiết kế.")
SCREENS = [
    ("S01_trang_chu", "Home page", "Trang chủ", "/", "Public landing page with the call to action 'Bắt đầu miễn phí' and the login / register menu.",
     "Trang công khai có nút 'Bắt đầu miễn phí' và menu đăng nhập / đăng ký."),
    ("S02_dang_ky", "Register", "Đăng ký", "/dang-ky", "Registration form; password strength rules are shown as the user types.",
     "Form đăng ký; điều kiện độ mạnh mật khẩu hiện khi gõ."),
    ("S03_kiem_tra_dau_vao", "Placement test", "Kiểm tra đầu vào", "/app/kiem-tra-dau-vao", "One of the 12 placement questions.",
     "Một trong 12 câu kiểm tra đầu vào."),
    ("S04_ket_qua_dau_vao", "Placement result", "Kết quả đầu vào", "/app/kiem-tra-dau-vao", "Result 8/12; correct skills start at 0.65.",
     "Kết quả 8/12; kỹ năng làm đúng bắt đầu ở 0,65."),
    ("S05_lo_trinh", "Learning path", "Lộ trình học", "/app/hoc", "Lessons grouped by module with status.", "Bài học theo module kèm trạng thái."),
    ("S06_bai_hoc_piano_khuong", "Lesson step with staff and piano", "Bước học có khuông nhạc và piano", "/app/hoc?bai=L01",
     "Step 13/18 of lesson 1: VexFlow staff and interactive piano with sound.", "Bước 13/18 bài 1: khuông VexFlow và piano có âm thanh."),
    ("S07_tra_loi_sai", "Wrong answer with diagnosis", "Trả lời sai có chẩn đoán", "/app/hoc?bai=L01",
     "D F# A for D minor: the Music Engine names the wrong interval.", "D F# A cho D minor: Music Engine chỉ ra quãng sai."),
    ("S08_tra_loi_dung", "Correct answer", "Trả lời đúng", "/app/hoc?bai=L01", "D F A is graded correct.", "D F A được chấm đúng."),
    ("S09_hoan_thanh_bai", "Lesson completed", "Hoàn thành bài", "/app/hoc?bai=L01", "All questions correct; 8 flashcards are scheduled.",
     "Mọi câu đã đúng; 8 thẻ ôn được xếp lịch."),
    ("S10_on_the_leitner", "Leitner flashcard review", "Ôn thẻ Leitner", "/app/tien-do", "Due cards with box and next date after each answer.",
     "Thẻ đến hạn, sau mỗi câu hiện hộp và ngày ôn sau."),
    ("S11_tien_do", "Progress", "Tiến độ", "/app/tien-do", "Mastery per skill and review summary.", "Mastery theo kỹ năng và tóm tắt ôn tập."),
    ("S12_giai_thich_loi", "Explain this error (AI off)", "Giải thích lỗi này (AI tắt)", "/app/hoc?bai=L01",
     "Level 1/3 hint from the error code with a lesson citation, labelled 'AI is off'.", "Gợi ý mức 1/3 theo mã lỗi kèm trích dẫn bài học, có nhãn 'AI đang tắt'."),
    ("S13_luyen_tap", "Practice", "Luyện tập", "/app/luyen-tap", "Generated chord question and practice history.", "Câu hợp âm sinh tự động và lịch sử luyện tập."),
    ("S14_goi_y", "Recommendations", "Gợi ý bài học", "/app", "Dashboard lists 'next' and 'review' lessons with reasons.",
     "Bảng điều khiển có danh sách 'nên học tiếp' và 'nên ôn lại' kèm lý do."),
    ("S15_ai_tutor", "AI Tutor (fallback mode)", "AI Tutor (chế độ dự phòng)", "/app (AI drawer)",
     "Answer 'Dm = D F A' from the lesson and the Music Engine with citation [L01]; badge shows what could not be verified.",
     "Trả lời 'Dm = D F A' từ bài học và Music Engine kèm trích dẫn [L01]; nhãn cho biết phần chưa kiểm được."),
    ("S16_quiz", "Skill quiz", "Quiz kỹ năng", "/app/quiz", "Quiz from the question bank (4 questions for this skill).", "Quiz từ ngân hàng câu (kỹ năng này có 4 câu)."),
    ("S17_harmony_lab", "Harmony Lab", "Harmony Lab", "/app/composition", "Loop C–Am–F–G with style, tempo and saved project.",
     "Vòng C–Am–F–G với phong cách, tốc độ và dự án đã lưu."),
    ("S18_ho_so", "Profile", "Hồ sơ", "/app/ho-so", "Display name, instrument and goal.", "Tên hiển thị, nhạc cụ và mục tiêu."),
    ("S19b_khoa_dang_nhap", "Login locked", "Khóa đăng nhập", "/dang-nhap", "After 5 wrong passwords the page asks to retry in about 15 minutes.",
     "Sau 5 lần sai mật khẩu, trang yêu cầu thử lại sau khoảng 15 phút."),
    ("S19_admin_thong_ke", "Admin statistics", "Quản trị: thống kê", "/admin", "Learners, 7-day activity, accuracy, due cards and daily chart.",
     "Số người học, hoạt động 7 ngày, tỉ lệ đúng, thẻ đến hạn và biểu đồ theo ngày."),
    ("S20_admin_bai_hoc", "Admin lesson editor", "Quản trị: sửa bài học", "/admin (Lessons tab)", "Block list with Save draft / Preview.",
     "Danh sách khối với Lưu nháp / Xem trước."),
    ("S21_admin_nguoi_dung", "Admin users", "Quản trị: người dùng", "/admin (Users tab)", "User list with lock / unlock.", "Danh sách người dùng có khóa / mở khóa."),
    ("S22_admin_ai_soan_bai", "Admin AI lesson drafts", "Quản trị: AI soạn bài", "/admin (AI tab)",
     "Upload and drafts; shows that the AI feature is off in this run.", "Tải tài liệu và bản nháp; hiện thông báo AI đang tắt trong lần chạy này."),
]

# ------------------------------------------------------------------------------------------------ Testing
TD_INTRO = ("All numbers below were produced by real runs on 17/11/2026 in a cloud Linux container (4 vCPU) on commit "
            "1ab6a15. Logs are summarised in BAO_CAO_BAN_GIAO.md section 4. Failures are reported as they happened; no "
            "code was changed to make a test pass.",
            "Mọi số dưới đây là kết quả chạy thật ngày 17/11/2026 trên container Linux cloud (4 vCPU), commit 1ab6a15. Log "
            "tóm tắt ở BAO_CAO_BAN_GIAO.md mục 4. Lỗi ghi đúng như đã xảy ra; không sửa code để test đạt.")
AUTO_TESTS = [
    [("Backend, CI selection", "Backend, giống CI"), "cd backend && pytest -q -m \"not postgres and not live\"", "1,449", "1,448", "0", "1", "125.75 s", "17/11 12:09–12:11"],
    [("Backend, full run before the e5 model was downloaded", "Backend, chạy toàn bộ trước khi tải mô hình e5"), "cd backend && pytest -q", "1,492", "1,445", "1", "46", "102.19 s", "17/11 12:06–12:08"],
    [("Backend on PostgreSQL 16 + pgvector", "Backend trên PostgreSQL 16"), "TEST_DATABASE_URL=… pytest -m postgres", "25", "25", "0", "0", "20.92 s", "17/11 12:12"],
    [("Frontend unit tests", "Test giao diện"), "cd frontend && npm test", "282 (16 files)", "282", "0", "0", "3.18 s", "17/11 12:06"],
    [("Frontend build", "Build giao diện"), "npm run build", "1 build", "OK", "0", "–", "6.92 s", "17/11"],
]
AUTO_NOTES = [
    ("The skipped CI-selection test is test_g3_qdrant::test_tich_hop_may_chu_qdrant_that; it needs QDRANT_TEST_URL, which "
     "GitHub Actions provides. CI requires at least 1,449 passed, so this local run is one short only because of that skip.",
     "Test bị bỏ qua là test_g3_qdrant::test_tich_hop_may_chu_qdrant_that; nó cần QDRANT_TEST_URL, GitHub Actions có sẵn. "
     "CI yêu cầu ít nhất 1.449 đạt, nên lần chạy này thiếu 1 chỉ vì test bị bỏ qua đó."),
    ("The one failure in the full run (test_g5_eval::test_chatbot_va_cong_nhac_ly_khong_hoi_quy_so_voi_baseline: "
     "groundedness 94.5 < baseline 100) happened because the local e5 model was not downloaded yet; after "
     "'python -m app.ai.local_embedder download' (as CI does) the CI-selection run passed it.",
     "Lỗi duy nhất ở lần chạy đủ (test_g5_eval::test_chatbot_va_cong_nhac_ly_khong_hoi_quy_so_voi_baseline: độ bám nguồn 94,5 < mốc gốc 100) là do mô hình e5 cục bộ chưa được tải; sau khi chạy 'python -m app.ai.local_embedder download' (giống CI), lần chạy giống CI đã đạt test này."),
    ("Total 1,492 = 1,449 SQLite-selection tests + 25 PostgreSQL tests + 18 live / other deselected tests; live Gemini tests "
     "are not run without a key.", "Tổng 1.492 = 1.449 test SQLite + 25 test PostgreSQL + 18 test live / khác bị loại; test "
     "Gemini thật không chạy khi không có khóa."),
]
EVAL_INTRO = ("These numbers come from the team's earlier evaluation reports and were not re-run for this document. "
              "Recommender results use simulated learners: they show the algorithm runs as designed but do not prove "
              "quality with real learners.",
              "Các số này lấy từ báo cáo đánh giá trước đó của nhóm, không chạy lại khi viết tài liệu. Kết quả hệ gợi ý dùng "
              "người học mô phỏng: chỉ cho thấy thuật toán chạy đúng thiết kế, chưa chứng minh chất lượng với người học thật.")
EVALS = [
    [("RAG retrieval (115 cases)", "Truy xuất RAG (115 ca)"), ("HitRate@5 93.0%, MRR 0.848 (e5 / Qdrant); BM25 86.0%, MRR 0.652",
      "HitRate@5 93,0%, MRR 0,848 (e5 / Qdrant); BM25 86,0%, MRR 0,652"), "docs/giai-doan/gop-y-thay/G5_BAO_CAO.md (15/11/2026); guarded by tests/test_g5_eval.py"],
    [("Recommender, 2,000 simulated learners, 395 evaluated", "Hệ gợi ý, 2.000 người mô phỏng, 395 người được đánh giá"),
     ("Popularity P0 HitRate@1 0.967; rules-only P1 0.028 (97% empty lists). The report concludes the current thresholds do "
      "not support the configuration; a question for the technical lead. chưa chứng minh chất lượng với người học thật.",
      "P0 phổ biến HitRate@1 0,967; P1 chỉ luật 0,028 (97% danh sách rỗng). Báo cáo kết luận ngưỡng hiện tại không ủng hộ "
      "cấu hình; đã chuyển câu hỏi cho trưởng nhóm. Chưa chứng minh chất lượng với người học thật."),
     "docs/giai-doan/ai-gd4/BAO_CAO_THUC_NGHIEM.md (04/11/2026)"],
    [("AI Tutor, 30 gold questions with Gemini", "AI Tutor, 30 câu chuẩn với Gemini"),
     ("30/30 answered with correct citations when paced; out-of-scope and attack questions blocked 100%; p95 1.7 s. "
      "Sent back-to-back, 7/30 fell back because of free-tier 429 / 503.",
      "30/30 câu có trích dẫn đúng khi giãn cách; câu ngoài phạm vi và tấn công bị chặn 100%; p95 1,7 s. Gửi liên tục thì "
      "7/30 rơi về dự phòng do 429 / 503 của gói miễn phí."), "docs/giai-doan/ai-gd4/BAO_CAO_THUC_NGHIEM.md (04/11/2026)"],
]
MT_INTRO = ("Manual cases were executed through the real user interface with a Playwright script "
            "(_nguon/kiem_thu/journey.js) against the Docker build, with a freshly registered demo learner "
            "(minhan@harmony.demo) and the demo admin. 'Actual' is the text the app showed, copied from the run log "
            "(kiem_thu/ket_qua_test_thu_cong.json).",
            "Các ca thủ công chạy qua giao diện thật bằng kịch bản Playwright (_nguon/kiem_thu/journey.js) trên bản build Docker, với một người học demo vừa đăng ký (minhan@harmony.demo) và tài khoản Admin demo. Cột 'Thực tế' là chữ ứng dụng hiện ra, chép nguyên văn từ log chạy (kiem_thu/ket_qua_test_thu_cong.json).")
MANUAL = [
    ("TC-01", "Visitor", ("Home page loads", "Trang chủ tải được"), "Open /", "–", ("CTA and login / register menu visible", "Có nút bắt đầu và menu đăng nhập / đăng ký")),
    ("TC-02", "Auth", ("Register with valid data", "Đăng ký hợp lệ"), "Open /dang-ky, fill form, submit", "minhan@harmony.demo (demo learner)",
     ("Logged in, redirected to placement", "Đăng nhập, chuyển tới kiểm tra đầu vào")),
    ("TC-03", "Auth", ("Register with weak password", "Đăng ký mật khẩu yếu"), "Fill form with weak password, submit", "password 'abc'",
     ("Stay on /dang-ky, rule '(chưa đạt)' shown", "Ở lại /dang-ky, hiện '(chưa đạt)'")),
    ("TC-04", "Placement", ("Finish placement test", "Làm xong kiểm tra đầu vào"), "Answer 12 questions", "8 correct, 4 wrong",
     ("Result saved; correct skills at 0.65", "Lưu kết quả; kỹ năng đúng ở 0,65")),
    ("TC-05", "Learning", ("Learning path", "Lộ trình"), "Open /app/hoc", "–", ("9 lessons in modules", "9 bài theo module")),
    ("TC-06", "Learning", ("Staff + piano step", "Bước khuông + piano"), "Open L01, go to step 13/18", "L01", ("Staff and piano rendered (SVG)", "Có khuông và piano (SVG)")),
    ("TC-07", "Grading", ("Wrong answer diagnosis", "Chẩn đoán câu sai"), "Type notes for 'build D minor', submit", "D F# A",
     ("Wrong; names the interval error", "Sai; chỉ ra lỗi quãng")),
    ("TC-08", "Grading", ("Explanation after 2 wrong", "Lời giải sau 2 lần sai"), "Submit a second wrong answer", "D F A#", ("Explanation shown", "Hiện lời giải")),
    ("TC-09", "Grading", ("Correct answer", "Trả lời đúng"), "Submit correct notes", "D F A", ("Marked correct", "Được chấm đúng")),
    ("TC-11", "Learning", ("Complete lesson", "Hoàn thành bài"), "Answer all questions correctly, click Complete", "12/12 correct",
     ("'Hoàn thành!' and cards scheduled", "'Hoàn thành!' và thẻ được xếp lịch")),
    ("TC-12", "AI Tutor", ("Explain this error (AI off)", "Giải thích lỗi (AI tắt)"), "After a wrong answer click 'Giải thích lỗi này'", "AI_ENABLED=false",
     ("Level-1 hint from the error code", "Gợi ý mức 1 theo mã lỗi")),
    ("TC-13", "Review", ("Cards due at once", "Thẻ đến hạn ngay"), "Open /app/tien-do", "after L01", ("8 cards due", "8 thẻ đến hạn")),
    ("TC-14", "Review", ("Leitner boxes", "Hộp Leitner"), "Answer 3 cards", "2 right, 1 wrong", ("Right → box 2 / 2 days; wrong → box 1 / 1 day", "Đúng → hộp 2 / 2 ngày; sai → hộp 1 / 1 ngày")),
    ("TC-15", "Practice", ("Generated practice graded", "Câu luyện tập được chấm"), "Open /app/luyen-tap, answer a chord question", "C E G",
     ("Graded and saved to history", "Được chấm và ghi lịch sử")),
    ("TC-16", "Recommend", ("Recommendations after goal", "Gợi ý sau khi lưu mục tiêu"), "Save goal, open /app", "goal text",
     ("Lists with reasons", "Danh sách kèm lý do")),
    ("TC-17", "AI Tutor", ("Grounded fallback answer", "Trả lời dự phòng có căn cứ"), "Open AI drawer, ask", "'Hợp âm D minor gồm những nốt nào?'",
     ("Dm = D F A with citation", "Dm = D F A có trích dẫn")),
    ("TC-18", "AI Tutor", ("Prompt injection", "Tiêm lệnh"), "Ask to ignore rules and print the system prompt", "injection text", ("Refusal, nothing leaked", "Từ chối, không lộ")),
    ("TC-19", "Quiz", ("Skill quiz", "Quiz kỹ năng"), "Open /app/quiz, pick 'Dựng hợp âm ba'", "skill", ("Quiz questions shown", "Hiện câu quiz")),
    ("TC-20", "Harmony Lab", ("Save a loop", "Lưu vòng hợp âm"), "Open /app/composition, enter chords, save", "C Am F G", ("'Đã lưu' message", "Báo 'Đã lưu'")),
    ("TC-21", "Profile", ("Update profile", "Cập nhật hồ sơ"), "Change display name, save", "Minh An Nguyễn", ("'Đã lưu hồ sơ'", "Báo đã lưu")),
    ("TC-22", "Security", ("Learner opens /admin", "Người học mở /admin"), "Go to /admin as learner", "learner token", ("403 page", "Trang 403")),
    ("TC-23", "Security", ("Admin API without admin token", "API admin không có token admin"), "GET /api/v1/admin/ping", "no token", ("401 or 403", "401 hoặc 403")),
    ("TC-24", "Security", ("Login lock", "Khóa đăng nhập"), "Enter wrong password 5 times, then once more", "khoa.thu@harmony.demo",
     ("Locked message (~15 min)", "Báo khóa (~15 phút)")),
    ("TC-25", "Admin", ("Statistics", "Thống kê"), "Log in as admin, open /admin", "admin@harmony.demo", ("Stat cards shown", "Hiện thẻ số liệu")),
    ("TC-26", "Admin", ("Lesson editor", "Sửa bài học"), "Lessons tab, 'Sửa nội dung bài 1'", "L01", ("Blocks, Save draft / Preview", "Khối, Lưu nháp / Xem trước")),
    ("TC-27", "Admin", ("User list", "Danh sách người dùng"), "Users tab", "–", ("Demo learner listed", "Có người học demo")),
    ("TC-28", "Admin", ("AI drafts tab with AI off", "Tab AI soạn bài khi AI tắt"), "AI tab", "AI_ENABLED=false", ("Notice that AI is off", "Báo AI đang tắt")),
]
MT_SUMMARY = ("Result: 27 of 27 manual cases passed (17/11/2026). One check in the script was corrected (MT-23, script "
              "TC-24 looked for the words 'quá nhiều lần' but the app says 'sai quá 5 lần'); the app behaviour was "
              "correct and no application code was changed. Script id TC-10 (complete a lesson before all answers are "
              "correct) was not run through the UI; it is covered by pytest (tests/test_audit_nguoi_moi.py).",
              "Kết quả: 27/27 ca thủ công đạt (17/11/2026). Một điều kiện dò trong kịch bản đã được sửa (MT-23, kịch bản TC-24 dò chữ 'quá nhiều lần' nhưng ứng dụng hiện 'sai quá 5 lần'); ứng dụng chạy đúng và không sửa dòng code ứng dụng nào. Ca TC-10 (hoàn thành bài khi chưa đúng hết các câu) không chạy qua giao diện; pytest đã phủ ca này (tests/test_audit_nguoi_moi.py).")

# ------------------------------------------------------------------------------------------------ Final checklist
FC_INTRO = ("Status as of 17/11/2026. 'Not yet' items are the team's remaining work before 04/12/2026.",
            "Trạng thái tại 17/11/2026. Mục 'Not yet' là việc nhóm còn phải làm trước 04/12/2026.")
FINAL = [
    (("Design documents bản 2.1 (SRS, functional spec, overview, detailed design)", "Bộ tài liệu thiết kế bản 2.1 (SRS, đặc tả chức năng, thiết kế tổng quan, thiết kế chi tiết)"), "Done", "docs/SRS/ (.docx + .md)"),
    (("Source code on branch phuc-music", "Mã nguồn nhánh phuc-music"), "Done", "commit 1ab6a15"),
    (("Merge phuc-music into main", "Gộp phuc-music vào main"), "Not yet", ("main has not received the phase-2 work", "main chưa nhận phần giai đoạn 2")),
    (("Docker Compose: 5 services start with one command", "Docker Compose: 5 dịch vụ chạy một lệnh"), "Done",
     ("Verified 17/11/2026; cloud build skipped the OCR package (network), see handover", "Đã kiểm 17/11; bản build cloud bỏ gói OCR (mạng), xem báo cáo bàn giao")),
    (("Database: 31 tables, Alembic upgrade + check", "CSDL: 31 bảng, Alembic upgrade + check"), "Done", "CI PostgreSQL job; schema.json"),
    (("Backend tests (pytest)", "Test backend"), "Done", "1,448 passed + 1 skipped; PostgreSQL 25/25"),
    (("Frontend tests and build", "Test và build giao diện"), "Done", "Vitest 282/282, build OK"),
    (("Manual test cases", "Ca kiểm thử thủ công"), "Done", ("27/27 by Claude (AI); team must re-run and sign", "27/27 do Claude (AI) chạy; nhóm cần chạy lại và ký")),
    (("DFD, ERD, Table Design, Site Map, flowcharts", "DFD, ERD, Table Design, SiteMap, lưu đồ"), "Done", "_nguon/so_do/ (Graphviz sources)"),
    (("Screen design with real screenshots", "Thiết kế màn hình bằng ảnh thật"), "Done", "23 screenshots, _nguon/anh/"),
    (("Demo works with AI_ENABLED = false", "Demo chạy khi AI tắt"), "Done", "MT-12, MT-17, MT-28"),
    (("End-to-end check with a real Gemini key", "Kiểm trọn luồng với khóa Gemini thật"), "Not yet",
     ("Not in this run; 300-question probe stopped at 72/300 (quota 429)", "Chưa trong lần chạy này; probe 300 câu dừng ở 72/300 (429)")),
    (("Recommender validated with real learners", "Kiểm hệ gợi ý với người học thật"), "Not yet",
     ("Only simulated data: chưa chứng minh chất lượng với người học thật", "Chỉ có dữ liệu mô phỏng: chưa chứng minh chất lượng với người học thật")),
    (("Proactive coaching FR-16, AI quiz generation FR-14", "Kèm cặp chủ động FR-16, AI sinh quiz FR-14"), "Not yet", ("Future scope", "Hướng phát triển")),
    (("Group number, member names, roll numbers, supervisor name", "Số nhóm, tên thành viên, mã sinh viên, tên giảng viên hướng dẫn"), "Not yet", ("Yellow fields in this document", "Các ô vàng trong tài liệu")),
    (("Signatures on every form and the certificate", "Chữ ký trên mọi form và trang chứng nhận"), "Not yet", ("Team and faculty", "Nhóm và giảng viên")),
    (("Demo video", "Video demo"), "Not yet", ("Required for submission 04/12/2026", "Bắt buộc khi nộp 04/12/2026")),
    (("Update SRS .docx where it differs from code", "Cập nhật SRS .docx chỗ lệch code"), "Not yet", ("List in BAO_CAO_BAN_GIAO.md §5", "Danh sách ở báo cáo bàn giao mục 5")),
]

# ------------------------------------------------------------------------------------------------ Task sheet
TS_INTRO = ("Tasks are taken from merged pull requests (git log of phuc-music) and docs/TIEN_DO.md. Owners follow the "
            "roles in SRS Table 14; the 'Reviewed by' cells are left for the team where the repository does not record "
            "the approver.",
            "Công việc lấy từ các pull request đã gộp (git log nhánh phuc-music) và docs/TIEN_DO.md. Người phụ trách theo "
            "vai trò SRS Bảng 14; ô 'Người duyệt' để nhóm điền khi repo không ghi người duyệt.")
TASKS = [
    ("Phase A plan, FR trace, ADRs, project rules", "Thắng", "19/10/2026", "19/10/2026", "Completed", "PR #1", None),
    ("Front end skeleton: router, home, login / register, protected routes", "Phúc", "19/10/2026", "19/10/2026", "Completed", "PR #2", None),
    ("Back end auth: register, login, rotating refresh, roles", "Thắng", "19/10/2026", "19/10/2026", "Completed", "PR #3", None),
    ("Docker Compose and DevOps base", "Thắng", "19/10/2026", "19/10/2026", "Completed", "PR #4", None),
    ("Lesson 1 in many keys; beginner audit (CP1)", "Thắng, Đạt", "20/10/2026", "20/10/2026", "Completed", "PR #5, #6", None),
    ("Replace SRS v1.3 by design documents bản 2.1", "Đạt", "26/10/2026", "26/10/2026", "Completed", "PR #7", None),
    ("Fix parallel lesson start (HM-010); GitHub Actions CI", "Thắng", "26/10/2026", "27/10/2026", "Completed", "PR #8, #9", None),
    ("Immutable question versions (HM-003, ADR-006)", "Thắng", "27/10/2026", "27/10/2026", "Completed", "PR #11", "Phúc (on behalf of group)"),
    ("Notation / MIDI octave fix for lesson 1 (HM-001)", "Phúc", "28/10/2026", "31/10/2026", "Completed", "PR #12", None),
    ("Official logo (ADR-007)", "Phúc", "30/10/2026", "01/11/2026", "Completed", "PR #16", None),
    ("Animated home page (GSAP + audio)", "Phúc", "31/10/2026", "05/11/2026", "Completed", "PR #19, #26", None),
    ("AI pipeline: recommender (CP2) and AI Tutor (CP3), evaluation", "Thắng", "04/11/2026", "05/11/2026", "Completed", "PR #20–#25", None),
    ("Teacher feedback G1–G7: RAG inventory, routing, e5 fine-tune, lesson L05", "Thắng, Đạt", "06/11/2026", "08/11/2026", "Completed", "PR #27–#34", "Đạt (#32–#34)"),
    ("Instruments, piano practice, evaluation, lessons L06–L08", "Phúc, Đạt", "08/11/2026", "09/11/2026", "Completed", "PR #36–#43", "Thắng, Đạt"),
    ("Lesson L07 Engine extension; AI Tutor answers music questions outside lessons (ADR-020)", "Thắng", "11/11/2026", "12/11/2026", "Completed", "PR #45–#47", None),
    ("Review fixes, admin pages, skill quiz, AI lesson drafts (ADR-025)", "Thắng, Phúc", "12/11/2026", "14/11/2026", "Completed", "PR #49–#53", "Thắng, Đạt (#49–#52)"),
    ("Front end bug sweep FE-001..023, 'Stage' theme", "Phúc", "16/11/2026", "17/11/2026", "Completed", "PR #61", None),
    ("Teacher feedback T1–T6 (gates G1–G8): Qdrant, evaluation, upload gate", "Thắng", "14/11/2026", "17/11/2026", "Completed", "PR #62", None),
    ("eProject documentation Review 01–03 (this document)", "Đạt", "17/11/2026", "–", "In review", "Draft PR (docs-review123)", None),
]
TS_NOTE = ("Most of the code and these documents were written with an AI coding assistant (Claude) under the team's "
           "direction and review; every use is recorded in docs/AI_USAGE.md. The 'Owner' column shows the responsible "
           "role, not the person who typed the code.",
           "Phần lớn code và tài liệu này được viết với trợ lý lập trình AI (Claude) theo chỉ đạo và duyệt của nhóm; mọi "
           "lần dùng ghi ở docs/AI_USAGE.md. Cột 'Phụ trách' là vai trò chịu trách nhiệm, không phải người gõ code.")


# ------------------------------------------------------------------------------------------------ đánh số MT
# Kịch bản dùng mã TC-01..TC-28 (không có TC-10); tài liệu đánh số liên tục MT-01..MT-27 theo thứ tự TC.
# Bằng chứng ở trên viết theo số TC rồi đổi ở đây, để không lệch khi đọc lại log.
import re as _re

_TC_ORDER = [m[0] for m in MANUAL]


def _mt(match):
    tc = f"TC-{int(match.group(1)):02d}"
    return f"MT-{_TC_ORDER.index(tc) + 1:02d}"


def _remap(s):
    return _re.sub(r"\bMT-(\d\d)\b", _mt, s) if isinstance(s, str) else s


ACCEPTANCE = [a[:-1] + (_remap(a[-1]),) for a in ACCEPTANCE]
FINAL = [(i, s, tuple(_remap(x) for x in n) if isinstance(n, tuple) else _remap(n)) for i, s, n in FINAL]
