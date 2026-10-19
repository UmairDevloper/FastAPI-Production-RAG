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

import logfire
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


def hit_at_k(
    ranked_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    if not relevant_ids:
        return 0.0
    return float(bool(set(ranked_ids[:k]) & relevant_ids))


def mrr_at_k(
    ranked_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    for rank, doc_id in enumerate(ranked_ids[:k], start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(
    ranked_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    if not relevant_ids:
        return 0.0

    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, doc_id in enumerate(ranked_ids[:k], start=1)
        if doc_id in relevant_ids
    )

    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))

    return dcg / idcg if idcg else 0.0


def latency_summary(values: list[float]) -> dict[str, float]:
    if not values:
        return {}

    ordered = sorted(values)

    def percentile(p: float) -> float:
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
    metrics = {f"hit@{k}": hit_at_k(ranked_ids, relevant_ids, k) for k in KS}
    metrics["mrr@20"] = mrr_at_k(ranked_ids, relevant_ids, 20)
    metrics["ndcg@10"] = ndcg_at_k(ranked_ids, relevant_ids, 10)
    return metrics


def retrieve_one(retriever: Any, query: str) -> list[Any]:
    if not query.strip():
        return []

    documents = retriever.invoke(query)
    return list(documents or [])


# Build queries for a requested transformation strategy.


async def build_strategy_queries(
    query: str,
    strategy_mode: str,
) -> tuple[str, list[str]]:
    with logfire.span(
        "evaluation.build_strategy_queries",
        strategy_mode=strategy_mode,
        query_chars=len(query),
    ):
        if strategy_mode == "direct":
            return "direct", [query]

        if strategy_mode == "rewrite":
            with logfire.span("evaluation.rewrite"):
                rewritten = await rewrite_query(query)

            if not rewritten or not rewritten.strip():
                raise ValueError("Rewrite returned an empty query")

            return "rewrite", [rewritten.strip()]

        if strategy_mode == "multi_query":
            with logfire.span("evaluation.multi_query"):
                variants = await generate_query_variants(query)

            variants = [
                item.strip()
                for item in (variants or [])
                if isinstance(item, str) and item.strip()
            ]
            queries = list(dict.fromkeys([query, *variants]))
            return "multi_query", queries

        if strategy_mode == "hyde":
            with logfire.span("evaluation.hyde"):
                hypothetical_document = await generate_hypothetical_document(query)

            if not hypothetical_document or not hypothetical_document.strip():
                raise ValueError("HyDE returned an empty hypothetical document")

            return "hyde", [hypothetical_document.strip()]

        if strategy_mode == "decompose":
            from app.query_transformation.decomposer import decompose_query

            with logfire.span("evaluation.decompose"):
                queries = await decompose_query(query)

            queries = [
                item.strip()
                for item in queries
                if isinstance(item, str) and item.strip()
            ]
            return "decompose", list(dict.fromkeys(queries))

        if strategy_mode == "auto":
            with logfire.span("evaluation.auto_transform"):
                result = await transform_query(query)

            strategy = result.analysis.strategy
            queries = result.retrieval_queries or []

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
    case_index: int | None = None,
) -> dict[str, Any]:
    query = get_query(case)
    case_started = time.perf_counter()

    with logfire.span(
        "evaluation.case",
        case_index=case_index,
        strategy_mode=strategy_mode,
        query_chars=len(query),
    ):
        relevant_ids = set(expected_ids(case, chunks, require_keyword=True))

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

        # Baseline retrieval.
        with logfire.span("evaluation.baseline_retrieval"):
            started = time.perf_counter()
            baseline_docs = retrieve_one(retriever, query)

            result["baseline_latency_ms"] = round(
                (time.perf_counter() - started) * 1000, 2
            )

            baseline_ids = [get_doc_id(doc) for doc in baseline_docs]
            result["baseline"] = evaluate_ranking(baseline_ids, relevant_ids)

            logfire.info(
                "Baseline retrieval completed",
                documents_returned=len(baseline_docs),
                relevant_document_count=len(relevant_ids),
                latency_ms=result["baseline_latency_ms"],
                hit_at_5=result["baseline"]["hit@5"],
                mrr_at_20=result["baseline"]["mrr@20"],
            )

        try:
            if strategy_mode == "rerank":
                if reranker is None:
                    raise ValueError("Reranker is required for reranking evaluation.")

                with logfire.span(
                    "evaluation.reranking",
                    input_documents=len(baseline_docs),
                ):
                    started = time.perf_counter()

                    transformed_docs = reranker.compress_documents(
                        baseline_docs,
                        query=query,
                    )

                    result["reranking_latency_ms"] = round(
                        (time.perf_counter() - started) * 1000, 2
                    )

                    result["reranked_total_latency_ms"] = round(
                        result["baseline_latency_ms"] + result["reranking_latency_ms"],
                        2,
                    )

                    result["strategy"] = "dense+minilm_rerank"

                    logfire.info(
                        "Reranking completed",
                        input_documents=len(baseline_docs),
                        output_documents=len(transformed_docs),
                        latency_ms=result["reranking_latency_ms"],
                    )

            elif strategy_mode == "orchestrated":
                if orchestrator is None:
                    raise ValueError(
                        "Orchestrator is required for orchestrated evaluation."
                    )

                with logfire.span("evaluation.orchestration"):
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
                    result["strategy"] = diagnostics.strategy
                    result["orchestration_diagnostics"] = retrieval_result.to_dict()
                    transformed_docs = retrieval_result.candidates

                    logfire.info(
                        "Orchestration completed",
                        strategy=result["strategy"],
                        candidate_count=len(transformed_docs),
                        transformation_ms=result["transformation_latency_ms"],
                        retrieval_ms=result["transformed_retrieval_latency_ms"],
                        fusion_ms=result["fusion_latency_ms"],
                        total_ms=result["orchestration_latency_ms"],
                    )

            else:
                # Query transformation.
                with logfire.span("evaluation.transformation"):
                    started = time.perf_counter()
                    strategy, queries = await build_strategy_queries(
                        query, strategy_mode
                    )

                    result["transformation_latency_ms"] = round(
                        (time.perf_counter() - started) * 1000, 2
                    )
                    result["strategy"] = strategy

                    logfire.info(
                        "Evaluation transformation completed",
                        strategy=strategy,
                        query_count=len(queries),
                        latency_ms=result["transformation_latency_ms"],
                    )

                if not queries:
                    result["error"] = "Transformation produced no retrieval queries"
                    result["transformed"] = evaluate_ranking([], relevant_ids)

                    logfire.warn(
                        "Transformation produced no retrieval queries",
                        strategy=strategy,
                    )

                    logfire.info(
                        "Evaluation case completed",
                        case_index=case_index,
                        status="no_retrieval_queries",
                        total_ms=round(
                            (time.perf_counter() - case_started) * 1000,
                            2,
                        ),
                    )
                    return result

                # Retrieve and fuse transformed queries.
                with logfire.span(
                    "evaluation.transformed_retrieval",
                    query_count=len(queries),
                    retrieval_k=RETRIEVAL_K,
                ):
                    started = time.perf_counter()

                    result_lists = [retrieve_one(retriever, item) for item in queries]

                    if len(result_lists) == 1:
                        transformed_docs = result_lists[0]
                    else:
                        with logfire.span(
                            "evaluation.reciprocal_rank_fusion",
                            result_list_count=len(result_lists),
                            rrf_k=RRF_K,
                        ):
                            transformed_docs = reciprocal_rank_fusion(
                                result_lists,
                                k=RRF_K,
                            )

                    result["transformed_retrieval_latency_ms"] = round(
                        (time.perf_counter() - started) * 1000, 2
                    )
                    result["retrieval_queries"] = queries

                    logfire.info(
                        "Transformed retrieval completed",
                        query_count=len(queries),
                        result_counts=[len(items) for items in result_lists],
                        fused_document_count=len(transformed_docs),
                        latency_ms=result["transformed_retrieval_latency_ms"],
                    )

            transformed_ids = [
                get_doc_id(doc) for doc in transformed_docs[:RETRIEVAL_K]
            ]

            with logfire.span("evaluation.ranking_metrics"):
                result["transformed"] = evaluate_ranking(transformed_ids, relevant_ids)

            logfire.info(
                "Evaluation ranking completed",
                strategy=result["strategy"],
                returned_documents=len(transformed_docs),
                hit_at_1=result["transformed"]["hit@1"],
                hit_at_5=result["transformed"]["hit@5"],
                hit_at_10=result["transformed"]["hit@10"],
                mrr_at_20=result["transformed"]["mrr@20"],
                ndcg_at_10=result["transformed"]["ndcg@10"],
                baseline_hit_at_5=result["baseline"]["hit@5"],
                hit_at_5_delta=(
                    result["transformed"]["hit@5"] - result["baseline"]["hit@5"]
                ),
            )

        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
            result["transformed"] = evaluate_ranking([], relevant_ids)

            logfire.error(
                "Evaluation case failed",
                case_index=case_index,
                strategy_mode=strategy_mode,
                error_type=type(exc).__name__,
            )
            logger.exception("Failed to evaluate query: %s", query)

        result["case_latency_ms"] = round(
            (time.perf_counter() - case_started) * 1000, 2
        )

        logfire.info(
            "Evaluation case completed",
            case_index=case_index,
            strategy=result["strategy"],
            status="error" if result["error"] else "success",
            baseline_latency_ms=result["baseline_latency_ms"],
            transformation_latency_ms=result["transformation_latency_ms"],
            transformed_retrieval_latency_ms=result["transformed_retrieval_latency_ms"],
            total_ms=result["case_latency_ms"],
        )

        return result


# Summary metrics and report output.


def summarize(results: list[dict[str, Any]]) -> None:
    with logfire.span(
        "evaluation.summarize",
        result_count=len(results),
    ):
        if not results:
            logger.warning("No evaluation results to summarize.")
            logfire.warn("No evaluation results to summarize")
            return

        logger.info("Queries evaluated: %d", len(results))

        for ranking_name in ("baseline", "transformed"):
            logger.info("%s metrics:", ranking_name)

            for metric in (
                "hit@1",
                "hit@3",
                "hit@5",
                "hit@10",
                "hit@20",
                "mrr@20",
                "ndcg@10",
            ):
                values = [
                    item[ranking_name][metric]
                    for item in results
                    if metric in item.get(ranking_name, {})
                ]
                mean = sum(values) / len(values) if values else 0.0
                logger.info("  %-10s %.3f", metric, mean)

                logfire.info(
                    "Evaluation aggregate metric",
                    ranking=ranking_name,
                    metric=metric,
                    mean=round(mean, 6),
                    sample_count=len(values),
                )

        strategy_counts = dict(
            Counter(item.get("strategy", "unknown") for item in results)
        )
        logger.info("Strategies: %s", strategy_counts)

        errors = [item for item in results if item.get("error")]
        logger.info("Queries with errors: %d", len(errors))

        logfire.info(
            "Evaluation aggregate status",
            total_cases=len(results),
            failed_cases=len(errors),
            successful_cases=len(results) - len(errors),
            strategy_counts=strategy_counts,
        )

        for item in errors:
            logger.warning(
                "Error for %r: %s",
                item["query"],
                item["error"],
            )

        for latency_key in (
            "baseline_latency_ms",
            "transformation_latency_ms",
            "transformed_retrieval_latency_ms",
            "fusion_latency_ms",
            "orchestration_latency_ms",
            "reranking_latency_ms",
            "reranked_total_latency_ms",
            "case_latency_ms",
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

                logfire.info(
                    "Evaluation latency aggregate",
                    stage=latency_key,
                    sample_count=len(values),
                    mean_ms=round(stats["mean"], 2),
                    p50_ms=round(stats["p50"], 2),
                    p95_ms=round(stats["p95"], 2),
                )


async def main(strategy_mode: str, limit: int) -> None:
    # Configure Logfire before emitting evaluation spans/events.
    configure_logfire()

    run_started = time.perf_counter()

    with logfire.span(
        "evaluation.run",
        strategy_mode=strategy_mode,
        limit=limit,
        retrieval_k=RETRIEVAL_K,
        rrf_k=RRF_K,
    ):
        logger.info(
            "Starting evaluator | strategy=%s | limit=%s",
            strategy_mode,
            limit,
        )

        with logfire.span("evaluation.load_chunks"):
            chunks = load_chunks()

        cases = list(CASES)
        if limit > 0:
            cases = cases[:limit]

        logfire.info(
            "Evaluation inputs loaded",
            chunk_count=len(chunks),
            case_count=len(cases),
            strategy_mode=strategy_mode,
        )
        logger.info(
            "Loaded %d chunks and %d evaluation cases",
            len(chunks),
            len(cases),
        )

        with logfire.span(
            "evaluation.build_dense_retriever",
            retrieval_k=RETRIEVAL_K,
        ):
            retriever = build_dense_retriever(k=RETRIEVAL_K)

        with logfire.span("evaluation.build_orchestrator"):
            orchestrator = RetrievalOrchestrator(
                retriever,
                rrf_k=RRF_K,
                max_concurrency=4,
            )

        reranker = None

        if strategy_mode == "rerank":
            with logfire.span("evaluation.load_and_warm_reranker"):
                reranker = CrossEncoderCompressor(
                    model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
                    top_n=RETRIEVAL_K,
                    batch_size=16,
                    max_length=512,
                    fail_open=False,
                )

                # Warm-up time is deliberately excluded from per-case timings.
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
            logfire.info("MiniLM reranker loaded and warmed up")

        # Initialize for every strategy, not only rerank.
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
                case_index=index,
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

        with (
            logfire.span(
                "evaluation.save_results",
                result_count=len(results),
                output_file=str(output_file),
            ),
            output_file.open("w", encoding="utf-8") as file,
        ):
            json.dump(results, file, indent=2, ensure_ascii=False)
            
        total_ms = round((time.perf_counter() - run_started) * 1000, 2)

        logger.info("Results saved to %s", output_file)
        logger.info("Log saved to %s", LOG_FILE)

        logfire.info(
            "Evaluation run completed",
            strategy_mode=strategy_mode,
            result_count=len(results),
            failed_cases=sum(bool(item["error"]) for item in results),
            total_ms=total_ms,
            output_file=str(output_file),
        )


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
