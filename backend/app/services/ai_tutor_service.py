"""AI Tutor: hỏi đáp có trích dẫn và giải thích lượt làm sai (04 mục 5.4, 5.5; đề GĐ3).

Luồng một câu hỏi:
  lưu tin người dùng → chặn tấn công prompt → phân loại ý định (ngoài phạm vi thì từ chối, không gọi LLM)
  → truy xuất đoạn bài học (dưới ngưỡng thì "mình chưa chắc", không gọi LLM) → tra trước Music Engine
  → AI tắt / hết ngân sách chung: trả lời viết sẵn từ đoạn bài học + dữ kiện Engine
  → hạn mức người dùng (429) → gọi Gemini → kiểm định dạng, trích dẫn, Music Engine, chuỗi canh gác
  → sai thì soạn lại đúng 1 lần kèm dữ kiện Engine → vẫn sai thì dùng câu viết sẵn.

Gửi cho Gemini chỉ những gì SRS 03 Bảng 3 cho phép: câu hỏi, tối đa 6 tin gần nhất, đoạn bài học truy xuất
được, mục tiêu học, tên kỹ năng yếu, mã lỗi và đề bài của lượt cần giải thích. Không email, tên, user_id, token.
"""

from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai.embedder import Embedder
from ..ai.mastery import vn_day
from ..ai.tutor import faq
from ..ai.tutor import fallback as fb
from ..ai.tutor import prompt as pr
from ..ai.tutor.guardrail import GuardResult, check_answer, engine_facts_for, run_tool, scan_reply
from ..ai.tutor.injection import looks_like_injection
from ..ai.tutor.intent import classify
from ..ai.tutor.llm import LLMProvider, LLMResult, LLMUnavailable
from ..ai.tutor.notes import solfege_to_letters, split_notes
from ..ai.tutor.engine_query import fact_text
from ..ai.tutor.general import fold
from ..ai.tutor.retriever import Hit, Retrieval, help_page, retrieve, retrieve_for_skill
from ..ai.tutor.router import decide
from ..ai.tutor.schema import LLM_SCHEMA, TutorAnswer, parse_answer
from ..ai.tutor.chunker import lesson_titles
from ..content.skill_graph import SKILLS
from ..core.config import settings
from ..db.models import (Attempt, AttemptError, ChatFeedback, ChatMessage, ChatSession, Exercise, ExerciseVersion,
                         MasteryState, User, utcnow)

HISTORY_LIMIT = 6
SKILL_NAMES = {s: name for s, name, _ in SKILLS}
VERIFIED_LABEL = "Đã kiểm bằng Music Engine"


class ChatNotFound(LookupError):
    pass


class AttemptNotFound(LookupError):
    pass


class AttemptNotWrong(ValueError):
    pass


class QuotaExceeded(RuntimeError):
    def __init__(self, used: int, quota: int):
        super().__init__("AI_QUOTA_EXCEEDED")
        self.used, self.quota = used, quota


@dataclass
class Draft:
    """Câu trả lời trước khi lưu. claims là danh sách đã kiểm (dict), không phải điều AI tự khai."""

    reply: str
    intent: str
    citations: list[dict[str, str]]
    claims: list[dict[str, Any]]
    status: str                    # ok | fallback | failed
    route: str                     # llm | refused_injection | out_of_scope | unsure | ai_off | ...
    hint_level: int = 0
    suggested_actions: list[str] | None = None
    llm: LLMResult | None = None
    llm_calls: int = 0
    fallback_reason: str | None = None
    flow: str = "A"                       # ADR-017: A trong bài | B ngoài bài (Engine) | C ngoài phạm vi | D hướng dẫn | G chào
    source_label: str | None = None       # nhãn nhỏ dưới câu trả lời: "Từ bài học", "Ngoài bài học, theo Music Engine"...
    suggested_lesson: str | None = None   # bài để mở khi "không biết"
    help_page: dict[str, str] | None = None


# --- Phiên và lịch sử --------------------------------------------------------------------------

def _now(now: datetime | None) -> datetime:
    return now or utcnow()


def get_session(db: Session, user_id: str, session_id: str) -> ChatSession:
    s = db.get(ChatSession, session_id)
    if s is None or s.user_id != user_id:
        raise ChatNotFound(session_id)  # của người khác cũng là 404 (nguyên tắc 4)
    return s


def create_session(db: Session, user_id: str, mode: str = "companion", now: datetime | None = None) -> ChatSession:
    t = _now(now)
    s = ChatSession(id=str(uuid.uuid4()), user_id=user_id, mode=mode, created_at=t, updated_at=t)
    db.add(s)
    db.flush()
    return s


def list_sessions(db: Session, user_id: str) -> list[ChatSession]:
    return list(db.scalars(select(ChatSession).where(ChatSession.user_id == user_id)
                           .order_by(ChatSession.updated_at.desc()).limit(50)))


def history(db: Session, user_id: str, session_id: str) -> list[ChatMessage]:
    get_session(db, user_id, session_id)
    return list(db.scalars(select(ChatMessage).where(ChatMessage.session_id == session_id)
                           .order_by(ChatMessage.id)))


def recent_turns(db: Session, session_id: str, before_id: int | None = None,
                 limit: int = HISTORY_LIMIT) -> list[tuple[str, str]]:
    q = select(ChatMessage).where(ChatMessage.session_id == session_id, ChatMessage.role.in_(("user", "assistant")))
    if before_id is not None:
        q = q.where(ChatMessage.id < before_id)
    rows = list(db.scalars(q.order_by(ChatMessage.id.desc()).limit(limit)))
    return [(m.role, m.content) for m in reversed(rows)]


# --- Hạn mức ------------------------------------------------------------------------------------

def _llm_rows_today(db: Session, now: datetime, user_id: str | None) -> int:
    """Số lượt đã gọi LLM trong ngày VN. Đếm trong Python vì tool_calls là JSON (SQLite và PostgreSQL khác cú pháp)."""
    day = vn_day(now)

    q = select(ChatMessage.tool_calls, ChatMessage.created_at).where(
        ChatMessage.role == "assistant", ChatMessage.created_at >= now - timedelta(days=1, hours=1))
    if user_id is not None:
        q = q.join(ChatSession, ChatSession.id == ChatMessage.session_id).where(ChatSession.user_id == user_id)
    n = 0
    for tool_calls, created in db.execute(q):
        if (tool_calls or {}).get("llm_calls") and vn_day(created) == day:
            n += 1
    return n


def quota_remaining(db: Session, user_id: str, now: datetime | None = None) -> int:
    return max(0, settings.ai_daily_quota - _llm_rows_today(db, _now(now), user_id))


# --- Dựng câu trả lời ---------------------------------------------------------------------------

def _citation(h: Hit, titles: dict[str, str]) -> dict[str, str]:
    return {"lesson_id": h.chunk.lesson_id, "block_id": h.chunk.block_id, "title": h.chunk.title,
            "lesson_title": titles.get(h.chunk.lesson_id, h.chunk.lesson_id)}


def _fact_claims(facts: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"tool": f["tool"], "args": f["args"], "claimed": f["result"], "engine": f["result"],
             "status": "verified", "origin": "engine_fact"} for f in facts]


def _fact_lines(facts: Sequence[dict[str, Any]]) -> str:
    return " ".join(f"{f['args']['symbol']} = {f['result']}." for f in facts if f["tool"] == "get_chord_tones")


def offline_answer(question_hits: Sequence[Hit], facts: Sequence[dict[str, Any]], titles: dict[str, str],
                   reason: str, lead: str | None = None) -> Draft:
    """Câu viết sẵn: dữ kiện Music Engine + trích đoạn bài học gần nhất. Không suy diễn gì thêm."""
    # "Tạm nghỉ" chỉ khi AI tắt; còn lại (quá tải, hết giờ, câu bị chặn) thì nói thật là chưa trả lời được.
    parts = [lead or (fb.UNAVAILABLE if reason == "ai_disabled" else fb.BUSY)]
    if facts:
        parts.append(f"Theo Music Engine: {_fact_lines(facts)}")
    cites = []
    if question_hits:
        h = question_hits[0]
        excerpt = h.chunk.text if len(h.chunk.text) <= 420 else h.chunk.text[:420].rsplit(" ", 1)[0] + "…"
        parts.append(f"Trong bài “{titles.get(h.chunk.lesson_id, h.chunk.lesson_id)}”, phần “{h.chunk.title}”: {excerpt}")
        cites = [_citation(h, titles)]
    text = " ".join(parts)
    # Trích đoạn bài học cũng được quét: nhãn "đã kiểm" chỉ hiện khi mọi khẳng định trong câu đều khớp Engine.
    fact_keys = {(f["tool"], f["args"].get("symbol"), f["result"]) for f in facts}
    scanned = [c.as_dict() for c in scan_reply(text) if (c.tool, c.args.get("symbol"), c.claimed) not in fact_keys]
    return Draft(text, "concept", cites, _fact_claims(facts) + scanned, "fallback", "ai_off", 0,
                 [f"Mở bài {cites[0]['lesson_id']}"] if cites else [], fallback_reason=reason)


def _check(ans: TutorAnswer, allowed: dict[str, Hit]) -> tuple[GuardResult, list[str], bool]:
    guard = check_answer(ans.reply, ans.engine_claims)
    bad_cites = [c.block_id for c in ans.citations if c.block_id not in allowed]
    leaked_prompt = pr.CANARY in ans.reply
    return guard, bad_cites, leaked_prompt


def _llm_round(provider: LLMProvider, build, allowed: dict[str, Hit], titles: dict[str, str],
               extra_check=None, system: str | None = None) -> tuple[TutorAnswer | None, GuardResult | None, list[LLMResult], str | None]:
    """Gọi LLM, kiểm, soạn lại tối đa 1 lần. Trả (câu đạt hoặc None, kết quả kiểm, các lần gọi, lý do hỏng)."""
    results: list[LLMResult] = []
    correction = None
    reason = None
    for round_no in (1, 2):
        res = provider.generate(system or pr.SYSTEM, build(correction), LLM_SCHEMA)
        results.append(res)
        ans = parse_answer(res.text)
        if ans is None:
            reason = "format_error"
            correction = pr.correction_note([], [], True)
            continue
        guard, bad_cites, leaked = _check(ans, allowed)
        extra = extra_check(ans) if extra_check else None
        if leaked:
            reason = "prompt_leak"
            return None, guard, results, reason  # không cho cơ hội thứ hai khi đã lộ lệnh hệ thống
        if not guard.contradicted and not extra and (not bad_cites or round_no == 2):
            # Lần 2 vẫn có trích dẫn lạ thì bỏ trích dẫn đó thay vì bỏ cả câu trả lời đúng nhạc lý.
            ans.citations = [c for c in ans.citations if c.block_id in allowed]
            return ans, guard, results, None
        reason = "engine_contradiction" if guard.contradicted else ("answer_leak" if extra else "bad_citation")
        correction = pr.correction_note([c.as_dict() for c in guard.contradicted], bad_cites, False)
        if extra:
            correction += "\n- " + extra
    return None, None, results, reason


def _finish(ans: TutorAnswer, guard: GuardResult, allowed: dict[str, Hit], titles: dict[str, str],
            results: list[LLMResult], facts: Sequence[dict[str, Any]]) -> Draft:
    cites, seen = [], set()
    for c in ans.citations:
        if c.block_id in seen:
            continue
        seen.add(c.block_id)
        cites.append(_citation(allowed[c.block_id], titles))  # tiêu đề lấy từ kho, không lấy chữ AI viết
    merged = _merge_results(results)
    return Draft(ans.reply, ans.intent, cites, [c.as_dict() for c in guard.claims], "ok", "llm", ans.hint_level,
                 list(ans.suggested_actions), merged, len(results))


def _weak_skill_names(db: Session, user_id: str, limit: int = 3) -> list[str]:
    rows = db.scalars(select(MasteryState).where(MasteryState.user_id == user_id, MasteryState.score < 0.6)
                      .order_by(MasteryState.score).limit(limit))
    return [SKILL_NAMES.get(m.skill_id, m.skill_id) for m in rows]


# --- Hỏi đáp ------------------------------------------------------------------------------------

def _engine_facts(dec_facts: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dữ kiện Engine dạng cũ {tool, args, result} cho prompt và nhãn kiểm (không gửi cờ nội bộ)."""
    return [{"tool": f["tool"], "args": f["args"], "result": f["result"]} for f in dec_facts]


def _engine_only_answer(dec, titles: dict[str, str]) -> Draft:
    """Luồng B có dữ kiện: câu viết sẵn từ Music Engine, không gọi LLM, không trích bài (bài chưa dạy)."""
    lines = [fb.OUTSIDE_LESSON] + [fact_text(f) for f in dec.engine.facts]
    if any(not f.get("sourced", True) for f in dec.engine.facts):
        lines.append(fb.NOT_SOURCED)
    text = " ".join(lines) + _pointer(dec, titles)
    facts = _engine_facts(dec.engine.facts)
    actions = [f"Mở bài {dec.nearest_lesson}"] if dec.nearest_lesson else []
    return Draft(text, "concept", [], _fact_claims(facts), "ok", "engine_only", 0, actions, flow="B",
                 source_label=fb.LABEL_ENGINE, suggested_lesson=dec.nearest_lesson)


def _pointer(dec, titles: dict[str, str]) -> str:
    if dec.later_lesson:
        return fb.later_lesson_line(dec.later_lesson, titles)
    return fb.nearest_lesson_line(dec.nearest_lesson, titles)


def _dont_know(dec, titles: dict[str, str]) -> Draft:
    text = (fb.DONT_KNOW_LATER if dec.later_lesson else fb.DONT_KNOW) + _pointer(dec, titles)
    actions = [f"Mở bài {dec.nearest_lesson}"] if dec.nearest_lesson else []
    label = fb.LABEL_LATER if dec.later_lesson else fb.LABEL_UNKNOWN
    return Draft(text, "concept", [], [], "ok", "unsure", 0, actions, flow="B", source_label=label,
                 suggested_lesson=dec.nearest_lesson)


def _says_unknown(reply: str) -> bool:
    """AI tự nói bài chưa dạy / không biết (prompt luồng A dặn câu này khi đoạn bài không trả lời được câu hỏi)."""
    return bool(re.search(r"\bkhong biet\b|\bchua (?:day|duoc day|co trong bai)\b", fold(reply)))


def _faq_answer(question: str, titles: dict[str, str], reason: str) -> Draft | None:
    """RS-07: câu định nghĩa cơ bản khi không gọi được AI. Trả lời từ kho hỏi đáp (nội dung đã soát bằng Engine
    trong test), kèm bài dạy phần đó; không có mục khớp thì None để dùng câu dự phòng cũ."""
    item = faq.match(question, show_draft=settings.show_draft_content)
    if item is None:
        return None
    text = f"{item.answer} Học kỹ ở bài {item.lesson_id} “{titles.get(item.lesson_id, item.lesson_id)}”."
    return Draft(text, "concept", [], [], "ok", "faq", 0, [f"Mở bài {item.lesson_id}"], flow="A",
                 source_label=fb.LABEL_FAQ, suggested_lesson=item.lesson_id, fallback_reason=reason)


def _b_without_ai(dec, titles: dict[str, str], reason: str, question: str = "") -> Draft:
    """Luồng B khi không gọi được AI (ADR-020, trả lời 4A): có dữ kiện Engine thì trả dữ kiện, không thì nói thật
    là chưa trả lời được lúc này kèm bài gần nhất. Không nói "không biết" vì thật ra là AI đang lỗi."""
    if dec.kind == "engine":
        d = _engine_only_answer(dec, titles)
        d.fallback_reason = reason
        return d
    hit = _faq_answer(question, titles, reason)
    if hit is not None:
        return hit
    text = (fb.B_OFF if reason == "ai_disabled" else fb.B_BUSY) + _pointer(dec, titles)
    actions = [f"Mở bài {dec.nearest_lesson}"] if dec.nearest_lesson else []
    return Draft(text, "concept", [], [], "fallback", "ai_off", 0, actions, flow="B", source_label=fb.LABEL_UNKNOWN,
                 suggested_lesson=dec.nearest_lesson, fallback_reason=reason)


def _general_answer(db: Session, user: User, question: str, turns: Sequence[tuple[str, str]], dec,
                    titles: dict[str, str], facts: Sequence[dict[str, Any]], provider: LLMProvider | None,
                    now: datetime) -> Draft:
    """Luồng B (ADR-020): câu âm nhạc mà kho bài chưa dạy. Gemini trả lời bằng kiến thức chung, kèm nhãn rõ "chưa có
    trong bài học"; mọi nốt/hợp âm/âm giai/quãng trong câu được Music Engine quét lại. Sai thì soạn lại 1 lần,
    vẫn sai thì bỏ câu AI và trả dữ kiện Engine (hoặc "chưa trả lời được")."""
    if provider is None:
        return _b_without_ai(dec, titles, "ai_disabled", question)
    if _llm_rows_today(db, now, None) >= settings.ai_global_daily_budget:
        return _b_without_ai(dec, titles, "global_budget", question)
    used = _llm_rows_today(db, now, user.id)
    if used >= settings.ai_daily_quota:
        raise QuotaExceeded(used, settings.ai_daily_quota)

    def build(correction: str | None) -> str:
        return pr.general_prompt(question, turns, facts, correction)

    try:
        ans, guard, results, reason = _llm_round(provider, build, {}, titles, system=pr.SYSTEM_GENERAL)
    except LLMUnavailable as exc:
        d = _b_without_ai(dec, titles, exc.reason, question)
        d.llm_calls = 1
        return d
    if ans is None:
        d = _b_without_ai(dec, titles, reason or "invalid", question)
        d.llm_calls, d.llm = len(results), results[-1] if results else None
        return d
    merged = _merge_results(results)
    if ans.intent == "out_of_scope":
        # Gemini là chốt thứ hai: câu không phải âm nhạc thì dùng câu từ chối viết sẵn, không tin chữ AI viết.
        return Draft(fb.OUT_OF_SCOPE, "out_of_scope", [], [], "ok", "out_of_scope", 0, [], merged, len(results),
                     flow="C", source_label=fb.LABEL_REFUSE)
    text = ans.reply.rstrip() + _pointer(dec, titles)
    actions = list(ans.suggested_actions) or ([f"Mở bài {dec.nearest_lesson}"] if dec.nearest_lesson else [])
    return Draft(text, ans.intent, [], [c.as_dict() for c in guard.claims], "ok", "general_llm", ans.hint_level,
                 actions, merged, len(results), flow="B", source_label=fb.LABEL_GENERAL,
                 suggested_lesson=dec.nearest_lesson)


def _merge_results(results: Sequence[LLMResult]) -> LLMResult:
    last = results[-1]
    return LLMResult(last.text, last.model, sum(r.tokens_in or 0 for r in results) or None,
                     sum(r.tokens_out or 0 for r in results) or None, sum(r.latency_ms for r in results),
                     len(results))


def _help_answer(dec) -> Draft:
    if not dec.help_hits:
        return Draft(fb.HELP_UNKNOWN, "help", [], [], "ok", "help_unknown", 0, [], flow="D",
                     source_label=fb.LABEL_HELP)
    h = dec.help_hits[0].chunk
    path, name = help_page(h.block_id) or ("/app", "Tổng quan")
    text = f"{fb.HELP_LEAD.format(page=name)} {h.text}"
    cite = {"lesson_id": "HELP", "block_id": h.block_id, "title": h.title, "lesson_title": f"Hướng dẫn · {name}"}
    return Draft(text, "help", [cite], [], "ok", "help", 0, [f"Mở trang {name}"], flow="D",
                 source_label=fb.LABEL_HELP, help_page={"path": path, "title": name})


# RS-27: "mình nên học bài nào tiếp" là câu xin tư vấn học, không phải câu nhạc lý hay ngoài phạm vi. Trả lời từ hệ gợi ý
# (cùng nguồn với mục "Bài nên học tiếp" ở Tổng quan) nên không cần AI và không bịa bài.
_STUDY_ADVICE = re.compile(
    r"\b(?:nen|can|phai) (?:hoc|bat dau|lam) (?:bai |cai |phan |gi |tiep|nao|tu )|"
    r"\bhoc (?:gi|bai nao|bai gi|cai gi|tiep (?:bai )?(?:nao|gi)?|bai tiep)\b.*\b(?:tiep|ke tiep|bay gio|dau tien)\b|"
    r"\bbai (?:nao|gi) (?:tiep|nen hoc|ke tiep|tiep theo)|\bbai tiep theo\b|\bbat dau tu (?:dau|bai nao)\b|"
    r"\bgoi y (?:bai|lo trinh|bai hoc)\b|\blo trinh (?:hoc|cua toi|cho toi)\b")


def is_study_advice(question: str) -> bool:
    return bool(_STUDY_ADVICE.search(fold(question)))


def _study_advice_answer(db: Session, user: User, embedder: Embedder | None, now: datetime) -> Draft:
    from .recommendation_service import recommend_for_user

    rec = recommend_for_user(db, user, k=3, now=now, embedder=embedder)
    started = rec.get("continue") or []
    nxt = rec.get("next") or []
    lines, lesson, actions = [], None, []
    if started:
        c = started[0]
        lines.append(f"Bạn đang học dở Bài {c['order']}. {c['title']}, hãy hoàn thành bài này trước.")
        lesson = c["lesson_id"]
    if nxt:
        n = nxt[0]
        lines.append(f"Bài nên học tiếp: Bài {n['order']}. {n['title']}. {n['reason']}")
        lesson = lesson or n["lesson_id"]
    if not lines:
        lines.append("Hiện chưa có bài mới đủ điều kiện để gợi ý. Bạn thử luyện tập thêm hoặc ôn lại thẻ đến hạn "
                     "nhé, mình sẽ gợi ý bài mới khi kỹ năng nền của bạn đủ vững.")
    if lesson:
        actions.append(f"Mở bài {lesson}")
    return Draft(" ".join(lines), "study_advice", [], [], "ok", "study_advice", 0, actions, flow="D",
                 source_label=fb.LABEL_ADVICE, suggested_lesson=lesson)


def answer_question(db: Session, user: User, question: str, turns: Sequence[tuple[str, str]],
                    embedder: Embedder | None, provider: LLMProvider | None, now: datetime) -> tuple[Draft, dict]:
    titles = lesson_titles()
    meta: dict[str, Any] = {}
    if looks_like_injection(question):
        return Draft(fb.INJECTION, "out_of_scope", [], [], "ok", "refused_injection", flow="C",
                     source_label=fb.LABEL_REFUSE), meta
    if is_study_advice(question):
        return _study_advice_answer(db, user, embedder, now), meta
    dec = decide(question, embedder, top_k=settings.rag_top_k)
    meta["router"] = dec.log()
    intent = classify(question)
    meta["intent_local"] = {"intent": intent.intent, "confidence": intent.confidence}
    meta["retrieval"] = {"method": dec.lesson.method, "best_score": dec.lesson.best_score,
                         "fallback_reason": dec.lesson.fallback_reason, "chunks": [h.chunk.chunk_id for h in dec.hits]}
    facts = _engine_facts(dec.engine.facts)
    meta["engine"] = facts
    if dec.flow == "G":
        thanks = any(w in question.lower() for w in ("cảm ơn", "cam on", "thank", "thanks", "thx"))
        return Draft(fb.THANKS if thanks else fb.GREETING, "greeting", [], [], "ok", "greeting", flow="G"), meta
    if dec.flow == "C":
        return Draft(fb.OUT_OF_SCOPE, "out_of_scope", [], [], "ok", "out_of_scope", flow="C",
                     source_label=fb.LABEL_REFUSE), meta
    if dec.flow == "D":
        return _help_answer(dec), meta
    if dec.flow == "B":
        return _general_answer(db, user, question, turns, dec, titles, facts, provider, now), meta

    # Luồng A: có đoạn bài đủ điểm.
    hits = dec.hits
    if provider is None:
        hit = _faq_answer(question, titles, "ai_disabled")
        if hit is not None:
            return hit, meta
        d = offline_answer(hits, facts, titles, "ai_disabled")
        d.flow, d.source_label = "A", fb.LABEL_LESSON
        return d, meta
    if _llm_rows_today(db, now, None) >= settings.ai_global_daily_budget:
        d = offline_answer(hits, facts, titles, "global_budget")
        d.flow, d.source_label = "A", fb.LABEL_LESSON
        return d, meta
    used = _llm_rows_today(db, now, user.id)
    if used >= settings.ai_daily_quota:
        raise QuotaExceeded(used, settings.ai_daily_quota)
    allowed = {h.chunk.block_id: h for h in hits}
    weak = _weak_skill_names(db, user.id)

    def build(correction: str | None) -> str:
        return pr.chat_prompt(question, hits, titles, turns, facts, user.goal_text, weak, correction)

    try:
        ans, guard, results, reason = _llm_round(provider, build, allowed, titles)
    except LLMUnavailable as exc:
        d = offline_answer(hits, facts, titles, exc.reason)
        d.llm_calls, d.flow, d.source_label = 1, "A", fb.LABEL_LESSON
        return d, meta
    if ans is None:
        d = offline_answer(hits, facts, titles, reason or "invalid")
        d.llm_calls, d.llm = len(results), results[-1] if results else None
        d.flow, d.source_label = "A", fb.LABEL_LESSON
        return d, meta
    d = _finish(ans, guard, allowed, titles, results, facts)
    # Câu LLM không trích được đoạn nào (trích dẫn bịa đã bị bỏ, hoặc LLM tự nói "không biết") thì không gắn nhãn
    # "Từ bài học": người học thấy rõ câu này chưa có nguồn trong bài (góp ý thầy G1).
    d.flow, d.source_label = "A", (fb.LABEL_LESSON if d.citations else fb.LABEL_UNCITED)
    # Không xét intent: prompt luồng A dặn câu "ngoài khóa học" đánh out_of_scope, nên Gemini gắn out_of_scope cho chính
    # câu "không biết" ("piano có bao nhiêu phím", thử thật 12/11). Câu ngoài âm nhạc đã bị bộ định tuyến chặn, và
    # prompt kiến thức chung là chốt thứ hai.
    if not d.citations and _says_unknown(d.reply):
        # Kho có đoạn "giống chữ" nhưng AI không trích được đoạn nào (thường là "bài chưa dạy", ví dụ "piano có bao
        # nhiêu phím"): hỏi lại theo kiến thức chung như luồng B (ADR-020). AI lỗi hoặc hết hạn mức thì giữ câu cũ.
        try:
            g = _general_answer(db, user, question, turns, dec, titles, facts, provider, now)
        except QuotaExceeded:
            return d, meta
        if g.route in ("general_llm", "out_of_scope"):
            g.llm_calls += d.llm_calls
            return g, meta
    return d, meta


def _save(db: Session, session: ChatSession, draft: Draft, meta: dict, started: float, now: datetime) -> ChatMessage:
    tool_calls = {"route": draft.route, "llm_calls": draft.llm_calls, "flow": draft.flow,
                  "source_label": draft.source_label, "suggested_lesson": draft.suggested_lesson,
                  "help_page": draft.help_page, **meta}
    if draft.llm:
        tool_calls["model"] = draft.llm.model
    if draft.fallback_reason:
        tool_calls["fallback_reason"] = draft.fallback_reason
    msg = ChatMessage(session_id=session.id, role="assistant", content=draft.reply, intent=draft.intent,
                      citations=draft.citations, engine_claims=draft.claims, tool_calls=tool_calls,
                      hint_level=draft.hint_level, status=draft.status,
                      latency_ms=int((time.perf_counter() - started) * 1000),
                      tokens_in=draft.llm.tokens_in if draft.llm else None,
                      tokens_out=draft.llm.tokens_out if draft.llm else None, created_at=now)
    db.add(msg)
    session.updated_at = now
    db.commit()
    return msg


def _lesson_ref(lesson_id: str | None) -> dict[str, str] | None:
    if not lesson_id:
        return None
    return {"lesson_id": lesson_id, "title": lesson_titles().get(lesson_id, lesson_id)}


def out(msg: ChatMessage, session: ChatSession, remaining: int) -> dict[str, Any]:
    claims = msg.engine_claims or []
    verified = bool(claims) and all(c.get("status") == "verified" for c in claims)
    tc = msg.tool_calls or {}
    return {"message_id": msg.id, "session_id": session.id, "reply": msg.content, "citations": msg.citations or [],
            "engine_claims": claims, "verified": verified, "verified_label": VERIFIED_LABEL if verified else None,
            "intent": msg.intent, "hint_level": msg.hint_level or 0, "status": msg.status,
            "suggested_actions": tc.get("suggested_actions", []), "fallback_reason": tc.get("fallback_reason"),
            "retrieval_method": (tc.get("retrieval") or {}).get("method"), "quiz": None,
            "flow": tc.get("flow"), "source_label": tc.get("source_label"),
            "suggested_lesson": _lesson_ref(tc.get("suggested_lesson")), "help_page": tc.get("help_page"),
            "quota_remaining_today": remaining}


def handle_message(db: Session, user: User, text: str, *, session_id: str | None = None,
                   context: dict[str, Any] | None = None, embedder: Embedder | None = None,
                   provider: LLMProvider | None = None, now: datetime | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    now = _now(now)
    session = get_session(db, user.id, session_id) if session_id else create_session(db, user.id, now=now)
    user_msg = ChatMessage(session_id=session.id, role="user", content=text, status="ok", created_at=now,
                           tool_calls={"context": _clean_context(context)})
    db.add(user_msg)
    db.flush()
    turns = recent_turns(db, session.id, before_id=user_msg.id)
    try:
        draft, meta = answer_question(db, user, text, turns, embedder, provider, now)
    except QuotaExceeded:
        db.commit()  # tin nhắn vẫn được lưu (04 Bảng 11, mã 429)
        raise
    meta["suggested_actions"] = draft.suggested_actions or []
    msg = _save(db, session, draft, meta, started, now)
    return out(msg, session, quota_remaining(db, user.id, now))


def _clean_context(context: dict[str, Any] | None) -> dict[str, str]:
    # Chỉ giữ khóa đã biết, để client không nhét dữ liệu tùy ý vào CSDL hay prompt.
    ctx = context or {}
    return {k: str(ctx[k])[:40] for k in ("page", "lesson_id", "block_id") if ctx.get(k)}


# --- Giải thích lượt làm sai -------------------------------------------------------------------

def _expected_strings(answer_key: dict[str, Any]) -> list[list[str] | str]:
    out: list[list[str] | str] = []
    exp = answer_key.get("expected")
    if isinstance(exp, list) and exp:
        out.append([str(x) for x in exp] if len(exp) > 1 else str(exp[0]))
    elif isinstance(exp, str) and exp.strip():
        out.append(exp.strip())
    for acc in answer_key.get("accepted") or []:
        if isinstance(acc, str) and len(acc.strip()) >= 3:
            out.append(acc.strip())
    return out


def leaks_answer(reply: str, answer_key: dict[str, Any]) -> bool:
    """Câu trả lời có nêu đáp án không (dùng cho mức gợi mở 1–2, 04 Bảng 28 "Không lộ đáp án")."""
    import re

    text = solfege_to_letters(reply)
    notes = split_notes(text)
    for exp in _expected_strings(answer_key):
        if isinstance(exp, list):
            n = len(exp)
            if any(notes[i:i + n] == exp for i in range(len(notes) - n + 1)):
                return True
        else:
            pat = rf"(?<![A-Za-z0-9#]){re.escape(exp)}(?![A-Za-z0-9#])"
            flags = 0 if len(exp) <= 4 else re.IGNORECASE  # m3 khác M3; cụm dài thì không phân biệt hoa thường
            if re.search(pat, text, flags):
                return True
    return False


def _grader_facts(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    kind = cfg.get("kind")
    if kind == "build_chord" and cfg.get("symbol"):
        value, _ = run_tool("get_chord_tones", {"symbol": cfg["symbol"]})
        return [{"tool": "get_chord_tones", "args": {"symbol": cfg["symbol"]}, "result": value}] if value else []
    if kind == "build_scale" and cfg.get("tonic"):
        args = {"tonic": cfg["tonic"], "scale_type": cfg.get("scale_type", "major")}
        value, _ = run_tool("get_scale", args)
        return [{"tool": "get_scale", "args": args, "result": value}] if value else []
    return []


def explain_attempt(db: Session, user: User, attempt_id: str, *, hint_level: int | None = None,
                    session_id: str | None = None, embedder: Embedder | None = None,
                    provider: LLMProvider | None = None, now: datetime | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    now = _now(now)
    attempt = db.get(Attempt, attempt_id)
    if attempt is None or attempt.user_id != user.id:
        raise AttemptNotFound(attempt_id)
    if attempt.correct:
        raise AttemptNotWrong(attempt_id)
    ev = db.get(ExerciseVersion, attempt.exercise_version_id)
    ex = db.get(Exercise, ev.exercise_id)
    # Mã lỗi lấy từ CSDL (đã chấm bằng Music Engine), không bao giờ nhận từ client.
    codes = [attempt.primary_error] if attempt.primary_error else []
    codes += [c for c in db.scalars(select(AttemptError.code).where(AttemptError.attempt_id == attempt.id)
                                    .order_by(AttemptError.id)) if c not in codes]
    session = get_session(db, user.id, session_id) if session_id else create_session(db, user.id, now=now)
    previous = [m.hint_level or 0 for m in db.scalars(
        select(ChatMessage).join(ChatSession, ChatSession.id == ChatMessage.session_id)
        .where(ChatSession.user_id == user.id, ChatMessage.role == "assistant", ChatMessage.intent == "explain_error"))
        if (m.tool_calls or {}).get("attempt_id") == attempt.id]
    level = hint_level if hint_level is not None else min(3, (max(previous) if previous else 0) + 1)
    skill_name = SKILL_NAMES.get(ex.skill_id, ex.skill_id)
    prompt_text = ev.prompt or ex.prompt

    db.add(ChatMessage(session_id=session.id, role="user", content=f"Giải thích lỗi: {prompt_text}"[:1000],
                       status="ok", created_at=now, tool_calls={"attempt_id": attempt.id, "hint_level": level}))
    db.flush()
    titles = lesson_titles()
    r = retrieve_for_skill(f"{skill_name}. {prompt_text}", embedder, [ex.lesson_id], top_k=3)
    facts = _grader_facts(ev.grader_config or {}) if level >= 3 else []
    meta: dict[str, Any] = {"attempt_id": attempt.id, "error_codes": codes,
                            "retrieval": {"method": r.method, "chunks": [h.chunk.chunk_id for h in r.hits]},
                            "engine": facts}

    def rule_draft(reason: str) -> Draft:
        text = fb.explain_text(codes, level, ev.explanation if level >= 3 else None) + fb.lesson_pointer(r.hits, titles)
        cites = [_citation(r.hits[0], titles)] if r.hits else []
        return Draft(text, "explain_error", cites, _fact_claims(facts), "fallback", "ai_off", level,
                     [f"Mở bài {ex.lesson_id}"], fallback_reason=reason)

    draft: Draft
    if provider is None:
        draft = rule_draft("ai_disabled")
    elif _llm_rows_today(db, now, None) >= settings.ai_global_daily_budget:
        draft = rule_draft("global_budget")
    else:
        used = _llm_rows_today(db, now, user.id)
        if used >= settings.ai_daily_quota:
            db.commit()
            raise QuotaExceeded(used, settings.ai_daily_quota)
        allowed = {h.chunk.block_id: h for h in r.hits}

        def build(correction: str | None) -> str:
            return pr.explain_prompt(prompt_text, codes, skill_name, level, r.hits, titles, facts, correction)

        def no_leak(ans: TutorAnswer) -> str | None:
            if level <= 2 and leaks_answer(ans.reply, ev.answer_key or {}):
                return "Câu trả lời đã nêu đáp án; ở mức gợi mở này chỉ được gợi ý, không nêu đáp án."
            return None

        try:
            ans, guard, results, reason = _llm_round(provider, build, allowed, titles, no_leak)
        except LLMUnavailable as exc:
            draft = rule_draft(exc.reason)
            draft.llm_calls = 1
        else:
            if ans is None:
                draft = rule_draft(reason or "invalid")
                draft.llm_calls, draft.llm = len(results), results[-1] if results else None
            else:
                ans.intent, ans.hint_level = "explain_error", level  # mức do máy chủ quyết, không theo AI
                draft = _finish(ans, guard, allowed, titles, results, facts)
                draft.hint_level = level
    meta["suggested_actions"] = draft.suggested_actions or []
    msg = _save(db, session, draft, meta, started, now)
    result = out(msg, session, quota_remaining(db, user.id, now))
    result["attempt_id"] = attempt.id
    result["next_hint_level"] = min(3, level + 1) if level < 3 else None
    return result


def rate_message(db: Session, user_id: str, message_id: int, stars: int, comment: str | None) -> None:
    msg = db.get(ChatMessage, message_id)
    if msg is None or msg.role != "assistant":
        raise ChatNotFound(str(message_id))
    get_session(db, user_id, msg.session_id)
    row = db.scalar(select(ChatFeedback).where(ChatFeedback.message_id == message_id))
    if row is None:
        db.add(ChatFeedback(message_id=message_id, user_id=user_id, stars=stars, comment=comment))
    else:
        row.stars, row.comment = stars, comment
    db.commit()
