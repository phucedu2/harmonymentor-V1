"""Sinh mọi sơ đồ của bộ tài liệu eProject (DFD, ERD kiểu Chen, hình sao thuộc tính, sơ đồ quan hệ,
SiteMap, 4 lưu đồ thuật toán) bằng Graphviz, kiểu đen trắng như file mẫu.

ERD, hình sao và sơ đồ quan hệ đọc từ ../du_lieu/schema.json (sinh bằng dump_schema.py từ SQLAlchemy models),
nên đổi models thì chạy lại hai script là sơ đồ khớp code. DFD, SiteMap và lưu đồ viết tay theo code đã đọc
(đường dẫn file ghi trong từng hàm).

Chạy:  python docs/review123/_nguon/so_do/gen_diagrams.py   (cần lệnh `dot` của Graphviz)
Kết quả: so_do/dot/*.dot (nguồn để sửa) và so_do/png/*.png (300 dpi, chèn vào .docx).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOT_DIR, PNG_DIR = HERE / "dot", HERE / "png"
SCHEMA = json.loads((HERE.parent / "du_lieu" / "schema.json").read_text(encoding="utf-8"))
TABLES = {t["name"]: t for t in SCHEMA}
FONT = "Liberation Serif"

# Nhóm bảng dùng chung cho ERD, hình sao, sơ đồ quan hệ và Table Design.
GROUPS = [
    ("learning", "Learning (Học tập)", [
        "users", "refresh_tokens", "skills", "skill_prerequisites", "lessons", "lesson_blocks", "source_works",
        "lesson_sources", "exercises", "exercise_versions", "attempts", "attempt_errors", "lesson_progress",
        "review_items", "review_states", "review_attempts", "practice_attempts", "mastery_states",
        "mastery_events", "placement_results"]),
    ("ai", "AI Tutor & Recommendation (AI Tutor và gợi ý)", [
        "recommendation_logs", "chat_sessions", "chat_messages", "chat_feedback"]),
    ("lab", "Harmony Lab", ["composition_projects", "chord_events", "drum_events"]),
    ("admin", "Administration (Quản trị)", [
        "content_revisions", "admin_audit_log", "source_documents", "ai_lesson_drafts"]),
]
LEARNING_CONTENT = ["skills", "skill_prerequisites", "lessons", "lesson_blocks", "source_works", "lesson_sources",
                    "exercises", "exercise_versions", "review_items"]
LEARNING_ACTIVITY = ["users", "refresh_tokens", "exercise_versions", "attempts", "attempt_errors", "lessons", "lesson_progress",
                     "review_items", "review_states", "review_attempts", "practice_attempts", "skills", "mastery_states",
                     "mastery_events", "placement_results"]
assert sorted(sum((g[2] for g in GROUPS), [])) == sorted(TABLES), "nhóm bảng phải phủ đúng 31 bảng trong models"


def render(name: str, src: str, engine: str = "dot") -> None:
    DOT_DIR.mkdir(exist_ok=True)
    PNG_DIR.mkdir(exist_ok=True)
    (DOT_DIR / f"{name}.dot").write_text(src, encoding="utf-8")
    subprocess.run([engine, "-Gdpi=300", "-Tpng", str(DOT_DIR / f"{name}.dot"), "-o", str(PNG_DIR / f"{name}.png")],
                   check=True)


def head(kind: str = "digraph", extra: str = "") -> str:
    return (f'{kind} G {{\n  graph [fontname="{FONT}", bgcolor=white, pad=0.2 {extra}];\n'
            f'  node [fontname="{FONT}", fontsize=11, color=black];\n'
            f'  edge [fontname="{FONT}", fontsize=9, color=black];\n')


def q(s: str) -> str:
    return '"' + s.replace('"', '\\"') + '"'


# ---------------------------------------------------------------------------------------------- DFD
def dfd_context() -> None:
    s = head(extra=", layout=dot, rankdir=LR, nodesep=0.35, ranksep=1.6")
    s += '  P0 [shape=circle, width=2.1, fixedsize=true, label="0\\nHarmonyMentor AI\\nSystem"];\n'
    for n, lab in [("G", "Guest"), ("L", "Learner"), ("A", "Admin"), ("GM", "Google Gemini API\\n(external AI service)")]:
        s += f'  {n} [shape=box, width=1.6, label="{lab}"];\n'
    flows = [
        ("G", "P0", "Register / login data"), ("P0", "G", "Home page, curriculum,\\nJWT + refresh cookie"),
        ("L", "P0", "Answers, piano input, flashcard answers,\\ngoal text, chat questions, chord grids"),
        ("P0", "L", "Grading result + error code, explanation,\\nmastery, review queue, recommendations,\\ncited AI answers, backing track"),
        ("A", "P0", "Lesson text edits, publish / hide,\\nuser lock, uploaded documents"),
        ("P0", "A", "Statistics, audit log,\\nAI lesson drafts with Engine flags"),
        ("P0", "GM", "Question, last 6 messages, lesson chunks,\\nweak skills, error code (no e-mail / name / id)"),
        ("GM", "P0", "JSON answer + citations\\n(checked by Music Engine)"),
    ]
    s += "  {rank=same; G; L; A;}\n"
    for a, b, lab in flows:
        s += f'  {a} -> {b} [label={q(lab)}];\n'
    render("dfd_level0", s + "}\n")


def dfd(name: str, procs: list[tuple[str, str]], ents: list[tuple[str, str]], stores: list[tuple[str, str]],
        flows: list[tuple[str, str, str]], rankdir: str = "TB") -> None:
    s = head(extra=f", rankdir={rankdir}, nodesep=0.3, ranksep=0.9")
    for n, lab in procs:
        s += f'  {n} [shape=circle, width=1.25, fixedsize=true, fontsize=10, label={q(lab)}];\n'
    for n, lab in ents:
        s += f'  {n} [shape=box, label={q(lab)}];\n'
    for n, lab in stores:
        # Kho dữ liệu kiểu mẫu: ô mã Dx | tên bảng.
        s += f'  {n} [shape=record, fontsize=10, label="{{{n}|{lab}}}"];\n'
    for a, b, lab in flows:
        s += f'  {a} -> {b} [label={q(lab)}];\n'
    render(name, s + "}\n")


def dfd_level1() -> None:
    # (1) auth/router.py, auth/service.py, auth/login_limiter.py, admin/ (users)
    dfd("dfd_l1_auth",
        [("P1", "1.0\nRegister"), ("P2", "2.0\nLogin +\ntemporary lock"), ("P3", "3.0\nRefresh /\nlogout"),
         ("P4", "4.0\nProfile &\nrole check"), ("P5", "5.0\nManage users\n(admin)")],
        [("U", "Guest / Learner"), ("A", "Admin")],
        [("D1", "users"), ("D2", "refresh_tokens"), ("R1", "Redis login_fail:ip|email"), ("D20", "admin_audit_log")],
        [("U", "P1", "name, e-mail, password"), ("P1", "D1", "new user (bcrypt hash)"), ("P1", "U", "access JWT"),
         ("U", "P2", "e-mail, password"), ("P2", "R1", "count failures"), ("R1", "P2", "locked seconds"),
         ("D1", "P2", "hashed_password, role"), ("P2", "D2", "refresh token hash"), ("P2", "U", "JWT / 401 / 429"),
         ("U", "P3", "refresh cookie"), ("D2", "P3", "valid token"), ("P3", "U", "new JWT"),
         ("U", "P4", "Bearer JWT"), ("D1", "P4", "user row"), ("P4", "U", "profile / 403"),
         ("A", "P5", "lock / unlock"), ("P5", "D1", "is_active"), ("P5", "D20", "action log")])
    # (2) services/learning_service.py, grading_service.py, mastery_service.py, review_scheduler.py, practice, placement
    dfd("dfd_l1_learning",
        [("P6", "6.0\nView lessons"), ("P7", "7.0\nSubmit answer\n(Music Engine)"), ("P8", "8.0\nUpdate EMA\nmastery"),
         ("P9", "9.0\nComplete lesson\n+ Leitner"), ("P10", "10.0\nReview\nflashcards"), ("P11", "11.0\nPractice /\nplacement / quiz")],
        [("L", "Learner")],
        [("D3", "lessons, lesson_blocks"), ("D4", "exercises, exercise_versions"), ("D5", "attempts, attempt_errors"),
         ("D6", "mastery_states, mastery_events"), ("D7", "lesson_progress"), ("D8", "review_items, review_states"),
         ("D9", "review_attempts"), ("D10", "practice_attempts, placement_results")],
        [("L", "P6", "open lesson"), ("D3", "P6", "blocks"), ("D4", "P6", "published version"), ("P6", "L", "theory, piano, staff, questions"),
         ("L", "P7", "answer + input method"), ("D4", "P7", "answer_key, grader_config"), ("P7", "D5", "attempt + error codes"),
         ("P7", "L", "correct?, error code, feedback"), ("P7", "P8", "result 1 / 0.5 / 0"), ("P8", "D6", "new score"),
         ("L", "P9", "complete"), ("D5", "P9", "all questions correct?"), ("P9", "D7", "completed"), ("P9", "D8", "cards due now (box 1)"),
         ("L", "P10", "card answer"), ("D8", "P10", "due card"), ("P10", "D8", "box 1..5, due_at"), ("P10", "D9", "review attempt"),
         ("P10", "P8", "due review result"), ("L", "P11", "answer"), ("P11", "D10", "history / placement"), ("P11", "D6", "placement 0.65")])
    # (3) services/recommendation_service.py, ai/recommender/*, services/ai_pipeline.py, ai_tutor_service.py
    dfd("dfd_l1_ai",
        [("P12", "12.0\nSave goal\n+ embed"), ("P13", "13.0\nHybrid\nrecommend"), ("P14", "14.0\nAI Tutor\nchat"),
         ("P15", "15.0\nExplain wrong\nanswer (3 levels)"), ("P16", "16.0\nRate answer")],
        [("L", "Learner"), ("GM", "Google Gemini")],
        [("D1", "users"), ("D6", "mastery_states"), ("D8", "review_states"), ("D11", "skills, skill_prerequisites"),
         ("D12", "recommendation_logs"), ("D13", "chat_sessions, chat_messages"), ("D14", "chat_feedback"),
         ("V1", "Qdrant harmony_knowledge (lesson chunks)")],
        [("L", "P12", "goal text"), ("P12", "D1", "goal_text, goal_embedding"), ("L", "P13", "GET /recommend"),
         ("D6", "P13", "mastery of all learners (KNN)"), ("D8", "P13", "due skills"), ("D11", "P13", "prerequisites, thresholds"),
         ("D1", "P13", "goal vector"), ("P13", "D12", "list + scores + reasons"), ("P13", "L", "continue / next / review lists"),
         ("L", "P14", "question"), ("D13", "P14", "last 6 messages"), ("V1", "P14", "top chunks"), ("P14", "GM", "prompt (no PII)"),
         ("GM", "P14", "JSON answer"), ("P14", "D13", "messages, citations, engine claims"), ("P14", "L", "answer + citations"),
         ("L", "P15", "attempt id"), ("P15", "GM", "error code, prompt"), ("P15", "L", "hint level 1–3"),
         ("L", "P16", "1–5 stars"), ("P16", "D14", "rating")])
    # (4) composition/, api/composition (projects), admin/ (lessons, stats, ai drafts)
    dfd("dfd_l1_lab_admin",
        [("P17", "17.0\nSuggest &\narrange chords"), ("P18", "18.0\nSave / open\nproject"), ("P19", "19.0\nEdit & publish\nlesson text"),
         ("P20", "20.0\nStatistics"), ("P21", "21.0\nAI lesson\ndraft")],
        [("L", "Learner"), ("A", "Admin"), ("GM", "Google Gemini")],
        [("D15", "composition_projects"), ("D16", "chord_events, drum_events"), ("D3", "lessons, lesson_blocks"),
         ("D17", "content_revisions"), ("D20", "admin_audit_log"), ("D18", "source_documents"), ("D19", "ai_lesson_drafts"),
         ("D5", "attempts (is_test = false)")],
        [("L", "P17", "key, chord grid, style, energy"), ("P17", "L", "suggestions, voicings, backing track"),
         ("L", "P18", "project"), ("P18", "D15", "header, form, mix"), ("P18", "D16", "events in beats"), ("D15", "P18", "own projects only"),
         ("A", "P19", "block text"), ("P19", "D17", "draft / published revision"), ("D3", "P19", "original block"),
         ("P19", "D20", "action"), ("D5", "P20", "attempts, reviews"), ("P20", "A", "charts, funnel"),
         ("A", "P21", "PDF / DOCX / text + source"), ("P21", "D18", "pages, relevance"), ("P21", "GM", "selected pages"),
         ("GM", "P21", "draft JSON"), ("P21", "D19", "draft + Engine report"), ("P21", "D3", "publish (admin click)")])


# ---------------------------------------------------------------------------------------------- ERD (Chen)
def fk_edges(tables: list[str]) -> list[tuple[str, str, str, bool]]:
    """(bảng con, bảng cha, cột FK, cột duy nhất?) chỉ lấy FK thật trong models."""
    out = []
    for t in tables:
        for c in TABLES[t]["columns"]:
            for target, _ in c["fk"]:
                parent = target.split(".")[0]
                if parent in tables:
                    out.append((t, parent, c["name"], c["unique"] or (c["pk"] and len([x for x in TABLES[t]["columns"] if x["pk"]]) == 1)))
    return out


REL_NAMES = {
    ("refresh_tokens", "users"): "owns", ("skill_prerequisites", "skills"): "requires", ("lesson_blocks", "lessons"): "contains",
    ("lesson_sources", "lessons"): "cites", ("lesson_sources", "source_works"): "used in", ("exercises", "lessons"): "has",
    ("exercises", "skills"): "trains", ("exercise_versions", "exercises"): "versioned as", ("attempts", "users"): "makes",
    ("attempts", "exercise_versions"): "answers", ("attempt_errors", "attempts"): "diagnoses", ("lesson_progress", "users"): "tracks",
    ("lesson_progress", "lessons"): "progress of", ("review_items", "lessons"): "has cards", ("review_items", "skills"): "reviews",
    ("review_states", "users"): "schedules", ("review_states", "review_items"): "state of", ("review_attempts", "review_states"): "logs",
    ("practice_attempts", "users"): "practises", ("mastery_states", "users"): "masters", ("mastery_states", "skills"): "measured",
    ("mastery_events", "users"): "history", ("mastery_events", "skills"): "event of", ("placement_results", "users"): "takes",
    ("recommendation_logs", "users"): "receives", ("chat_sessions", "users"): "opens", ("chat_messages", "chat_sessions"): "holds",
    ("chat_feedback", "chat_messages"): "rates", ("chat_feedback", "users"): "gives", ("composition_projects", "users"): "creates",
    ("chord_events", "composition_projects"): "chords", ("drum_events", "composition_projects"): "drums",
    ("content_revisions", "lessons"): "revises", ("admin_audit_log", "users"): "acts", ("source_documents", "users"): "uploads",
    ("ai_lesson_drafts", "source_documents"): "summarises", ("ai_lesson_drafts", "users"): "drafts",
}


def chen(name: str, tables: list[str], skip_users_fk: set[str] | None = None, size: str = "7.2,9.5") -> None:
    s = head("graph", extra=f', layout=neato, overlap=false, sep="+14", splines=true, size="{size}"')
    for t in tables:
        s += f'  {q(t)} [shape=box, style=bold, fontsize=12];\n'
    seen: dict[tuple[str, str], int] = {}
    for child, parent, col, one in fk_edges(tables):
        if skip_users_fk and child in skip_users_fk and parent == "users":
            continue
        k = (child, parent)
        seen[k] = seen.get(k, 0) + 1
        rid = f"R_{child}_{parent}_{col}"
        lab = REL_NAMES.get(k, "has")
        if seen[k] > 1:
            lab = col.replace("_", " ")
        s += f'  {q(rid)} [shape=diamond, fontsize=9, width=0.9, height=0.5, label={q(lab)}];\n'
        s += f'  {q(parent)} -- {q(rid)} [label="1"];\n'
        s += f'  {q(rid)} -- {q(child)} [label="{"1" if one else "n"}"];\n'
    render(name, s + "}\n", engine="neato")


def erd() -> None:
    core = ["users", "lessons", "skills", "exercises", "exercise_versions", "attempts", "review_items", "review_states",
            "mastery_states", "lesson_progress", "chat_sessions", "chat_messages", "recommendation_logs", "composition_projects"]
    chen("erd_tong_quan", core, size="7.2,8.5")
    # Nhóm Learning có 20 bảng, vẽ một hình thì chữ quá nhỏ trên A4 nên tách 2 hình: nội dung và hoạt động.
    chen("erd_learning_content", LEARNING_CONTENT, size="7.2,9.2")
    chen("erd_learning_activity", LEARNING_ACTIVITY, size="7.2,9.2")
    for key, _, tabs in GROUPS[1:]:
        extra = ["users"] if "users" not in tabs else []
        if key == "admin":
            extra += ["lessons"]
        chen(f"erd_{key}", extra + tabs, size="7.2,9.2")


def attr_star(t: str) -> None:
    # Không giới hạn size: Word co ảnh theo khung, nên chữ to đều nhau giữa bảng ít và nhiều cột.
    cols = TABLES[t]["columns"]
    ln = 1.6 if len(cols) <= 8 else 2.1 if len(cols) <= 13 else 2.6
    s = head("graph", extra=', layout=neato, overlap=false, sep="+4"')
    s += f'  E [shape=box, style=bold, fontsize=16, label={q(t)}];\n'
    for i, c in enumerate(cols):
        lab = f"<<U>{c['name']}</U>>" if c["pk"] else q(c["name"])
        s += f'  a{i} [shape=ellipse, fontsize=14, margin="0.05,0.02", label={lab}];\n  E -- a{i} [len={ln}];\n'
    render(f"attr_{t}", s + "}\n", engine="neato")


# ---------------------------------------------------------------------------------------------- Relationship diagram
def rel_diagram(key: str, tables: list[str]) -> None:
    s = head(extra=', rankdir=LR, nodesep=0.25, ranksep=0.9, splines=true')
    for t in tables:
        rows = "".join(
            f'<TR><TD ALIGN="LEFT" PORT="{c["name"]}">{"<B>" if c["pk"] else ""}{c["name"]}{"</B>" if c["pk"] else ""}</TD>'
            f'<TD ALIGN="LEFT"><FONT POINT-SIZE="8">{(("PK " if c["pk"] else "") + ("FK" if c["fk"] else "")).strip() or " "}</FONT></TD></TR>'
            for c in TABLES[t]["columns"])
        s += (f'  {q(t)} [shape=plaintext, fontsize=9, label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2">'
              f'<TR><TD COLSPAN="2" BGCOLOR="black"><FONT COLOR="white"><B>{t}</B></FONT></TD></TR>{rows}</TABLE>>];\n')
    for t in tables:
        for c in TABLES[t]["columns"]:
            for target, _ in c["fk"]:
                p, pc = target.split(".")
                if p in tables:
                    s += f'  {q(p)}:{pc} -> {q(t)}:{c["name"]} [arrowhead=crow, arrowtail=tee, dir=both];\n'
    render(f"rel_{key}", s + "}\n")


# ---------------------------------------------------------------------------------------------- SiteMap
def sitemap() -> None:
    s = head(extra=', rankdir=LR, nodesep=0.12, ranksep=0.55')
    s += '  node [shape=box, style=rounded, fontsize=10];\n'
    nodes = {
        "root": "/  Home (public)", "login": "/dang-nhap  Login", "reg": "/dang-ky  Register", "nf": "*  404 Not found",
        "prog": "/#chuong-trinh  Curriculum", "feat": "/#tinh-nang  Features",
        "app": "/app  Dashboard\\n[login required]", "hoc": "/app/hoc  Lessons", "bai": "/app/hoc?bai=L01  Lesson runner",
        "lt": "/app/luyen-tap  Practice", "td": "/app/tien-do  Progress & flashcards", "quiz": "/app/quiz  Skill quiz",
        "comp": "/app/composition  Harmony Lab", "hs": "/app/ho-so  Profile", "kt": "/app/kiem-tra-dau-vao  Placement test",
        "ai": "AI Tutor drawer\\n(on every /app page)", "adm": "/admin  Administration\\n[role = admin, else 403]",
        "t1": "Tab: Statistics", "t2": "Tab: Lessons (edit, preview,\\npublish, history, hide)", "t3": "Tab: AI lesson drafts",
        "t4": "Tab: Users (lock / unlock)",
    }
    for k, v in nodes.items():
        extra = ", style=\"rounded,bold\"" if k in ("root", "app", "adm") else ""
        extra += ", style=\"rounded,dashed\"" if k == "ai" else ""
        s += f'  {k} [label="{v}"{extra}];\n'
    for a, b in [("root", "login"), ("root", "reg"), ("root", "prog"), ("root", "feat"), ("root", "nf"), ("login", "app"),
                 ("reg", "kt"), ("root", "app"), ("app", "hoc"), ("hoc", "bai"), ("app", "lt"), ("app", "td"), ("app", "quiz"),
                 ("app", "comp"), ("app", "hs"), ("app", "kt"), ("app", "ai"), ("login", "adm"), ("adm", "t1"), ("adm", "t2"),
                 ("adm", "t3"), ("adm", "t4")]:
        s += f"  {a} -> {b};\n"
    render("sitemap", s + "}\n")


# ---------------------------------------------------------------------------------------------- Flowcharts
def flow(name: str, nodes: list[tuple[str, str, str]], edges: list[tuple[str, str, str]]) -> None:
    shapes = {"start": "ellipse", "io": "parallelogram", "dec": "diamond", "proc": "box"}
    s = head(extra=", nodesep=0.35, ranksep=0.35")
    s += '  node [fontsize=10];\n'
    for n, kind, lab in nodes:
        s += f'  {n} [shape={shapes[kind]}, label={q(lab)}{", margin=0.02" if kind == "dec" else ""}];\n'
    for a, b, lab in edges:
        s += f'  {a} -> {b}{" [label=" + q(lab) + "]" if lab else ""};\n'
    render(name, s + "}\n")


def algorithms() -> None:
    # auth/service.py authenticate(), auth/login_limiter.py (5 lần sai / 15 phút theo cặp IP + email)
    flow("alg_1_dang_nhap", [
        ("s", "start", "Start"), ("i", "io", "Input e-mail, password\n(client IP from proxy)"),
        ("k", "proc", "key = ip | normalised e-mail"), ("d1", "dec", "failures(key) >= 5\nin 15 minutes?"),
        ("o1", "io", "Return 429 LOGIN_LOCKED\n+ Retry-After"), ("f", "proc", "Find user by e-mail;\nbcrypt verify (dummy hash if none)"),
        ("d2", "dec", "Password OK and user\nactive, not synthetic?"), ("r", "proc", "Redis INCR login_fail:key\n(TTL 15 min on first failure)"),
        ("o2", "io", "Return 401\nINVALID_CREDENTIALS"), ("z", "proc", "Reset counter;\ncreate refresh token (SHA-256 stored)"),
        ("o3", "io", "Return access JWT (30 min)\n+ HttpOnly refresh cookie (7 days)"), ("e", "start", "End")],
        [("s", "i", ""), ("i", "k", ""), ("k", "d1", ""), ("d1", "o1", "Yes"), ("d1", "f", "No"), ("f", "d2", ""),
         ("d2", "r", "No"), ("r", "o2", ""), ("d2", "z", "Yes"), ("z", "o3", ""), ("o1", "e", ""), ("o2", "e", ""), ("o3", "e", "")])
    # services/learning_service.py submit_attempt/complete_lesson, ai/mastery.py, services/review_scheduler.py
    flow("alg_2_nop_bai", [
        ("s", "start", "Start"), ("i", "io", "Input exercise_version_id,\nanswer, input method"),
        ("d0", "dec", "Version is the current\npublished one?"), ("o0", "io", "Return 409\nEXERCISE_VERSION_SUPERSEDED"),
        ("d1", "dec", "Input method allowed\nfor this question?"), ("o1", "io", "Return 422 (no attempt saved)"),
        ("g", "proc", "Music Engine grades with the version's\nanswer_key + grader_config"),
        ("a", "proc", "Save attempt + attempt_errors\n(is_test = true if admin)"),
        ("d2", "dec", "Admin test attempt?"), ("d3", "dec", "Correct?"), ("d4", "dec", "First attempt\nof this question?"),
        ("d5", "dec", "Previous attempt\nwas wrong?"), ("r1", "proc", "result = 1"), ("r05", "proc", "result = 0.5"),
        ("r0", "proc", "result = 0"), ("rn", "proc", "repeat correct:\ncount only, score unchanged"),
        ("m", "proc", "mastery = old + 0.3 × (result − old)\nlevel: weak < 0.60 (≥5 tries), ready ≥ 0.60, mastered ≥ 0.80"),
        ("o2", "io", "Return correct?, error code, feedback;\nexplanation if correct or wrong ≥ 2 times"),
        ("d6", "dec", "Learner presses\nComplete lesson?"), ("d7", "dec", "Every question correct\nat least once?"),
        ("o3", "io", "Return 409\nLESSON_NOT_MASTERED"),
        ("l", "proc", "Mark completed; create review_states\nbox 1, due_at = now"),
        ("rv", "proc", "Review card: correct when due → box+1\n(1-2-4-8-16 days); wrong → box 1, +1 day;\ncorrect before due → keep box"),
        ("e", "start", "End")],
        [("s", "i", ""), ("i", "d0", ""), ("d0", "o0", "No"), ("d0", "d1", "Yes"), ("d1", "o1", "No"), ("d1", "g", "Yes"),
         ("g", "a", ""), ("a", "d2", ""), ("d2", "o2", "Yes"), ("d2", "d3", "No"), ("d3", "r0", "No"), ("d3", "d4", "Yes"),
         ("d4", "r1", "Yes"), ("d4", "d5", "No"), ("d5", "r05", "Yes"), ("d5", "rn", "No"), ("r1", "m", ""), ("r05", "m", ""),
         ("r0", "m", ""), ("rn", "o2", ""), ("m", "o2", ""), ("o2", "d6", ""), ("d6", "e", "No"), ("d6", "d7", "Yes"),
         ("d7", "o3", "No"), ("d7", "l", "Yes"), ("l", "rv", ""), ("rv", "e", ""), ("o0", "e", ""), ("o1", "e", ""), ("o3", "e", "")])
    # services/recommendation_service.py recommend_for_user, ai/recommender/engine.py, scoring.py, knn.py
    flow("alg_3_goi_y", [
        ("s", "start", "Start"), ("i", "io", "Input: learner (token), goal text,\nmastery, due cards"),
        ("v", "proc", "Build 14-dimension vector\n(mean mastery per group_code)"),
        ("d1", "dec", "≥ 1 neighbour sharing\n≥ 3 assessed dimensions?"),
        ("w1", "proc", "Weights 0.35 content, 0.25 mastery,\n0.20 due, 0.20 collaborative (KNN k = 10)"),
        ("w2", "proc", "Cold start: content 0.55,\nmastery 0.25, due 0.20, CF 0"),
        ("loop", "proc", "For each lesson"), ("d2", "dec", "Has a skill below 0.80 and every\nprerequisite ≥ 0.60? (layer 1)"),
        ("x", "proc", "Exclude lesson\n(reason stored)"),
        ("sc", "proc", "Skill score = w·content (cosine goal vs skill, layer 2)\n+ w·(1 − mastery) + w·due + w·CF (layer 3)\nLesson score = mean over open skills"),
        ("d3", "dec", "More lessons?"), ("t", "proc", "Sort by score, then curriculum order;\ntake top 5; write reason sentence"),
        ("sp", "proc", "Split: Continue (started) / Next (new) /\nReview (completed, label \"Ôn lại\")"),
        ("lg", "proc", "Save recommendation_logs"), ("o", "io", "Output: 3 lists with reasons"), ("e", "start", "End")],
        [("s", "i", ""), ("i", "v", ""), ("v", "d1", ""), ("d1", "w1", "Yes"), ("d1", "w2", "No"), ("w1", "loop", ""), ("w2", "loop", ""),
         ("loop", "d2", ""), ("d2", "x", "No"), ("d2", "sc", "Yes"), ("x", "d3", ""), ("sc", "d3", ""), ("d3", "loop", "Yes"),
         ("d3", "t", "No"), ("t", "sp", ""), ("sp", "lg", ""), ("lg", "o", ""), ("o", "e", "")])
    # services/ai_pipeline.py (Node), docs/AI_PIPELINE.md, ai/tutor/router.py, guardrail.py
    flow("alg_4_ai_tutor", [
        ("s", "start", "Start"), ("i", "io", "Input question, session_id"),
        ("d0", "dec", "> 20 questions\nin 60 s?"), ("o0", "io", "Return 429 AI_RATE_LIMITED"),
        ("d1", "dec", "Prompt injection\ndetected?"), ("o1", "io", "Fixed refusal"),
        ("r", "proc", "Intent + rewrite follow-up;\nretrieve top chunks (Qdrant e5,\nfallback e5 in memory + BM25)"),
        ("d2", "dec", "Route?"), ("g", "proc", "Greeting / help\n(fixed text)"), ("ot", "proc", "Off-topic: ≤ 2 sentences,\nthen lead back"),
        ("gen", "proc", "Outside lessons: Gemini general\nanswer, Engine scans notes"),
        ("d3", "dec", "AI enabled and\ndaily quota (30) left?"), ("fb", "proc", "Answer from lesson text +\nMusic Engine (no AI)"),
        ("p", "proc", "Build prompt: question, 6 last messages,\nchunks, weak skills (no PII)"), ("llm", "proc", "Call Gemini → JSON"),
        ("c", "proc", "Keep only citations whose block id\nwas in the retrieved context"),
        ("d4", "dec", "Music Engine confirms every\nnote / chord / interval?"), ("d5", "dec", "Already\nretried once?"),
        ("rule", "proc", "Rule-based fallback answer"), ("sv", "proc", "Save chat_messages (citations,\nengine claims, latency, tokens)"),
        ("o", "io", "Output answer + citations + verified flag"), ("e", "start", "End")],
        [("s", "i", ""), ("i", "d0", ""), ("d0", "o0", "Yes"), ("d0", "d1", "No"), ("d1", "o1", "Yes"), ("d1", "r", "No"),
         ("r", "d2", ""), ("d2", "g", "G / D"), ("d2", "ot", "C"), ("d2", "gen", "B"), ("d2", "d3", "A (in lessons)"),
         ("d3", "fb", "No"), ("d3", "p", "Yes"), ("p", "llm", ""), ("llm", "c", ""), ("c", "d4", ""), ("d4", "sv", "Yes"),
         ("d4", "d5", "No"), ("d5", "p", "No (retry)"), ("d5", "rule", "Yes"), ("rule", "sv", ""), ("fb", "sv", ""), ("g", "sv", ""),
         ("ot", "sv", ""), ("gen", "sv", ""), ("o1", "sv", ""), ("sv", "o", ""), ("o", "e", ""), ("o0", "e", "")])


def main() -> None:
    dfd_context()
    dfd_level1()
    erd()
    for t in TABLES:
        attr_star(t)
    rel_diagram("learning_content", LEARNING_CONTENT)
    rel_diagram("learning_activity", LEARNING_ACTIVITY)
    for key, _, tabs in GROUPS[1:]:
        rel_diagram(key, tabs)
    sitemap()
    algorithms()
    print(f"Đã dựng {len(list(PNG_DIR.glob('*.png')))} hình vào {PNG_DIR}")


if __name__ == "__main__":
    main()
