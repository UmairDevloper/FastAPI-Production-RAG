"""Query transformation service for routing questions to a retrieval strategy."""

import time

import logfire

from app.query_transformation.analyzer import analyze_query
from app.query_transformation.decomposer import decompose_query
from app.query_transformation.hyde import generate_hypothetical_document
from app.query_transformation.multi_query import generate_query_variants
from app.query_transformation.rewriter import rewrite_query
from app.query_transformation.schemas import QueryAnalysis, TransformedQuery


def _is_obviously_direct(query: str) -> bool:
    """Identify simple technical queries that can be searched as written."""
    text = query.strip()

    if not text:
        return False

    has_technical_marker = any(
        marker in text for marker in ("@", "()", "->", "::", "Traceback")
    )

    words = text.split()
    is_short_direct_question = len(words) <= 10 and (
        text.startswith(("How do I ", "What is ", "How to ")) or text.endswith("?")
    )

    return has_technical_marker or is_short_direct_question


def _is_obviously_out_of_scope(query: str) -> bool:
    """Detect clearly unrelated or live-information requests."""
    text = query.casefold()

    out_of_scope_patterns = (
        "current weather",
        "latest stock price",
        "write a poem",
        "latest fifa world cup",
    )

    return any(pattern in text for pattern in out_of_scope_patterns)


async def transform_query(query: str) -> TransformedQuery:
    """Analyze a question and produce retrieval queries."""
    started = time.perf_counter()
    original = query.strip()

    with logfire.span(
        "query_transformation",
        query_chars=len(original),
    ):
        if not original:
            logfire.warn("Query transformation rejected an empty query")
            raise ValueError("Query cannot be empty.")

        if _is_obviously_out_of_scope(original):
            logfire.info(
                "Query transformation fast path",
                strategy="out_of_scope",
                analyzer_skipped=True,
            )
            return TransformedQuery(
                original_query=original,
                analysis=QueryAnalysis(
                    strategy="out_of_scope",
                    reason=(
                        "Fast path: request is outside FastAPI documentation scope."
                    ),
                    search_query="",
                ),
                retrieval_queries=[],
            )

        if _is_obviously_direct(original):
            logfire.info(
                "Query transformation fast path",
                strategy="direct",
                analyzer_skipped=True,
            )
            return TransformedQuery(
                original_query=original,
                analysis=QueryAnalysis(
                    strategy="direct",
                    reason="Fast path: query is directly searchable.",
                    search_query=original,
                ),
                retrieval_queries=[original],
            )

        analysis_started = time.perf_counter()

        try:
            with logfire.span("query.analyze"):
                analysis = await analyze_query(original)

        except Exception as exc:
            logfire.error(
                "Query analysis failed; falling back to direct retrieval",
                error_type=type(exc).__name__,
                elapsed_ms=round((time.perf_counter() - analysis_started) * 1000, 2),
            )
            analysis = QueryAnalysis(
                strategy="direct",
                reason="Query analysis failed; using original query.",
                search_query=original,
            )

        result = TransformedQuery(
            original_query=original,
            analysis=analysis,
        )

        strategy = analysis.strategy

        logfire.info(
            "Query strategy selected",
            strategy=strategy,
            analyzer_ms=round((time.perf_counter() - analysis_started) * 1000, 2),
        )

        if strategy in {"clarify", "out_of_scope"}:
            logfire.info(
                "Query transformation completed",
                strategy=strategy,
                retrieval_query_count=0,
                total_ms=round((time.perf_counter() - started) * 1000, 2),
            )
            return result

        with logfire.span("query.generate_retrieval_queries", strategy=strategy):
            if strategy == "direct":
                result.retrieval_queries = [original]

            elif strategy == "rewrite":
                with logfire.span("query.rewrite"):
                    rewritten = await rewrite_query(analysis.search_query or original)
                result.retrieval_queries = [rewritten]

            elif strategy == "multi_query":
                with logfire.span("query.multi_query"):
                    result.retrieval_queries = await generate_query_variants(
                        analysis.search_query or original
                    )

                # Always retain the original wording as a candidate.
                if original not in result.retrieval_queries:
                    result.retrieval_queries.insert(0, original)

            elif strategy == "hyde":
                result.retrieval_queries = [original]
                with logfire.span("query.hyde"):
                    result.hypothetical_document = await generate_hypothetical_document(
                        original
                    )

            elif strategy == "decompose":
                with logfire.span("query.decompose"):
                    result.retrieval_queries = await decompose_query(
                        analysis.search_query or original
                    )

        if not result.retrieval_queries:
            result.retrieval_queries = [original]

        logfire.info(
            "Query transformation completed",
            strategy=strategy,
            retrieval_query_count=len(result.retrieval_queries),
            hypothetical_document_generated=(result.hypothetical_document is not None),
            total_ms=round((time.perf_counter() - started) * 1000, 2),
        )

        return result
