"""Pydantic request/response models — API contract per TECHNICAL_ARCHITECTURE.md §2.3."""

from pydantic import BaseModel, Field


class ClassifyRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class TermContribution(BaseModel):
    term: str
    weight: float


class ClassifyResponse(BaseModel):
    category: str
    confidence: float
    top_terms: list[TermContribution]


class ClusterSummary(BaseModel):
    cluster_id: int
    label: str
    top_terms: list[str]
    size: int
    centroid: dict[str, float]
    sample_ticket_ids: list[str]


class ClusterListResponse(BaseModel):
    n_clusters: int
    n_noise: int
    n_tickets: int
    silhouette_score: float | None
    clusters: list[ClusterSummary]


class SampleTicket(BaseModel):
    ticket_id: str
    ticket_text: str


class ClusterDetailResponse(ClusterSummary):
    sample_tickets: list[SampleTicket]


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=10)


class AskSource(BaseModel):
    ticket_id: str
    snippet: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[AskSource]


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
