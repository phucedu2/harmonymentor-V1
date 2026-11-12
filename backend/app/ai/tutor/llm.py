"""Nhà cung cấp LLM cho AI Tutor: Gemini khi bật AI, FakeProvider trong test (không gọi mạng).

Đề GĐ3 mục 3: hết giờ 15 giây, thử lại đúng 1 lần khi 429/503 (GĐ0 đã gặp 503 "high demand" thật với
gemini-3.6-flash), ghi token và độ trễ. Lần thử lại dùng mô hình dự phòng. Lỗi nào cũng thành
LLMUnavailable để dịch vụ chuyển sang câu trả lời dự phòng theo luật, không trả 500 cho người học."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, Sequence


class LLMUnavailable(RuntimeError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason  # timeout | rate_limited | unavailable | blocked


@dataclass(frozen=True)
class LLMResult:
    text: str
    model: str
    tokens_in: int | None
    tokens_out: int | None
    latency_ms: int
    attempts: int = 1


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


class GeminiProvider:
    def __init__(self, *, api_key: str, model: str, fallback_model: str | None = None, timeout_s: float = 15.0,
                 client: Any | None = None, sleep: Callable[[float], None] = time.sleep):
        self.model, self.fallback_model, self.timeout_s, self._sleep = model, fallback_model, timeout_s, sleep
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
                                               response_json_schema=schema, temperature=0.2,
                                               max_output_tokens=max_output_tokens or 1024))

    def generate(self, system: str, user: str, schema: dict[str, Any], max_output_tokens: int | None = None) -> LLMResult:
        start = time.perf_counter()
        models = [self.model, self.fallback_model or self.model]
        last = "unavailable"
        for attempt, model in enumerate(models, start=1):
            try:
                resp = self._call(model, system, user, schema, max_output_tokens)
                usage = getattr(resp, "usage_metadata", None)
                text = resp.text or ""
                if not text:
                    raise LLMUnavailable("blocked")
                return LLMResult(text, model, getattr(usage, "prompt_token_count", None),
                                 getattr(usage, "candidates_token_count", None),
                                 int((time.perf_counter() - start) * 1000), attempt)
            except LLMUnavailable:
                raise
            except Exception as exc:  # SDK, httpx: nhiều loại lỗi
                code = _status(exc)
                name = type(exc).__name__.lower()
                if "timeout" in name or "timeout" in str(exc).lower()[:80]:
                    last = "timeout"
                    break  # đã chờ 15 giây, không bắt người học chờ thêm 15 giây nữa
                last = "rate_limited" if code == 429 else "unavailable"
                if code not in (429, 503) or attempt == len(models):
                    break
                self._sleep(1.0)
        raise LLMUnavailable(last)


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


def get_provider(cfg) -> LLMProvider | None:
    if not cfg.ai_enabled or not cfg.gemini_api_key:
        return None
    return GeminiProvider(api_key=cfg.gemini_api_key, model=cfg.gemini_model,
                          fallback_model=cfg.gemini_fallback_model, timeout_s=cfg.ai_timeout_seconds)
