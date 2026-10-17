from dataclasses import dataclass, field
from typing import Literal

"""
Schema definitions for query transformation components."""

Strategy = Literal[
    "direct",
    "rewrite",
    "multi_query",
    "decompose",
    "hyde",
    "clarify",
    "out_of_scope",
]


@dataclass
class QueryAnalysis:
    strategy: Strategy
    reason: str
    search_query: str
    needs_clarification: bool = False


@dataclass
class TransformedQuery:
    original_query: str
    analysis: QueryAnalysis
    retrieval_queries: list[str] = field(default_factory=list)
    hypothetical_document: str | None = None