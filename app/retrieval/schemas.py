
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from langchain_core.documents import Document


@dataclass
class RetrievalDiagnostics:
    strategy: str
    query_count: int

    successful_queries: int = 0
    failed_queries: int = 0
    retrieved_per_query: list[int] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    # Stage timings in milliseconds.
    transformation_latency_ms: float = 0.0
    retrieval_latency_ms: float = 0.0
    fusion_latency_ms: float = 0.0
    total_latency_ms: float = 0.0


@dataclass
class RetrievalResult:
    original_query: str
    candidates: list[Document]
    diagnostics: RetrievalDiagnostics
    hypothetical_document: str | None = None

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_query": self.original_query,
            "candidate_count": self.candidate_count,
            "strategy": self.diagnostics.strategy,
            "query_count": self.diagnostics.query_count,
            "successful_queries": self.diagnostics.successful_queries,
            "failed_queries": self.diagnostics.failed_queries,
            "retrieved_per_query": self.diagnostics.retrieved_per_query,
            "errors": self.diagnostics.errors,
            "transformation_latency_ms":
                self.diagnostics.transformation_latency_ms,
            "retrieval_latency_ms":
                self.diagnostics.retrieval_latency_ms,
            "fusion_latency_ms":
                self.diagnostics.fusion_latency_ms,
            "total_latency_ms":
                self.diagnostics.total_latency_ms,
        }