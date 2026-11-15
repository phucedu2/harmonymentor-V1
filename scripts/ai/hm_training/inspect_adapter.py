"""One-question, locally generated TutorAnswer JSON (GPU for 4-bit base model).

Standalone smoke test only. Never bypass existing HarmonyMentor guardrail in API.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "backend"))

DEFAULT_MODEL = "unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=DEFAULT_MODEL)
    ap.add_argument("--adapter", type=Path, required=True)
    ap.add_argument("--question", default="Cmaj7 khac C7 o dau?")
    args = ap.parse_args()
    import torch
    from peft import PeftModel
    from unsloth import FastLanguageModel
    from app.ai.tutor.schema import parse_answer

    base, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.base, max_seq_length=1024, load_in_4bit=True,
    )
    model = PeftModel.from_pretrained(base, str(args.adapter))
    FastLanguageModel.for_inference(model)
    messages = [
        {"role": "system", "content": "Return only TutorAnswer JSON. Do not invent citations or music facts."},
        {"role": "user", "content": "LESSON_CHUNKS: []\nENGINE_FACTS: []\nQUESTION: " + args.question},
    ]
    ids = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, return_tensors="pt"
    ).to(model.device)
    with torch.inference_mode():
        generated = model.generate(input_ids=ids, max_new_tokens=300, do_sample=False,
                                   pad_token_id=tokenizer.eos_token_id)
    raw = tokenizer.decode(generated[0][ids.shape[-1]:], skip_special_tokens=True)
    print(raw)
    print("TutorAnswer valid JSON:", parse_answer(raw) is not None)
    print("NOTE: JSON validity does not imply accuracy, grounding or Engine verification")


if __name__ == "__main__":
    main()
