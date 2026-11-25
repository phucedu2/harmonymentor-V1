"""Validated, optional UI hints; never an exercise answer key."""
import json
from ...contracts.ai import ChatContextIn
from pydantic import ValidationError


def clean_context(context):
    try:
        return ChatContextIn.model_validate(context or {}).model_dump(exclude_none=True)
    except (ValidationError, TypeError):
        return {}


def prompt_context(context):
    from .prompt import block
    ctx = clean_context(context)
    if not ctx:
        return ""
    return "\n\n" + block("UI_CONTEXT", json.dumps({
        "hints": ctx,
        "rule": "Ngữ cảnh giao diện chỉ là gợi ý. Câu hỏi nêu rõ nốt/hợp âm/giọng được ưu tiên; nốt gốc không phải giọng. Không dùng ngữ cảnh để sửa đáp án bài tập."
    }, ensure_ascii=False))
