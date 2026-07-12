"""T8.3 — prediction logging for /classify and /ask.

Logs timestamp, a hash of the input (not the raw input text — SECURITY_AND_ACCESS.md §1's
public-data-only policy means there's no real PII here, but hashing is still the right default
for a log that could grow to include real user input if this were ever pointed at production
traffic), and the output. Append-only JSONL, one line per prediction — exactly what a rolling-
accuracy or drift-over-time analysis needs if extended beyond this portfolio's v1 scope
(TECHNICAL_ARCHITECTURE.md §2.5).
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path("monitoring/logs")
LOG_PATH = LOG_DIR / "predictions.jsonl"


def _hash_input(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def log_prediction(endpoint: str, input_text: str, output: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "input_hash": _hash_input(input_text),
        "output": output,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
