"""T2.1 — TF-IDF + Logistic Regression baseline classifier, tracked in MLflow.

Run: python -m src.classification.train_baseline
"""

import json
from pathlib import Path

import joblib
import mlflow
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline

DATA_DIR = Path("data/processed")
MODELS_DIR = Path("models")

TFIDF_PARAMS = dict(ngram_range=(1, 2), min_df=2, max_features=20000, sublinear_tf=True)
LOGREG_PARAMS = dict(max_iter=2000, C=5.0, class_weight="balanced")


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    train = pd.read_csv(DATA_DIR / "banking77_train.csv")
    test = pd.read_csv(DATA_DIR / "banking77_test.csv")
    return train, test


def train() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    train_df, test_df = load_data()

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
            ("clf", LogisticRegression(**LOGREG_PARAMS)),
        ]
    )

    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment("signal-classification")

    with mlflow.start_run(run_name="tfidf-logreg-baseline"):
        mlflow.log_params({f"tfidf__{k}": v for k, v in TFIDF_PARAMS.items()})
        mlflow.log_params({f"logreg__{k}": v for k, v in LOGREG_PARAMS.items()})

        pipeline.fit(train_df["ticket_text"], train_df["label_name"])

        preds = pipeline.predict(test_df["ticket_text"])
        acc = accuracy_score(test_df["label_name"], preds)
        macro_f1 = f1_score(test_df["label_name"], preds, average="macro")
        weighted_f1 = f1_score(test_df["label_name"], preds, average="weighted")

        mlflow.log_metric("test_accuracy", acc)
        mlflow.log_metric("test_macro_f1", macro_f1)
        mlflow.log_metric("test_weighted_f1", weighted_f1)

        model_path = MODELS_DIR / "baseline_tfidf_logreg.joblib"
        joblib.dump(pipeline, model_path)
        mlflow.log_artifact(str(model_path))

        print(f"test_accuracy={acc:.4f} test_macro_f1={macro_f1:.4f} test_weighted_f1={weighted_f1:.4f}")

    metrics_path = MODELS_DIR / "baseline_tfidf_logreg_metrics.json"
    metrics_path.write_text(
        json.dumps(
            {"test_accuracy": acc, "test_macro_f1": macro_f1, "test_weighted_f1": weighted_f1}, indent=2
        )
    )
    print(f"Saved model to {model_path}, metrics to {metrics_path}")


if __name__ == "__main__":
    train()
