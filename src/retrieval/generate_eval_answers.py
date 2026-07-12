"""Generates AskPipeline answers for the T4.4 test set, for manual usefulness rating.

Run: python -m src.retrieval.generate_eval_answers
"""

import json
from pathlib import Path

from src.retrieval.ask import AskPipeline
from src.retrieval.eval_retrieval import TEST_SET

REPORT_DIR = Path("reports/retrieval")


def main() -> None:
    pipeline = AskPipeline(top_k=5)
    results = []
    for case in TEST_SET:
        result = pipeline.ask(case["question"])
        results.append({"question": case["question"], **result})
        print(f"Q: {case['question']}\nA: {result['answer']}\n")

    (REPORT_DIR / "generated_answers.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
