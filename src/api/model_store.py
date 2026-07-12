"""Loads all Phase 2-4 artifacts once at API startup — API is stateless per request, but models
are loaded into memory once (TECHNICAL_ARCHITECTURE.md §2.3).
"""

import json
from pathlib import Path

import joblib

from src.classification.interpretability import TermInterpreter
from src.retrieval.ask import AskPipeline

MODELS_DIR = Path("models")
DATA_DIR = Path("data/processed")


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

        # Retrieval/summarization models are the heaviest to load (bart-large-cnn, MiniLM) — load
        # once here rather than per-request.
        self.ask_pipeline = AskPipeline(top_k=5)

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
