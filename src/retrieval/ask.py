"""End-to-end Ask-a-Question pipeline: retrieve top-k tickets, synthesize a cited answer.

This is the `/ask`-equivalent logic required to work end-to-end before Phase 5 wraps it in the
API (T4's acceptance criterion). See src/retrieval/retrieve.py and src/retrieval/summarize.py
for the individual stages.

Run: python -m src.retrieval.ask "your question here"
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.retrieval.retrieve import TicketRetriever
from src.retrieval.summarize import AnswerSynthesizer


class AskPipeline:
    def __init__(self, top_k: int = 5):
        self.retriever = TicketRetriever()
        self.synthesizer = AnswerSynthesizer()
        self.top_k = top_k

    def ask(self, question: str) -> dict:
        sources = self.retriever.search(question, top_k=self.top_k)
        answer = self.synthesizer.synthesize(question, sources)
        return {
            "answer": answer,
            "sources": [
                {"ticket_id": s["ticket_id"], "snippet": s["ticket_text"], "score": s["score"]}
                for s in sources
            ],
        }


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What are people saying about flight delays?"
    pipeline = AskPipeline()
    result = pipeline.ask(question)
    print(f"Q: {question}\n")
    print(f"A: {result['answer']}\n")
    print("Sources:")
    for i, s in enumerate(result["sources"]):
        print(f"  [{i + 1}] {s['ticket_id']} (score={s['score']:.3f})  {s['snippet'][:90]}")
