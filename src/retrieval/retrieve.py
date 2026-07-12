"""T4.2 — top-k semantic search over the FAISS ticket index given a natural-language question."""

from pathlib import Path

import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer

INDEX_DIR = Path("data/processed/faiss_index")


class TicketRetriever:
    def __init__(self, index_dir: Path = INDEX_DIR):
        self.index = faiss.read_index(str(index_dir / "tickets.index"))
        self.meta = pd.read_parquet(index_dir / "tickets_meta.parquet")
        embedding_model = (index_dir / "embedding_model.txt").read_text(encoding="utf-8").strip()
        self.embedder = SentenceTransformer(embedding_model)

    def search(self, question: str, top_k: int = 5) -> list[dict]:
        query_vec = self.embedder.encode([question]).astype("float32")
        faiss.normalize_L2(query_vec)
        scores, indices = self.index.search(query_vec, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            row = self.meta.iloc[idx]
            results.append(
                {
                    "ticket_id": row["ticket_id"],
                    "ticket_text": row["ticket_text"],
                    "score": float(score),
                }
            )
        return results


if __name__ == "__main__":
    retriever = TicketRetriever()
    for r in retriever.search("what are people saying about checkout problems", top_k=5):
        print(f"{r['score']:.3f}  {r['ticket_id']}  {r['ticket_text'][:90]}")
