# Monitoring & Retraining Plan
## Signal — Support Ticket Intelligence Platform

**Status:** v1 (documented plan, partially automated — see §5 for exactly what's live vs. planned)

This is a portfolio project (`PRD.md` explicitly scopes "a documented plan for [automated
retraining], not automated execution" as in-scope for v1). This document is that plan — written
against the numbers this project actually measured, not generic boilerplate.

---

## 1. What's monitored, and why

| Signal | Source | Why it matters |
|---|---|---|
| Input feature drift (text length, word count) | `monitoring/reports/` (Evidently AI) | Cheap, fast proxy for "incoming tickets look different than training data" — doesn't need labels. |
| Prediction distribution drift (predicted label, confidence) | Same | Model *behavior* changing is often the more actionable signal — a classifier can degrade even when raw input features look stable, if the input semantics shift within similar-looking text. |
| Prediction volume | `monitoring/logs/predictions.jsonl` | Sudden volume changes (a queue backing up, or traffic silently dropping to zero) are themselves worth alerting on, independent of drift. |

## 2. Drift detection — what we found, and the methodology lesson from finding it

Two Evidently AI reports are committed in `monitoring/reports/` (T8.1-T8.2):

- **`drift_no_shift_test_split_a_vs_b.html`** — banking77 test set randomly split in half.
  Result: **0/4 features drifted.** This is the sanity-check baseline: if two random samples
  from the same distribution get flagged as "drifted," the monitor is useless (cries wolf on
  every deploy). It doesn't here.
- **`drift_domain_shift_twitter_vs_test.html`** — the Twitter customer-support corpus vs.
  banking77 test, simulating what monitoring would show if incoming production traffic started
  looking like a different ticket population. Result: **4/4 features drifted**, including a
  large shift in predicted-label distribution and confidence. This is what real, actionable
  drift looks like in this system.

**A real methodology bug was caught and fixed while building this, worth stating explicitly
because it's the kind of mistake a monitoring setup can silently ship with:** the first version
of the drift script used the *training* set as the reference distribution. That produced a
"confidence drift" false positive between train and test — not real drift, just the classifier
being more confident on data it was fit on (an overfitting-adjacent artifact, not a data shift).
Using train as a drift-monitoring reference would flag *every* future deployment as "drifted" on
day one, making the monitor noise rather than signal. **The fix: the reference distribution for
drift monitoring must always be a held-out set the model never trained on** — the reports in this
repo use banking77 test-set splits for exactly this reason. Any future retraining should carry
this forward: re-derive the reference distribution from a held-out split of the *new* training
data, never the training data itself.

## 3. Retraining triggers

These are the conditions that should trigger a retraining review — not necessarily automatic
retraining (see §5 for what would need to change to make it automatic).

| Trigger | Threshold | Rationale |
|---|---|---|
| **Drift share** (Evidently `DatasetDriftMetric`) on a rolling sample of live `/classify` inputs vs. the held-out reference | ≥ 50% of monitored features flagged drifted | Our domain-shift example hit 100%; our no-shift baseline hit 0%. 50% is a deliberately conservative middle ground — investigate before it reaches "obviously different domain" territory. |
| **Classifier accuracy** on a periodically hand-labeled sample of live traffic | Drops below **85%** (vs. the current 89.2% baseline — see `reports/classification/evaluation.md`) | A ~4-point drop is bigger than normal sampling noise for this task and dataset size, and starts eating into the margin that justified deploying the interpretable baseline over the higher-accuracy embedding model in the first place. |
| **Per-class recall** on the smallest/highest-risk classes (see `reports/classification/evaluation.md`'s lowest-recall-classes table) | Any of the tracked security/financial-risk classes (`lost_or_stolen_card`, `compromised_card`, etc.) drops recall by >10 points from baseline | These are exactly the classes the Phase 2 business-cost writeup argued should be protected against false negatives — a recall drop here is a targeted regression, not just aggregate noise. |
| **Retrieval hit rate** (re-run `src/retrieval/eval_retrieval.py`'s test set periodically — manually, not by the scheduled workflow; see §5's note on why) | Drops below **80%** (vs. current 100%) | The 15-question test set is small, so some variance is expected as the underlying ticket corpus is refreshed — 80% still means the vast majority of hand-verified questions retrieve a relevant ticket. |
| **Prediction volume anomaly** (from `monitoring/logs/predictions.jsonl`) | Volume drops to 0 for >1 hour during expected traffic, or spikes >10x baseline | Independent of model quality — this catches the pipeline being broken or (given the $0 free-tier hosting) potential abuse consuming the rate-limit budget. |

## 4. Cadence

Given this is single-tenant, demo-scale, no-real-time-ingestion (`PRD.md` §6 explicitly puts
real-time ingestion and this scale of ops out of scope for v1):

- **Drift check:** re-run `src/monitoring/generate_drift_report.py` against a fresh sample of
  logged predictions **weekly**, or immediately after any noticeable spike in `predictions.jsonl`
  volume.
- **Accuracy/recall spot-check:** hand-label a random sample of ~50-100 live `/classify` calls
  **monthly**, compare against the triggers in §3.
- **Retrieval hit-rate re-run:** **monthly**, or whenever the underlying ticket corpus changes
  (Phase 1's ingestion scripts are already idempotent/re-runnable — see `README.md`'s Data
  section — so refreshing the corpus and re-indexing is a known, tested path).

This cadence is intentionally lightweight — appropriate for a $0, single-user-concurrency
portfolio deployment (`TECHNICAL_ARCHITECTURE.md` §5's honest scoping statement), not a
production SLA.

## 5. What's automated today vs. what would need to change to fully automate this

**Automated today:**
- Prediction logging (`src/monitoring/prediction_log.py`) — every `/classify` and `/ask` call is
  logged automatically, no manual step.
- **Scheduled pipeline regression check** (`.github/workflows/monitoring.yml`, GitHub Actions,
  free for public repos): runs weekly (Monday 06:00 UTC) and on manual dispatch. Re-runs the
  pipeline from scratch (ingestion → classifier training → clustering), regenerates both drift
  reports, and checks classifier accuracy + the no-shift drift baseline against §3's thresholds
  (`src/monitoring/check_thresholds.py`). If a threshold is breached, it opens a GitHub issue
  (labeled `monitoring`) with the details and fails the workflow run (visible as a red X in the
  Actions tab); either way it commits refreshed drift report artifacts back to the repo if they
  changed.

  **Scoping honesty, including a real bug this surfaced on its first run:** this checks the
  pipeline re-run against fresh source data, not live production traffic —
  `monitoring/logs/predictions.jsonl` lives on the deployed container's ephemeral filesystem and
  isn't reachable from a GitHub Actions runner. It still catches real problems (an accuracy
  regression from a dependency bump or code change; the no-shift drift baseline breaking, which
  would indicate a pipeline bug) — but it is a regression check, not a production-traffic
  monitor. Closing that gap is item 1 below.

  **Retrieval hit-rate evaluation was originally included in this automated check and had to be
  removed.** On the very first real run, it reported a false "regression" (13.3% vs. the real,
  human-verified 100%) — and the auto-commit step briefly overwrote the authoritative
  `reports/retrieval/retrieval_hit_rate.json` with that wrong number before this was caught and
  fixed. Root cause: `eval_retrieval.py`'s ground truth is "which cluster does this ticket
  belong to," tied to a *specific* clustering run's cluster IDs — re-clustering from scratch each
  week (as this workflow does) reassigns those IDs even with a fixed random seed (clustering
  isn't bit-identical across platforms — see the README's Clustering results note), silently
  invalidating the hardcoded ground truth. This is now excluded from the automated check and
  documented at the top of both `check_thresholds.py` and the workflow file; retrieval evaluation
  stays a manual, monthly re-run (§4) where a human reviews the numbers before they're reported
  anywhere.

**Not automated (by design, per `PRD.md`'s explicit non-goal):**
- No automatic retraining or redeployment when a trigger fires.
- No labeled-sample accuracy spot-check on live traffic (see item 2 below for what this would take).

**What it would take to automate further, if this moved beyond portfolio scope:**
1. **Monitor actual production traffic, not just source-data reruns.** Would need
   `monitoring/logs/predictions.jsonl` to be reachable from CI — e.g. a small authenticated
   export endpoint on the API, or switching prediction logging to write to a free hosted store
   (a free-tier Postgres like Supabase/Neon, or even a private GitHub Gist via API) that the
   scheduled workflow can read from instead of (or in addition to) re-running the pipeline.
2. **Labeled sample pipeline:** a lightweight review queue for the monthly accuracy spot-check on
   real predictions — even a simple CSV export + manual labeling + a small script to compute
   accuracy against §3's thresholds would close most of the gap without needing a full labeling
   platform. Depends on item 1 (needs access to real predictions first).
3. **Automatic retraining + redeploy:** the highest-effort piece. Would need: a training job
   (re-run `src/classification/train_baseline.py` against refreshed data — the scheduled workflow
   already does this part), an evaluation gate (don't promote a retrained model that scores worse
   than the current one on `reports/classification/evaluation.md`'s test set), and a redeploy step
   (rebuild + push the Docker image, trigger a new Render deploy via their API). Individually
   feasible on $0 tooling (GitHub Actions + Render's deploy hooks), but deliberately out of scope
   here per `PRD.md` §3's stated non-goal — this document is the plan for it, not a request to
   auto-promote unreviewed models to production.
