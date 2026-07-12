"""T3.1-T3.3 — embed, cluster, and auto-label the unlabeled ticket corpus.

Pipeline: sentence-transformer embeddings (all-MiniLM-L6-v2, same model as the classification
upgrade for consistency) -> UMAP (to a low-dim space for HDBSCAN, and separately to 2D for the
Cluster Explorer scatter layout) -> HDBSCAN (chosen over k-means per
TECHNICAL_ARCHITECTURE.md §2.2: no k needed, models noise explicitly as cluster -1) -> auto-label
each cluster with its top TF-IDF terms.

Writes data/processed/clusters.json — the artifact the API/frontend read for the Cluster
Explorer and Dashboard "Flagged clusters" panel.

Run: python -m src.clustering.cluster
"""

import json
from pathlib import Path

import hdbscan
import numpy as np
import pandas as pd
import umap
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score

DATA_DIR = Path("data/processed")
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
MIN_CLUSTER_SIZE = 25
MIN_SAMPLES = 5
TOP_TERMS_PER_CLUSTER = 6
SEED = 42


def top_terms_for_cluster(texts: list[str], all_texts: list[str], top_k: int) -> list[str]:
    """TF-IDF fit on the full corpus, terms ranked by mean TF-IDF weight within this cluster."""
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1, max_features=5000)
    vectorizer.fit(all_texts)
    matrix = vectorizer.transform(texts)
    mean_weights = np.asarray(matrix.mean(axis=0)).ravel()
    top_idx = np.argsort(-mean_weights)[:top_k]
    feature_names = np.array(vectorizer.get_feature_names_out())
    return [term for term, weight in zip(feature_names[top_idx], mean_weights[top_idx]) if weight > 0]


def run() -> None:
    df = pd.read_csv(DATA_DIR / "twitter_support.csv")
    texts = df["ticket_text"].tolist()

    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    embeddings = embedder.encode(texts, show_progress_bar=True, batch_size=64)

    # Low-dim projection for clustering (HDBSCAN struggles in raw 384-dim embedding space).
    reducer_cluster = umap.UMAP(n_components=10, random_state=SEED, metric="cosine")
    embedding_cluster_space = reducer_cluster.fit_transform(embeddings)

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="leaf",
    )
    labels = clusterer.fit_predict(embedding_cluster_space)

    # Separate 2D projection for the scatter/constellation visualization.
    reducer_2d = umap.UMAP(n_components=2, random_state=SEED, metric="cosine")
    embedding_2d = reducer_2d.fit_transform(embeddings)

    df["cluster_id"] = labels
    df["x"] = embedding_2d[:, 0]
    df["y"] = embedding_2d[:, 1]

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = int((labels == -1).sum())
    print(f"Found {n_clusters} clusters, {n_noise} noise points out of {len(df)} tickets")

    # Silhouette score over clustered (non-noise) points only, in the same space HDBSCAN
    # clustered in — noise points have no assigned cluster so aren't meaningful here.
    clustered_mask = labels != -1
    if n_clusters >= 2 and clustered_mask.sum() > n_clusters:
        silhouette = float(
            silhouette_score(embedding_cluster_space[clustered_mask], labels[clustered_mask])
        )
    else:
        silhouette = None
    print(f"Silhouette score (clustered points only): {silhouette}")

    clusters = []
    for cluster_id in sorted(set(labels)):
        if cluster_id == -1:
            continue
        cluster_df = df[df["cluster_id"] == cluster_id]
        terms = top_terms_for_cluster(
            cluster_df["ticket_text"].tolist(), texts, TOP_TERMS_PER_CLUSTER
        )
        label = " / ".join(terms[:3]) if terms else f"cluster_{cluster_id}"
        clusters.append(
            {
                "cluster_id": int(cluster_id),
                "label": label,
                "top_terms": terms,
                "size": int(len(cluster_df)),
                "centroid": {
                    "x": float(cluster_df["x"].mean()),
                    "y": float(cluster_df["y"].mean()),
                },
                "sample_ticket_ids": cluster_df["ticket_id"].head(10).tolist(),
            }
        )

    clusters.sort(key=lambda c: -c["size"])

    output = {
        "embedding_model": EMBEDDING_MODEL_NAME,
        "min_cluster_size": MIN_CLUSTER_SIZE,
        "n_clusters": n_clusters,
        "n_noise": n_noise,
        "n_tickets": len(df),
        "silhouette_score": silhouette,
        "clusters": clusters,
        "tickets": df[["ticket_id", "ticket_text", "cluster_id", "x", "y"]].to_dict(orient="records"),
    }

    out_path = DATA_DIR / "clusters.json"
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} ({n_clusters} clusters)")


if __name__ == "__main__":
    run()
