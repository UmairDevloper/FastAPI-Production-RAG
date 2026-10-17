"""Deterministic retrieval and context-retention metrics."""

import math
from collections.abc import Sequence


def hit_at_k(relevant_ids: set[str], ranked_ids: Sequence[str], k: int) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    return float(bool(relevant_ids.intersection(ranked_ids[:k])))


def reciprocal_rank(relevant_ids: set[str], ranked_ids: Sequence[str]) -> float:
    for rank, item_id in enumerate(ranked_ids, start=1):
        if item_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(
    relevant_ids: set[str],
    ranked_ids: Sequence[str],
    k: int,
) -> float:
    if k <= 0:
        raise ValueError("k must be positive")

    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, item_id in enumerate(ranked_ids[:k], start=1)
        if item_id in relevant_ids
    )
    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / idcg if idcg else 0.0


def evaluate_ranking(
    relevant_ids: set[str],
    ranked_ids: Sequence[str],
    ks: tuple[int, ...] = (1, 3, 5, 10, 20),
) -> dict[str, float]:
    if not relevant_ids:
        raise ValueError("Cannot evaluate ranking without relevance labels")

    result = {f"hit_at_{k}": hit_at_k(relevant_ids, ranked_ids, k) for k in ks}
    result["mrr"] = reciprocal_rank(relevant_ids, ranked_ids)
    result["ndcg_at_10"] = ndcg_at_k(relevant_ids, ranked_ids, 10)
    return result


def evaluate_context_retention(
    relevant_ids: set[str],
    retrieved_ids: Sequence[str],
    context_ids: Sequence[str],
) -> dict[str, float | int]:
    """Measure relevant evidence retained through reranking and packing."""
    if not relevant_ids:
        raise ValueError("Cannot evaluate context retention without relevance labels")

    retrieved_relevant = relevant_ids.intersection(retrieved_ids)
    context_relevant = relevant_ids.intersection(context_ids)

    return {
        "relevant_retrieved_count": len(retrieved_relevant),
        "relevant_in_context_count": len(context_relevant),
        "retrieval_recall": len(retrieved_relevant) / len(relevant_ids),
        "context_recall": len(context_relevant) / len(relevant_ids),
        "retention_of_retrieved_relevant": (
            len(context_relevant) / len(retrieved_relevant)
            if retrieved_relevant
            else 0.0
        ),
    }
