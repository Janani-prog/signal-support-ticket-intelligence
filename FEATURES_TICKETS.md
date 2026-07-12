# Feature Ticket List — Phased Execution Plan
## Signal — Support Ticket Intelligence Platform

Each phase should be fully working and demo-able before moving to the next — this maximizes
productivity by avoiding rework and keeps the project in a "could stop here and still show
something real" state at every stage.

---

## Phase 0 — Project Setup
- **T0.1** Initialize repo structure per `TECHNICAL_ARCHITECTURE.md` §6.
- **T0.2** Set up `requirements.txt`, virtual env, `.env.example`.
- **T0.3** Set up MLflow local tracking, verify a dummy run logs correctly.
- **T0.4** Write initial `README.md` skeleton (sections only, filled in later phases).
- **Acceptance:** `pip install -r requirements.txt` works clean; MLflow UI launches locally.

## Phase 1 — Data Ingestion
- **T1.1** Write ingestion script for `banking77` (labeled).
- **T1.2** Write ingestion script for Twitter Customer Support dataset (unlabeled).
- **T1.3** Basic cleaning (dedup, strip PII-shaped tokens as a precaution, normalize whitespace).
- **T1.4** Exploratory notebook: class balance, text length distribution, sample tickets.
- **Acceptance:** `data/processed/` contains clean, documented, reproducible files; ingestion
  scripts are idempotent and re-runnable from scratch.

## Phase 2 — Classification
- **T2.1** Baseline: TF-IDF + Logistic Regression, tracked in MLflow.
- **T2.2** Upgrade: transformer-based classifier (fine-tuned DistilBERT or embeddings + head).
- **T2.3** Evaluation: per-class precision/recall, confusion matrix, business-cost writeup
  (which error type was optimized against, per `PRD.md` §7).
- **T2.4** Export interpretability signal (top contributing terms per prediction) for the
  Classifier UI screen.
- **Acceptance:** best model + metrics logged in MLflow; a documented decision on which model
  is used in the deployed app and why.

## Phase 3 — Clustering
- **T3.1** Generate sentence-transformer embeddings for unlabeled ticket set.
- **T3.2** UMAP dimensionality reduction + HDBSCAN clustering.
- **T3.3** Auto-label clusters (top TF-IDF terms per cluster, or short generated summary).
- **T3.4** Human-legibility review: manually read 5 clusters, write one sentence each on
  coherence/actionability — this table goes directly in the README (per `PRD.md` §7).
- **Acceptance:** cluster assignments + labels saved as an artifact the API/frontend can read;
  legibility table written.

## Phase 4 — Retrieval + Summarization
- **T4.1** Build vector index (Chroma/FAISS) over ticket corpus.
- **T4.2** Implement retrieval (top-k semantic search) given a natural-language question.
- **T4.3** Implement summarization of retrieved tickets into a short synthesized answer.
- **T4.4** Build ~15-question hand-labeled test set with expected relevant ticket IDs; measure
  retrieval hit rate; manually rate summary usefulness 1–5.
- **Acceptance:** `/ask`-equivalent logic works end-to-end in a script/notebook before it's
  wrapped in the API.

## Phase 5 — API Layer
- **T5.1** Scaffold FastAPI app; implement `/health`.
- **T5.2** Implement `/classify` using Phase 2 model.
- **T5.3** Implement `/clusters` and `/clusters/{id}` using Phase 3 artifacts.
- **T5.4** Implement `/ask` using Phase 4 pipeline.
- **T5.5** Add input validation, CORS config, basic rate limiting (per `SECURITY_AND_ACCESS.md`).
- **Acceptance:** all endpoints testable via `curl`/Swagger UI (`/docs`) with real responses.

## Phase 6 — Frontend Implementation
- **T6.1** Import/reference the Stitch design export (`/design/stitch-export/`) as the visual
  source of truth.
- **T6.2** Implement Overview Dashboard screen, wired to live API data.
- **T6.3** Implement Ticket Classifier screen.
- **T6.4** Implement Cluster Explorer screen (constellation/scatter visualization).
- **T6.5** Implement Ask a Question screen with cited sources.
- **Acceptance:** all four screens functional against the live local API, visually matching the
  Stitch design's structure and style.

## Phase 7 — Containerization & Deployment
- **T7.1** Write `Dockerfile` (+ `docker-compose.yml` if API/frontend are split).
- **T7.2** Verify full stack runs via Docker locally.
- **T7.3** Deploy to Hugging Face Spaces (or Streamlit Community Cloud if frontend is
  Streamlit-based).
- **T7.4** Smoke test the live deployed URL against all four screens.
- **Acceptance:** publicly accessible URL, loads and functions correctly.

## Phase 8 — Monitoring
- **T8.1** Set up Evidently AI drift comparison (training data vs. a held-out/simulated
  "new data" batch).
- **T8.2** Generate and commit an example drift report to `monitoring/reports/`.
- **T8.3** Implement prediction logging (timestamp, input hash, output) for `/classify` and
  `/ask`.
- **T8.4** Write `MONITORING.md`: retraining triggers, cadence, what would need to change to
  automate this.
- **Acceptance:** a real Evidently report exists in the repo; `MONITORING.md` reads as a genuine
  plan, not boilerplate.

## Phase 9 — Documentation & Polish
- **T9.1** Finalize `README.md`: business framing, architecture diagram, evaluation results
  tables (classification, clustering legibility, retrieval hit rate), link to live app,
  screenshots.
- **T9.2** Add resume bullet draft (from earlier project brief) to README or a `RESUME.md`.
- **T9.3** Final pass: remove dead code, confirm reproducibility instructions work on a clean
  clone.
- **Acceptance:** a stranger can read the README in ~3 minutes and understand what was built,
  why, and how well it performs — and can click through to a live, working demo.

---

## Notes for Claude Code

- Phases should be completed **in order** — each one should leave the project in a working,
  demoable state before starting the next.
- Within a phase, tickets can be reordered if there's a clear dependency reason, but don't skip
  ahead to a later phase's tickets before the current phase's acceptance criteria are met.
- If a ticket turns out to be based on a wrong assumption (e.g. a dataset doesn't download
  cleanly), fix the assumption and note the change — don't silently substitute something
  materially different without flagging it.
