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

_TBD — filled in as each phase completes:_

- **Classification:** per-class precision/recall, business-cost framing — Phase 2.
- **Clustering:** silhouette score + human-legibility review — Phase 3.
- **Retrieval:** hit-rate against a hand-built test set — Phase 4.

---

## Running locally

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash; use .venv\Scripts\activate on cmd/PowerShell
pip install -r requirements.txt
cp .env.example .env
```

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
  unlabeled corpus for clustering/retrieval (Phases 3-4).

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
