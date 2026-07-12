# Technical Architecture Document
## Signal — Support Ticket Intelligence Platform

**Status:** Shipped — v1.0
**Companion docs:** `PRD.md`, `SECURITY_AND_ACCESS.md`, `FEATURES_TICKETS.md`, `MONITORING.md`

---

## 1. System Overview (data flow, in words)

```
Raw ticket data (public dataset)
        │
        ▼
Data ingestion & cleaning (src/data/)
        │
        ├──────────────► Classification pipeline (src/classification/)
        │                    - TF-IDF+LogReg baseline → transformer upgrade
        │                    - tracked in MLflow
        │
        ├──────────────► Clustering pipeline (src/clustering/)
        │                    - sentence-transformers embeddings
        │                    - UMAP → HDBSCAN
        │                    - auto-labeling (top TF-IDF terms per cluster)
        │
        └──────────────► Retrieval index (src/retrieval/)
                             - sentence-transformers embeddings
                             - FAISS vector store
                             - extractive TF-IDF+MMR summarization
                             │
                             ▼
                    FastAPI service (src/api/)
                    - /classify, /clusters, /ask, /health endpoints
                             │
                             ▼
                    Frontend (per Stitch design export)
                    - Dashboard / Classifier / Cluster Explorer / Ask-a-Question screens
                             │
                             ▼
                    Monitoring (monitoring/)
                    - Evidently AI drift reports, generated on a schedule or on-demand
```

---

## 2. Components

### 2.1 Data Layer
- **Source datasets:** `banking77` (labeled, for classification baseline) + Twitter Customer
  Support dataset or similar (unlabeled, for clustering/retrieval).
- **Storage:** flat files (Parquet/CSV) in `data/processed/` — no database needed for v1 given
  scale. If it becomes useful, SQLite is the free upgrade path (no separate DB server to manage).
- Ingestion scripts must be idempotent and documented (so a reviewer can re-run them from
  scratch).

### 2.2 ML Layer
- **Classification:** scikit-learn baseline, optional transformer upgrade
  (`distilbert-base-uncased` fine-tuned, or frozen embeddings + classifier head). All models
  run on CPU — no GPU dependency, since this must stay free and portable.
- **Clustering:** `sentence-transformers` (`all-MiniLM-L6-v2`) → UMAP → HDBSCAN. Chosen over
  k-means because it doesn't require pre-specifying cluster count and models noise explicitly.
- **Retrieval + summarization:** FAISS for the vector index (an `IndexFlatIP` over
  all-MiniLM-L6-v2 embeddings); extractive TF-IDF + MMR sentence selection (scikit-learn only,
  no neural model) for summarization.

  **Implementation update (Phase 4 + Phase 7):** every "or" choice in this section's original
  draft was tried and dropped after hitting a real problem, not just preference:
  - **Chroma was dropped for FAISS.** Chroma's Rust bindings segfaulted unpredictably on the
    Windows dev environment, reproducible in minimal cases with no other project code involved.
    FAISS (this doc's own named alternative) worked cleanly.
  - **flan-t5-base was dropped for bart-large-cnn (Phase 4).** Prompted to synthesize a
    cross-ticket theme, flan-t5-base failed on 15/15 hand-built test questions — it echoed its
    own prompt template instead of generating content (verified not to be a prompt-tuning gap:
    several prompt variants were tried, and flan-t5-large showed the same failure mode while
    being ~3x slower). bart-large-cnn, a real summarization model rather than an
    instruction-follower, fixed this and scored 3.7/5 mean usefulness.
  - **bart-large-cnn was then dropped for an extractive TF-IDF+MMR approach (Phase 7).**
    Deploying to Render's free tier (512MB RAM cap) hit an out-of-memory crash — bart-large-cnn's
    weights alone are ~1.6GB, over 3x the entire container's budget by itself. No realistic
    smaller neural model closes that gap (even a distilled ~230M-param variant still needs
    ~900MB+ loaded). The extractive replacement scored the same 3.7/5 mean usefulness with zero
    hallucination risk and a few KB of memory. Full evidence and reasoning in
    `reports/retrieval/evaluation.md`.

  **Latency fallback (optional):** local CPU inference for generative summarization can be slow
  enough to make a live demo feel broken, especially on free-tier hosting (e.g. HF Spaces' free
  CPU tier). If local summarization latency is too high in practice, the summarization step can
  swap in a **free serverless inference API** — e.g. Groq (very fast free
  tier, good for small/open models) or the Hugging Face Inference API's free tier. Requirements
  if this path is used:
  - Retrieval itself (embeddings + vector search) stays local regardless — only the final
    summarization call goes out to an API. This keeps the core RAG architecture intact and
    keeps external request volume low (one call per question, not per ticket).
  - The API key must be handled per `SECURITY_AND_ACCESS.md` §2 (env var / hosting secret
    manager, never hardcoded, `.env.example` updated with the new placeholder).
  - This counts as a **material deviation** from the local-only default — it should be noted in
    the README and this doc updated to reflect which path was actually used and why (e.g. "local
    flan-t5-base met latency targets, no fallback needed" or "switched to Groq for summarization
    due to CPU latency on HF Spaces free tier").
- **Experiment tracking:** MLflow, local file-based backend (no hosted MLflow server needed).

### 2.3 API Layer
- **Framework:** FastAPI.
- **Endpoints (draft contract):**
  - `POST /classify` — body: `{ "text": string }` → `{ category, confidence, top_terms[] }`
  - `GET /clusters` — → list of clusters with id, label, size, sample_ticket_ids
  - `GET /clusters/{id}` — → cluster detail + sample tickets
  - `POST /ask` — body: `{ "question": string }` → `{ answer, sources: [{ticket_id, snippet}] }`
  - `GET /health` — liveness check
  - `GET /stats` — **added in Phase 6**, not in the original draft contract — aggregate numbers
    (total tickets, classifier accuracy, cluster count/silhouette, retrieval hit rate, category
    breakdown) for the Overview Dashboard. Additive only; doesn't change any endpoint above.
- API is stateless; all models loaded at startup from `models/` artifacts.

### 2.4 Frontend Layer
- **Source of truth for visual design:** the Stitch export provided separately
  (`/design/stitch-export/`). Implementation should follow that design's structure, screens, and
  visual language rather than inventing new UI patterns.
- **Implementation (decided in Phase 6): plain HTML/CSS/JS, no build step** — Tailwind via CDN
  plus vanilla JS `fetch()` calls to the API. This is literally the stack the Stitch export
  itself ships as (`code.html` per screen, Tailwind CDN script tag, no framework), so it's the
  most direct translation with zero build tooling, consistent with the project's $0/simple-choices
  ethos. React was considered but adds a build step for no functional benefit at this scale.
- Frontend calls the FastAPI backend directly (same-origin during local dev; configure CORS for
  deployed environment — see Security doc).

### 2.5 Monitoring Layer
- **Evidently AI** for drift reports: compares feature/embedding distribution and prediction
  distribution of new data vs. training data. Output: HTML report artifact committed to
  `monitoring/reports/`.
- Prediction logging: every `/classify` and `/ask` call logged (input hash, output, timestamp)
  to a local log file — this is what a rolling-accuracy or drift-over-time analysis would need
  if extended beyond v1.

---

## 3. Tech Stack Summary

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11 | Standard for ML/data work |
| Classification | scikit-learn, optional HF transformers | Free, CPU-friendly |
| Embeddings | sentence-transformers | Free, local, no API key |
| Clustering | UMAP + HDBSCAN | No k needed, handles noise |
| Vector store | FAISS (`IndexFlatIP`) | Free, embedded, no server; Chroma tried first but segfaulted on the Windows dev environment |
| Summarization | Extractive TF-IDF + MMR (scikit-learn) | Free, ~0 RAM; `flan-t5-base` and `bart-large-cnn` both tried and dropped (see §2.2) |
| Experiment tracking | MLflow (local) | Free, no signup |
| API | FastAPI | Async, typed, fast to build |
| Frontend | Per Stitch export | Custom, non-templated design |
| Monitoring | Evidently AI | Free, open-source, purpose-built for drift |
| Containerization | Docker | Portable, signals production awareness |
| Hosting | Render (free web-service tier) | HF Spaces requires PRO for Docker SDK now — see §4 |

---

## 4. Deployment Topology

- Single container (API + frontend served together — see §2.4), via `docker-compose` for local
  dev.
- Model artifacts (`models/`) baked into the image at build time (the Dockerfile runs the full
  ingestion/training/clustering/indexing pipeline as a build step) rather than committed to git
  or downloaded from an HF Hub repo — see the Dockerfile's comments for why.
- **Deployed target (changed in Phase 7): Render, not Hugging Face Spaces.** HF Spaces was the
  original plan, but as of this deployment, HF Spaces requires a **PRO subscription** to run
  Docker/Gradio SDKs on free `cpu-basic` hardware — only Static Spaces are free, and those can't
  run a FastAPI backend. That's a real $0-budget violation (`PRD.md` §8, `SECURITY_AND_ACCESS.md`),
  so it wasn't worked around — Render's free web-service tier was chosen instead (750 instance-hours/month, no card required for the free tier, direct
  Docker support — the existing `Dockerfile` needed no changes beyond respecting `$PORT`). Deploy
  via the `render.yaml` Blueprint in this repo. Tradeoff: Render's free tier spins down after
  ~15 min idle, so the first request after idle is a slow cold start (container restart + model
  reload) — an honest, disclosed limitation of $0 hosting, not hidden from the README.

---

## 5. Scalability & Performance Notes (portfolio-scale, stated honestly)

- This system is designed for demo-scale data (thousands, not millions, of tickets) and
  single-user concurrency. The README should say this explicitly rather than overclaim
  production readiness — an honest scoping statement is itself a signal of engineering maturity.
- If asked "how would this scale," the documented answer (put in README or an `ADR` note) is:
  swap Chroma for a managed vector DB, move from local MLflow to a tracked server, move batch
  scoring to a queue (e.g. Celery/Redis), and add caching in front of `/ask`.

---

## 6. Repo Structure (as built)

```
signal-support-ticket-intelligence/
├── .github/workflows/         # scheduled monitoring automation (see MONITORING.md §5)
├── data/                      # gitignored — regenerate via src/data/ingest_*.py
├── design/stitch-export/      # visual design reference
├── docs/screenshots/          # README screenshots
├── models/                    # trained artifacts, gitignored — regenerate via training scripts
├── monitoring/reports/        # committed Evidently drift reports
├── notebooks/                 # EDA
├── reports/                   # evaluation write-ups (classification, clustering, retrieval)
├── src/
│   ├── data/
│   ├── classification/
│   ├── clustering/
│   ├── retrieval/
│   ├── api/
│   └── monitoring/
├── frontend/                  # plain HTML/CSS/JS, served by the API in production
├── mlruns/                    # gitignored
├── Dockerfile
├── docker-compose.yml
├── render.yaml                # Render deployment blueprint
├── PRD.md
├── TECHNICAL_ARCHITECTURE.md
├── SECURITY_AND_ACCESS.md
├── FEATURES_TICKETS.md
├── MONITORING.md
├── README.md
└── requirements.txt
```
