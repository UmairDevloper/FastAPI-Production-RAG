import logging

from app.query_transformation.analyzer import analyze_query
from app.query_transformation.decomposer import decompose_query
from app.query_transformation.hyde import generate_hypothetical_document
from app.query_transformation.multi_query import generate_query_variants
from app.query_transformation.rewriter import rewrite_query
from app.query_transformation.schemas import QueryAnalysis, TransformedQuery

logger = logging.getLogger(__name__)

"""
Query transformation service for routing questions to the appropriate
retrieval strategy.
"""

def _is_obviously_direct(query: str) -> bool:
    """Identify simple technical queries that can be searched as written."""
    text = query.strip()

    if not text:
        return False

    # Code, API names, configuration values, and error-like strings
    # are usually best searched without rewriting.
    has_technical_marker = any(
        marker in text for marker in ("@", "()", "->", "::", "Traceback")
    )

    # Short, focused technical questions are usually directly searchable.
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
    original = query.strip()


    if not original:
        raise ValueError("Query cannot be empty.")

    if _is_obviously_out_of_scope(original):
        logger.info("Out-of-scope fast path used; skipping analyzer.")
        return TransformedQuery(
            original_query=original,
            analysis=QueryAnalysis(
                strategy="out_of_scope",
                reason="Fast path: request is outside FastAPI documentation scope.",
                search_query="",
            ),
            retrieval_queries=[],
        )

    if _is_obviously_direct(original):
        logger.info("Query transformation fast path used; skipping analyzer.")
        return TransformedQuery(
            original_query=original,
            analysis=QueryAnalysis(
                strategy="direct",
                reason="Fast path: query is directly searchable.",
                search_query=original,
            ),
            retrieval_queries=[original],
        )

    try:
        analysis = await analyze_query(original)
    except Exception:
        logger.exception(
            "Query analysis failed; falling back to direct retrieval."
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

    if analysis.strategy in {"clarify", "out_of_scope"}:
        return result

    if analysis.strategy == "direct":
        result.retrieval_queries = [original]

    elif analysis.strategy == "rewrite":
        rewritten = await rewrite_query(
            analysis.search_query or original
        )
        result.retrieval_queries = [rewritten]

    elif analysis.strategy == "multi_query":
        result.retrieval_queries = await generate_query_variants(
            analysis.search_query or original
        )

        # Always retain the original wording as a candidate.
        if original not in result.retrieval_queries:
            result.retrieval_queries.insert(0, original)

    elif analysis.strategy == "hyde":
        result.retrieval_queries = [original]
        result.hypothetical_document = (
            await generate_hypothetical_document(original)
        )

    elif analysis.strategy == "decompose":
        result.retrieval_queries = await decompose_query(
            analysis.search_query or original
        )

    if not result.retrieval_queries:
        result.retrieval_queries = [original]

    return result

