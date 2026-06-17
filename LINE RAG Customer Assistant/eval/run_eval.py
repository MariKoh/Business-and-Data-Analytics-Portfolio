"""Lightweight offline evaluation harness.

Runs the eval set through the live RAG chain and scores:
  * grounding accuracy  — did the bot correctly answer vs. escalate?
  * keyword recall      — did grounded answers contain expected facts?

This is the 'model evaluation / monitoring' signal the JD asks for, kept simple
and dependency-light. Swap in ragas (faithfulness, answer-relevancy) for a
deeper LLM-graded eval when an eval budget is available.

Usage:  python -m eval.run_eval
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, ".")

from src.rag_chain import answer_question  # noqa: E402

EVAL_FILE = Path("eval/eval_questions.jsonl")


def main() -> None:
    cases = [json.loads(line) for line in EVAL_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]

    grounding_ok = 0
    keyword_ok = 0
    keyword_total = 0

    for c in cases:
        res = answer_question(c["question"])

        if res.grounded == c["should_be_grounded"]:
            grounding_ok += 1

        if c["should_be_grounded"] and c["expected_keywords"]:
            keyword_total += 1
            if any(kw in res.answer for kw in c["expected_keywords"]):
                keyword_ok += 1

        flag = "OK " if res.grounded == c["should_be_grounded"] else "MISS"
        print(f"[{flag}] grounded={res.grounded!s:5}  {c['question']}")

    n = len(cases)
    print("\n--- Eval summary ---")
    print(f"Grounding accuracy : {grounding_ok}/{n} ({grounding_ok / n:.0%})")
    if keyword_total:
        print(f"Keyword recall     : {keyword_ok}/{keyword_total} ({keyword_ok / keyword_total:.0%})")


if __name__ == "__main__":
    main()
