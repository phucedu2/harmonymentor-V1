"""Pipeline chatbot kiểu n8n (G4, góp ý thầy T3). Mỗi bước là một Node trong danh sách NODES; sơ đồ ở docs/AI_PIPELINE.md.

  Trigger → RateLimit → Guard → StudyAdvice → Intent → Rewrite → Retrieve → Rerank → Route
          → [nhánh theo luồng] Greeting | Help | OffTopic | LowConfidence → General | AnswerGate → Prompt → LLM → Parse
            → CitationCheck → Safety (có thể quay lại Prompt 1 lần) → UnknownFallback
          → Log

Luồng A/B/C/D/G và mọi ngưỡng định tuyến giữ nguyên như ADR-017/020; G4 chỉ tách thành bước, thêm Qdrant (RAG_ENABLED),
rerank, viết lại câu hỏi nối tiếp, giới hạn tốc độ, trả lời ngắn câu lạc đề và nhật ký chi phí/độ trễ."""

from __future__ import annotations

import logging
import re
import time
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Sequence

from ..ai.embedder import Embedder, EmbeddingUnavailable
from ..ai.pipeline.core import Ctx, Node, Pipeline
from ..ai.tutor import fallback as fb
from ..ai.tutor import prompt as pr
from ..ai.tutor.chunker import Chunk, lesson_titles, split_sentences
from ..ai.tutor.engine_query import engine_answer
from ..ai.tutor.general import blocked, broad_music, fold
from ..ai.tutor.guardrail import check_answer
from ..ai.tutor.injection import looks_like_injection
from ..ai.tutor.intent import classify
from ..ai.tutor.llm import LLMUnavailable
from ..ai.tutor.retriever import Hit, Retrieval, help_base, retrieve
from ..ai.tutor.route_classifier import classify_route
from ..ai.tutor.router import (Signals, _th, later_lesson, outside_kb, route, unknown_terms, untaught_concept)
from ..ai.tutor.schema import LLM_SCHEMA, parse_answer
from ..core.ai_config import PipelineConfig, pipeline_config, rag_config
from . import ai_tutor_service as ts

log = logging.getLogger("harmonymentor.pipeline")


RateLimited = ts.RateLimited


_windows: dict[str, deque[float]] = defaultdict(deque)


def reset_rate_limits() -> None:
    _windows.clear()


def _done(ctx: Ctx, draft: ts.Draft) -> None:
    ctx.set(draft=draft)
    ctx.done = True


def _lesson_flow(d: ts.Draft) -> ts.Draft:
    d.flow, d.source_label = "A", fb.LABEL_LESSON
    return d


# --- 1. Trigger, giới hạn tốc độ, chốt chặn --------------------------------------------------------------------------

class Trigger(Node):
    name = "trigger"

    def run(self, ctx: Ctx) -> None:
        q = " ".join(ctx.question.split())
        ctx.set(question=q, query=q)


class RateLimit(Node):
    """Cửa sổ trượt 60 giây theo người dùng. Trong bộ nhớ tiến trình: đủ để chặn bấm liên tục; chống lạm dụng đa tiến trình
    đã có hạn mức ngày (AI_DAILY_QUOTA) ở cơ sở dữ liệu."""

    name = "rate_limit"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.pcfg.rate_limit_per_min > 0

    def run(self, ctx: Ctx) -> None:
        now, win, limit = time.monotonic(), _windows[ctx.user.id], ctx.pcfg.rate_limit_per_min
        while win and now - win[0] >= 60:
            win.popleft()
        if len(win) >= limit:
            raise RateLimited(max(1, int(60 - (now - win[0])) + 1))
        win.append(now)


class Guard(Node):
    """Chặn tiêm lệnh, và nhận ra câu lạc đề rõ ràng sớm (trước khi tốn truy xuất). Luật lạc đề sớm = đúng luật đầu tiên
    của bộ định tuyến (nhãn ngoài phạm vi, chắc chắn, không có dữ kiện Engine, không có từ khóa âm nhạc)."""

    name = "guard"

    def run(self, ctx: Ctx) -> None:
        q = ctx.question
        if looks_like_injection(q):
            return _done(ctx, ts.Draft(fb.INJECTION, "out_of_scope", [], [], "ok", "refused_injection", flow="C",
                                       source_label=fb.LABEL_REFUSE))
        label, eng = classify_route(q), engine_answer(q)
        ctx.set(label=label, eng=eng)
        th = _th(ctx.embedder)
        if (label.label == "ngoai_pham_vi" and label.confidence >= th["oos_conf"] and not eng.facts
                and not broad_music(q) and not ts.is_study_advice(q)):
            ctx.set(flow="C", dec=None, facts=[])
            ctx.meta["router"] = {"flow": "C", "kind": "refuse", "reason": "guard_label_out_of_scope",
                                  "label": {"label": label.label, "confidence": label.confidence}}


class StudyAdvice(Node):
    name = "study_advice"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow is None and ts.is_study_advice(ctx.question)

    def run(self, ctx: Ctx) -> None:
        _done(ctx, ts._study_advice_answer(ctx.db, ctx.user, ctx.embedder, ctx.now))


# --- 2. Hiểu câu hỏi, viết lại, truy xuất, xếp hạng lại ----------------------------------------------------------------

class Intent(Node):
    name = "intent"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow is None

    def run(self, ctx: Ctx) -> None:
        intent = classify(ctx.question)
        ctx.meta["intent_local"] = {"intent": intent.intent, "confidence": intent.confidence}


_FOLLOW_UP = re.compile(r"^(?:vay|con|the|nhu vay|va|roi|tiep|no|cai (?:do|nay|kia)|chung|sao|tai sao|vi sao)\b")


def rewrite_query(question: str, turns: Sequence[tuple[str, str]]) -> str:
    """Câu hỏi nối tiếp ngắn ("còn Dm7 thì sao?") thiếu chủ đề nên truy xuất kém; nối thêm câu hỏi người học vừa hỏi trước đó.
    Bảo thủ: chỉ khi câu ≤ 7 chữ và mở đầu bằng từ nối/đại từ. Chỉ dùng cho truy xuất, bộ định tuyến vẫn xét câu gốc."""
    previous = next((c for r, c in reversed(turns) if r == "user"), None)
    if not previous or len(question.split()) > 7 or not _FOLLOW_UP.match(fold(question)):
        return question
    return f"{previous} {question}"


class Rewrite(Node):
    name = "rewrite"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow is None

    def run(self, ctx: Ctx) -> None:
        q = rewrite_query(ctx.question, ctx.turns)
        if q != ctx.question:
            ctx.meta["rewrite"] = {"original": ctx.question, "query": q}
        ctx.set(query=q)


_stores: dict[tuple[str, str], Any] = {}


def _store(rcfg):
    key = (rcfg.qdrant_url, rcfg.collection)
    if key not in _stores:
        from ..rag.store import QdrantStore, make_client

        _stores[key] = QdrantStore(make_client(rcfg), rcfg.collection, rcfg.dim)
    return _stores[key]


def _to_hit(h) -> Hit:
    p = h.payload
    block = p.get("block_id", "")
    return Hit(Chunk(p.get("chunk_id") or f"{block}#{p.get('chunk_idx', 0)}", p.get("lesson_id", ""), block,
                     p.get("title", ""), p.get("text", ""), p.get("license", ""), p.get("content_hash", ""),
                     p.get("search_hint", "")), round(h.score, 4))


def qdrant_retrieve(query: str, embedder: Embedder | None, pcfg: PipelineConfig) -> tuple[Retrieval | None, str]:
    """(kết quả, ghi chú). None = không dùng được Qdrant, bước Retrieve lùi về đường cũ (e5 trong bộ nhớ + BM25)."""
    rcfg = rag_config()
    if embedder is None:
        return None, "no_embedder"
    if not rcfg.qdrant_url:
        return None, "no_qdrant_url"
    if getattr(embedder, "dim", None) != rcfg.dim:
        return None, "dim_mismatch"
    try:
        store = _store(rcfg)
        if store.count({"source": list(pcfg.rag_sources)}) == 0:
            return None, "collection_empty"
        vec = embedder.embed([query], "RETRIEVAL_QUERY")[0]
        raw = store.search(vec, top_k=pcfg.rerank_pool, min_score=-1.0, filters={"source": list(pcfg.rag_sources)})
    except EmbeddingUnavailable:
        return None, "embedding_unavailable"
    except Exception as exc:   # noqa: BLE001 - Qdrant sập/chưa sẵn sàng: chatbot vẫn trả lời bằng đường cũ
        log.warning("qdrant_error type=%s", type(exc).__name__)
        _stores.clear()
        return None, f"qdrant_error:{type(exc).__name__}"
    hits = [_to_hit(h) for h in raw]
    return Retrieval(hits, "embedding", hits[0].score if hits else 0.0), "ok"


class Retrieve(Node):
    name = "retrieve"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow is None

    def run(self, ctx: Ctx) -> None:
        lesson, source, note = None, "legacy", None
        if ctx.pcfg.rag_enabled:
            lesson, note = qdrant_retrieve(ctx.query, ctx.embedder, ctx.pcfg)
            source = "qdrant" if lesson is not None else "legacy"
        if lesson is None:
            lesson = retrieve(ctx.query, ctx.embedder, top_k=ts.settings.rag_top_k, min_score=-1.0, bm25_min_score=-1.0)
        helps = retrieve(ctx.query, ctx.embedder, top_k=2, min_score=-1.0, bm25_min_score=-1.0, chunks=list(help_base()))
        ctx.set(lesson=lesson, helps=helps, retrieval_source=source, retrieval_note=note)


_STOP = frozenset("la gi cua va cho the nao nhu co khong trong mot cac nhung duoc de voi khi thi ma nay do roi hay se".split())


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9#]+", fold(text)) if len(w) >= 2 and w not in _STOP}


def rerank(query: str, hits: Sequence[Hit], weight: float, top_k: int) -> list[Hit]:
    """Xếp lại nhóm ứng viên theo điểm vector + trọng số nhỏ cho độ trùng từ với tiêu đề/nội dung, bỏ trùng block_id.
    Giữ NGUYÊN điểm vector của từng đoạn: ngưỡng định tuyến hiệu chỉnh trên điểm đó, rerank chỉ đổi thứ tự."""
    q = _words(query)
    if not q:
        return list(hits)[:top_k]

    def key(h: Hit) -> float:
        overlap = len(q & _words(f"{h.chunk.title} {h.chunk.text}")) / len(q)
        return h.score + weight * overlap

    seen, out = set(), []
    for h in sorted(hits, key=key, reverse=True):
        if h.chunk.block_id not in seen:
            seen.add(h.chunk.block_id)
            out.append(h)
    return out[:top_k]


class Rerank(Node):
    name = "rerank"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow is None and ctx.retrieval_source == "qdrant"

    def run(self, ctx: Ctx) -> None:
        r = ctx.lesson
        ctx.set(lesson=Retrieval(rerank(ctx.query, r.hits, ctx.pcfg.rerank_weight, ts.settings.rag_top_k), r.method,
                                 r.best_score, r.fallback_reason))


class Route(Node):
    """Cùng bộ luật ADR-017/020: nhãn tầng 1 + điểm truy xuất + Music Engine → luồng A/B/C/D/G."""

    name = "route"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow is None

    def run(self, ctx: Ctx) -> None:
        q, eng = ctx.question, ctx.eng
        sig = Signals(q, ctx.label, eng, ctx.lesson, ctx.helps, later_lesson(q), outside_kb(eng), unknown_terms(q),
                      untaught_concept(q), broad_music(q))
        dec = route(sig, _th(ctx.embedder))
        facts = ts._engine_facts(dec.engine.facts)
        ctx.set(dec=dec, flow=dec.flow, facts=facts)
        ctx.meta["router"] = dec.log()
        ctx.meta["retrieval"] = {"method": dec.lesson.method, "best_score": dec.lesson.best_score,
                                 "fallback_reason": dec.lesson.fallback_reason,
                                 "chunks": [h.chunk.chunk_id for h in dec.hits],
                                 "source": ctx.retrieval_source, "note": ctx.retrieval_note}
        ctx.meta["engine"] = facts


# --- 3. Nhánh trả lời không qua LLM kiểu A ------------------------------------------------------------------------------

class Greeting(Node):
    name = "greeting"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow == "G"

    def run(self, ctx: Ctx) -> None:
        thanks = any(w in ctx.question.lower() for w in ("cảm ơn", "cam on", "thank", "thanks", "thx"))
        _done(ctx, ts.Draft(fb.THANKS if thanks else fb.GREETING, "greeting", [], [], "ok", "greeting", flow="G"))


class Help(Node):
    name = "help"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow == "D"

    def run(self, ctx: Ctx) -> None:
        _done(ctx, ts._help_answer(ctx.dec))


def clip_sentences(text: str, max_sentences: int, max_chars: int = 280) -> str:
    """Giữ tối đa max_sentences câu đầu, và không quá max_chars ký tự (một "câu" không dấu chấm vẫn bị cắt)."""
    kept = " ".join(split_sentences(" ".join(text.split()))[:max_sentences]).strip()
    if len(kept) > max_chars:
        kept = kept[:max_chars].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return kept


class OffTopic(Node):
    """Câu lạc đề: trả lời TỐI ĐA 2 câu rồi dẫn về nhạc lý (Phúc chốt 14/11/2026, khác ADR-020 trước đây chỉ từ chối).
    Câu thuộc nhóm cấm, AI tắt/hết hạn mức/lỗi, hoặc OFFTOPIC_MODE=refuse thì dùng câu từ chối viết sẵn."""

    name = "off_topic"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow == "C"

    def _refusal(self) -> ts.Draft:
        return ts.Draft(fb.OUT_OF_SCOPE, "out_of_scope", [], [], "ok", "out_of_scope", flow="C", source_label=fb.LABEL_REFUSE)

    def run(self, ctx: Ctx) -> None:
        pc, provider, q = ctx.pcfg, ctx.provider, ctx.question
        if (pc.offtopic_mode != "brief" or provider is None or blocked(q)
                or ts._llm_rows_today(ctx.db, ctx.now, None) >= ts.settings.ai_global_daily_budget
                or ts._llm_rows_today(ctx.db, ctx.now, ctx.user.id) >= ts.settings.ai_daily_quota):
            return _done(ctx, self._refusal())
        try:
            ans, guard, results, _ = ts._llm_round(provider, lambda c: pr.offtopic_prompt(q, ctx.turns, c), {},
                                                   ctx.titles, system=pr.SYSTEM_OFFTOPIC)
        except LLMUnavailable:
            d = self._refusal()
            d.llm_calls = 1
            return _done(ctx, d)
        if ans is None:
            d = self._refusal()
            d.llm_calls, d.llm = len(results), results[-1] if results else None
            return _done(ctx, d)
        brief = clip_sentences(ans.reply, pc.offtopic_max_sentences)
        d = ts.Draft(f"{brief} {fb.STEER_BACK}" if brief else fb.OUT_OF_SCOPE, "out_of_scope", [],
                     [c.as_dict() for c in guard.claims], "ok", "out_of_scope_brief" if brief else "out_of_scope", 0, [],
                     ts._merge_results(results), len(results), flow="C", source_label=fb.LABEL_OFFTOPIC if brief else fb.LABEL_REFUSE)
        _done(ctx, d)


class LowConfidence(Node):
    """RAG_STRICT_GROUNDING=1: truy xuất không đủ tin cậy thì nói "mình không biết" và gợi ý bài, không để Gemini đoán."""

    name = "low_confidence"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow == "B" and ctx.pcfg.strict_grounding and ctx.dec.kind == "unknown"

    def run(self, ctx: Ctx) -> None:
        _done(ctx, ts._dont_know(ctx.dec, ctx.titles))


class General(Node):
    name = "general"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow == "B"

    def run(self, ctx: Ctx) -> None:
        _done(ctx, ts._general_answer(ctx.db, ctx.user, ctx.question, ctx.turns, ctx.dec, ctx.titles, ctx.facts,
                                      ctx.provider, ctx.now))


# --- 4. Luồng A: prompt → LLM → kiểm trích dẫn → kiểm an toàn (vòng soạn lại tối đa 1 lần) --------------------------------

class AnswerGate(Node):
    name = "answer_gate"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow == "A"

    def run(self, ctx: Ctx) -> None:
        hits, facts, titles = ctx.dec.hits, ctx.facts, ctx.titles
        ctx.set(hits=hits, allowed={h.chunk.block_id: h for h in hits}, attempt=0, correction=None, results=[],
                ans=None, accepted=False)
        if ctx.provider is None:
            faq = ts._faq_answer(ctx.question, titles, "ai_disabled")
            return _done(ctx, faq if faq is not None else _lesson_flow(ts.offline_answer(hits, facts, titles, "ai_disabled")))
        if ts._llm_rows_today(ctx.db, ctx.now, None) >= ts.settings.ai_global_daily_budget:
            return _done(ctx, _lesson_flow(ts.offline_answer(hits, facts, titles, "global_budget")))
        used = ts._llm_rows_today(ctx.db, ctx.now, ctx.user.id)
        if used >= ts.settings.ai_daily_quota:
            raise ts.QuotaExceeded(used, ts.settings.ai_daily_quota)
        ctx.set(weak=ts._weak_skill_names(ctx.db, ctx.user.id))


class BuildPrompt(Node):
    name = "prompt"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow == "A"

    def run(self, ctx: Ctx) -> None:
        ctx.set(prompt=pr.chat_prompt(ctx.question, ctx.hits, ctx.titles, ctx.turns, ctx.facts, ctx.user.goal_text,
                                      ctx.weak, ctx.correction), attempt=ctx.attempt + 1)


class CallLLM(Node):
    name = "llm"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow == "A"

    def run(self, ctx: Ctx) -> None:
        try:
            ctx.results.append(ctx.provider.generate(pr.SYSTEM, ctx.prompt, LLM_SCHEMA))
        except LLMUnavailable as exc:
            d = _lesson_flow(ts.offline_answer(ctx.hits, ctx.facts, ctx.titles, exc.reason))
            d.llm_calls = 1
            _done(ctx, d)


class Parse(Node):
    name = "parse"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow == "A"

    def run(self, ctx: Ctx) -> None:
        ctx.set(ans=parse_answer(ctx.results[-1].text), bad_cites=[], guard=None, leaked=False)


class CitationCheck(Node):
    """Máy chủ tự đối chiếu từng trích dẫn với các đoạn đã truy xuất; trích dẫn không có trong danh sách bị loại."""

    name = "citation_check"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow == "A" and ctx.ans is not None

    def run(self, ctx: Ctx) -> None:
        ctx.set(bad_cites=[c.block_id for c in ctx.ans.citations if c.block_id not in ctx.allowed])


class Safety(Node):
    """Music Engine kiểm mọi khẳng định nhạc lý, chuỗi canh gác kiểm lộ lệnh hệ thống; quyết định nhận / soạn lại / dự phòng."""

    name = "safety"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow == "A"

    def _fail(self, ctx: Ctx, reason: str) -> None:
        # G8: AI hai lần liền không nêu đúng kết quả Engine thì trả kết quả Engine kèm đoạn bài (có trích dẫn, vẫn "từ bài học").
        lead = "Mình trả lời theo Music Engine và bài học nhé." if reason == "fact_missing" else None
        d = _lesson_flow(ts.offline_answer(ctx.hits, ctx.facts, ctx.titles, reason or "invalid", lead=lead))
        d.llm_calls, d.llm = len(ctx.results), ctx.results[-1]
        _done(ctx, d)

    def run(self, ctx: Ctx) -> None:
        ans, round_no = ctx.ans, ctx.attempt
        if ans is None:
            reason, note = "format_error", pr.correction_note([], [], True)
        else:
            guard = check_answer(ans.reply, ans.engine_claims)
            ctx.set(guard=guard)
            if pr.CANARY in ans.reply:
                return self._fail(ctx, "prompt_leak")      # đã lộ lệnh hệ thống: không cho cơ hội thứ hai
            anchor = None if guard.contradicted else ts.anchor_note(ctx.question, ans.reply, ctx.facts)
            if not guard.contradicted and not anchor and (not ctx.bad_cites or round_no == 2):
                ans.citations = [c for c in ans.citations if c.block_id in ctx.allowed]
                return self._accept(ctx, ans, guard)
            reason = "engine_contradiction" if guard.contradicted else ("fact_missing" if anchor else "bad_citation")
            note = pr.correction_note([c.as_dict() for c in guard.contradicted], ctx.bad_cites, False)
            if anchor:
                note += "\n- " + anchor
        if round_no == 1:
            ctx.set(correction=note)
            ctx.goto = "prompt"
        else:
            self._fail(ctx, reason)

    def _accept(self, ctx: Ctx, ans, guard) -> None:
        d = ts._finish(ans, guard, ctx.allowed, ctx.titles, ctx.results, ctx.facts)
        # Không trích được đoạn nào thì không gắn "Từ bài học": người học thấy rõ câu này chưa có nguồn (góp ý thầy G1).
        d.flow, d.source_label = "A", (fb.LABEL_LESSON if d.citations else fb.LABEL_UNCITED)
        ctx.set(draft=d, accepted=True)


class UnknownFallback(Node):
    """AI tự nói "không biết" mà không trích được đoạn nào: hỏi lại theo kiến thức chung như luồng B (ADR-020), trừ khi
    đang bật RAG_STRICT_GROUNDING (khi đó giữ câu "không biết")."""

    name = "unknown_fallback"

    def applies(self, ctx: Ctx) -> bool:
        return ctx.flow == "A" and ctx.accepted

    def run(self, ctx: Ctx) -> None:
        d = ctx.draft
        if d.citations or not ts._says_unknown(d.reply) or ctx.pcfg.strict_grounding:
            return
        try:
            g = ts._general_answer(ctx.db, ctx.user, ctx.question, ctx.turns, ctx.dec, ctx.titles, ctx.facts,
                                   ctx.provider, ctx.now)
        except ts.QuotaExceeded:
            return
        if g.route in ("general_llm", "out_of_scope"):
            g.llm_calls += d.llm_calls
            ctx.set(draft=g)


# --- 5. Nhật ký -------------------------------------------------------------------------------------------------------

class Log(Node):
    """Ghi vết từng bước, tổng độ trễ, token và chi phí ước tính vào tool_calls của tin nhắn. Không ghi nội dung câu hỏi."""

    name = "log"
    always = True

    def run(self, ctx: Ctx) -> None:
        d: ts.Draft = ctx.draft
        tin = d.llm.tokens_in if d.llm else None
        tout = d.llm.tokens_out if d.llm else None
        cost = None
        if (ctx.pcfg.price_in_per_m or ctx.pcfg.price_out_per_m) and (tin or tout):
            cost = round((tin or 0) * ctx.pcfg.price_in_per_m / 1e6 + (tout or 0) * ctx.pcfg.price_out_per_m / 1e6, 6)
        steps = [{"node": t.node, "status": t.status, "ms": t.ms} for t in ctx.trace]
        steps.append({"node": self.name, "status": "ok", "ms": 0.0})    # chính bước này chưa vào vết lúc ghi
        total = round(sum(t.ms for t in ctx.trace), 2)
        ctx.meta["pipeline"] = {"nodes": steps, "pipeline_ms": total, "flow": d.flow, "llm_calls": d.llm_calls,
                                "tokens_in": tin, "tokens_out": tout, "cost_usd": cost,
                                "retrieval_source": ctx.retrieval_source}
        log.info("chat flow=%s route=%s llm_calls=%s tokens_in=%s tokens_out=%s pipeline_ms=%s retrieval=%s",
                 d.flow, d.route, d.llm_calls, tin, tout, total, ctx.retrieval_source)


NODES: list[Node] = [Trigger(), RateLimit(), Guard(), StudyAdvice(), Intent(), Rewrite(), Retrieve(), Rerank(), Route(),
                     Greeting(), Help(), OffTopic(), LowConfidence(), General(),
                     AnswerGate(), BuildPrompt(), CallLLM(), Parse(), CitationCheck(), Safety(), UnknownFallback(), Log()]
PIPELINE = Pipeline(NODES)


def run(db, user, question: str, turns: Sequence[tuple[str, str]], embedder: Embedder | None, provider, now: datetime
        ) -> tuple[ts.Draft, dict]:
    ctx = Ctx(data=dict(db=db, user=user, question=question, query=question, turns=turns, embedder=embedder,
                        provider=provider, now=now, pcfg=pipeline_config(), titles=lesson_titles(), meta={}, flow=None,
                        dec=None, facts=[], draft=None, label=None, eng=None, lesson=None, helps=None,
                        retrieval_source=None, retrieval_note=None, accepted=False))
    PIPELINE.run(ctx)
    return ctx.draft, ctx.meta
