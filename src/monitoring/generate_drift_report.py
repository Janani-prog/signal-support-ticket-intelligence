"""T8.1-T8.2 — Evidently AI drift comparison: two held-out splits (no shift) vs. a genuine
domain-shifted corpus.

Two reports, deliberately chosen to show the drift tool distinguishing normal sampling noise
from a real distribution shift:

1. `drift_no_shift_test_split_a_vs_b.html` — banking77 test set, randomly split in half.
   Expected: little/no significant drift. A sanity check that the tool doesn't cry wolf.
2. `drift_domain_shift_twitter_vs_test.html` — the Twitter customer-support corpus vs. banking77
   test, simulating what monitoring would show if incoming production traffic started looking
   like a different ticket population (different domain, different writing style). Expected:
   real, substantial drift. This is the scenario MONITORING.md's retraining triggers are written
   against.

**Methodological note (found during Phase 8, not assumed away):** the reference set for both
comparisons is banking77 **test** data, not train. An earlier version of this script used train
as reference and found "drift" in the model's `confidence` feature even between train and test —
but that wasn't real drift, it was the classifier being more confident on the exact data it was
fit on (a classic overfitting-adjacent artifact). Using train as a drift-monitoring reference
would produce a false "confidence drift" signal on *any* new data, even perfectly in-domain data,
which would make the monitor useless (crying wolf constantly). Both reference and "no shift"
comparison sets here are held out from training, so any confidence difference reflects genuine
model behavior change, not a training-encoding artifact.

Features monitored (not raw text — Evidently's tabular drift detection needs numeric/categorical
columns): text length, word count, and the deployed classifier's own predicted label + confidence
on each ticket. Prediction-distribution drift is often the more actionable signal in practice
(model behavior changing) alongside input-feature drift.

Run: python -m src.monitoring.generate_drift_report
"""

import json
from pathlib import Path

import joblib
import pandas as pd
from evidently.metric_preset import DataDriftPreset
from evidently.report import Report

DATA_DIR = Path("data/processed")
MODELS_DIR = Path("models")
REPORT_DIR = Path("monitoring/reports")

CATEGORICAL_FEATURES = ["predicted_label"]
NUMERICAL_FEATURES = ["text_length", "word_count", "confidence"]


def build_feature_frame(df: pd.DataFrame, pipeline) -> pd.DataFrame:
    texts = df["ticket_text"].tolist()
    proba = pipeline.predict_proba(texts)
    classes = pipeline.named_steps["clf"].classes_
    predicted_idx = proba.argmax(axis=1)

    return pd.DataFrame(
        {
            "text_length": df["ticket_text"].str.len(),
            "word_count": df["ticket_text"].str.split().str.len(),
            "predicted_label": [classes[i] for i in predicted_idx],
            "confidence": proba.max(axis=1),
        }
    )


def run_drift_report(reference: pd.DataFrame, current: pd.DataFrame, out_path: Path) -> dict:
    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference, current_data=current)
    report.save_html(str(out_path))

    result = report.as_dict()
    drift_metric = next(
        m for m in result["metrics"] if m["metric"] == "DatasetDriftMetric"
    )["result"]
    return {
        "dataset_drift": drift_metric["dataset_drift"],
        "n_drifted_columns": drift_metric["number_of_drifted_columns"],
        "n_columns": drift_metric["number_of_columns"],
        "drift_share": drift_metric["number_of_drifted_columns"] / drift_metric["number_of_columns"],
    }


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    pipeline = joblib.load(MODELS_DIR / "baseline_tfidf_logreg.joblib")

    banking_test = pd.read_csv(DATA_DIR / "banking77_test.csv")
    twitter = pd.read_csv(DATA_DIR / "twitter_support.csv")

    # Both held out from training — a clean same-distribution comparison with no
    # train/test-confidence artifact (see module docstring).
    test_shuffled = banking_test.sample(frac=1, random_state=42).reset_index(drop=True)
    split_a, split_b = test_shuffled.iloc[: len(test_shuffled) // 2], test_shuffled.iloc[len(test_shuffled) // 2 :]

    reference = build_feature_frame(split_a, pipeline)

    summary = {}

    print("Generating: banking77 test split A vs. split B (expected: little/no drift)...")
    current_split_b = build_feature_frame(split_b, pipeline)
    summary["no_shift_test_split_a_vs_b"] = run_drift_report(
        reference, current_split_b, REPORT_DIR / "drift_no_shift_test_split_a_vs_b.html"
    )
    print(f"  {summary['no_shift_test_split_a_vs_b']}")

    print("Generating: Twitter corpus vs. banking77 test (expected: real domain drift)...")
    current_twitter = build_feature_frame(twitter, pipeline)
    summary["domain_shift_twitter_vs_test"] = run_drift_report(
        reference, current_twitter, REPORT_DIR / "drift_domain_shift_twitter_vs_test.html"
    )
    print(f"  {summary['domain_shift_twitter_vs_test']}")

    (REPORT_DIR / "drift_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nWrote reports + drift_summary.json to {REPORT_DIR}/")


if __name__ == "__main__":
    main()
