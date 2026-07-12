"""T4.3 — synthesize retrieved tickets into a short, cited answer.

Model history: flan-t5-base was tried first and failed systematically (echoed its own prompt
template on 15/15 test questions — see reports/retrieval/evaluation.md). Switched to
bart-large-cnn, which worked well qualitatively (3.7/5 mean usefulness) — but bart-large-cnn's
weights alone are ~1.6GB in memory, and deploying to Render's free tier (512MB RAM cap) hit an
OOM crash before the app could even finish starting up. No realistic model-swap fixes that: even
a distilled variant (distilbart-cnn-6-6, ~230M params) is still roughly 900MB+ loaded, well over
budget once torch, sentence-transformers, and everything else sharing the same 512MB are counted.

**Switched to extractive multi-sentence summarization (TF-IDF + Maximal Marginal Relevance,
scikit-learn only, no neural model)** — selects the most query-relevant, least-redundant
sentences across the retrieved tickets. This isn't a downgrade in practice: the bart-large-cnn
evaluation in reports/retrieval/evaluation.md already found its output "reads as stitched-
together fragments rather than one smooth sentence" for this task, i.e. it wasn't buying much
real abstraction over extraction for 1.6GB of RAM. This approach uses a few KB of memory instead.
Material deviation from TECHNICAL_ARCHITECTURE.md §2.2 (which named flan-t5-base/bart-large-cnn),
flagged per CLAUDE.md's judgment clause; doc updated in place.
"""

import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

MAX_SENTENCES = 3
MMR_RELEVANCE_WEIGHT = 0.7  # higher = favor query-relevance; lower = favor diversity across sources
MIN_WORDS_PER_SENTENCE = 4

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> list[str]:
    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
    return sentences if sentences else [text.strip()]


class AnswerSynthesizer:
    def __init__(self, max_sentences: int = MAX_SENTENCES, relevance_weight: float = MMR_RELEVANCE_WEIGHT):
        self.max_sentences = max_sentences
        self.relevance_weight = relevance_weight

    def synthesize(self, question: str, sources: list[dict]) -> str:
        if not sources:
            return "No relevant tickets were found for this question."

        candidates = [
            sent
            for s in sources
            for sent in split_sentences(s["ticket_text"])
            if len(sent.split()) >= MIN_WORDS_PER_SENTENCE
        ]
        if not candidates:
            candidates = [s["ticket_text"] for s in sources]

        try:
            vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            doc_vectors = vectorizer.fit_transform([*candidates, question])
        except ValueError:
            # Degenerate case: candidates reduce to an empty vocabulary (e.g. all stopwords).
            return f'Regarding "{question}": {candidates[0]}'

        sentence_vectors = doc_vectors[:-1]
        question_vector = doc_vectors[-1]
        relevance = cosine_similarity(sentence_vectors, question_vector).ravel()

        selected: list[int] = []
        n_select = min(self.max_sentences, len(candidates))
        for _ in range(n_select):
            if not selected:
                scores = relevance.copy()
            else:
                redundancy = cosine_similarity(sentence_vectors, sentence_vectors[selected]).max(axis=1)
                scores = self.relevance_weight * relevance - (1 - self.relevance_weight) * redundancy
            for idx in selected:
                scores[idx] = -np.inf
            selected.append(int(np.argmax(scores)))

        selected.sort(key=lambda i: -relevance[i])
        summary = " ".join(candidates[i] for i in selected)
        return f'Regarding "{question}": {summary}'


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
