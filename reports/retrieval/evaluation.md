# Retrieval + Summarization Evaluation — Phase 4 (T4.4)

## Retrieval hit rate

15-question hand-built test set, each grounded in a real, manually-verified cluster from
Phase 3 (`reports/clustering/legibility_review.md`, `data/processed/clusters.json`). A ticket is
"relevant" to a question if HDBSCAN assigned it to that question's target cluster. See
`src/retrieval/eval_retrieval.py` for the full question list and
`reports/retrieval/retrieval_hit_rate.json` for per-question results.

- **Hit rate (>=1 relevant ticket in top-5): 100%** (15/15 questions)
- **Mean recall@5: 78.7%** — most of top-5 is genuinely relevant, not just one lucky hit

## Model decision: bart-large-cnn, not flan-t5-base

`flan-t5-base` was tried first (TECHNICAL_ARCHITECTURE.md §2.2's first-listed default), prompted
to synthesize a cross-ticket theme. It failed systematically: across all 15 questions, it echoed
the prompt template itself ("Multiple customers submitted the separate support messages
below...") instead of producing real content — not a one-off, a 15/15 failure. This wasn't a
prompt-engineering gap we didn't try to close: several prompt variants were tested (citation-style,
"do not quote directly", few-shot lead-in), and a larger variant (`flan-t5-large`, 780M params)
was also tried and showed the same behavior (verbatim-quoting one source) while taking ~3x longer
to load and generate. This looks like a genuine capability limit of small flan-t5 models on
multi-document synthesis, not a fixable prompt issue.

Switched to `bart-large-cnn` — a real summarization model (trained on CNN/DailyMail) rather than
an instruction-follower — applied to the concatenated retrieved ticket text. Result: reliable,
genuinely synthesized, on-topic answers across all 15 test questions (see ratings below). It also
loads ~13x faster (~5s vs ~60s) with comparable generation time, so this is a strict improvement,
not a quality/speed tradeoff. This is a **material deviation** from the doc's first-listed default,
flagged per CLAUDE.md's judgment clause, and TECHNICAL_ARCHITECTURE.md should be read as: use
bart-large-cnn as the default, not flan-t5-base.

## Summary usefulness ratings (manual, 1-5)

Rated for: does the answer actually reflect the shared theme across multiple retrieved tickets,
in readable prose, without hallucinating specifics not present in the sources?

| # | Question | Rating | Notes |
|---|---|---|---|
| 1 | flight delays | 4 | Coherently combines two distinct tickets' complaints; on-topic. |
| 2 | Xbox/PlayStation trouble | 3 | On-topic (Xbox) but latched onto a shipping/delivery complaint rather than in-game issues — cluster 21 turned out to mix hardware delivery and gameplay complaints (see caveat below). |
| 3 | account/password problems | 4 | Directly on-topic, combines two real complaints clearly. |
| 4 | Uber/Uber Eats driver complaints | 4 | On-topic: driver safety, lack of a complaint channel. |
| 5 | packages not delivered | 4 | On-topic, concrete (tracking/vehicle-loading detail). |
| 6 | iPhone battery issues | 4 | Short but clear and on-topic. |
| 7 | internet/network outage | 3 | On-topic but reads as a run-on list of near-duplicate outage mentions rather than a synthesized sentence — readable, not elegant. |
| 8 | credit/payment card problems | 4 | On-topic, captures the "errors despite different cards" pattern. |
| 9 | Comcast TV channels | 3 | On-topic for Comcast, but drifted to billing/DVR-fee complaints rather than channels specifically. |
| 10 | trains delayed/cancelled | 4 | Concise and on-topic (one word garbled by the known source-data "xp" corruption — see `reports/clustering/legibility_review.md`). |
| 11 | Amazon Prime delivery | 3 | On-topic but the concatenation reads awkwardly ("today being told delivery will happen on amazing service") — theme is clear despite rough prose. |
| 12 | Spotify/music streaming | 4 | On-topic, specific (pricing mismatch, forced registration). |
| 13 | Hulu/streaming show issues | 5 | Best of the set — specific, clear, directly answers the question. |
| 14 | in-store stock availability | 3 | Theme (scarce stock tied to promotions) comes through but mixed with a tangential general-anger complaint. |
| 15 | Wells Fargo/bank account issues | 4 | Clear narrative (card hold, fraud dept) directly on-topic. |

**Mean rating: 3.7/5.** Consistently on-topic and non-hallucinatory (no answer invented a detail
absent from the retrieved tickets — a real risk we checked for specifically). The main weakness is
prose fluency: because the underlying approach is closer to extractive-concatenative than fully
abstractive, some answers read as stitched-together fragments rather than one smooth sentence.
This is an honest, expected tradeoff for a free, local, CPU-only model — the documented upgrade
path (TECHNICAL_ARCHITECTURE.md §2.2's Groq/HF Inference API fallback) would likely improve
fluency, but requires a user-supplied API key and is out of scope for the default $0 build.

## Known caveat surfaced by this evaluation

Question 2 (Xbox/PlayStation) revealed that cluster 21 (`xbox / game / ps4`) is not purely about
gameplay issues — it also contains Xbox *hardware delivery* complaints. This wasn't visible in
the Phase 3 legibility review (which sampled different tickets from the same cluster) and is a
useful, concrete example of why retrieval-level spot-checking catches things a clustering review
alone doesn't.

## Artifacts

- `retrieval_hit_rate.json` — full per-question hit/recall results.
- `generated_answers.json` — full answers + sources for all 15 questions.
