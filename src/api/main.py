"""FastAPI service — Phase 5. Endpoints per TECHNICAL_ARCHITECTURE.md §2.3.

Run: uvicorn src.api.main:app --reload
Docs: http://127.0.0.1:8000/docs
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.api.model_store import ModelStore, get_model_store
from src.api.schemas import (
    AskRequest,
    AskResponse,
    AskSource,
    ClassifyRequest,
    ClassifyResponse,
    ClusterDetailResponse,
    ClusterListResponse,
    HealthResponse,
    StatsResponse,
    TermContribution,
)

load_dotenv()

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Signal API", description="Support ticket intelligence platform API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*")
allow_origins = ["*"] if cors_origins.strip() == "*" else [o.strip() for o in cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_store: ModelStore | None = None


@app.on_event("startup")
def load_models() -> None:
    global _store
    _store = get_model_store()


def store() -> ModelStore:
    if _store is None:
        raise HTTPException(status_code=503, detail="Models not yet loaded")
    return _store


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", models_loaded=_store is not None)


@app.post("/classify", response_model=ClassifyResponse)
@limiter.limit("20/minute")
def classify(request: Request, body: ClassifyRequest) -> ClassifyResponse:
    category, confidence, top_terms = store().classify(body.text)
    return ClassifyResponse(
        category=category,
        confidence=confidence,
        top_terms=[TermContribution(**t) for t in top_terms],
    )


@app.get("/stats", response_model=StatsResponse)
def stats() -> StatsResponse:
    """Additive endpoint (not in TECHNICAL_ARCHITECTURE.md §2.3's original draft contract) for
    the Overview Dashboard — real aggregate numbers computed from Phase 1-4 artifacts."""
    return StatsResponse(**store().stats)


@app.get("/clusters", response_model=ClusterListResponse)
def list_clusters() -> ClusterListResponse:
    s = store()
    return ClusterListResponse(
        n_clusters=s.n_clusters,
        n_noise=s.n_noise,
        n_tickets=s.n_tickets,
        silhouette_score=s.silhouette_score,
        clusters=s.list_clusters(),
    )


@app.get("/clusters/{cluster_id}", response_model=ClusterDetailResponse)
def get_cluster(cluster_id: int) -> ClusterDetailResponse:
    cluster = store().get_cluster(cluster_id)
    if cluster is None:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    return ClusterDetailResponse(**cluster)


@app.post("/ask", response_model=AskResponse)
@limiter.limit("10/minute")
def ask(request: Request, body: AskRequest) -> AskResponse:
    result = store().ask_pipeline.ask(body.question, top_k=body.top_k)
    return AskResponse(
        answer=result["answer"],
        sources=[AskSource(**s) for s in result["sources"]],
    )
