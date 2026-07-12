"""Ingests the Twitter Customer Support dataset (unlabeled) for clustering/retrieval (T1.2).

Source: MohammadOthman/mo-customer-support-tweets-945k (HF Hub) — a restructured version of the
public "Customer Support on Twitter" corpus, as (customer request, agent response) pairs.

We keep only the customer-initiated `input` text as the "ticket" (the analog of an inbound
support ticket) and drop the agent `output`. The full corpus is ~945k rows; per
TECHNICAL_ARCHITECTURE.md's portfolio-scale scoping ("thousands, not millions"), we take a fixed,
seeded random sample so clustering/retrieval run in seconds-to-minutes on CPU, not hours. This is
a non-material implementation choice (sample size only), not a change to the dataset/source.

Idempotent: re-running overwrites data/processed/twitter_support.csv from scratch. The sample
seed is fixed so the output is reproducible.

Run: python -m src.data.ingest_twitter_support
"""

from pathlib import Path

from datasets import load_dataset

from src.data.cleaning import clean_dataframe

PROCESSED_DIR = Path("data/processed")
SAMPLE_SIZE = 8000
SEED = 42


def ingest() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    ds = load_dataset("MohammadOthman/mo-customer-support-tweets-945k")["train"]
    df = ds.to_pandas()[["input"]].rename(columns={"input": "ticket_text"})

    df = clean_dataframe(df, "ticket_text")
    # Drop very short remnants (e.g. a lone "[HANDLE]" after PII stripping) that add noise
    # without signal for clustering/retrieval.
    df = df[df["ticket_text"].str.split().str.len() >= 4].reset_index(drop=True)

    n = min(SAMPLE_SIZE, len(df))
    df = df.sample(n=n, random_state=SEED).reset_index(drop=True)
    df.insert(0, "ticket_id", [f"TW-{i:06d}" for i in range(len(df))])

    out_path = PROCESSED_DIR / "twitter_support.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df):,} rows (sampled from {ds.num_rows:,}) to {out_path}")


if __name__ == "__main__":
    ingest()
