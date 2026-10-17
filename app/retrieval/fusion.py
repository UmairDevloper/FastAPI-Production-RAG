from __future__ import annotations

from collections import defaultdict

from langchain_core.documents import Document

from app.retrieval.deduplication import get_document_id


def reciprocal_rank_fusion(
    result_lists: list[list[Document]],
    k: int = 60,
) -> list[Document]:
    """Fuse ranked document lists using Reciprocal Rank Fusion."""
    if k < 1:
        raise ValueError("k must be at least 1.")

    scores: dict[str, float] = defaultdict(float)
    documents: dict[str, Document] = {}
    ranks: dict[str, list[int]] = defaultdict(list)

    for result_list in result_lists:
        # Avoid counting the same chunk twice within one query's results.
        seen_in_list: set[str] = set()

        for rank, doc in enumerate(result_list, start=1):
            document_id = get_document_id(doc)

            if document_id in seen_in_list:
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

    return fused

