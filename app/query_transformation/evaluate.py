from __future__ import annotations

import argparse
import asyncio
import json
import logging
import math
import time
from collections import Counter
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

from app.indexing.dense_indexing.reranker2 import CrossEncoderCompressor
from app.ingestion.embedding4.embedder import load_chunks
from app.ingestion.embedding4.models_config import configure_logfire
from app.ingestion.evaluate import CASES, expected_ids
from app.query_transformation.hyde import generate_hypothetical_document
from app.query_transformation.multi_query import generate_query_variants
from app.query_transformation.rewriter import rewrite_query
from app.query_transformation.service import transform_query
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.orchestrator import RetrievalOrchestrator
from app.retrieval.retriever import build_dense_retriever

# Configuration

KS = (1, 3, 5, 10, 20)
RETRIEVAL_K = 20
RRF_K = 60

OUTPUT_DIR = Path("reports/query_transformation")
LOG_FILE = OUTPUT_DIR / "evaluator.log"

STRATEGIES = (
    "auto",
    "direct",
    "rewrite",
    "multi_query",
    "decompose",
    "hyde",
    "orchestrated",
    "rerank",
)


# Logging

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
    force=True,
)

logger = logging.getLogger(__name__)


# General helpers

def get_query(case: Any) -> str:
    if isinstance(case, str):
        return case

    if isinstance(case, dict):
        for key in ("query", "question", "input"):
            if case.get(key):
                return str(case[key])

    for key in ("query", "question", "input"):
        value = getattr(case, key, None)
        if value:
            return str(value)

    raise ValueError(f"Cannot extract query from case: {case!r}")


def get_doc_id(doc: Any) -> str:
    metadata = getattr(doc, "metadata", {}) or {}

    for key in ("chunk_id", "id", "point_id"):
        value = metadata.get(key)
        if value is not None:
            return str(value)

    url = metadata.get("url", "")
    heading = metadata.get("heading_path", "")
    content = getattr(doc, "page_content", "")
    return f"{url}|{heading}|{content[:150]}"


def hit_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    return float(bool(set(ranked_ids[:k]) & relevant_ids))


def mrr_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    for rank, doc_id in enumerate(ranked_ids[:k], start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0

    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, doc_id in enumerate(ranked_ids[:k], start=1)
        if doc_id in relevant_ids
    )

    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(
        1.0 / math.log2(rank + 1)
        for rank in range(1, ideal_hits + 1)
    )

    return dcg / idcg if idcg else 0.0

def latency_summary(values: list[float]) -> dict[str, float]:
    if not values:
        return {}

    ordered = sorted(values)

    def percentile(p: float) -> float:
        # Nearest-rank percentile.
        index = max(0, math.ceil(p * len(ordered)) - 1)
        return ordered[index]

    return {
        "mean": sum(ordered) / len(ordered),
        "p50": percentile(0.50),
        "p95": percentile(0.95),
    }

def evaluate_ranking(
    ranked_ids: list[str],
    relevant_ids: set[str],
) -> dict[str, float]:
    metrics = {
        f"hit@{k}": hit_at_k(ranked_ids, relevant_ids, k)
        for k in KS
    }
    metrics["mrr@20"] = mrr_at_k(ranked_ids, relevant_ids, 20)
    metrics["ndcg@10"] = ndcg_at_k(ranked_ids, relevant_ids, 10)
    return metrics



def retrieve_one(retriever: Any, query: str) -> list[Any]:
    if not query.strip():
        return []

    documents = retriever.invoke(query)
    return list(documents or [])


# Run one requested transformation strategy.

async def build_strategy_queries(
    query: str,
    strategy_mode: str,
) -> tuple[str, list[str]]:
    if strategy_mode == "direct":
        return "direct", [query]

    if strategy_mode == "rewrite":
        rewritten = await rewrite_query(query)
        if not rewritten or not rewritten.strip():
            raise ValueError("Rewrite returned an empty query")
        return "rewrite", [rewritten.strip()]

    if strategy_mode == "multi_query":
        variants = await generate_query_variants(query)
        variants = [
            item.strip()
            for item in (variants or [])
            if isinstance(item, str) and item.strip()
        ]
        queries = list(dict.fromkeys([query, *variants]))
        return "multi_query", queries

    if strategy_mode == "hyde":
        hypothetical_document = await generate_hypothetical_document(query)
        if not hypothetical_document or not hypothetical_document.strip():
            raise ValueError("HyDE returned an empty hypothetical document")
        return "hyde", [hypothetical_document.strip()]

    if strategy_mode == "decompose":
        from app.query_transformation.decomposer import decompose_query

        queries = await decompose_query(query)
        queries = [
            item.strip()
            for item in queries
            if isinstance(item, str) and item.strip()
        ]
        return "decompose", list(dict.fromkeys(queries))
    
    if strategy_mode == "auto":
        result = await transform_query(query)

        # TransformedQuery is a dataclass:
        # strategy is inside result.analysis
        strategy = result.analysis.strategy
        queries = result.retrieval_queries or []

        # HyDE creates a hypothetical document separately.
        # Use it for retrieval when available.
        if strategy == "hyde" and result.hypothetical_document:
            queries = [result.hypothetical_document]

        queries = [
            item.strip()
            for item in queries
            if isinstance(item, str) and item.strip()
        ]

        return strategy, queries
    
    raise ValueError(f"Unsupported strategy: {strategy_mode}")


async def evaluate_case(
    case: Any,
    chunks: list[Any],
    retriever: Any,
    strategy_mode: str,
    orchestrator: RetrievalOrchestrator | None = None,
    reranker: CrossEncoderCompressor | None = None,
) -> dict[str, Any]:
    query = get_query(case)
    relevant_ids = set(
        expected_ids(case, chunks, require_keyword=True)
    )

    result: dict[str, Any] = {
        "query": query,
        "strategy_mode": strategy_mode,
        "strategy": strategy_mode,
        "baseline": {},
        "transformed": {},
        "baseline_latency_ms": 0.0,
        "transformation_latency_ms": 0.0,
        "transformed_retrieval_latency_ms": 0.0,
        "error": None,
        "orchestration_latency_ms": None,
        "orchestration_diagnostics": {},
        "reranking_latency_ms": None,
        "reranked_total_latency_ms": None,
    }

    # Baseline retrieval uses the original query.
    started = time.perf_counter()
    baseline_docs = retrieve_one(retriever, query)
    result["baseline_latency_ms"] = round(
        (time.perf_counter() - started) * 1000, 2
    )

    baseline_ids = [get_doc_id(doc) for doc in baseline_docs]
    result["baseline"] = evaluate_ranking(baseline_ids, relevant_ids)


    # Transform the query and retrieve candidates.
    try:
        if strategy_mode == "rerank":
            if reranker is None:
                raise ValueError(
                    "Reranker is required for reranking evaluation."
                )

            started = time.perf_counter()

            transformed_docs = reranker.compress_documents(
                baseline_docs,
                query=query,
            )

            result["reranking_latency_ms"] = round(
                (time.perf_counter() - started) * 1000,
                2,
            )

            result["reranked_total_latency_ms"] = round(
                result["baseline_latency_ms"]
                + result["reranking_latency_ms"],
                2,
            )

            result["strategy"] = "dense+minilm_rerank"

        elif strategy_mode == "orchestrated":
            if orchestrator is None:
                raise ValueError(
                    "Orchestrator is required for orchestrated evaluation."
                )

            started = time.perf_counter()
            retrieval_result = await orchestrator.retrieve(query)

            diagnostics = retrieval_result.diagnostics

            result["transformation_latency_ms"] = (
                diagnostics.transformation_latency_ms
            )
            result["transformed_retrieval_latency_ms"] = (
                diagnostics.retrieval_latency_ms
            )
            result["fusion_latency_ms"] = diagnostics.fusion_latency_ms

            result["orchestration_latency_ms"] = round(
                (time.perf_counter() - started) * 1000, 2
            )

            result["strategy"] = (
                retrieval_result.diagnostics.strategy
            )
            result["orchestration_diagnostics"] = (
                retrieval_result.to_dict()
            )

            transformed_docs = retrieval_result.candidates

        else:
            started = time.perf_counter()
            strategy, queries = await build_strategy_queries(
                query, strategy_mode
            )

            result["transformation_latency_ms"] = round(
                (time.perf_counter() - started) * 1000, 2
            )
            result["strategy"] = strategy

            if not queries:
                result["error"] = (
                    "Transformation produced no retrieval queries"
                )
                result["transformed"] = evaluate_ranking(
                    [], relevant_ids
                )
                return result

            started = time.perf_counter()

            result_lists = [
                retrieve_one(retriever, item)
                for item in queries
            ]

            if len(result_lists) == 1:
                transformed_docs = result_lists[0]
            else:
                transformed_docs = reciprocal_rank_fusion(
                    result_lists,
                    k=RRF_K,
                )

            result["transformed_retrieval_latency_ms"] = round(
                (time.perf_counter() - started) * 1000, 2
            )
            result["retrieval_queries"] = queries

        transformed_ids = [
            get_doc_id(doc)
            for doc in transformed_docs[:RETRIEVAL_K]
        ]

        result["transformed"] = evaluate_ranking(
            transformed_ids, relevant_ids
        )

    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["transformed"] = evaluate_ranking([], relevant_ids)
        logger.exception("Failed to evaluate query: %s", query)

    return result




# Print summary metrics and save the detailed results.

def summarize(results: list[dict[str, Any]]) -> None:
    if not results:
        logger.warning("No evaluation results to summarize.")
        return

    logger.info("Queries evaluated: %d", len(results))

    for ranking_name in ("baseline", "transformed"):
        logger.info("%s metrics:", ranking_name)

        for metric in (
            "hit@1", "hit@3", "hit@5", "hit@10", "hit@20",
            "mrr@20", "ndcg@10",
        ):
            values = [
                item[ranking_name][metric]
                for item in results
                if metric in item.get(ranking_name, {})
            ]
            mean = sum(values) / len(values) if values else 0.0
            logger.info("  %-10s %.3f", metric, mean)

    logger.info(
        "Strategies: %s",
        dict(Counter(item.get("strategy", "unknown") for item in results)),
    )

    errors = [item for item in results if item.get("error")]
    logger.info("Queries with errors: %d", len(errors))

    for item in errors:
        logger.warning("Error for %r: %s", item["query"], item["error"])

    for latency_key in (
        "baseline_latency_ms",
        "transformation_latency_ms",
        "transformed_retrieval_latency_ms",
        "fusion_latency_ms",
        "orchestration_latency_ms",
        "reranking_latency_ms",
        "reranked_total_latency_ms",
    ):
        values = [
                float(item[latency_key])
                for item in results
                if item.get(latency_key) is not None
        ]

        stats = latency_summary(values)
        if stats:
            logger.info(
                    "%s | mean=%.1f ms | p50=%.1f ms | p95=%.1f ms",
                    latency_key,
                    stats["mean"],
                    stats["p50"],
                    stats["p95"],
            )

async def main(strategy_mode: str, limit: int) -> None:
    logger.info(
        "Starting evaluator | strategy=%s | limit=%s",
        strategy_mode,
        limit,
    )
    configure_logfire()

    chunks = load_chunks()
    cases = list(CASES)

    if limit > 0:
        cases = cases[:limit]

    logger.info("Loaded %d chunks and %d evaluation cases", len(chunks), len(cases))
    retriever = build_dense_retriever(k=RETRIEVAL_K)
    orchestrator = RetrievalOrchestrator(
        retriever,
        rrf_k=RRF_K,
        max_concurrency=4,
    )
    
    reranker = None

    if strategy_mode == "rerank":
        reranker = CrossEncoderCompressor(
            model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
            top_n=RETRIEVAL_K,
            batch_size=16,
            max_length=512,
            fail_open=False,
        )

        # Warm up the model so model loading does not distort
        # the measured per-query reranking latency.
        reranker.compress_documents(
            [
                Document(
                    page_content="FastAPI request body",
                    metadata={},
                )
            ],
            query="FastAPI request body",
        )

        logger.info("MiniLM reranker loaded and warmed up.")

        results: list[dict[str, Any]] = []

    for index, case in enumerate(cases, start=1):
        query = get_query(case)
        logger.info("[%d/%d] %s", index, len(cases), query)

        result = await evaluate_case(
            case=case,
            chunks=chunks,
            retriever=retriever,
            strategy_mode=strategy_mode,
            orchestrator=orchestrator,
            reranker=reranker,
        )

        results.append(result)

        logger.info(
            "  baseline hit@5=%.2f | transformed hit@5=%.2f | strategy=%s",
            result["baseline"].get("hit@5", 0.0),
            result["transformed"].get("hit@5", 0.0),
            result.get("strategy", "unknown"),
        )

    summarize(results)

    output_file = OUTPUT_DIR / f"results_{strategy_mode}.json"
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=2, ensure_ascii=False)

    logger.info("Results saved to %s", output_file)
    logger.info("Log saved to %s", LOG_FILE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strategy",
        choices=STRATEGIES,
        default="direct",
        help="Strategy to evaluate",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of cases; use 0 to evaluate all cases",
    )
    args = parser.parse_args()

    asyncio.run(main(args.strategy, args.limit))
