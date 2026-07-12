"""Ingests the banking77 dataset (labeled) for the classification pipeline (T1.1).

banking77 (PolyAI, HF Hub "banking77") is a single-domain intent-classification dataset:
~13k customer banking queries across 77 fine-grained intents. Used as the labeled corpus for
Phase 2 classification.

Idempotent: re-running overwrites data/processed/banking77_{train,test}.csv from scratch.

Run: python -m src.data.ingest_banking77
"""

from pathlib import Path

import pandas as pd
from datasets import load_dataset

from src.data.cleaning import clean_dataframe

PROCESSED_DIR = Path("data/processed")


def ingest() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    ds = load_dataset("banking77")
    label_names = ds["train"].features["label"].names

    for split in ("train", "test"):
        df = ds[split].to_pandas()
        df["label_name"] = df["label"].map(lambda i: label_names[i])
        df = df.rename(columns={"text": "ticket_text"})
        df = clean_dataframe(df, "ticket_text")
        out_path = PROCESSED_DIR / f"banking77_{split}.csv"
        df.to_csv(out_path, index=False)
        print(f"Wrote {len(df):,} rows to {out_path}")

    labels_path = PROCESSED_DIR / "banking77_labels.csv"
    pd.DataFrame({"label": range(len(label_names)), "label_name": label_names}).to_csv(
        labels_path, index=False
    )
    print(f"Wrote {len(label_names)} label names to {labels_path}")


if __name__ == "__main__":
    ingest()
