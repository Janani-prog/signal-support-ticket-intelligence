"""T2.4 — top contributing terms per prediction, for the Ticket Classifier UI screen.

Interpretability is computed from the TF-IDF + Logistic Regression baseline regardless of which
model is actually deployed for predictions (see reports/classification/evaluation.md for the
deployed-model decision): it's a linear model over sparse term features, so "top contributing
terms" are exact coefficient contributions, not a post-hoc approximation (e.g. LIME/SHAP) with
its own error surface. This matches the Stitch Classifier screen design (signed term weights like
+0.82 "refund"), and satisfies PRD F2's "not a black box" requirement directly.
"""

from pathlib import Path

import joblib
import numpy as np

MODELS_DIR = Path("models")


class TermInterpreter:
    def __init__(self, model_path: Path = MODELS_DIR / "baseline_tfidf_logreg.joblib", pipeline=None):
        if pipeline is None:
            pipeline = joblib.load(model_path)
        self.vectorizer = pipeline.named_steps["tfidf"]
        self.clf = pipeline.named_steps["clf"]
        self.feature_names = np.array(self.vectorizer.get_feature_names_out())

    def top_terms(self, text: str, predicted_label: str, top_k: int = 5) -> list[dict]:
        """Returns the top_k terms (by signed contribution) for `predicted_label` present in `text`."""
        class_idx = list(self.clf.classes_).index(predicted_label)
        coefs = self.clf.coef_[class_idx]

        x = self.vectorizer.transform([text])
        nz_idx = x.nonzero()[1]
        if len(nz_idx) == 0:
            return []

        contributions = x[0, nz_idx].toarray().ravel() * coefs[nz_idx]
        order = np.argsort(-np.abs(contributions))[:top_k]

        return [
            {"term": self.feature_names[nz_idx[i]], "weight": round(float(contributions[i]), 4)}
            for i in order
        ]


if __name__ == "__main__":
    interpreter = TermInterpreter()
    sample = "I was double charged for my subscription last month and I need a refund immediately."
    pipeline = joblib.load(MODELS_DIR / "baseline_tfidf_logreg.joblib")
    pred = pipeline.predict([sample])[0]
    print(f"Predicted: {pred}")
    for t in interpreter.top_terms(sample, pred):
        print(f"  {t['weight']:+.4f}  {t['term']!r}")
