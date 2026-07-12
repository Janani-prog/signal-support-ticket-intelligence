# Classification Evaluation — Phase 2 (T2.3)

## Model comparison (banking77 test set, 3,079 tickets)

| Model | Accuracy | Macro F1 | Weighted F1 |
|---|---|---|---|
| Baseline: TF-IDF + Logistic Regression | 0.8925 | 0.8930 | 0.8929 |
| Upgrade: all-MiniLM-L6-v2 embeddings + Logistic Regression | 0.9302 | 0.9298 | 0.9298 |

The embedding-based upgrade scores +3.8% accuracy over the TF-IDF baseline — a real, non-trivial improvement from using pretrained semantic representations instead of bag-of-words features.

## Deployed model decision

**The TF-IDF + Logistic Regression baseline is the model deployed in the app**, despite scoring lower on aggregate accuracy. Reasoning:

- PRD F2 requires the Classifier screen to show "the top contributing terms/phrases (interpretability — not a black box)", and the Stitch design's Classifier screen displays exactly this: signed term weights (e.g. `+0.82 "refund"`).
- TF-IDF + Logistic Regression is a linear model over sparse term features, so its term-level explanations are *exact* coefficient contributions — not a post-hoc approximation. The embedding-based model's features are dense, uninterpretable vector dimensions; explaining its predictions at the term level would require a separate approximation method (e.g. LIME) that explains a *different* decision boundary than the one that actually produced the prediction — which would be misleading to show as "why the model decided this."
- The baseline is also faster (no embedding model to load) and lighter to serve on free-tier CPU hosting, at effectively no latency cost.
- The accuracy/F1 gap (3.8%) is real but not so large that it outweighs trading away genuine, PRD-required interpretability for a black-box-ish gain. If this were a pure accuracy-optimization task without an interpretability requirement, the embedding upgrade would be the better choice — that tradeoff is exactly why both are trained and compared here rather than only building one.

## Business-cost framing: which error type was optimized against

**False negatives on security/financial-risk categories are optimized against more heavily than false positives elsewhere.** A ticket about a lost/stolen card or a compromised account that gets misclassified into a routine queue delays response to a time-sensitive, financially risky issue — a materially worse outcome than, say, a routine balance inquiry being misrouted to a similar routine queue. Concretely:

- `LogisticRegression(class_weight="balanced")` was used for both models specifically to avoid trading away recall on the smaller classes (some banking77 intents have as few as 35 training examples — see `notebooks/01_eda.ipynb`) for aggregate accuracy on the larger, easier ones.

Recall on identified security/fraud-adjacent classes (baseline model):

| Class | Recall |
|---|---|
| `compromised_card` | 0.875 |
| `lost_or_stolen_card` | 0.925 |
| `lost_or_stolen_phone` | 0.975 |

### Lowest-recall classes (baseline model) — worth monitoring

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| `pending_transfer` | 0.824 | 0.700 | 0.757 | 40 |
| `card_payment_not_recognised` | 0.875 | 0.700 | 0.778 | 40 |
| `wrong_exchange_rate_for_cash_withdrawal` | 0.857 | 0.750 | 0.800 | 40 |
| `balance_not_updated_after_bank_transfer` | 0.652 | 0.750 | 0.698 | 40 |
| `verify_my_identity` | 0.816 | 0.775 | 0.795 | 40 |

## Artifacts

- `baseline_per_class_metrics.csv` / `transformer_per_class_metrics.csv` — full per-class precision/recall/F1/support.
- `baseline_confusion_matrix.png` — full 77x77 confusion matrix for the deployed model.
- Both training runs (params + metrics) are logged in MLflow under the `signal-classification` experiment (`mlflow ui --backend-store-uri file:./mlruns`).