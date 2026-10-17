from __future__ import annotations

import argparse
import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

from app.indexing.dense_indexing.reranker2 import CrossEncoderCompressor
from app.ingestion.embedding4.embedder import load_chunks
from app.ingestion.embedding4.models_config import configure_logfire
from app.ingestion.evaluate import CASES, expected_ids
from app.retrieval.context_assembly import assemble_context
from app.retrieval.deduplication import get_document_id
from app.retrieval.orchestrator import RetrievalOrchestrator
from app.retrieval.retriever import build_dense_retriever

# Configuration

OUTPUT_DIR = Path("reports/context_assembly")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = OUTPUT_DIR / "evaluator.log"
RESULT_FILE = OUTPUT_DIR / "results_context.json"

RETRIEVAL_K = 20
RERANK_TOP_N = 8
MAX_CONTEXT_TOKENS = 4000
MAX_CONTEXT_DOCUMENTS = 8


# Logging

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


# Helpers


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


def relevant_hit(
    documents: list[Document],
    relevant_ids: set[str] | list[str],
) -> bool:
    expected = {str(value) for value in relevant_ids}

    for doc in documents:
        metadata = doc.metadata

        # Ground-truth IDs are raw chunk_id values.
        chunk_id = metadata.get("chunk_id")
        if chunk_id is not None and str(chunk_id) in expected:
            return True

    return False


# Evaluation


async def evaluate_case(
    case: Any,
    chunks: list[Any],
    orchestrator: RetrievalOrchestrator,
    reranker: CrossEncoderCompressor,
) -> dict[str, Any]:
    query = get_query(case)
    relevant_ids = set(expected_ids(case, chunks, require_keyword=True))

    print("\n--- RELEVANCE ID DEBUG ---")
    print("Query:", query)
    print("Relevant IDs:", list(relevant_ids)[:5])

    debug_retrieval = await orchestrator.retrieve(query)

    print("Retrieved document IDs:")
    for doc in debug_retrieval.candidates[:5]:
        print(
            get_document_id(doc),
            "| metadata:",
            {
                key: doc.metadata.get(key)
                for key in ("chunk_id", "point_id", "id")
            },
        )

    print("Relevant IDs type:", {
        type(value).__name__ for value in relevant_ids
    })
    print("--- END DEBUG ---\n")
    
    result: dict[str, Any] = {
        "query": query,
        "relevant_id_count": len(relevant_ids),
        "retrieved_count": 0,
        "reranked_count": 0,
        "selected_count": 0,
        "context_tokens": 0,
        "omitted_documents": 0,
        "retrieved_hit@20": False,
        "reranked_hit@8": False,
        "context_hit@8": False,
        "context_hit@5": False,
        "duplicate_evidence": 0,
        "retrieval_latency_ms": 0.0,
        "reranking_latency_ms": 0.0,
        "assembly_latency_ms": 0.0,
        "error": None,
    }

    try:
        # Retrieve candidates.
        started = time.perf_counter()
        retrieval = await orchestrator.retrieve(query)

        result["retrieval_latency_ms"] = round(
            (time.perf_counter() - started) * 1000,
            2,
        )

        candidates = retrieval.candidates
        result["retrieved_count"] = len(candidates)

        result["retrieved_hit@20"] = relevant_hit(
            candidates[:20],
            relevant_ids,
        )

        # Rerank candidates.
        started = time.perf_counter()
        reranked = reranker.compress_documents(
            candidates,
            query=query,
        )

        result["reranking_latency_ms"] = round(
            (time.perf_counter() - started) * 1000,
            2,
        )

        result["reranked_count"] = len(reranked)

        result["reranked_hit@8"] = relevant_hit(
            reranked[:8],
            relevant_ids,
        )

        # Count repeated document IDs before context assembly.
        candidate_ids = [get_document_id(doc) for doc in reranked]

        result["duplicate_evidence"] = len(candidate_ids) - len(set(candidate_ids))

        # Assemble final context.
        started = time.perf_counter()
        assembled = assemble_context(
            list(reranked),
            max_tokens=MAX_CONTEXT_TOKENS,
            max_documents=MAX_CONTEXT_DOCUMENTS,
        )

        result["assembly_latency_ms"] = round(
            (time.perf_counter() - started) * 1000,
            2,
        )

        result["selected_count"] = len(assembled.evidence)
        result["context_tokens"] = assembled.estimated_tokens
        result["omitted_documents"] = assembled.omitted_documents

        
        context_documents = [
            Document(
                page_content=item.content,
                metadata={"chunk_id": item.evidence_id.removeprefix("chunk_id:")},
            )
            for item in assembled.evidence
        ]

        result["context_hit@8"] = relevant_hit(
            context_documents,
            relevant_ids,
        )

        result["context_hit@5"] = relevant_hit(
            context_documents[:5],
            relevant_ids,
        )

        result["strategy"] = retrieval.diagnostics.strategy
        result["retrieval_errors"] = retrieval.diagnostics.errors

    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        logger.exception("Failed to evaluate query: %s", query)

    return result


# Reporting


def summarize(results: list[dict[str, Any]]) -> None:
    successful = [item for item in results if item["error"] is None]

    logger.info("Queries evaluated: %d", len(results))
    logger.info("Successful queries: %d", len(successful))
    logger.info("Failed queries: %d", len(results) - len(successful))

    if not successful:
        return

    total = len(successful)

    for key in (
        "retrieved_hit@20",
        "reranked_hit@8",
        "context_hit@8",
        "context_hit@5",
    ):
        hits = sum(bool(item[key]) for item in successful)

        logger.info(
            "%-20s %.3f (%d/%d)",
            key,
            hits / total,
            hits,
            total,
        )

    for key in (
        "retrieved_count",
        "reranked_count",
        "selected_count",
        "context_tokens",
        "omitted_documents",
        "duplicate_evidence",
        "retrieval_latency_ms",
        "reranking_latency_ms",
        "assembly_latency_ms",
    ):
        values = [float(item[key]) for item in successful]

        logger.info(
            "%-24s mean=%.2f",
            key,
            sum(values) / len(values),
        )

    over_budget = sum(
        item["context_tokens"] > MAX_CONTEXT_TOKENS for item in successful
    )

    logger.info(
        "Contexts over token budget: %d/%d",
        over_budget,
        total,
    )

    errors = [item for item in results if item["error"]]

    for item in errors:
        logger.error(
            "Query failed: %r | %s",
            item["query"],
            item["error"],
        )


# Main


async def main(limit: int) -> None:
    configure_logfire()

    chunks = load_chunks()
    cases = list(CASES)

    if limit > 0:
        cases = cases[:limit]

    logger.info(
        "Loaded %d chunks and %d cases",
        len(chunks),
        len(cases),
    )

    retriever = build_dense_retriever(k=RETRIEVAL_K)

    orchestrator = RetrievalOrchestrator(
        retriever,
        rrf_k=60,
        max_concurrency=4,
    )

    reranker = CrossEncoderCompressor(
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        top_n=RERANK_TOP_N,
        batch_size=16,
        max_length=512,
        fail_open=False,
    )

    results: list[dict[str, Any]] = []

    for index, case in enumerate(cases, start=1):
        query = get_query(case)

        logger.info(
            "[%d/%d] %s",
            index,
            len(cases),
            query,
        )

        result = await evaluate_case(
            case=case,
            chunks=chunks,
            orchestrator=orchestrator,
            reranker=reranker,
        )

        results.append(result)

        logger.info(
            "  retrieved@20=%s | reranked@8=%s | context@8=%s | tokens=%s",
            result["retrieved_hit@20"],
            result["reranked_hit@8"],
            result["context_hit@8"],
            result["context_tokens"],
        )

    summarize(results)

    with RESULT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False,
        )

    logger.info("Results saved to %s", RESULT_FILE)
    logger.info("Logs saved to %s", LOG_FILE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Number of cases; use 0 for all cases",
    )

    args = parser.parse_args()

    asyncio.run(main(args.limit))
