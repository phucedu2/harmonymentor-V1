"""Nhà cung cấp LLM cho AI Tutor: Gemini khi bật AI, FakeProvider trong test (không gọi mạng).

Hết giờ 8 giây (RS-29, Phúc chốt 14/11/2026), thử lại đúng 1 lần khi 429/503/hết giờ (GĐ0 đã gặp 503 "high demand"
thật với gemini-3.6-flash), ghi token, độ trễ và mã lỗi (không ghi khóa hay nội dung câu hỏi). Lần thử lại dùng mô hình dự phòng. Lỗi nào cũng thành
LLMUnavailable để dịch vụ chuyển sang câu trả lời dự phòng theo luật, không trả 500 cho người học."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, Sequence


log = logging.getLogger("harmonymentor.llm")


class LLMUnavailable(RuntimeError):
    def __init__(self, reason: str, *, attempts: int = 1, scope: str | None = None):
        super().__init__(reason)
        self.reason = reason  # timeout | rate_limited | unavailable | blocked
        # ADR-042: số lần gọi HTTP thật đã tốn (Google tính cả lần lỗi) để bộ đếm lượt không thấp hơn AI Studio.
        self.attempts = attempts
        # 429 vì quá nhanh trong 1 phút ("minute") hay hết lượt trong ngày ("day"); None = không rõ.
        self.scope = scope


@dataclass(frozen=True)
class LLMResult:
    text: str
    model: str
    tokens_in: int | None
    tokens_out: int | None
    latency_ms: int
    attempts: int = 1
    # Lý do dừng của mô hình (STOP, MAX_TOKENS, SAFETY...). MAX_TOKENS = JSON bị cắt giữa chừng (zip thầy G-25).
    finish_reason: str | None = None


class LLMProvider(Protocol):
    model: str

    def generate(self, system: str, user: str, schema: dict[str, Any], max_output_tokens: int | None = None) -> LLMResult: ...


def _status(exc: Exception) -> int | None:
    for attr in ("code", "status_code", "status"):
        v = getattr(exc, attr, None)
        if isinstance(v, int):
            return v
    text = str(exc)
    for code in (429, 503, 500, 504):
        if str(code) in text[:40]:
            return code
    return None


def _rate_scope(exc: Exception) -> str | None:
    """Gemini ghi tên hạn mức trong lỗi 429 (vd GenerateRequestsPerDayPerProjectPerModel-FreeTier). Chỉ đọc tên, không ghi log."""
    text = str(exc)
    if "PerDay" in text or "per day" in text.lower():
        return "day"
    if "PerMinute" in text or "per minute" in text.lower():
        return "minute"
    return None


# ADR-042: thời điểm gọi gần nhất của từng mô hình, dùng chung mọi GeminiProvider trong tiến trình (Tutor + soạn bài
# dùng chung một khóa nên chung hạn mức 15 lượt/phút).
_pace_lock = threading.Lock()
_last_call: dict[str, float] = {}


def _finish_reason(resp: Any) -> str | None:
    try:
        reason = resp.candidates[0].finish_reason
    except (AttributeError, IndexError, TypeError):
        return None
    if reason is None:
        return None
    return str(getattr(reason, "name", reason)).rsplit(".", 1)[-1]


class GeminiProvider:
    def __init__(self, *, api_key: str, model: str, fallback_model: str | None = None, timeout_s: float = 8.0,
                 client: Any | None = None, sleep: Callable[[float], None] = time.sleep,
                 temperature: float = 0.2, seed: int | None = None, min_interval_s: float = 0.0,
                 rate_wait_s: float = 0.0, clock: Callable[[], float] = time.monotonic):
        self.model, self.fallback_model, self.timeout_s, self._sleep = model, fallback_model, timeout_s, sleep
        # ADR-042, chỉ bật cho soạn bài (việc nền, không ai ngồi chờ): giãn các lần gọi cùng mô hình ít nhất `min_interval_s`
        # giây, và gặp 429 theo phút thì chờ `rate_wait_s` giây rồi thử lại CÙNG mô hình thay vì đốt mô hình dự phòng.
        # Tutor để 0 cả hai: học sinh đang chờ, chuyển mô hình dự phòng ngay như trước.
        self.min_interval_s, self.rate_wait_s, self._clock = min_interval_s, rate_wait_s, clock
        # Chạy đánh giá đặt temperature=0 và seed cố định để hai lần chạy so được với nhau (zip thầy G-25).
        self.temperature, self.seed = temperature, seed
        if client is None:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key,
                                  http_options=types.HttpOptions(timeout=int(timeout_s * 1000)))
        self._client = client  # không giữ khóa trên đối tượng

    def __repr__(self) -> str:
        return f"GeminiProvider(model={self.model!r}, fallback={self.fallback_model!r})"

    def _call(self, model: str, system: str, user: str, schema: dict[str, Any], max_output_tokens: int | None = None):
        from google.genai import types

        return self._client.models.generate_content(
            model=model, contents=user,
            config=types.GenerateContentConfig(system_instruction=system, response_mime_type="application/json",
                                               response_json_schema=schema, temperature=self.temperature,
                                               seed=self.seed, max_output_tokens=max_output_tokens or 1024))

    def _pace(self, model: str) -> None:
        if self.min_interval_s <= 0:
            return
        with _pace_lock:
            wait = _last_call.get(model, -1e9) + self.min_interval_s - self._clock()
        if wait > 0:
            self._sleep(wait)

    def _mark(self, model: str) -> None:
        with _pace_lock:
            _last_call[model] = self._clock()

    def generate(self, system: str, user: str, schema: dict[str, Any], max_output_tokens: int | None = None) -> LLMResult:
        start = time.perf_counter()
        plan = [self.model, self.fallback_model or self.model]
        last, scope, attempt, waited = "unavailable", None, 0, False
        i = 0
        while i < len(plan):
            model = plan[i]
            attempt += 1
            self._pace(model)
            try:
                self._mark(model)
                resp = self._call(model, system, user, schema, max_output_tokens)
                usage = getattr(resp, "usage_metadata", None)
                text = resp.text or ""
                if not text:
                    raise LLMUnavailable("blocked", attempts=attempt)
                return LLMResult(text, model, getattr(usage, "prompt_token_count", None),
                                 getattr(usage, "candidates_token_count", None),
                                 int((time.perf_counter() - start) * 1000), attempt, _finish_reason(resp))
            except LLMUnavailable:
                raise
            except Exception as exc:  # SDK, httpx: nhiều loại lỗi
                code = _status(exc)
                name = type(exc).__name__.lower()
                is_timeout = "timeout" in name or "timeout" in str(exc).lower()[:80]
                last = "timeout" if is_timeout else ("rate_limited" if code == 429 else "unavailable")
                scope = _rate_scope(exc) if code == 429 else None
                # Chỉ ghi loại lỗi và mã HTTP: không ghi nội dung lỗi (có thể chứa URL/khóa) hay câu hỏi của người học.
                log.warning("gemini_error model=%s attempt=%d reason=%s status=%s scope=%s type=%s",
                            model, attempt, last, code, scope, type(exc).__name__)
                if code == 429 and scope != "day" and self.rate_wait_s > 0:
                    if waited:
                        break   # đã chờ một lần mà vẫn quá nhanh: dừng, không đốt mô hình dự phòng
                    waited = True
                    self._sleep(self.rate_wait_s)
                    continue    # thử lại cùng mô hình
                if not (is_timeout or code in (429, 503)) or i == len(plan) - 1:
                    break
                self._sleep(1.0)
                i += 1
        raise LLMUnavailable(last, attempts=attempt, scope=scope)


@dataclass
class FakeProvider:
    """Trả lần lượt các câu soạn sẵn (chuỗi JSON, hàm (system, user) → chuỗi, hoặc Exception). Ghi lại mọi lời gọi để test kiểm payload."""

    script: Sequence[Any] = ()
    model: str = "fake-llm"
    calls: list[tuple[str, str]] = field(default_factory=list)

    def generate(self, system: str, user: str, schema: dict[str, Any], max_output_tokens: int | None = None) -> LLMResult:
        self.calls.append((system, user))
        i = len(self.calls) - 1
        item = self.script[i] if i < len(self.script) else (self.script[-1] if self.script else "{}")
        if isinstance(item, Exception):
            raise item
        if callable(item):
            item = item(system, user)
        return LLMResult(item, self.model, len(user) // 4, len(item) // 4, 1)


@dataclass
class CallCounter:
    """Bọc một provider trong MỘT yêu cầu, cộng số lần gọi HTTP thật (cả lần lỗi, cả mô hình dự phòng) để ghi vào tin nhắn
    Tutor (ADR-042). Trước đây Tutor đếm mỗi tin nhắn là 1 lượt dù có vòng soạn lại."""

    inner: Any
    http: int = 0

    @property
    def model(self) -> str:
        return self.inner.model

    def generate(self, system: str, user: str, schema: dict[str, Any], max_output_tokens: int | None = None) -> LLMResult:
        try:
            res = self.inner.generate(system, user, schema, max_output_tokens)
        except LLMUnavailable as exc:
            self.http += max(1, exc.attempts)
            raise
        self.http += max(1, res.attempts)
        return res


def get_provider(cfg, *, authoring: bool = False) -> LLMProvider | None:
    """`authoring=True`: soạn bài chạy nền, giãn lượt gọi (gói miễn phí 15 lượt/phút → 1 lượt mỗi 4,5 giây) và chờ khi 429
    theo phút (ADR-042)."""
    if not cfg.ai_enabled or not cfg.gemini_api_key:
        return None
    extra = {"min_interval_s": 4.5, "rate_wait_s": 30.0} if authoring else {}
    return GeminiProvider(api_key=cfg.gemini_api_key, model=cfg.gemini_model,
                          fallback_model=cfg.gemini_fallback_model, timeout_s=cfg.ai_timeout_seconds, **extra)
