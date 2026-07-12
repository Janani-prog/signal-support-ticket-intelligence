# Signal — Support Ticket Intelligence Platform

> A portfolio project demonstrating full ML-lifecycle competency: experimentation → evaluation →
> deployment → monitoring. Built entirely with free/open-source tools, $0 budget, CPU-only.

**Live demo:** _TBD (Phase 7)_
**Screenshots:** _TBD (Phase 9)_

---

## What it does

Signal turns unstructured customer support tickets into structured, actionable business
intelligence:

- **Classifies** incoming tickets into categories, with confidence scores and interpretable
  top-contributing terms (not a black box).
- **Clusters** tickets to surface emerging issues before a human has labeled them.
- **Answers natural-language questions** about the ticket corpus with cited source tickets
  (retrieval-augmented summarization).

See `PRD.md` for the full problem statement, users, and scope.

---

## Architecture

_TBD — diagram and summary added in Phase 9. See `TECHNICAL_ARCHITECTURE.md` for the full design._

---

## Results

### Classification (Phase 2)

| Model | Accuracy | Macro F1 |
|---|---|---|
| Baseline: TF-IDF + Logistic Regression (**deployed**) | 89.2% | 0.893 |
| Upgrade: MiniLM embeddings + Logistic Regression | 93.0% | 0.930 |

The embedding upgrade is more accurate, but the **TF-IDF baseline is what's deployed** — it gives
exact, per-term interpretability (required by PRD F2 and the Stitch Classifier screen design),
which the embedding model's dense features can't provide without a separate, potentially
misleading approximation layer. Full reasoning, per-class metrics, confusion matrix, and the
business-cost writeup (which error type is optimized against and why) are in
[`reports/classification/evaluation.md`](reports/classification/evaluation.md).

### Clustering (Phase 3)

- **56 clusters** found across 8,000 unlabeled Twitter customer-support tickets (HDBSCAN;
  4,321 tickets — 54% — left as noise, expected for short, topically diverse social text).
- **Silhouette score: 0.51** (clustered points only, 10-D UMAP space).
- **Human-legibility review** of 5 clusters: 4/5 genuinely coherent and actionable (account
  access, flight delays, gaming platform issues, negative flying sentiment); 1/5 turned out to be
  off-topic social chatter (McDonald's cravings) that isn't a support issue at all — a real
  finding a legibility review catches that an accuracy metric wouldn't. Full review:
  [`reports/clustering/legibility_review.md`](reports/clustering/legibility_review.md).

### Retrieval + Summarization (Phase 4)

- **Retrieval hit rate: 100%** (15/15 hand-built questions had a relevant ticket in the top-5),
  **mean recall@5: 78.7%** — FAISS + all-MiniLM-L6-v2 over the Twitter ticket corpus.
- **Summarization: bart-large-cnn, not flan-t5-base** (the doc's first-listed default). Detailed
  side-by-side in
  [`reports/retrieval/evaluation.md`](reports/retrieval/evaluation.md): flan-t5-base failed on
  15/15 test questions, echoing its own prompt template instead of synthesizing content; switching
  to bart-large-cnn (a real summarization model) fixed this and is also ~13x faster to load.
- **Vector store: FAISS, not Chroma.** Chroma's Rust bindings segfaulted unpredictably on this
  Windows dev environment, reproducible even in minimal cases outside this codebase. Switched to
  FAISS — TECHNICAL_ARCHITECTURE.md §2.2's own named alternative.
- **Manual usefulness rating: 3.7/5 mean** across the 15 test answers — consistently on-topic and
  non-hallucinatory, main weakness is prose fluency (reads as stitched fragments rather than fully
  fluent prose on some questions), an honest tradeoff for a free CPU-only model.

---

## Running locally

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash; use .venv\Scripts\activate on cmd/PowerShell
pip install -r requirements.txt
cp .env.example .env
```

### Frontend

```bash
cd frontend && python -m http.server 5500
```

Then open `http://127.0.0.1:5500/dashboard.html` (API must be running on `http://127.0.0.1:8000` —
override via `window.SIGNAL_API_BASE` in each page if needed). Plain HTML/CSS/JS, no build step —
the same stack the Stitch export itself uses (Tailwind CDN + vanilla JS), per
TECHNICAL_ARCHITECTURE.md §2.4's "whichever stack the export produces" guidance. Four screens:
`dashboard.html`, `classifier.html`, `clusters.html`, `ask.html`, sharing `shared/api.js` (API
client), `shared/nav.js` (sidebar/topbar), and `shared/tailwind-config.js` (design tokens
extracted from `design/stitch-export/archive_intelligence/DESIGN.md`). Verified in a real browser
(Playwright) against the live API — all four screens render, the golden path on each works
(classify a ticket, click a cluster bubble, ask a question), no console errors.

**Honest simplifications vs. the Stitch mockup** (flagged since the mockup numbers looked
plausible but aren't backed by real data): the mockup's Resolution Rate, Avg Sentiment, 30-day
trend deltas, and per-cluster Trend/MTTR tiles have no corresponding field in either source
dataset (no timestamps, no resolution status, no sentiment scores were computed). Rather than
fabricate those numbers, the dashboard shows real computed metrics instead (classifier accuracy,
retrieval hit rate, cluster count/silhouette, category volume) and the "Flagged Emerging
Clusters" panel is explicitly labeled as ranked by volume, not recency. Added one endpoint beyond
TECHNICAL_ARCHITECTURE.md §2.3's original draft contract, `GET /stats`, to serve these.

### API

```bash
uvicorn src.api.main:app --reload
```

Swagger UI at `http://127.0.0.1:8000/docs`. Endpoints (see `TECHNICAL_ARCHITECTURE.md` §2.3 for
the full contract): `GET /health`, `POST /classify`, `GET /clusters`, `GET /clusters/{id}`,
`POST /ask`. All models (classifier, clustering artifacts, retrieval index, summarizer) load once
at startup. `/classify` and `/ask` are rate-limited (20/min, 10/min respectively — `slowapi`, per
`SECURITY_AND_ACCESS.md` §3) and validate input via Pydantic (empty/oversized/malformed requests
return 422). CORS origins configurable via `CORS_ALLOWED_ORIGINS` in `.env`.

### Data

```bash
python -m src.data.ingest_banking77       # labeled: 77-intent banking support queries
python -m src.data.ingest_twitter_support  # unlabeled: real-world customer support tweets
```

Both scripts are idempotent (safe to re-run) and write to `data/processed/` (gitignored — not
committed; regenerate from these scripts). Sources:

- **banking77** (HF Hub `banking77`, PolyAI) — ~13k customer banking queries across 77
  fine-grained intents. Used as the labeled corpus for classification (Phase 2).
- **Twitter Customer Support** (HF Hub
  [`MohammadOthman/mo-customer-support-tweets-945k`](https://huggingface.co/datasets/MohammadOthman/mo-customer-support-tweets-945k))
  — real customer-support tweets, ~945k rows. We use a fixed, seeded random sample of 8,000
  customer-initiated messages (portfolio scale, per `TECHNICAL_ARCHITECTURE.md` §5) as the
  unlabeled corpus for clustering/retrieval (Phases 3-4). Filtered to English-only via
  `langdetect` — an early clustering run (Phase 3) showed non-English tickets collapsing into
  language-identity clusters instead of topical ones, so this is filtered at ingestion.

Both are cleaned via `src/data/cleaning.py`: PII-shaped tokens (emails, phone numbers, URLs,
@handles) are redacted, whitespace is normalized, and exact duplicates are dropped — see
`SECURITY_AND_ACCESS.md` §1. See `notebooks/01_eda.ipynb` for class balance, text length
distribution, and sample tickets.

_Further run instructions (training, API, frontend) added as each phase lands._

---

## Project status

See `CLAUDE.md` for the phase-by-phase checklist.

---

## Honest scope note

This is a portfolio project, not a production system: designed for demo-scale data (thousands,
not millions, of tickets) and single-user concurrency. No real customer data is used — see
`SECURITY_AND_ACCESS.md`.
