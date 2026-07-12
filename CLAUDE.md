# CLAUDE.md — Project Context for Claude Code

This file is auto-loaded by Claude Code at the start of every session. It's the standing
context for this project. Read it fully before starting or resuming work.

---

## What this project is

**Signal** — a support ticket intelligence platform. It classifies unstructured customer
support tickets, clusters them to surface emerging issues, and answers natural-language
questions about the ticket corpus with cited sources. This is a portfolio project built to
demonstrate full ML-lifecycle competency (experimentation → evaluation → deployment →
monitoring), built entirely with free/open-source tools.

## Source-of-truth documents (read these before writing code)

- `PRD.md` — what to build and why; feature scope, users, success metrics.
- `TECHNICAL_ARCHITECTURE.md` — how to build it; system design, tech stack, data flow, API
  contract.
- `SECURITY_AND_ACCESS.md` — security/access constraints, proportionate to a free portfolio
  deployment (not enterprise-grade, not careless either).
- `FEATURES_TICKETS.md` — the phased execution plan. **Work through phases in order.** Each
  phase should leave the project in a working, demoable state before the next begins.
- `/design/stitch-export/` — the visual design reference for the frontend, produced by Google
  Stitch. **Treat this as the source of truth for look, feel, layout, and screen structure.**
  The PRD describes *what* each screen needs to do functionally; the Stitch export describes
  *what it should look like*. When the two are ambiguous or conflict, functionality wins, but
  visual style should follow the Stitch export, not a generic default.

## Standing instruction: use judgment beyond these documents

These documents (and any prompts given during the session) are the baseline plan, not a rigid
script. If you see a better way to implement something — a cleaner architecture, a more robust
approach, a library that solves a problem more simply — **use it**. You don't need to ask
permission for reasonable implementation improvements that stay within the project's stated
constraints ($0 budget, no real PII, free/open-source tools only, portfolio-scale deployment).

That said:
- If a deviation is **material** — it changes the tech stack, the deployment target, the data
  source, or anything a reader of the docs above would notice — **say so explicitly** in your
  response and ideally update the relevant doc, rather than silently diverging.
- If a deviation would violate a stated constraint (introducing a paid service, real user data,
  a security shortcut the Security doc explicitly warns against), don't make it — flag the
  tension instead and propose an alternative.
- Prefer simple, explainable choices over clever ones. This project needs to be defensible in
  an interview — every design choice should have a one-sentence reason a reviewer would find
  reasonable.

## Working conventions

- Python 3.11, type hints where reasonable, no unnecessary abstraction for a project this size.
- All models/pipelines must run on CPU — no GPU dependency, no paid API keys required for the
  default build.
- Every phase's acceptance criteria (see `FEATURES_TICKETS.md`) should be genuinely verified,
  not assumed — run it, check the output, then move on.
- Commit as you go with clear messages tied to ticket IDs (e.g. `T2.3: add per-class business
  cost writeup to classification evaluation`).
- Don't commit large model artifacts, raw data, or secrets — see `.gitignore` and
  `SECURITY_AND_ACCESS.md`.

## Current status

_Update this section as phases complete, so any new session picks up context immediately:_

- [x] Phase 0 — Project Setup
- [x] Phase 1 — Data Ingestion
- [ ] Phase 2 — Classification
- [ ] Phase 3 — Clustering
- [ ] Phase 4 — Retrieval + Summarization
- [ ] Phase 5 — API Layer
- [ ] Phase 6 — Frontend Implementation
- [ ] Phase 7 — Containerization & Deployment
- [ ] Phase 8 — Monitoring
- [ ] Phase 9 — Documentation & Polish
