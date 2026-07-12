"""T4.3 — synthesize retrieved tickets into a short, cited answer.

Model choice: bart-large-cnn (TECHNICAL_ARCHITECTURE.md §2.2's other named default), not
flan-t5-base. flan-t5-base was tried first and prompted to synthesize a cross-ticket theme, but
it systematically failed — across all 15 questions in the T4.4 test set, it echoed the prompt
template ("Multiple customers submitted the separate support messages below...") instead of
producing real content (see reports/retrieval/evaluation.md for the full before/after). This
isn't a prompt-tuning issue we worked around: it's a genuine capability limit of a 250M-param
instruction model on multi-document synthesis. bart-large-cnn is a real summarization model
(trained on CNN/DailyMail) rather than an instruction-follower, so it reliably produces
abstractive-ish content from the concatenated ticket text, and also loads ~13x faster
(~5s vs ~60s) and is not slower to run. Flagged per CLAUDE.md's material-deviation clause.
"""

from transformers import pipeline

MODEL_NAME = "facebook/bart-large-cnn"
MAX_SUMMARY_TOKENS = 80
MIN_SUMMARY_TOKENS = 20


class AnswerSynthesizer:
    def __init__(self, model_name: str = MODEL_NAME):
        self.pipe = pipeline("summarization", model=model_name, device=-1)

    def synthesize(self, question: str, sources: list[dict]) -> str:
        if not sources:
            return "No relevant tickets were found for this question."

        combined_text = " ".join(s["ticket_text"] for s in sources)
        # bart-large-cnn's max input is 1024 tokens; ~4 chars/token is a safe conservative estimate.
        combined_text = combined_text[:3500]

        result = self.pipe(
            combined_text,
            max_length=MAX_SUMMARY_TOKENS,
            min_length=MIN_SUMMARY_TOKENS,
            do_sample=False,
        )
        summary = result[0]["summary_text"].strip()
        return f"Regarding \"{question}\": {summary}"


if __name__ == "__main__":
    from src.retrieval.retrieve import TicketRetriever

    retriever = TicketRetriever()
    synthesizer = AnswerSynthesizer()

    question = "What are people saying about flight delays?"
    sources = retriever.search(question, top_k=5)
    answer = synthesizer.synthesize(question, sources)

    print(f"Q: {question}\n")
    print(f"A: {answer}\n")
    print("Sources:")
    for i, s in enumerate(sources):
        print(f"  [{i + 1}] {s['ticket_id']}  {s['ticket_text'][:90]}")
