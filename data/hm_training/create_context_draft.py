"""Generate ORIGINAL DRAFT examples for human review, not production training.
No network, model, database or application startup. Existing demo is untouched.
Run from repo root with python -B data/hm_training/create_context_draft.py.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts/ai/hm_training"))
from app.ai.tutor.prompt import SYSTEM, chat_prompt, explain_prompt
from app.ai.tutor.context import prompt_context
from app.ai.tutor.guardrail import run_tool
from prepare_dataset import validate, verify_engine


def fact(tool, **args):
    result, raw = run_tool(tool, args)
    if result is None:
        raise ValueError(f"No supported fact for {tool}: {args}: {raw}")
    return {"tool": tool, "args": args, "result": result}


def roman(key, chord, mode):
    return fact("get_roman_numeral", key=key, chord=chord, mode=mode)


def build_rows():
    rows = []
    def add(group, split, question, reply, facts=(), claims=None, context=None, hint=0):
        if hint:
            prompt = explain_prompt(question, ["WRONG_ROMAN"], "Số La Mã", hint, [], {}, facts)
        else:
            prompt = chat_prompt(question, [], {}, [], facts, None, [])
        prompt += prompt_context(context)
        answer = {"reply": reply, "citations": [], "engine_claims": list(facts if claims is None else claims),
                  "hint_level": hint, "suggested_actions": [], "intent": "explain_error" if hint else "concept"}
        rows.append({"id": f"context-{len(rows)+1:03}", "group_id": group, "split": split,
                     "source_id": "HM-ORIGINAL-CONTEXT-DRAFT-V1", "reviewed_by_human": False,
                     "rights_cleared": False, "allowed_block_ids": [],
                     "review": {"question": question, "context": context or {}, "facts": list(facts),
                                "provenance": "Original assistant-authored draft; engine-derived numerical facts; human pedagogical and rights review pending."},
                     "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt},
                                  {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)}]})
    a_minor = {"selected_root": "A", "selected_chord": "Am", "selected_key": "A", "mode": "natural_minor"}
    c_major = {"selected_root": "A", "selected_chord": "Am", "selected_key": "C", "mode": "major"}
    add("roman-major", "train", "Am trong C trưởng là bậc mấy?", "Trong giọng C trưởng, Am là vi.", [roman("C", "Am", "major")])
    add("roman-natural", "train", "Hợp âm này là bậc mấy?", "Trong giọng A thứ tự nhiên, Am là i.", [roman("A", "Am", "natural_minor")], context=a_minor)
    add("explicit-over-ui", "train", "Am trong C trưởng là bậc mấy?", "Trong giọng C trưởng, Am là vi. Mình dùng giọng bạn nêu rõ trong câu hỏi, không dùng giọng đang chọn trên giao diện.", [roman("C", "Am", "major")], context=a_minor)
    add("explicit-over-ui", "train", "Am trong A thứ tự nhiên là bậc mấy?", "Trong giọng A thứ tự nhiên, Am là i. Mình ưu tiên giọng bạn nêu rõ trong câu hỏi.", [roman("A", "Am", "natural_minor")], context=c_major)
    add("missing-context", "train", "Am trong A thứ là bậc mấy?", "Bạn muốn xét A thứ tự nhiên, thứ hòa thanh hay thứ giai điệu? Mình cần làm rõ dạng giọng thứ trước khi phân tích.")
    add("missing-context", "train", "Hợp âm này là bậc mấy?", "Bạn đang chọn nốt gốc A, nhưng chưa xác định hợp âm và giọng. Bạn muốn xét hợp âm nào trong giọng nào?", context={"selected_root": "A"})
    value, raw = run_tool("get_roman_numeral", {"key": "A", "chord": "E7", "mode": "natural_minor"})
    if value is not None or raw.get("ok"):
        raise ValueError("E7 must not be a supported diatonic chord in A natural minor")
    outside = {"tool": "get_roman_numeral", "args": {"key": "A", "chord": "E7", "mode": "natural_minor"}, "error": raw.get("error")}
    add("outside-selected-scale", "train", "E7 trong A thứ tự nhiên có sai nhạc lý không?", "E7 nằm ngoài tập hợp âm thuận giọng A thứ tự nhiên mà engine đang xét. Điều đó không có nghĩa E7 sai nhạc lý; mình chưa gán số La Mã cho trường hợp này trong phạm vi hiện tại.", [outside], claims=[])
    add("roman-natural", "train", "Bm7b5 trong A thứ tự nhiên là bậc mấy?", "Trong giọng A thứ tự nhiên, Bm7b5 là iiø7.", [roman("A", "Bm7b5", "natural_minor")])
    ex = "Trong giọng C trưởng, Am7 mang số La Mã nào? Người học vừa nhập i7 và được chấm chưa đúng."
    correct = [roman("C", "Am7", "major")]
    add("roman-error-hints", "train", ex, "Hãy đọc lại giọng mà đề bài yêu cầu trước khi phân tích. Giọng đang chọn trong chatbot không thay đổi giọng của bài tập.", correct, claims=[], context=a_minor, hint=1)
    add("roman-error-hints", "train", ex, "Bạn hãy xác định vị trí nốt gốc của hợp âm trong giọng đề bài, rồi kiểm tra ký hiệu cho hợp âm bảy. Chưa cần đổi lựa chọn trong chatbot.", correct, claims=[], context=a_minor, hint=2)
    add("roman-error-hints", "train", ex, "Trong giọng C trưởng, Am7 là vi7. Mình chấm theo giọng C trưởng của đề bài, không theo giọng đang chọn trong chatbot.", correct, context=a_minor, hint=3)
    add("roman-major", "train", "Dm trong C trưởng là bậc mấy?", "Trong giọng C trưởng, Dm là ii.", [roman("C", "Dm", "major")])
    add("seventh-alias", "dev", "Cmaj7 trong A thứ tự nhiên là bậc mấy?", "Trong giọng A thứ tự nhiên, Cmaj7 là IIImaj7.", [roman("A", "Cmaj7", "natural_minor")])
    add("seventh-alias", "dev", "Fmaj7 trong A thứ tự nhiên là bậc mấy?", "Trong giọng A thứ tự nhiên, Fmaj7 là VImaj7.", [roman("A", "Fmaj7", "natural_minor")])
    add("missing-evidence", "test", "Hãy giải thích cấu trúc fugue theo bài học của mình.", "Mình chưa có đoạn học liệu về fugue trong ngữ cảnh hiện tại, nên chưa thể giải thích dựa trên khóa học. Bạn có thể cung cấp đoạn tài liệu cần học không?")
    add("missing-evidence", "test", "Bài học nói gì về hòa âm tứ độ?", "Ngữ cảnh hiện tại chưa có đoạn bài học về hòa âm tứ độ. Mình không suy đoán nội dung bài học khi thiếu tài liệu.")
    return rows


def main():
    rows = build_rows()
    summary = validate(rows, allow_demo=True)
    verify_engine(rows)
    base = Path(__file__).parent
    out = base / "examples.context.draft.jsonl"
    if out.exists() or (base / "CONTEXT-DRAFT-REVIEW.md").exists():
        raise SystemExit("STOP: draft already exists; do not overwrite human review")
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    lines = ["# Mẫu huấn luyện nháp — cần người duyệt", "", "16 mẫu gốc đề xuất, không phải dữ liệu đã duyệt. Train/dev/test = 12/2/2 chỉ để thử quy trình; không đủ đánh giá chất lượng. Chưa train hoặc tải model.", "", "Các con số nhạc lý được engine kiểm tra trong phạm vi nhận diện được. Lời giải, độ phù hợp, quyền sử dụng vẫn cần người duyệt. Không tự đánh dấu reviewed_by_human/rights_cleared.", "", "## Cách duyệt", "Đọc câu hỏi, ngữ cảnh và câu trả lời. Ghi Giữ / Sửa / Loại cùng lý do. Xác nhận riêng nguồn và quyền sử dụng. Không cần tự viết JSON."]
    for r in rows:
        answer = json.loads(r["messages"][-1]["content"])
        review = r["review"]
        lines += ["", f"## {r['id']} — {r['group_id']} ({r['split']})", f"**Câu hỏi/đề:** {review['question']}", f"**Ngữ cảnh UI:** `{json.dumps(review['context'], ensure_ascii=False)}`", f"**Mức gợi ý:** {answer['hint_level']}", f"**Dữ kiện đầu vào:** `{json.dumps(review['facts'], ensure_ascii=False)}`", f"**Trả lời dự kiến:** {answer['reply']}", "- [ ] Nội dung đúng và trả lời đúng câu hỏi", "- [ ] Mức gợi ý phù hợp; không lộ đáp án sớm", "- [ ] Nguồn và quyền sử dụng được xác nhận", "**Quyết định / sửa đề nghị:** …"]
    (base / "CONTEXT-DRAFT-REVIEW.md").write_text("\n\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    print("Recognizable engine claims checked; human review remains pending.")


if __name__ == "__main__":
    main()
