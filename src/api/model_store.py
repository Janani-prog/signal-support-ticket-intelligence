"""Loads all Phase 2-4 artifacts once at API startup — API is stateless per request, but models
are loaded into memory once (TECHNICAL_ARCHITECTURE.md §2.3).
"""

import gc
import json
from pathlib import Path

import joblib
import pandas as pd
import torch

from src.classification.interpretability import TermInterpreter
from src.retrieval.ask import AskPipeline

# Free-tier memory (Render's 512MB cap) is the binding constraint, not CPU throughput — a single
# torch thread avoids each worker thread allocating its own buffers. See also the Dockerfile's
# OMP_NUM_THREADS/MALLOC_ARENA_MAX env vars for the same reasoning applied at the process level.
torch.set_num_threads(1)

MODELS_DIR = Path("models")
DATA_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")


class ModelStore:
    def __init__(self):
        classifier_path = MODELS_DIR / "baseline_tfidf_logreg.joblib"
        clusters_path = DATA_DIR / "clusters.json"

        if not classifier_path.exists():
            raise FileNotFoundError(
                f"{classifier_path} not found — run `python -m src.classification.train_baseline` first."
            )
        if not clusters_path.exists():
            raise FileNotFoundError(
                f"{clusters_path} not found — run `python -m src.clustering.cluster` first."
            )

        self.classifier_pipeline = joblib.load(classifier_path)
        self.interpreter = TermInterpreter(pipeline=self.classifier_pipeline)

        clusters_data = json.loads(clusters_path.read_text(encoding="utf-8"))
        self.n_clusters = clusters_data["n_clusters"]
        self.n_noise = clusters_data["n_noise"]
        self.n_tickets = clusters_data["n_tickets"]
        self.silhouette_score = clusters_data["silhouette_score"]
        self.clusters_by_id = {c["cluster_id"]: c for c in clusters_data["clusters"]}
        self.ticket_text_by_id = {t["ticket_id"]: t["ticket_text"] for t in clusters_data["tickets"]}

        # Retrieval's embedding model (all-MiniLM-L6-v2) is the heaviest thing loaded here —
        # load once at startup rather than per-request. Summarization is extractive
        # (scikit-learn only, no neural model — see src/retrieval/summarize.py) specifically to
        # stay within Render's free-tier 512MB RAM cap.
        self.ask_pipeline = AskPipeline(top_k=5)

        self.stats = self._compute_stats()
        gc.collect()  # stats computation loads 3 CSVs into pandas; release that memory promptly

    def _compute_stats(self) -> dict:
        """Real aggregate numbers for the dashboard, computed from artifacts already on disk —
        no fabricated metrics (no resolution-rate/sentiment/time-series fields exist in either
        source dataset, so those Stitch-mockup tiles are intentionally not reproduced here; see
        README's Phase 6 notes).
        """
        banking_train = pd.read_csv(DATA_DIR / "banking77_train.csv")
        banking_test = pd.read_csv(DATA_DIR / "banking77_test.csv")
        twitter = pd.read_csv(DATA_DIR / "twitter_support.csv")

        category_counts = banking_train["label_name"].value_counts()
        total_banking = len(category_counts.index) and int(category_counts.sum())
        category_breakdown = [
            {"category": cat, "count": int(count), "pct": round(100 * count / total_banking, 1)}
            for cat, count in category_counts.head(8).items()
        ]

        classifier_metrics = json.loads(
            (MODELS_DIR / "baseline_tfidf_logreg_metrics.json").read_text(encoding="utf-8")
        )

        hit_rate_path = REPORTS_DIR / "retrieval" / "retrieval_hit_rate.json"
        retrieval = json.loads(hit_rate_path.read_text(encoding="utf-8")) if hit_rate_path.exists() else None

        return {
            "total_tickets": len(banking_train) + len(banking_test) + len(twitter),
            "banking77_tickets": len(banking_train) + len(banking_test),
            "twitter_tickets": len(twitter),
            "classifier_accuracy": classifier_metrics["test_accuracy"],
            "classifier_macro_f1": classifier_metrics["test_macro_f1"],
            "n_clusters": self.n_clusters,
            "n_noise": self.n_noise,
            "silhouette_score": self.silhouette_score,
            "retrieval_hit_rate": retrieval["hit_rate"] if retrieval else None,
            "category_breakdown": category_breakdown,
        }

    def classify(self, text: str) -> tuple[str, float, list[dict]]:
        proba = self.classifier_pipeline.predict_proba([text])[0]
        classes = self.classifier_pipeline.named_steps["clf"].classes_
        best_idx = proba.argmax()
        category = classes[best_idx]
        confidence = float(proba[best_idx])
        top_terms = self.interpreter.top_terms(text, category)
        return category, confidence, top_terms

    def list_clusters(self) -> list[dict]:
        return sorted(self.clusters_by_id.values(), key=lambda c: -c["size"])

    def get_cluster(self, cluster_id: int) -> dict | None:
        cluster = self.clusters_by_id.get(cluster_id)
        if cluster is None:
            return None
        sample_tickets = [
            {"ticket_id": tid, "ticket_text": self.ticket_text_by_id.get(tid, "")}
            for tid in cluster["sample_ticket_ids"]
        ]
        return {**cluster, "sample_tickets": sample_tickets}


_store: ModelStore | None = None


def get_model_store() -> ModelStore:
    global _store
    if _store is None:
        _store = ModelStore()
    return _store
