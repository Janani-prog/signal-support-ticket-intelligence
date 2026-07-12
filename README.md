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

_Full run instructions (data ingestion, training, API, frontend) added as each phase lands._

---

## Project status

See `CLAUDE.md` for the phase-by-phase checklist.

---

## Honest scope note

This is a portfolio project, not a production system: designed for demo-scale data (thousands,
not millions, of tickets) and single-user concurrency. No real customer data is used — see
`SECURITY_AND_ACCESS.md`.
