"""T4.4 — hand-built ~15-question retrieval test set + hit-rate measurement.

Ground truth: each question targets a real, human-verified cluster from Phase 3
(data/processed/clusters.json). "Relevant" tickets = all tickets HDBSCAN assigned to that
cluster (not just the 10 samples cached in the cluster summary) — a ticket is relevant if it's
topically about the question, which is exactly what cluster membership encodes here.

Hit rate = fraction of questions where at least one of the top-k retrieved tickets belongs to
the target cluster. Also reports mean recall@k (of relevant tickets found in top-k) since a
single-hit rate can look good even when most of top-k is irrelevant.

Run: python -m src.retrieval.eval_retrieval
"""

import json
from pathlib import Path

from src.retrieval.retrieve import TicketRetriever

DATA_DIR = Path("data/processed")
REPORT_DIR = Path("reports/retrieval")
TOP_K = 5

# Each question is grounded in a real, manually-inspected cluster from Phase 3
# (see reports/clustering/legibility_review.md and data/processed/clusters.json).
TEST_SET = [
    {"question": "What are people saying about flight delays?", "target_cluster": 15},
    {"question": "Are customers having trouble with Xbox or PlayStation games?", "target_cluster": 21},
    {"question": "What account access or password problems are customers reporting?", "target_cluster": 27},
    {"question": "What complaints are there about Uber or Uber Eats drivers?", "target_cluster": 4},
    {"question": "Are packages not being delivered?", "target_cluster": 55},
    {"question": "What issues are people having with their iPhone battery?", "target_cluster": 52},
    {"question": "Is there an internet or network outage customers are reporting?", "target_cluster": 40},
    {"question": "What credit card or payment card problems are customers having?", "target_cluster": 29},
    {"question": "What are people saying about Comcast TV channels?", "target_cluster": 47},
    {"question": "Are trains being delayed or cancelled?", "target_cluster": 8},
    {"question": "What are customers saying about Amazon Prime delivery?", "target_cluster": 44},
    {"question": "Are customers complaining about Spotify or music streaming?", "target_cluster": 0},
    {"question": "What Hulu or streaming show issues are being reported?", "target_cluster": 46},
    {"question": "Are customers unhappy with in-store stock availability?", "target_cluster": 28},
    {"question": "What Wells Fargo or bank account issues are customers reporting?", "target_cluster": 31},
]


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    clusters_data = json.loads((DATA_DIR / "clusters.json").read_text(encoding="utf-8"))
    cluster_members = {
        c["cluster_id"]: {
            t["ticket_id"] for t in clusters_data["tickets"] if t["cluster_id"] == c["cluster_id"]
        }
        for c in clusters_data["clusters"]
    }

    retriever = TicketRetriever()

    rows = []
    for case in TEST_SET:
        relevant_ids = cluster_members[case["target_cluster"]]
        results = retriever.search(case["question"], top_k=TOP_K)
        retrieved_ids = [r["ticket_id"] for r in results]

        hits = [tid for tid in retrieved_ids if tid in relevant_ids]
        any_hit = len(hits) > 0
        recall_at_k = len(hits) / min(TOP_K, len(relevant_ids))

        rows.append(
            {
                "question": case["question"],
                "target_cluster": case["target_cluster"],
                "n_relevant_in_corpus": len(relevant_ids),
                "any_hit": any_hit,
                "hits_in_top_k": len(hits),
                "recall_at_k": round(recall_at_k, 3),
                "top_result": retrieved_ids[0] if retrieved_ids else None,
            }
        )

    hit_rate = sum(r["any_hit"] for r in rows) / len(rows)
    mean_recall = sum(r["recall_at_k"] for r in rows) / len(rows)

    print(f"Hit rate (>=1 relevant in top-{TOP_K}): {hit_rate:.1%}")
    print(f"Mean recall@{TOP_K}: {mean_recall:.1%}")

    output = {
        "top_k": TOP_K,
        "hit_rate": hit_rate,
        "mean_recall_at_k": mean_recall,
        "results": rows,
    }
    (REPORT_DIR / "retrieval_hit_rate.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {REPORT_DIR / 'retrieval_hit_rate.json'}")


if __name__ == "__main__":
    main()
