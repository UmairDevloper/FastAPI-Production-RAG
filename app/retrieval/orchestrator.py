from __future__ import annotations

import asyncio
import logging
import time

import logfire
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
        *,
        query_index: int,
    ) -> list[Document]:
        with logfire.span(
            "retrieval.single_query",
            query_index=query_index,
            query_chars=len(query),
        ):
            async with self._semaphore:
                # Keep synchronous retrieval work off the event loop.
                with logfire.span("retrieval.dense_search"):
                    return await asyncio.to_thread(
                        self.retriever.invoke,
                        query,
                    )

    async def retrieve(self, query: str) -> RetrievalResult:
        total_started = time.perf_counter()
        original = query.strip()

        if not original:
            raise ValueError("Query cannot be empty.")

        with logfire.span(
            "retrieval.orchestrate",
            query_chars=len(original),
            rrf_k=self.rrf_k,
            max_concurrency=self.max_concurrency,
        ) as orchestration_span:
            # Transform the original query.
            transform_started = time.perf_counter()

            with logfire.span(
                "retrieval.query_transformation",
                query_chars=len(original),
            ):
                transformed = await transform_query(original)

            transformation_ms = (time.perf_counter() - transform_started) * 1000

            strategy = transformed.analysis.strategy

            log.info(
                "Query transformation | strategy=%s | retrieval_query_count=%d",
                strategy,
                len(transformed.retrieval_queries),
            )

            diagnostics = RetrievalDiagnostics(
                strategy=strategy,
                query_count=0,
                transformation_latency_ms=round(transformation_ms, 2),
            )

            orchestration_span.set_attribute("retrieval.strategy", strategy)
            orchestration_span.set_attribute(
                "retrieval.transformation_latency_ms",
                round(transformation_ms, 2),
            )

            # Stop early when clarification is required or the query
            # is outside the supported scope.
            if strategy in {"clarify", "out_of_scope"}:
                diagnostics.total_latency_ms = round(
                    (time.perf_counter() - total_started) * 1000,
                    2,
                )

                logfire.info(
                    "retrieval.skipped",
                    strategy=strategy,
                    reason="clarification_or_out_of_scope",
                    total_latency_ms=diagnostics.total_latency_ms,
                )

                return RetrievalResult(
                    original_query=original,
                    candidates=[],
                    diagnostics=diagnostics,
                    hypothetical_document=(transformed.hypothetical_document),
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

            orchestration_span.set_attribute("retrieval.query_count", len(queries))

            # Retrieve queries concurrently.
            retrieval_started = time.perf_counter()

            with logfire.span(
                "retrieval.parallel_search",
                query_count=len(queries),
                max_concurrency=self.max_concurrency,
            ):
                outcomes = await asyncio.gather(
                    *(
                        self._retrieve_one(
                            item,
                            query_index=index,
                        )
                        for index, item in enumerate(queries)
                    ),
                    return_exceptions=True,
                )

            diagnostics.retrieval_latency_ms = round(
                (time.perf_counter() - retrieval_started) * 1000,
                2,
            )

            result_lists: list[list[Document]] = []

            # Record successful and failed retrievals independently.
            for index, (retrieval_query, outcome) in enumerate(zip(queries, outcomes)):
                if isinstance(outcome, asyncio.CancelledError):
                    raise outcome

                if isinstance(outcome, Exception):
                    diagnostics.failed_queries += 1
                    diagnostics.retrieved_per_query.append(0)

                    log.warning(
                        "Retrieval failed for query index %d: %s",
                        index,
                        type(outcome).__name__,
                        exc_info=(
                            type(outcome),
                            outcome,
                            outcome.__traceback__,
                        ),
                    )

                    logfire.error(
                        "retrieval.query_failed",
                        query_index=index,
                        query_chars=len(retrieval_query),
                        error_type=type(outcome).__name__,
                    )

                    diagnostics.errors.append(
                        f"{retrieval_query}: {type(outcome).__name__}"
                    )
                    continue

                diagnostics.successful_queries += 1
                diagnostics.retrieved_per_query.append(len(outcome))
                result_lists.append(outcome)

                logfire.info(
                    "retrieval.query_completed",
                    query_index=index,
                    retrieved_count=len(outcome),
                )

            # Fuse and deduplicate candidates.
            fusion_started = time.perf_counter()

            with logfire.span(
                "retrieval.fusion",
                successful_query_count=len(result_lists),
                rrf_k=self.rrf_k,
            ):
                if len(result_lists) > 1:
                    candidates = reciprocal_rank_fusion(
                        result_lists,
                        k=self.rrf_k,
                    )
                    fused_count = len(candidates)
                    candidates = deduplicate_documents(candidates)
                elif result_lists:
                    fused_count = len(result_lists[0])
                    candidates = deduplicate_documents(result_lists[0])
                else:
                    fused_count = 0
                    candidates = []

            diagnostics.fusion_latency_ms = round(
                (time.perf_counter() - fusion_started) * 1000,
                2,
            )

            diagnostics.total_latency_ms = round(
                (time.perf_counter() - total_started) * 1000,
                2,
            )

            logfire.info(
                "retrieval.completed",
                strategy=strategy,
                query_count=diagnostics.query_count,
                successful_queries=diagnostics.successful_queries,
                failed_queries=diagnostics.failed_queries,
                retrieved_per_query=diagnostics.retrieved_per_query,
                fused_candidate_count=fused_count,
                final_candidate_count=len(candidates),
                transformation_latency_ms=diagnostics.transformation_latency_ms,
                retrieval_latency_ms=diagnostics.retrieval_latency_ms,
                fusion_latency_ms=diagnostics.fusion_latency_ms,
                total_latency_ms=diagnostics.total_latency_ms,
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
