# Technical Architecture Document
## Signal — Support Ticket Intelligence Platform

**Status:** Draft v1
**Companion docs:** `PRD.md`, `SECURITY_AND_ACCESS.md`, `FEATURES_TICKETS.md`, `CLAUDE.md`

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
                             - Chroma (or FAISS) vector store
                             - local summarization model (flan-t5-base / bart-large-cnn)
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
- Ingestion scripts must be idempotent and documented (so Claude Code or a reviewer can
  re-run them from scratch).

### 2.2 ML Layer
- **Classification:** scikit-learn baseline, optional transformer upgrade
  (`distilbert-base-uncased` fine-tuned, or frozen embeddings + classifier head). All models
  run on CPU — no GPU dependency, since this must stay free and portable.
- **Clustering:** `sentence-transformers` (`all-MiniLM-L6-v2`) → UMAP → HDBSCAN. Chosen over
  k-means because it doesn't require pre-specifying cluster count and models noise explicitly.
- **Retrieval + summarization:** FAISS for the vector index (an `IndexFlatIP` over
  all-MiniLM-L6-v2 embeddings); `bart-large-cnn` via `transformers` for summarization as the
  default, local-only path.

  **Implementation update (Phase 4):** both of this section's "or" choices were tried and one
  side of each was dropped after hitting real problems, not just preference:
  - **Chroma was dropped for FAISS.** Chroma's Rust bindings segfaulted unpredictably on the
    Windows dev environment, reproducible in minimal cases with no other project code involved.
    FAISS (this doc's own named alternative) worked cleanly.
  - **flan-t5-base was dropped for bart-large-cnn.** Prompted to synthesize a cross-ticket theme,
    flan-t5-base failed on 15/15 hand-built test questions — it echoed its own prompt template
    instead of generating content (verified not to be a prompt-tuning gap: several prompt variants
    were tried, and flan-t5-large showed the same failure mode while being ~3x slower).
    bart-large-cnn, a real summarization model rather than an instruction-follower, fixed this
    and loads ~13x faster. Full evidence in `reports/retrieval/evaluation.md`.

  **Latency fallback (optional):** local CPU inference for generative summarization can be slow
  enough to make a live demo feel broken, especially on free-tier hosting (e.g. HF Spaces' free
  CPU tier). If local summarization latency is too high in practice, Claude Code may swap in a
  **free serverless inference API** for the summarization step only — e.g. Groq (very fast free
  tier, good for small/open models) or the Hugging Face Inference API's free tier. Requirements
  if this path is used:
  - Retrieval itself (embeddings + vector search) stays local regardless — only the final
    summarization call goes out to an API. This keeps the core RAG architecture intact and
    keeps external request volume low (one call per question, not per ticket).
  - The API key must be handled per `SECURITY_AND_ACCESS.md` §2 (env var / hosting secret
    manager, never hardcoded, `.env.example` updated with the new placeholder).
  - This counts as a **material deviation** from the local-only default per `CLAUDE.md`'s "use
    judgment" clause — it should be noted in the README and this doc updated to reflect which
    path was actually used and why (e.g. "local flan-t5-base met latency targets, no fallback
    needed" or "switched to Groq for summarization due to CPU latency on HF Spaces free tier").
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
  (`/design/stitch-export/`). Claude Code should implement against that design's structure,
  screens, and visual language rather than inventing new UI patterns.
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
| Summarization | HF transformers (`bart-large-cnn`), fallback to Groq / HF Inference API if CPU latency is too high | Free either way; local by default, serverless as a documented latency escape hatch. `flan-t5-base` tried first but failed to synthesize (see §2.2) |
| Experiment tracking | MLflow (local) | Free, no signup |
| API | FastAPI | Async, typed, fast to build |
| Frontend | Per Stitch export | Custom, non-templated design |
| Monitoring | Evidently AI | Free, open-source, purpose-built for drift |
| Containerization | Docker | Portable, signals production awareness |
| Hosting | Streamlit Community Cloud or Hugging Face Spaces | Free tiers |

---

## 4. Deployment Topology

- Single container (or two: `api` + `frontend`, via `docker-compose` for local dev).
- Model artifacts (`models/`) baked into the image or downloaded at container start from a
  public HF Hub repo you control — avoid committing large binaries to git.
- Deployed target: Hugging Face Spaces (Docker Space) is preferred over Streamlit Community
  Cloud if the frontend isn't Streamlit-based, since Spaces supports arbitrary Docker apps.

---

## 5. Scalability & Performance Notes (portfolio-scale, stated honestly)

- This system is designed for demo-scale data (thousands, not millions, of tickets) and
  single-user concurrency. The README should say this explicitly rather than overclaim
  production readiness — an honest scoping statement is itself a signal of engineering maturity.
- If asked "how would this scale," the documented answer (put in README or an `ADR` note) is:
  swap Chroma for a managed vector DB, move from local MLflow to a tracked server, move batch
  scoring to a queue (e.g. Celery/Redis), and add caching in front of `/ask`.

---

## 6. Repo Structure

```
support-ticket-intelligence/
├── data/
├── design/stitch-export/     # provided design reference
├── models/                    # trained artifacts (gitignored if large; document how to regenerate)
├── monitoring/reports/
├── notebooks/
├── src/
│   ├── data/
│   ├── classification/
│   ├── clustering/
│   ├── retrieval/
│   └── api/
├── frontend/
├── mlruns/                    # gitignored
├── tests/
├── Dockerfile
├── docker-compose.yml
├── CLAUDE.md
├── PRD.md
├── TECHNICAL_ARCHITECTURE.md
├── SECURITY_AND_ACCESS.md
├── FEATURES_TICKETS.md
├── MONITORING.md
├── README.md
└── requirements.txt
```
