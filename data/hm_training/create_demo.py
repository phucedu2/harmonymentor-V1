"""Create 6 ORIGINAL, UNAPPROVED samples. For code workflow demonstration only.

Before real training, replace with 200+ professionally reviewed and rights-cleared examples.
"""
import json
from pathlib import Path

OUT = Path(__file__).with_name("examples.demo.jsonl")
SYS = (
    "B\u1ea1n l\u00e0 tr\u1ee3 gi\u1ea3ng nh\u1ea1c l\u00fd c\u1ee7a HarmonyMentor. "
    "Tr\u1ea3 l\u1eddi b\u1eb1ng JSON TutorAnswer, tr\u00edch d\u1eabn ch\u1ec9 t\u1eeb LESSON_CHUNKS, "
    "kh\u00f4ng t\u1ef1 suy \u0111o\u00e1n c\u00e1c n\u1ed1t."
)


def segment(lesson, block, title, text):
    return [{"lesson_id": lesson, "block_id": block, "title": title, "text": text}]


def row(id, group, split, q, reply, chunks, claims=None, hint=0, intent="concept", acts=None):
    citations = [{k: c[k] for k in ("lesson_id", "block_id", "title")} for c in chunks]
    answer = {"reply": reply, "citations": citations, "engine_claims": claims or [],
              "hint_level": hint, "suggested_actions": acts or [], "intent": intent}
    user = "MODE: " + ("explain_error" if intent == "explain_error" else "chat") + "\n"
    user += "LESSON_CHUNKS: " + json.dumps(chunks, ensure_ascii=False) + "\n"
    user += "ENGINE_FACTS: " + json.dumps(claims or [], ensure_ascii=False) + "\n"
    user += "QUESTION: " + q
    return {"id": id, "group_id": group, "split": split, "source_id": "DEMO-ORIGINAL-V1",
            "reviewed_by_human": False, "rights_cleared": False,
            "allowed_block_ids": [c["block_id"] for c in chunks],
            "messages": [{"role": "system", "content": SYS},
                         {"role": "user", "content": user},
                         {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)}]}


def claim(symbol, notes):
    return {"tool": "get_chord_tones", "args": {"symbol": symbol}, "result": notes}


b01 = segment("L01", "L01-B08", "5. H\u1ee3p \u00e2m ba n\u1ed1t",
              "H\u1ee3p \u00e2m ba tr\u01b0\u1edfng d\u1ef1ng t\u1eeb 1, 3 tr\u01b0\u1edfng v\u00e0 5 \u0111\u00fang.")
b02 = segment("L02", "L02-B05", "4. H\u1ee3p \u00e2m b\u1ea3y",
              "maj7 d\u00f9ng qu\u00e3ng b\u1ea3y tr\u01b0\u1edfng; 7 d\u00f9ng qu\u00e3ng b\u1ea3y th\u1ee9.")
b03 = segment("L03", "L03-B02", "1. Ba ch\u1ee9c n\u0103ng", "V7 c\u00f3 xu h\u01b0\u1edbng v\u1ec1 I.")
b04 = segment("L04", "L04-B06", "5. Voice leading", "B th\u01b0\u1eddng d\u1eabn l\u00ean C, F d\u1eabn xu\u1ed1ng E.")

rows = [
    row("demo-001", "triad-major", "train",
        "H\u1ee3p \u00e2m C tr\u01b0\u1edfng g\u1ed3m nh\u1eefng n\u1ed1t n\u00e0o?",
        "C tr\u01b0\u1edfng c\u00f3 ba n\u1ed1t C, E, G. B\u1ea1n c\u00f3 th\u1ec3 \u0111\u00e1nh t\u1eebng n\u1ed1t tr\u00ean piano.",
        b01, [claim("C", "C E G")]),
    row("demo-002", "triad-minor", "train",
        "V\u00ec sao h\u1ee3p \u00e2m Dm l\u00e0 h\u1ee3p \u00e2m th\u1ee9?",
        "Dm s\u1eed d\u1ee5ng D, F, A; n\u1ed1t F t\u1ea1o qu\u00e3ng ba th\u1ee9 v\u1edbi n\u1ed1t g\u1ed1c D.",
        b01, [claim("Dm", "D F A")]),
    row("demo-003", "no-evidence", "train",
        "Fugue l\u00e0 g\u00ec?",
        "Kho b\u00e0i h\u1ecdc \u0111ang truy xu\u1ea5t ch\u01b0a c\u00f3 t\u00e0i li\u1ec7u v\u1ec1 fugue; m\u00ecnh kh\u00f4ng \u0111o\u00e1n n\u1ed9i dung.",
        []),
    row("demo-004", "hint-first", "train",
        "G\u1ee3i \u00fd m\u1ee9c 1: c\u00e1ch d\u1ef1ng h\u1ee3p \u00e2m Dm?",
        "H\u00e3y ki\u1ec3m tra qu\u00e3ng ba: h\u1ee3p \u00e2m th\u1ee9 c\u1ea7n m3 t\u1eeb n\u1ed1t g\u1ed1c. T\u1ef1 \u0111\u1ebfm ba n\u1eeda cung tr\u01b0\u1edbc nh\u00e9.",
        b01, [], hint=1, intent="explain_error"),
    row("demo-005", "seventh-comparison", "dev",
        "Cmaj7 kh\u00e1c C7 \u1edf \u0111i\u1ec3m n\u00e0o?",
        "Hai h\u1ee3p \u00e2m chung C E G. Cmaj7 c\u00f3 B; C7 c\u00f3 Bb, kh\u00e1c lo\u1ea1i qu\u00e3ng b\u1ea3y.",
        b02, [claim("Cmaj7", "C E G B"), claim("C7", "C E G Bb")]),
    row("demo-006", "dominant-resolution", "test",
        "T\u1ea1i sao G7 th\u01b0\u1eddng v\u1ec1 Cmaj7?",
        "Trong gi\u1ecdng C tr\u01b0\u1edfng, G7 gi\u1eef vai tr\u00f2 \u00e1t. B c\u00f3 xu h\u01b0\u1edbng l\u00ean C, F xu\u1ed1ng E.",
        b03 + b04, [claim("G7", "G B D F")]),
]

with OUT.open("w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=True) + "\n")
print("Wrote", OUT, "rows", len(rows))
