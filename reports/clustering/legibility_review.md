# Clustering Human-Legibility Review — Phase 3 (T3.4)

**Silhouette score (clustered points only, 10-D UMAP space used for HDBSCAN): 0.51** — a
moderate-to-good separation for short, noisy social-media text; consistent with the qualitative
review below (most reviewed clusters are coherent, one is off-topic noise rather than a
poorly-separated cluster).

Manually read sample tickets from 5 clusters (out of 56 total on this run; see README's Results
section for a note on why this count varies slightly — 56-59 — across platforms despite a fixed
random seed, and `data/processed/clusters.json`) to assess coherence and actionability — the
differentiator PRD.md §7 calls out ("most similar projects skip it"). Auto-labels are the top-3
TF-IDF terms per
cluster; reviewed against the actual sample ticket text below each one.

| Cluster | Auto-label | Size | Coherence / actionability (one sentence) |
|---|---|---|---|
| 27 | account / password / email | 147 | Coherent and actionable: every sample is a distinct account-access failure (2FA codes not arriving, password reset looping, unexplained ban, chat support not recognizing the account) — a real "account access" queue, though the auto-label undersells that it's specifically *access failures*, not general account questions. |
| 15 | flight / delayed / plane | 125 | Coherent and highly actionable: consistently flight-delay/cancellation complaints with flight numbers and routes — this is exactly the kind of cluster PRD F1's "flagged emerging clusters" panel is meant to surface (a real, nameable operational issue, not noise). |
| 21 | xbox / game / ps4 | 162 | Coherent theme (gaming platform technical issues — server disconnects, download errors, DRM/licensing confusion) but more heterogeneous than its neighbors: mixes Xbox, PlayStation, and Activision-specific complaints under one cluster, so a human triager would still need to sub-route by platform — auto-label alone isn't quite actionable enough here. |
| 48 | mcdonalds / mcrib / mcflurry | 43 | **Not a support-ticket cluster** — these are casual social-media posts about wanting/craving McDonald's food, with no company complaint or request in them at all. This is a real, useful finding: it shows the raw Twitter corpus contains off-topic chatter that slipped through the "customer support" framing of the source dataset, and a legibility review is exactly what catches it (an accuracy metric alone would never flag this). |
| 6 | eerience / worst / flying | 48 | Thematically coherent (negative-sentiment complaints, several about flying) but the auto-label term `eerience` is a data-quality artifact, not noise from our pipeline: the upstream source dataset has ~100/8000 rows (1.25%) where "xp" is missing from words (`experience` → `eerience`, `inexperienced` → `ineerienced`) — confirmed present in the raw HF dataset before any of our cleaning runs. Doesn't materially hurt legibility here since the surrounding words still carry the topic, but it's worth knowing about if term-based auto-labels look slightly off elsewhere. |

## Takeaways

- **4/5 reviewed clusters are genuinely coherent and would be actionable for a support-ops
  manager** (account access, flight delays, gaming platform issues, negative flying experiences).
- **1/5 (`mcdonalds/mcrib/mcflurry`) is off-topic noise**, not a support issue — a legitimate
  finding, not a pipeline bug. In a real deployment this is the kind of cluster an ops manager
  would mark "not actionable" and the system should let them suppress from the flagged panel.
  Since PRD F1 only surfaces the top 2-3 flagged clusters by size/recency, and this one is
  smaller than the top clusters, it's unlikely to surface by default — but the API/frontend
  should not assume every cluster is actionable.
- **Known data-quality caveat**: ~1.25% of the Twitter corpus has a source-dataset text
  corruption (missing "xp" substrings). Documented here rather than silently patched, since it
  wasn't introduced by our ingestion/cleaning pipeline and doesn't materially affect the clusters
  reviewed.
- 56 clusters from 8,000 tickets, 4,321 (54%) unclustered as noise (HDBSCAN cluster -1) — high,
  but expected for short, topically diverse social-media text where most individual tickets don't
  share a dense semantic neighborhood with 25+ similar others. The clusters that *do* form are
  meaningfully coherent, which is the property that matters for the "flagged emerging issues"
  use case (PRD F1) — we don't need every ticket clustered, just the ones forming a real pattern.
