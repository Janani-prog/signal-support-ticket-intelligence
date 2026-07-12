# Retrieval + Summarization Evaluation — Phase 4 (T4.4), updated in Phase 7

## Retrieval hit rate

15-question hand-built test set, each grounded in a real, manually-verified cluster from
Phase 3 (`reports/clustering/legibility_review.md`, `data/processed/clusters.json`). A ticket is
"relevant" to a question if HDBSCAN assigned it to that question's target cluster. See
`src/retrieval/eval_retrieval.py` for the full question list and
`reports/retrieval/retrieval_hit_rate.json` for per-question results.

- **Hit rate (>=1 relevant ticket in top-5): 100%** (15/15 questions)
- **Mean recall@5: 78.7%** — most of top-5 is genuinely relevant, not just one lucky hit

Retrieval itself (FAISS + all-MiniLM-L6-v2) is unaffected by the summarization model changes
below — these numbers are unchanged from the original Phase 4 evaluation.

## Summarization model history: three models, two real failures, one that fit the $0 budget

**1. `flan-t5-base`** (TECHNICAL_ARCHITECTURE.md §2.2's first-listed default) — failed on 15/15
test questions, echoing its own prompt template instead of producing content. Several prompt
variants were tried, and `flan-t5-large` showed the same failure mode. Not a capability this
model class has for multi-document synthesis in a zero-shot prompt.

**2. `bart-large-cnn`** — worked well. Produced genuine multi-source synthesis, rated 3.7/5 mean
usefulness across the 15 test questions, no hallucination observed. This was the Phase 4
deployed choice.

**3. Deploying to Render (Phase 7) hit an out-of-memory crash: "Ran out of memory (used over
512MB)."** Root cause: `bart-large-cnn`'s weights alone are ~1.6GB in memory (400M params × 4
bytes, fp32) — over 3x Render's free-tier RAM cap by itself, before counting torch, FastAPI,
sentence-transformers, or anything else sharing that 512MB. No realistic same-architecture
fix closes that gap: even a distilled variant (`distilbart-cnn-6-6`, ~230M params) still needs
roughly 900MB+ loaded, still well over budget.

**Switched to extractive multi-sentence summarization** (`src/retrieval/summarize.py`):
TF-IDF + Maximal Marginal Relevance (MMR) sentence selection, scikit-learn only, no neural model
for this step at all. Selects the most query-relevant, least-redundant sentences across the
retrieved tickets' text. Uses a few KB of memory instead of 1.6GB.

**This is not treated as a quality downgrade we're quietly accepting** — the original
`bart-large-cnn` evaluation (see the git history of this file) already found its output "reads as
stitched-together fragments rather than one smooth sentence," i.e. it was already behaving mostly
extractively on this task. Below is the re-rating of all 15 test questions with the extractive
approach, done the same way as the original (honest 1-5, checked for on-topic accuracy and
absence of hallucination).

## Summary usefulness ratings (manual, 1-5) — extractive MMR summarizer

| # | Question | Rating | Notes |
|---|---|---|---|
| 1 | flight delays | 4 | Pulls 3 distinct complaints (delay, seat-saving gripe, "why do I keep flying with you") — genuinely reflects multiple sources, reads a bit disjointed at the sentence-boundary seams. |
| 2 | Xbox/PlayStation trouble | 4 | Same cluster quirk as before (mixes a delivery complaint with actual gameplay issues) but each selected sentence is accurate to its source. |
| 3 | account/password problems | 4 | Three genuinely distinct password/account-access complaints, no overlap, clearly on-topic. |
| 4 | Uber/Uber Eats driver complaints | 4 | Covers complaint-channel, overcharge, and driver-safety angles — good topic coverage from 3 different tickets. |
| 5 | packages not delivered | 4 | Redundant-looking but accurate: multiple tickets really do all say "marked delivered, never arrived" — MMR correctly found this is the dominant theme, not an error. |
| 6 | iPhone battery issues | 4 | Concise, on-topic, specific (iOS 11 update blamed). |
| 7 | internet/network outage | 3 | On-topic but terse/choppy — short sentence fragments strung together read less naturally than question 5's set. |
| 8 | credit/payment card problems | 4 | Covers payment-method errors and a customer-service-friction angle — good complementary coverage. |
| 9 | Comcast TV channels | 4 | Better than the bart-large-cnn version — stays on "channels" specifically (on-demand fees, losing channels) rather than drifting to general billing. |
| 10 | trains delayed/cancelled | 3 | On-topic but one selected fragment ("DELAYED TRAINS ARE NOT") is a truncated sentence start, reads oddly out of context. |
| 11 | Amazon Prime delivery | 4 | Three clear, distinct complaints (praise-then-sarcasm, cancelled delivery, customer service) — actually reads better than the bart-large-cnn version. |
| 12 | Spotify/music streaming | 3 | On-topic but the three sentences pull in slightly different directions (data plan, premium pricing, playlist visibility) without a unifying thread. |
| 13 | Hulu/streaming show issues | 4 | Specific and on-topic (Roku app breakage, WS viewing issue). |
| 14 | in-store stock availability | 4 | Same strong selection as the bart-large-cnn version (this MMR selection happened to converge on very similar sentences). |
| 15 | Wells Fargo/bank account issues | 3 | On-topic but the 3rd sentence ("Best bank to have?") is a rhetorical fragment that reads as filler rather than adding information. |

**Mean rating: 3.7/5** — statistically identical to the `bart-large-cnn` version (also 3.7/5).
Consistently on-topic, zero hallucination (every word traces to a real retrieved ticket, by
construction — this approach literally cannot invent content, which is a genuine advantage over
a generative model for a support-ops tool). Weaknesses are the same class as before (sentence-
to-sentence flow can read as choppy) plus one new failure mode extraction always risks:
selecting a sentence fragment that reads oddly out of its original context (questions 10, 15).

## Why this is the right tradeoff, not just a workaround

- **Zero hallucination risk is a real property, not a consolation prize.** SECURITY_AND_ACCESS.md
  §3 already flags prompt-injection-adjacent risk from treating retrieved ticket text as
  untrusted content in a future LLM prompt — extractive summarization has no generation step to
  attack in the first place.
- **Comparable measured quality (3.7/5 both ways)** means this wasn't a quality-for-memory
  trade — it was closer to a free lunch once you account for what the neural model was actually
  doing on this task.
- **Removes ~1.6GB from the Docker image and eliminates the container startup model-download**,
  which also directly improves cold-start latency on Render's free tier (spins down after ~15min
  idle) beyond just fixing the OOM crash.

## Artifacts

- `retrieval_hit_rate.json` — full per-question hit/recall results (unchanged by this update).
- `generated_answers.json` — regenerated with the extractive summarizer.
