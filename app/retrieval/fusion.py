from __future__ import annotations

import time
from collections import defaultdict

import logfire
from langchain_core.documents import Document

from app.retrieval.deduplication import get_document_id


def reciprocal_rank_fusion(
    result_lists: list[list[Document]],
    k: int = 60,
) -> list[Document]:
    """Fuse ranked document lists using Reciprocal Rank Fusion."""
    if k < 1:
        raise ValueError("k must be at least 1.")

    started = time.perf_counter()

    input_count = sum(len(result_list) for result_list in result_lists)
    scores: dict[str, float] = defaultdict(float)
    documents: dict[str, Document] = {}
    ranks: dict[str, list[int]] = defaultdict(list)
    duplicate_count = 0

    with logfire.span(
        "retrieval.reciprocal_rank_fusion",
        result_list_count=len(result_lists),
        input_document_count=input_count,
        rrf_k=k,
    ) as span:
        for result_list in result_lists:
            # Avoid counting the same chunk twice within one query's results.
            seen_in_list: set[str] = set()

            for rank, doc in enumerate(result_list, start=1):
                document_id = get_document_id(doc)

                if document_id in seen_in_list:
                    duplicate_count += 1
                    continue

                seen_in_list.add(document_id)

                scores[document_id] += 1.0 / (k + rank)
                ranks[document_id].append(rank)

                if document_id not in documents:
                    documents[document_id] = doc

        ordered_ids = sorted(
            scores,
            key=lambda document_id: scores[document_id],
            reverse=True,
        )

        fused: list[Document] = []

        for document_id in ordered_ids:
            original = documents[document_id]

            metadata = {
                **original.metadata,
                "fusion_score": scores[document_id],
                "fusion_ranks": ranks[document_id],
                "retrieval_id": document_id,
            }

            fused.append(
                Document(
                    page_content=original.page_content,
                    metadata=metadata,
                )
            )

        elapsed_ms = round(
            (time.perf_counter() - started) * 1000,
            2,
        )

        span.set_attribute("fusion.unique_document_count", len(fused))
        span.set_attribute("fusion.duplicate_count", duplicate_count)
        span.set_attribute("fusion.latency_ms", elapsed_ms)

        logfire.info(
            "retrieval.fusion_completed",
            input_document_count=input_count,
            unique_document_count=len(fused),
            duplicate_count=duplicate_count,
            result_list_count=len(result_lists),
            latency_ms=elapsed_ms,
        )

        return fused
