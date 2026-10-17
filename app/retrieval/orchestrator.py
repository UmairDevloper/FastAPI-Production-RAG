
from __future__ import annotations

import asyncio
import logging
import time

from langchain_core.documents import Document

from app.query_transformation.service import transform_query
from app.retrieval.deduplication import deduplicate_documents
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.retriever import (
    DEFAULT_K,
    QdrantDenseRetriever,
    build_dense_retriever,
)
from app.retrieval.schemas import (
    RetrievalDiagnostics,
    RetrievalResult,
)

log = logging.getLogger(__name__)


class RetrievalOrchestrator:
    def __init__(
        self,
        retriever: QdrantDenseRetriever,
        *,
        rrf_k: int = 60,
        max_concurrency: int = 4,
    ) -> None:
        if rrf_k < 1:
            raise ValueError("rrf_k must be at least 1.")
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1.")

        self.retriever = retriever
        self.rrf_k = rrf_k
        self.max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def _retrieve_one(
        self,
        query: str,
    ) -> list[Document]:
        async with self._semaphore:
            # Keep synchronous retrieval work off the event loop.
            return await asyncio.to_thread(
                self.retriever.invoke,
                query,
            )

    async def retrieve(self, query: str) -> RetrievalResult:
        total_started = time.perf_counter()

        original = query.strip()
        if not original:
            raise ValueError("Query cannot be empty.")

        # Transform the original query.
        transform_started = time.perf_counter()
        transformed = await transform_query(original)

        transformation_ms = (
            time.perf_counter() - transform_started
        ) * 1000

        strategy = transformed.analysis.strategy

        log.info(
            "Query transformation | original=%r | strategy=%s | "
            "search_query=%r | retrieval_queries=%r",
            original,
            strategy,
            transformed.analysis.search_query,
            transformed.retrieval_queries,
        )

        diagnostics = RetrievalDiagnostics(
            strategy=strategy,
            query_count=0,
            transformation_latency_ms=round(
                transformation_ms, 2
            ),
        )

        # Stop early when clarification is required or the query
        # is outside the supported scope.
        if strategy in {"clarify", "out_of_scope"}:
            diagnostics.total_latency_ms = round(
                (time.perf_counter() - total_started) * 1000,
                2,
            )

            return RetrievalResult(
                original_query=original,
                candidates=[],
                diagnostics=diagnostics,
                hypothetical_document=(
                    transformed.hypothetical_document
                ),
            )

        # HyDE uses its hypothetical document as a retrieval input.
        # It is not user-facing evidence.
        if strategy == "hyde" and transformed.hypothetical_document:
            queries = [transformed.hypothetical_document]
        else:
            queries = transformed.retrieval_queries

        # Remove empty and duplicate queries while preserving order.
        queries = list(
            dict.fromkeys(
                item.strip()
                for item in queries
                if isinstance(item, str) and item.strip()
            )
        )

        # Fall back to the original query if necessary.
        if not queries:
            queries = [original]

        diagnostics.query_count = len(queries)

        # Retrieve queries concurrently.
        retrieval_started = time.perf_counter()

        outcomes = await asyncio.gather(
            *(self._retrieve_one(item) for item in queries),
            return_exceptions=True,
        )

        diagnostics.retrieval_latency_ms = round(
            (time.perf_counter() - retrieval_started) * 1000,
            2,
        )

        result_lists: list[list[Document]] = []

        # Record successful and failed retrievals independently.
        for retrieval_query, outcome in zip(queries, outcomes):
            if isinstance(outcome, asyncio.CancelledError):
                raise outcome

            if isinstance(outcome, Exception):
                diagnostics.failed_queries += 1
                diagnostics.retrieved_per_query.append(0)

                log.warning(
                    "Retrieval failed for one query: %s",
                    retrieval_query,
                    exc_info=(
                        type(outcome),
                        outcome,
                        outcome.__traceback__,
                    ),
                )

                diagnostics.errors.append(
                    f"{retrieval_query}: "
                    f"{type(outcome).__name__}"
                )
                continue

            diagnostics.successful_queries += 1
            diagnostics.retrieved_per_query.append(len(outcome))
            result_lists.append(outcome)

        # Fuse and deduplicate candidates.
        fusion_started = time.perf_counter()

        if len(result_lists) > 1:
            candidates = reciprocal_rank_fusion(
                result_lists,
                k=self.rrf_k,
            )
            candidates = deduplicate_documents(candidates)
        elif result_lists:
            candidates = deduplicate_documents(result_lists[0])
        else:
            candidates = []

        diagnostics.fusion_latency_ms = round(
            (time.perf_counter() - fusion_started) * 1000,
            2,
        )

        diagnostics.total_latency_ms = round(
            (time.perf_counter() - total_started) * 1000,
            2,
        )

        return RetrievalResult(
            original_query=original,
            candidates=candidates,
            diagnostics=diagnostics,
            hypothetical_document=transformed.hypothetical_document,
        )


def build_retrieval_orchestrator(
    k: int = DEFAULT_K,
    *,
    rrf_k: int = 60,
    max_concurrency: int = 4,
) -> RetrievalOrchestrator:
    retriever = build_dense_retriever(k=k)

    return RetrievalOrchestrator(
        retriever,
        rrf_k=rrf_k,
        max_concurrency=max_concurrency,
    )