"""Compares this run's metrics against MONITORING.md §3's documented thresholds and reports
whether any were breached — used by .github/workflows/monitoring.yml to decide whether to open
an alert issue.

Scoping note (also in MONITORING.md §5): this checks the *pipeline re-run from scratch*, not live
production traffic — `monitoring/logs/predictions.jsonl` lives on the deployed container's
ephemeral filesystem and isn't reachable from CI. Re-running from source data weekly is a
genuine regression check (it catches an accuracy drop from a dependency update, a code change, or
an upstream dataset change) even though it isn't literally "watching production."

Deliberately NOT checked here: retrieval hit rate. Found the hard way on this workflow's first
real run: `src/retrieval/eval_retrieval.py`'s ground truth is tied to a specific clustering run's
cluster IDs, which shift when clustering is re-run (even with a fixed seed — see README's
Clustering results note on cross-platform variance). Gating on it here produced a false breach
(13.3% vs. the real, human-verified 100%) from ground-truth drift, not a real regression. Kept as
a manual, monthly check per MONITORING.md §4 instead.

Exits 0 with no output if everything is within threshold. Exits 1 and prints a breach summary
(consumed by the GitHub Actions step that opens an issue) otherwise.

Run: python -m src.monitoring.check_thresholds
"""

import json
import sys
from pathlib import Path

MODELS_DIR = Path("models")
REPORT_DIR = Path("monitoring/reports")

# Thresholds from MONITORING.md §3 — keep these in sync if one changes.
MIN_ACCURACY = 0.85
MAX_NO_SHIFT_DRIFT_SHARE = 0.0  # two held-out splits of the same data should show zero drift


def main() -> int:
    breaches = []

    classifier_metrics = json.loads((MODELS_DIR / "baseline_tfidf_logreg_metrics.json").read_text())
    accuracy = classifier_metrics["test_accuracy"]
    if accuracy < MIN_ACCURACY:
        breaches.append(f"Classifier accuracy {accuracy:.1%} is below the {MIN_ACCURACY:.0%} threshold.")

    drift_summary = json.loads((REPORT_DIR / "drift_summary.json").read_text())
    no_shift_share = drift_summary["no_shift_test_split_a_vs_b"]["drift_share"]
    if no_shift_share > MAX_NO_SHIFT_DRIFT_SHARE:
        breaches.append(
            f"No-shift baseline (two held-out splits of the same data) showed "
            f"{no_shift_share:.0%} drift — expected 0%. This suggests a pipeline or data problem, "
            f"not real drift (see MONITORING.md §2's methodology note)."
        )

    if breaches:
        print("MONITORING THRESHOLD BREACH:\n" + "\n".join(f"- {b}" for b in breaches))
        return 1

    print("All monitored metrics within threshold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
