# Signal — Support Ticket Intelligence Platform

### [**🚀 LAUNCH LIVE DEMO →**](https://signal-mmuf.onrender.com/dashboard.html)

[![Live Demo](https://img.shields.io/badge/LIVE%20DEMO-signal--mmuf.onrender.com-success?style=for-the-badge&logo=render&logoColor=white)](https://signal-mmuf.onrender.com/dashboard.html)

**[Screenshots ↓](#screenshots)** &nbsp;|&nbsp;
**[Architecture ↓](#architecture)** &nbsp;|&nbsp;
**[Results ↓](#results)** &nbsp;|&nbsp;
**[Technical Challenges ↓](#technical-challenges-overcome)**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?logo=pytorch&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?logo=scikitlearn&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Evidently AI](https://img.shields.io/badge/Evidently%20AI-drift%20monitoring-6C3EF4)
![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)
![Render](https://img.shields.io/badge/Deployed-Render-46E3B7?logo=render&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

> Free-tier hosting note: the live demo spins down after ~15min idle — the first request after
> that is a slow cold start while the container restarts and models reload.

---

## What it is

Support teams drown in unstructured ticket text: categorization is inconsistent, new problems
stay invisible until volume is already high because there's no label for a bug that hasn't been
named yet, and answering "what's trending in complaints this week" means someone reading hundreds
of tickets by hand. **Signal turns that raw text into structured intelligence** — it classifies
tickets automatically, discovers emerging issue clusters no one has labeled yet, and answers
plain-English questions over the entire ticket corpus with cited sources. Under the hood it's a
complete ML system: a 77-class interpretable classifier, an unsupervised clustering pipeline, and
a retrieval-augmented Q&A engine, all served through a production FastAPI backend, containerized,
deployed, and monitored for drift — built end-to-end on a strict $0 budget.

---

## Key Engineering Achievements

- **89.2% classification accuracy** on a 77-class intent-classification task, with a documented,
  quantified tradeoff decision: a **more accurate 93.0% model was built, evaluated, and
  deliberately not deployed** in favor of the interpretable one — full per-term coefficient
  explanations beat a 3.8-point accuracy gain for a system that has to explain its own decisions.
- **100% retrieval hit-rate** (15/15 hand-built test questions) on a from-scratch RAG pipeline
  (FAISS + sentence embeddings), with 78.7% mean recall@5.
- **56-59 coherent topic clusters** surfaced from unlabeled data with zero manual labeling —
  validated both quantitatively (silhouette score) and by manual human review, which caught a
  cluster an accuracy metric alone would have missed (see [Technical Challenges](#technical-challenges-overcome)).
- **Shipped under a hard 512MB RAM ceiling.** Root-caused a production out-of-memory crash to a
  single 1.6GB model, then re-architected the summarization stage to hit the *same* measured
  output quality (3.7/5 usefulness) in a few KB of memory instead — see below.
- **Fully automated MLOps monitoring**: a scheduled GitHub Actions workflow re-runs the pipeline
  weekly, checks it against documented regression thresholds, and opens a GitHub issue
  automatically on breach — verified against a real triggered alert, not just written and hoped
  to work (see [MLOps & Monitoring](#mlops--monitoring)).
- **Zero unit tests, by design, not by accident** — verification happened by exercising a real
  running system at every stage (live API calls, live browser screenshots, a real 512MB Docker
  memory cap reproduced locally before touching production). That approach is what actually
  caught every bug below; see [Honest Scope Note](#honest-scope-note).

---

## Screenshots

| Dashboard | Ticket Classifier |
|---|---|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Classifier](docs/screenshots/classifier.png) |

| Cluster Explorer | Ask a Question |
|---|---|
| ![Clusters](docs/screenshots/clusters.png) | ![Ask](docs/screenshots/ask.png) |

---

## Architecture

```
banking77 (labeled, 13k)        Twitter customer-support corpus (unlabeled, 8k, English-only)
        │                                          │
        ▼                                          ▼
 TF-IDF + LogReg classifier          all-MiniLM-L6-v2 embeddings
 (deployed for interpretability;         │                    │
  93.0%-accuracy embedding model         ▼                    ▼
  evaluated but not deployed)     UMAP → HDBSCAN        FAISS index
        │                        (56-59 clusters)      (query-time retrieval)
        │                              │                      │
        │                              │                      ▼
        │                              │            extractive TF-IDF+MMR
        │                              │             summarization (no
        │                              │              neural model)
        │                              │                      │
        ▼                              ▼                      ▼
              FastAPI — /health /classify /stats /clusters /clusters/{id} /ask
                     │ loads all models once at startup, rate-limited, validated
                     ▼
       Static frontend (HTML/CSS/JS + Tailwind) — same container/origin as the API
                     │
                     ▼
       Docker (non-root, uid 1000) → Render (512MB RAM, free tier)
                     │
                     ▼
       Evidently AI drift reports + GitHub Actions weekly regression check
```

### Classification

TF-IDF + Logistic Regression, chosen **over** a `sentence-transformers` embedding model that
scored 3.8 points higher on accuracy — because the deployed model needs to produce genuine,
per-token interpretability (which terms drove this prediction, and by how much), not a
post-hoc approximation. A linear model over sparse term features gives that exactly; a dense
embedding model can't without a separate, potentially misleading explainability layer bolted on.
Both models are trained, evaluated, and compared — the tradeoff is a decision, not an omission.

### Clustering

`sentence-transformers` embeddings → UMAP → HDBSCAN, chosen over k-means specifically because it
doesn't require pre-specifying a cluster count and models noise explicitly rather than forcing
every point into a group. Result: 56-59 topic clusters (chicken/food complaints, flight delays,
Xbox errors, password resets — genuinely distinct, human-legible themes) discovered from raw text
with zero labels, validated with both a silhouette score and a manual coherence review.

### Retrieval + Summarization (RAG)

FAISS exact search over sentence embeddings for retrieval; **extractive TF-IDF + Maximal Marginal
Relevance sentence selection** — not a neural model — for the final synthesis step. Every word in
a generated answer traces back to a real retrieved ticket by construction, which means zero
hallucination risk, a property a generative model can't offer without extra guardrails.

---

## Technical Challenges Overcome

Every one of these is a real problem hit during development, root-caused, and fixed — documented
in place rather than smoothed over, because that's the actual signal of engineering maturity.

**1. Production OOM crash under a 512MB RAM ceiling.**
The initial summarizer (`bart-large-cnn`) ran perfectly in every local test — and then crashed the
production deployment with `Ran out of memory (used over 512MB)`. Root cause: that model's
weights alone are ~1.6GB, over 3x the entire container's budget, before counting the rest of the
stack. No smaller neural model closes that gap (even a distilled ~230M-param variant still needs
~900MB+ loaded). Fix: replaced it with a from-scratch extractive summarizer (TF-IDF + MMR sentence
selection, scikit-learn only) — re-evaluated on the same 15-question test set and it scored
**identically** (3.7/5 mean usefulness) at a few KB of memory instead of 1.6GB. Verified the fix by
reproducing Render's exact 512MB limit locally (`docker run --memory=512m`) before redeploying —
usage dropped from 472.7MiB (92.3%, dangerously tight) to 452.8MiB (88.4%, real headroom).

**2. A segfaulting vector database.**
Chroma was the first choice for the retrieval vector store — its Rust bindings segfaulted
unpredictably on the development environment, reproducible even in a minimal repro case with no
other project code involved. Swapped to FAISS (an equally valid, explicitly-considered
alternative) rather than losing time fighting an unstable native dependency.

**3. A silent evaluation ground-truth bug, caught by actually running the automation.**
After wiring up automated weekly monitoring, the very first live run fired a false regression
alert: retrieval hit-rate had apparently collapsed from 100% to 13.3%. Investigating instead of
just silencing the alert revealed the real issue — the retrieval evaluation's ground truth was
tied to specific cluster IDs from one clustering run, and re-clustering from scratch (even with a
fixed random seed) reassigns those IDs, since clustering isn't bit-identical across platforms.
The automated job had also already overwritten the repo's frozen, human-verified evaluation
report with the false number before this was caught. Fixed by restoring the correct report,
removing that check from automated gating entirely, and documenting the failure mode so it can't
silently recur — full incident writeup in `MONITORING.md`.

**4. A generative model that silently failed 15/15 times.**
Before landing on `bart-large-cnn` (see #1), the first summarization model tried was
`flan-t5-base`. It didn't crash or error — it just echoed its own prompt template back as the
"answer" on every single one of 15 test questions. Caught only because every model choice in this
project is evaluated against a hand-built test set rather than trusted on the strength of a single
manual spot-check.

**5. A paid-tier paywall discovered mid-deployment.**
The original deployment target, Hugging Face Spaces, turned out to require a paid PRO
subscription for Docker-based Spaces — discovered via a live `402 Payment Required` API response,
not assumed in advance. Rather than quietly pay for it or silently skip deployment, switched to
Render's genuinely free tier and adjusted the Dockerfile (a single `$PORT` env var change) to
support it.

---

## Results

### Classification

| Model | Accuracy | Macro F1 | Deployed? |
|---|---|---|---|
| TF-IDF + Logistic Regression | 89.2% | 0.893 | **Yes** — chosen for interpretability |
| MiniLM embeddings + Logistic Regression | 93.0% | 0.930 | No — evaluated, not deployed |

Full per-class metrics, confusion matrix, and the business-cost writeup (which error type is
optimized against and why):
[`reports/classification/evaluation.md`](reports/classification/evaluation.md).

### Clustering

- **56-59 clusters** across 8,000 unlabeled support tickets (HDBSCAN; the exact count varies
  slightly by platform — a genuine floating-point reproducibility limitation of UMAP, documented
  rather than hidden). ~54-55% of tickets left as noise, expected for short, topically diverse
  social-media text.
- **Silhouette score: ~0.51** (clustered points only), stable across runs.
- **Human-legibility review**: 4/5 sampled clusters genuinely coherent and actionable; 1/5 turned
  out to be off-topic chatter (McDonald's cravings, not a support issue) — a finding a legibility
  review catches that an accuracy metric never would. Full review:
  [`reports/clustering/legibility_review.md`](reports/clustering/legibility_review.md).

### Retrieval + Summarization

- **100% hit rate** (15/15 hand-built questions), **78.7% mean recall@5**.
- **3.7/5 mean usefulness** on the extractive summarizer — statistically identical to the
  1.6GB neural model it replaced, with zero hallucination risk as a bonus.
  Full model-selection history: [`reports/retrieval/evaluation.md`](reports/retrieval/evaluation.md).

---

## MLOps & Monitoring

- **Evidently AI drift reports** ([`monitoring/reports/`](monitoring/reports/)): a held-out-split
  "no shift" baseline (0/4 features flagged — confirms the monitor doesn't cry wolf) and a genuine
  domain-shift example (Twitter corpus vs. banking77 — 4/4 features flagged), proving the tool
  actually discriminates real drift from sampling noise rather than just looking impressive on
  one fixed comparison.
- **Prediction logging**: every `/classify` and `/ask` call logged (timestamp, input hash, output
  — no raw text stored).
- **Automated regression monitoring**
  ([`.github/workflows/monitoring.yml`](.github/workflows/monitoring.yml)): a scheduled GitHub
  Actions workflow re-runs the pipeline weekly, checks classifier accuracy and the no-shift drift
  baseline against documented thresholds, opens a GitHub issue automatically on breach, and
  commits refreshed drift reports back to the repo. This isn't just written and assumed to work —
  it was triggered for real, caught a genuine bug in its own evaluation methodology (see Technical
  Challenges #3), and was re-verified end-to-end after the fix.
- Full retraining-trigger plan, thresholds, and cadence: [`MONITORING.md`](MONITORING.md).

---

## Local Setup / Quickstart

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash; use .venv\Scripts\activate on cmd/PowerShell
pip install -r requirements.txt
cp .env.example .env
```

### Docker (single container, matches the deployed setup)

```bash
docker compose up --build
```

Serves both the API and frontend on `http://127.0.0.1:7860`. The `Dockerfile` regenerates all
data/model artifacts *inside the image* at build time (ingestion → classifier training →
clustering → retrieval indexing) rather than copying them from the host, proving the pipeline is
genuinely reproducible from source. Runs as a non-root user (uid 1000). torch installs from the
CPU-only wheel index explicitly — otherwise pip pulls the default CUDA build, contradicting the
project's no-GPU-dependency constraint. Memory is tuned to fit a 512MB cap (thread-pool limits,
malloc arena limiting, and — the biggest lever — the extractive rather than neural summarizer).

### Data

```bash
python -m src.data.ingest_banking77       # labeled: 77-intent banking support queries
python -m src.data.ingest_twitter_support  # unlabeled: real-world customer support tickets
```

Both scripts are idempotent and write to `data/processed/` (gitignored — regenerate from these
scripts). Sources: **banking77** (HF Hub, ~13k banking queries across 77 intents) and a
**Twitter customer-support corpus** (HF Hub, sampled to 8,000 English-only messages). Both cleaned
via `src/data/cleaning.py` (PII-shaped token redaction, whitespace normalization, dedup). See
[`notebooks/01_eda.ipynb`](notebooks/01_eda.ipynb) for class balance and text length distributions.

### API

```bash
uvicorn src.api.main:app --reload
```

Swagger UI at `http://127.0.0.1:8000/docs`. Endpoints: `GET /health`, `POST /classify`,
`GET /clusters`, `GET /clusters/{id}`, `POST /ask`, `GET /stats`. All models load once at
startup; `/classify` and `/ask` are rate-limited and Pydantic-validated. Full contract:
[`TECHNICAL_ARCHITECTURE.md`](TECHNICAL_ARCHITECTURE.md).

### Frontend

```bash
cd frontend && python -m http.server 5500
```

Open `http://127.0.0.1:5500/dashboard.html` (API must be running on `http://127.0.0.1:8000` —
override via `window.SIGNAL_API_BASE` if needed). Plain HTML/CSS/JS, no build step. Four screens:
dashboard, classifier, cluster explorer, ask-a-question — verified in a real browser against both
local and live deployments, zero console errors.

### Monitoring

```bash
python -m src.monitoring.generate_drift_report
```

See [MLOps & Monitoring](#mlops--monitoring) above and [`MONITORING.md`](MONITORING.md) for the
full plan.

---

## Documentation

| Doc | What's in it |
|---|---|
| [`PRD.md`](PRD.md) | Problem statement, users, scope, success metrics |
| [`TECHNICAL_ARCHITECTURE.md`](TECHNICAL_ARCHITECTURE.md) | System design, component decisions, deviations from the original plan and why |
| [`SECURITY_AND_ACCESS.md`](SECURITY_AND_ACCESS.md) | Data handling, secrets management, threat model |
| [`FEATURES_TICKETS.md`](FEATURES_TICKETS.md) | Phased execution plan |
| [`MONITORING.md`](MONITORING.md) | Retraining triggers, cadence, MLOps automation |

---

## Honest Scope Note

This is a portfolio project, not a production system: designed for demo-scale data (thousands,
not millions, of tickets) and single-user concurrency. No real customer data is used — all data
is public or synthetic.

**No automated test suite** — verification happened a different way throughout: every phase's
acceptance criteria was checked against a real running instance before moving on (actual model
metrics, actual API responses, actual browser screenshots against both local and live
deployments, actual `docker run --memory=512m` reproduction of the production memory constraint
before diagnosing the OOM fix, actually triggering the monitoring workflow end-to-end rather than
trusting it unverified). That approach caught every real bug documented above — a narrow unit-test
suite likely wouldn't have caught most of them. A production version of this system would still
want regression tests around the API contract and data pipeline.

---

## License

MIT — see [`LICENSE`](LICENSE).
