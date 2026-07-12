# Product Requirements Document (PRD)
## Signal — Support Ticket Intelligence Platform

**Status:** Shipped — v1.0
**Last updated:** 2026-07-12

---

## 1. Summary

Signal is an internal analytics platform that turns unstructured customer support tickets into
structured, actionable business intelligence. It automatically classifies incoming tickets,
surfaces emerging issues via unsupervised clustering before a human has labeled them, and lets
non-technical managers query the ticket corpus in plain English and get a synthesized,
source-cited answer.

This is a portfolio project built to demonstrate full ML lifecycle competency (experimentation →
evaluation → deployment → monitoring), not a production SaaS product — but it should be built
and documented to the standard of one.

---

## 2. Problem Statement

Support teams generate large volumes of unstructured text (tickets, chat transcripts) that
mostly goes unanalyzed. Three specific pains:

1. **Manual/inconsistent categorization** — tickets are tagged inconsistently or not at all,
   making routing and reporting unreliable.
2. **Blind spots on emerging issues** — a new bug or complaint pattern isn't visible until
   volume is already high, because there's no existing label for it.
3. **No self-serve insight layer** — a manager who wants to know "what's trending in
   complaints this week" has to wait on a data person to pull and read tickets manually.

---

## 3. Goals / Non-Goals

**Goals**
- Automatically classify tickets into categories with per-class precision/recall reported in
  business terms (cost of false negative vs. false positive).
- Detect and visually surface clusters of tickets that don't map cleanly to existing categories.
- Provide a natural-language Q&A interface over the ticket corpus with cited source tickets.
- Deploy as a live, usable web app — not a notebook.
- Include a real (if lightweight) monitoring and retraining plan.

**Non-Goals**
- Not building a multi-tenant, authenticated, production-grade SaaS product.
- Not handling real customer PII — all data is public/synthetic.
- Not building a fully automated MLOps pipeline with CI/CD-triggered retraining (a **documented
  plan** for this is in scope; automated execution of it is not required for v1).

---

## 4. Users / Personas

| Persona | Need |
|---|---|
| Support Ops Manager | Wants a fast, plain-English way to understand what's happening across tickets without reading hundreds of them. |
| Data/Analytics stakeholder | Wants to trust that categorization and clustering are evaluated rigorously, not just accuracy-washed. |
| (You, presenting this) | Needs a live, screenshot-able, demoable system with a coherent business narrative for interviews. |

---

## 5. Scope: Features

### F1 — Overview Dashboard
- Ticket volume over time (line/bar).
- Category distribution (from classifier).
- A "Flagged clusters" panel: 2–3 clusters the system has detected that don't map cleanly to an
  existing category, ranked by size/recency.

### F2 — Ticket Classifier
- Input: paste a ticket or select a sample one.
- Output: predicted category, confidence score, and the top contributing terms/phrases
  (interpretability — not a black box).

### F3 — Cluster Explorer
- Visual map of ticket clusters (constellation/scatter layout per the Stitch design — cluster
  size = volume, proximity = semantic similarity).
- Selecting a cluster shows: auto-generated theme label, sample tickets, and size over time.

### F4 — Ask a Question (Retrieval + Summarization)
- Natural-language search bar.
- Returns a short synthesized answer plus the source tickets it drew from, shown as citations
  (ticket ID + snippet).

### F5 — Evaluation & Monitoring Artifacts (visible in-repo, not necessarily in the UI)
- Classification report with business-cost framing.
- Cluster legibility table (human-reviewed sample of clusters, one sentence each on coherence).
- Retrieval hit-rate against a hand-built test set.
- Evidently AI drift report.
- `MONITORING.md` describing retraining triggers.

---

## 6. Out of Scope for v1

- User accounts / login (unless a simple demo-gate is wanted — see Security doc).
- Multi-language support.
- Real-time ticket ingestion (batch/static dataset is fine).
- Mobile-optimized layout (nice-to-have, not required).

---

## 7. Success Metrics

Since this is a portfolio project, "success" is measured by demonstration quality, not business
KPIs:

- Classifier: per-class precision/recall reported, with an explicit statement of which error
  type was optimized against and why.
- Clustering: silhouette score **and** a human-legibility review (this is the differentiator —
  most similar projects skip it).
- Retrieval: hit rate against a hand-built ~15-question test set.
- Deployment: publicly accessible URL, loads in <5s, no crashes on the demo data.
- Repo: a stranger (recruiter or engineer) can read the README in 3 minutes and understand
  what was built, why, and how well it works.

---

## 8. Constraints

- **Budget: $0.** All tools, models, and hosting must be free tier / open source.
- All data must be public or synthetic — no real customer PII.
- Frontend visual design must follow the Stitch export (see `/design/stitch-export/`) — treat
  that as the source of truth for look and feel, and the PRD/tech docs as the source of truth for
  functionality and data flow.

---

## 9. Open Questions

- Final category taxonomy — reuse `banking77`'s labels or define a coarser custom set? (Default:
  start with `banking77` labels for baseline speed; revisit once F1–F4 are working end-to-end.)
- Whether "Ask a Question" needs conversation memory (multi-turn) or single-shot Q&A is enough
  for v1. (Default: single-shot for v1.)
