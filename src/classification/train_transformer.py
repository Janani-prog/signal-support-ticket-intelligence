"""T2.2 — transformer-based classifier upgrade, tracked in MLflow.

Implementation choice: frozen sentence-transformer embeddings (all-MiniLM-L6-v2) + a
LogisticRegression head, rather than a fully fine-tuned DistilBERT. Both are explicitly sanctioned
by TECHNICAL_ARCHITECTURE.md §2.2 ("distilbert-base-uncased fine-tuned, or frozen embeddings +
classifier head"). Frozen embeddings were chosen because full fine-tuning of DistilBERT on CPU
for 77 classes is impractically slow for a $0/CPU-only portfolio deployment (the doc's own stated
constraint), while embeddings + a linear head trains in seconds and still gives a real
transformer-representation upgrade over TF-IDF's bag-of-words features. This choice is recorded
here and in reports/classification/evaluation.md — it is a documented implementation choice
within an explicitly allowed option, not a deviation from the doc.

Run: python -m src.classification.train_transformer
"""

import json
from pathlib import Path

import joblib
import mlflow
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

DATA_DIR = Path("data/processed")
MODELS_DIR = Path("models")
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
LOGREG_PARAMS = dict(max_iter=2000, C=5.0, class_weight="balanced")


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    train = pd.read_csv(DATA_DIR / "banking77_train.csv")
    test = pd.read_csv(DATA_DIR / "banking77_test.csv")
    return train, test


def train() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    train_df, test_df = load_data()

    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    X_train = embedder.encode(
        train_df["ticket_text"].tolist(), show_progress_bar=True, batch_size=64
    )
    X_test = embedder.encode(test_df["ticket_text"].tolist(), show_progress_bar=True, batch_size=64)

    clf = LogisticRegression(**LOGREG_PARAMS)

    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment("signal-classification")

    with mlflow.start_run(run_name="minilm-embeddings-logreg"):
        mlflow.log_param("embedding_model", EMBEDDING_MODEL_NAME)
        mlflow.log_params({f"logreg__{k}": v for k, v in LOGREG_PARAMS.items()})

        clf.fit(X_train, train_df["label_name"])
        preds = clf.predict(X_test)

        acc = accuracy_score(test_df["label_name"], preds)
        macro_f1 = f1_score(test_df["label_name"], preds, average="macro")
        weighted_f1 = f1_score(test_df["label_name"], preds, average="weighted")

        mlflow.log_metric("test_accuracy", acc)
        mlflow.log_metric("test_macro_f1", macro_f1)
        mlflow.log_metric("test_weighted_f1", weighted_f1)

        clf_path = MODELS_DIR / "transformer_embed_logreg.joblib"
        joblib.dump(clf, clf_path)
        mlflow.log_artifact(str(clf_path))

        print(f"test_accuracy={acc:.4f} test_macro_f1={macro_f1:.4f} test_weighted_f1={weighted_f1:.4f}")

    metrics_path = MODELS_DIR / "transformer_embed_logreg_metrics.json"
    metrics_path.write_text(
        json.dumps(
            {
                "embedding_model": EMBEDDING_MODEL_NAME,
                "test_accuracy": acc,
                "test_macro_f1": macro_f1,
                "test_weighted_f1": weighted_f1,
            },
            indent=2,
        )
    )
    print(f"Saved classifier head to {clf_path}, metrics to {metrics_path}")


if __name__ == "__main__":
    train()
