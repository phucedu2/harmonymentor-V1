"""HarmonyMentor offline QLoRA chat contract; no change to the live provider."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .guardrail import check_declared, scan_reply
from .intent import INTENTS
from .bm25 import strip_accents
from .schema import LLM_SCHEMA, parse_answer
from .semantic_checks import asks_lesson, safe_lesson_abstention, conflicting_degree_statements

FIELDS = tuple(LLM_SCHEMA['required'])
CITE = ('lesson_id', 'block_id', 'title')
CLAIM = ('tool', 'args', 'result')
BLOCK = re.compile(r'^<<<HM_DATA kind="([A-Z_]+)">>>\n(.*?)\n<<<HM_END>>>$', re.M | re.S)
MAX_SEQ, MAX_NEW, MAX_REPLY = 1280, 256, 360


def _fold(text: str) -> str:
    return strip_accents(text or "").lower()


def _behavior_issues(obj: dict, question: str, prompt: str, citations: list[dict]) -> list[str]:
    """Deterministic safety checks for failures that JSON/schema validation cannot see."""
    q = _fold(question)
    reply = _fold(obj.get("reply", ""))
    issues = []
    # Health, diagnosis, finance and unrelated requests must never be answered as music concepts.
    if any(term in q for term in ("dau dau", "trieu chung", "chan doan benh", "chan doan giup", "chan doan cho", "dieu tri benh", "bao hiem", "tai chinh")):
        if obj.get("intent") != "out_of_scope":
            issues.append("scope_intent")
    # A request explicitly grounded in the lesson must fail closed when no lesson evidence was supplied.
    if asks_lesson(question) and not citations and not safe_lesson_abstention(obj.get("reply", "")):
        issues.append("ungrounded_lesson_answer")
    return issues
CONTRACT = f'''

Chỉ xuất một JSON theo thứ tự: {', '.join(FIELDS)}. Không markdown hay chữ sau dấu đóng. reply: tiếng Việt, tối đa {MAX_REPLY} ký tự; hint_level: số nguyên 0–3; suggested_actions: mảng chuỗi; intent: {', '.join(INTENTS)}. Hỏi nhạc lý hoặc hỏi lại vì thiếu dữ kiện: concept, không dùng question.
Nếu hỏi theo bài học mà thiếu trích đoạn phù hợp: nói rõ chưa có đủ học liệu và đề nghị gửi đoạn bài; không suy đoán. Thiếu giọng, dạng giọng, hợp âm hoặc nốt để tính: hỏi đúng thông tin còn thiếu. Yêu cầu ngoài âm nhạc: từ chối lịch sự với out_of_scope. Không có nguồn thì citations và engine_claims là [].
Chỉ trích đúng lesson_id, block_id, title của LESSON_CHUNKS đã dùng. Chỉ khai tool, args, result có thật trong ENGINE_FACTS; không ghi verified. Không nêu đáp án ở mức gợi ý 1–2.'''


def compact(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def project(obj, fields):
    return {k: obj[k] for k in fields}


def strict_json(text):
    def pairs(items):
        out = dict(items)
        if len(out) != len(items):
            raise ValueError('Duplicate JSON key')
        return out

    def invalid(_):
        raise ValueError('Non-JSON constant')
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def evidence(prompt, kind, fields):
    matches = [x for k, x in BLOCK.findall(prompt) if k == kind]
    if len(matches) > 1:
        raise ValueError('Ambiguous evidence block')
    rows = strict_json(matches[0]) if matches else []
    if not isinstance(rows, list) or len(rows) > 16:
        raise ValueError('Invalid evidence list')
    # Error facts are valid input evidence but are not declarable engine claims.
    return [project(row, fields) for row in rows if isinstance(row, dict) and all(k in row for k in fields)]


def validate_output(raw, prompt):
    """Strict wrapper around the backend parser; returns issues, not repaired output."""
    try:
        obj = strict_json(raw)
    except (ValueError, TypeError, RecursionError):
        return None, ['json']
    if not isinstance(obj, dict) or set(obj) != set(FIELDS):
        return None, ['schema']
    if obj['intent'] not in INTENTS:
        return None, ['intent']
    if (not all(isinstance(obj[k], list) for k in ('citations', 'engine_claims', 'suggested_actions'))
            or type(obj['hint_level']) is not int or '\ufffd' in raw
            or 'HM-7F3A-CANARY' in raw.upper()):
        return None, ['schema']
    def valid_str(s, limit):
        return (isinstance(s, str) and bool(s.strip()) and len(s) <= limit
                and not any(0xD800 <= ord(c) <= 0xDFFF or c == '\ufffd' for c in s)
                and 'HM-7F3A-CANARY' not in s.upper())
    if not valid_str(obj['reply'], MAX_REPLY) or not all(valid_str(a, 100) for a in obj['suggested_actions']):
        return None, ['schema']
    for k, fields in (('citations', CITE), ('engine_claims', CLAIM)):
        if any(not isinstance(x, dict) or set(x) != set(fields) for x in obj[k]):
            return None, ['schema']
    if any(not isinstance(x['args'], dict) or not all(isinstance(v, str) and v for v in x['args'].values())
           for x in obj['engine_claims']):
        return None, ['schema']
    try:
        parsed = parse_answer(raw)
        cites = evidence(prompt, 'LESSON_CHUNKS', CITE)
        facts = evidence(prompt, 'ENGINE_FACTS', CLAIM)
    except (ValueError, TypeError, KeyError, AttributeError):
        return None, ['schema_or_evidence']
    if parsed is None:
        return None, ['schema']
    issues = []
    if (any(c not in cites for c in obj['citations'])
            or len({c.block_id for c in parsed.citations}) != len(parsed.citations)):
        issues.append('citations')
    declared = check_declared(parsed.engine_claims)
    scanned = scan_reply(parsed.reply)
    def key(c):
        return c.tool, tuple(sorted(c.args.items())), c.engine
    declared_keys = {key(c) for c in declared}
    if (any(c not in facts for c in obj['engine_claims'])
            or any(c.status != 'verified' for c in declared + scanned)
            or any(key(c) not in declared_keys for c in scanned)):
        issues.append('engine')
    # The backend prose scanner may miss short forms such as "bậc V7" or "bậc 2".
    question = next((s for k, s in BLOCK.findall(prompt) if k == 'QUESTION'), '')
    issues.extend(_behavior_issues(obj, question, prompt, obj['citations']))
    degree_request = (re.search(r'\bbậc\s+(?:nào|mấy)\b|\bsố\s+la\s+mã\s+(?:nào|gì)\b', question, re.I)
                      and (re.search(r'\bhợp\s+âm\b|\bgiọng\b|\bsố\s+la\s+mã\b', question, re.I)
                           or re.search(r'\b[A-G](?:[#b])?(?:m|maj|min|dim|aug|sus|add)?(?:7|9|11|13)?\b', question)))
    roman = r'[IViv]{1,5}(?:maj7|M7|ø7|°7|7)?'
    degree_statement = (re.search(r'\b(?:bậc\s+(?:[1-7]|' + roman + r')|hợp\s+âm\s+thứ\s+[1-7])\b', parsed.reply, re.I)
                        or re.fullmatch(roman + r'[.!]?', parsed.reply.strip()))
    if degree_request and not any(f['tool'] == 'get_roman_numeral' for f in facts) and not degree_statement:
        if '?' not in parsed.reply or not re.search(r'giọng|thứ|trưởng|giong|thu|truong', parsed.reply, re.I):
            issues.append('missing_context_clarification')
    if degree_request and degree_statement and not any(c.tool == 'get_roman_numeral' for c in declared):
        issues.append('engine_missing_claim' if any(f['tool'] == 'get_roman_numeral' for f in facts)
                      else 'context_unsubstantiated_degree')
    elif degree_request and degree_statement:
        from .engine_query import engine_answer
        expected = [f for f in engine_answer(question).facts if f.get('tool') == 'get_roman_numeral']
        matching = [f for f in expected if any(
            c.tool == 'get_roman_numeral' and c.args == f['args'] and c.claimed == f['result']
            and c.status == 'verified' for c in declared)
            and any(all(g.get(k) == f.get(k) for k in CLAIM) for g in facts)]
        if not matching:
            issues.append('context_unsubstantiated_degree')
        # Match the service's conservative exact-numeral requirement.
        elif not any(re.search(r'(?<![A-Za-z0-9])' + re.escape(f['result']) + r'(?![A-Za-z0-9])', parsed.reply)
                     and not conflicting_degree_statements(parsed.reply, f['result']) for f in matching):
            issues.append('degree_answer_mismatch')
    hint = re.match(r'^MODE: explain_error\nHINT_LEVEL: ([0-3])(?:\n|$)', prompt)
    if hint and (parsed.intent != 'explain_error' or parsed.hint_level != int(hint[1])
                 or (parsed.hint_level in (1, 2) and parsed.engine_claims)):
        issues.append('hint')
    if parsed.intent == 'out_of_scope' and (parsed.citations or parsed.engine_claims):
        issues.append('intent')
    return parsed, issues


def chat_prefix(tokenizer, messages):
    if [m.get('role') for m in messages] != ['system', 'user']:
        raise ValueError('Expected system + user')
    prompt = messages[1]['content']
    question = next((text for kind, text in BLOCK.findall(prompt) if kind == 'QUESTION'), '')
    guidance = ''
    folded_question = _fold(question)
    if any(term in folded_question for term in ("dau dau", "trieu chung", "chan doan benh", "chan doan giup", "chan doan cho", "dieu tri benh", "bao hiem", "tai chinh")):
        guidance = '\nĐây là yêu cầu ngoài phạm vi trợ giảng âm nhạc. Chỉ từ chối lịch sự với intent out_of_scope; không trả lời nội dung y tế, bảo hiểm hoặc tài chính.'
    elif (re.search(r"\bbậc\s+(?:nào|mấy)\b|\bsố\s+la\s+mã\s+(?:nào|gì)\b", question, re.I)
            and (re.search(r"\bhợp\s+âm\b|\bgiọng\b|\bsố\s+la\s+mã\b", question, re.I)
                 or re.search(r"\b[A-G](?:[#b])?(?:m|maj|min|dim|aug|sus|add)?(?:7|9|11|13)?\b", question))):
        roman_facts = [f for f in evidence(prompt, 'ENGINE_FACTS', CLAIM) if f['tool'] == 'get_roman_numeral']
        if roman_facts:
            guidance = '\nNếu reply nêu bậc/số La Mã, bắt buộc chép nguyên vẹn, đúng chữ hoa/thường và hậu tố, giá trị result của get_roman_numeral tương ứng từ ENGINE_FACTS vào reply và chép đủ đối tượng đó vào engine_claims. Không thay result bằng riêng chữ số Ả Rập hoặc bỏ hậu tố; không nêu bậc khác.'
        else:
            guidance = '\nKhông có kết quả số La Mã đã xác minh. Chỉ hỏi lại giọng và loại giọng (trưởng/thứ); không nêu bất kỳ bậc hoặc giọng suy đoán nào.'
    elif asks_lesson(question) and not evidence(prompt, 'LESSON_CHUNKS', CITE):
        guidance = '\nKhông có trích đoạn học liệu để trả lời theo nguồn. Chỉ nói: Mình chưa có trích đoạn bài học để xác minh. Bạn hãy gửi trích đoạn nhé. Không khẳng định bài học có hoặc không có nội dung, không thêm ví dụ.'
    turns = [dict(messages[0], content=messages[0]['content'] + CONTRACT + guidance), dict(messages[1])]
    prefix = tokenizer.apply_chat_template(turns, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    # This verified Qwen template inserts an empty think block for a completed assistant turn.
    # Place the same fixed (unsupervised) block on the generation side if needed.
    marker = 'HM_TEMPLATE_PREFIX_CHECK_5029'
    shadow = tokenizer.apply_chat_template(turns + [dict(role='assistant', content=marker)], tokenize=False,
                                           add_generation_prompt=False, enable_thinking=False)
    if shadow.count(marker) != 1:
        raise ValueError('Ambiguous assistant boundary')
    trained_prefix = shadow.split(marker, 1)[0]
    if trained_prefix not in (prefix, prefix + '<think>\n\n</think>\n\n'):
        raise ValueError('Unsupported assistant prefix')
    return turns, trained_prefix


def encode(tokenizer, row, max_length, label):
    messages = row['messages']
    turns, prefix = chat_prefix(tokenizer, messages[:-1])
    raw = messages[-1]['content']
    _, issues = validate_output(raw, messages[1]['content'])
    if issues or messages[-1].get('role') != 'assistant':
        raise ValueError(f'{label}: rejected target ({issues})')
    answer = project(strict_json(raw), FIELDS)
    answer['citations'] = [project(c, CITE) for c in answer['citations']]
    answer['engine_claims'] = [project(c, CLAIM) for c in answer['engine_claims']]
    target = compact(answer)
    eos, eid = tokenizer.eos_token, tokenizer.eos_token_id
    if not eos or tokenizer(eos, add_special_tokens=False)['input_ids'] != [eid]:
        raise ValueError(f'{label}: invalid EOS')
    full = tokenizer.apply_chat_template(turns + [dict(role='assistant', content=target)], tokenize=False,
                                         add_generation_prompt=False, enable_thinking=False)
    text = prefix + target + eos
    if not full.startswith(text) or full[len(text):].strip():
        raise ValueError(f'{label}: training/inference template mismatch')
    context = tokenizer(prefix, add_special_tokens=False)['input_ids']
    ids = tokenizer(text, add_special_tokens=False)['input_ids']
    tail = ids[len(context):]
    if (not context or ids[:len(context)] != context or not tail or len(tail) > MAX_NEW
            or len(ids) > max_length or tail[-1] != eid
            or any(x in tokenizer.all_special_ids for x in tail[:-1])
            or tokenizer.decode(tail[:-1], clean_up_tokenization_spaces=False) != target):
        raise ValueError(f'{label}: token boundary, supervised EOS or token budget mismatch')
    return dict(input_ids=ids, labels=[-100] * len(context) + tail,
                assistant_masks=[0] * len(context) + [1] * len(tail))


def grammar(prompt):
    """JSON grammar with fields in train order and source-bound metadata."""
    import regex
    ws = r'[ \t\n\r]{0,8}'
    comma = ws + ',' + ws
    def obj(items):
        return r'\{' + ws + comma.join(atom(k) + ws + ':' + ws + v for k, v in items) + ws + r'\}'
    def atom(value):
        if isinstance(value, dict):
            return obj([(k, atom(v)) for k, v in value.items()])
        return regex.escape(compact(value))
    def alt(patterns):
        return '(?:' + '|'.join(dict.fromkeys(patterns)) + ')' if patterns else ''
    def arr(pattern, n):
        content = '(?:' + pattern + '(?:' + comma + pattern + '){0,' + str(n - 1) + '})?' if pattern else ''
        return r'\[' + ws + content + ws + r'\]'
    def string(n):
        return r'"(?:[^"\\\x00-\x1f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4})){1,' + str(n) + r'}"'
    cites = evidence(prompt, 'LESSON_CHUNKS', CITE)
    facts = evidence(prompt, 'ENGINE_FACTS', CLAIM)
    fields = (string(MAX_REPLY), arr(alt([atom(c) for c in cites]), 8), arr(alt([atom(c) for c in facts]), 12),
              '[0-3]', arr(string(100), 5), alt([atom(i) for i in INTENTS]))
    return regex.compile(ws + obj(list(zip(FIELDS, fields))) + ws)


@dataclass(frozen=True)
class Result:
    raw: str
    issues: tuple[str, ...]
    tokens: int


def generate(model, tokenizer, messages, *, constrained=True):
    """Deterministic offline generation. Invalid/budget-exhausted outputs fail closed."""
    import torch
    from transformers import GenerationConfig, LogitsProcessorList
    _, prefix = chat_prefix(tokenizer, messages)
    prompt = messages[1]['content']
    x = tokenizer(prefix, add_special_tokens=False, return_tensors='pt').input_ids.to(model.device)
    width = x.shape[-1]
    cap = min(MAX_NEW, MAX_SEQ - width)
    if cap < 32:
        return Result('', ('context_budget',), 0)
    eos = tokenizer.eos_token_id
    special = set(tokenizer.all_special_ids)
    pattern = grammar(prompt) if constrained else None
    blocked = False

    def process(ids, scores):
        nonlocal blocked
        tokens = ids[0, width:].tolist()
        text = tokenizer.decode(tokens, clean_up_tokenization_spaces=False)
        masked = torch.full_like(scores, -float('inf'))
        try:
            if not pattern.fullmatch(text, timeout=0.05):
                top = scores[0].topk(min(128, scores.shape[-1])).indices.tolist()
                allowed = [j for j in top if j not in special and j < len(tokenizer)]
                continuations = tokenizer.batch_decode([tokens + [j] for j in allowed], clean_up_tokenization_spaces=False)
                for token, nxt in zip(allowed, continuations):
                    if nxt != text and pattern.fullmatch(nxt, partial=True, timeout=0.05):
                        masked[0, token] = 0.0
                        return masked
                blocked = True
        except TimeoutError:
            blocked = True
        masked[0, eos] = 0.0
        return masked

    config = GenerationConfig(max_new_tokens=cap, do_sample=False, eos_token_id=eos,
                              pad_token_id=tokenizer.pad_token_id, use_cache=True)
    with torch.inference_mode():
        y = model.generate(input_ids=x, attention_mask=torch.ones_like(x), generation_config=config,
                           logits_processor=LogitsProcessorList([process] if constrained else []))
    ids = y[0, width:].tolist()
    ended = bool(ids and ids[-1] == eos)
    raw = tokenizer.decode(ids[:-1] if ended else ids, clean_up_tokenization_spaces=False).strip()
    _, issues = validate_output(raw, prompt)
    if blocked or not ended:
        issues.insert(0, 'decoder_blocked' if blocked else 'output_budget')
    return Result(raw, tuple(issues), len(ids))
