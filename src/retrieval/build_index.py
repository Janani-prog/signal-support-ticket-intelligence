"""T4.1 — build a FAISS vector index over the unlabeled ticket corpus.

Indexes twitter_support.csv (not banking77 — per TECHNICAL_ARCHITECTURE.md §2.1, the Twitter
corpus is the unlabeled "real ticket" set used for clustering/retrieval; banking77 is reserved
for the labeled classification task). Uses the same all-MiniLM-L6-v2 embedding model as
clustering/classification for consistency.

Implementation note: TECHNICAL_ARCHITECTURE.md §2.2 names "Chroma (or FAISS)" as the vector
store. Chroma was tried first but its Rust bindings segfaulted unpredictably on this Windows
environment even in minimal repro cases (bare `collection.add()` calls with no other libraries
loaded) — a native-library stability issue, not something fixable in this codebase. Switched to
FAISS, the doc's own named alternative. Flagged per CLAUDE.md's material-deviation clause and
noted in README.

FAISS only stores vectors, not metadata, so ticket text/ids are kept alongside in a parquet file
with matching row order. Both are gitignored — regenerate via this script.

Run: python -m src.retrieval.build_index
"""

from pathlib import Path

import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer

DATA_DIR = Path("data/processed")
INDEX_DIR = Path("data/processed/faiss_index")
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


def build() -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_DIR / "twitter_support.csv").reset_index(drop=True)

    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    embeddings = embedder.encode(
        df["ticket_text"].tolist(), show_progress_bar=True, batch_size=64
    ).astype("float32")

    # Normalize + inner product = cosine similarity, exact (flat) search — the corpus is small
    # enough (8k rows) that approximate indexing (IVF/HNSW) isn't needed for portfolio scale.
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, str(INDEX_DIR / "tickets.index"))
    df[["ticket_id", "ticket_text"]].to_parquet(INDEX_DIR / "tickets_meta.parquet", index=False)
    (INDEX_DIR / "embedding_model.txt").write_text(EMBEDDING_MODEL_NAME, encoding="utf-8")

    print(f"Indexed {index.ntotal} tickets into FAISS index at {INDEX_DIR}")


if __name__ == "__main__":
    build()
