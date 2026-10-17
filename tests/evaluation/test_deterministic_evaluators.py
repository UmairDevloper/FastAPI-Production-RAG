import sys
from pathlib import Path

import pytest

# Ensure the project root is importable when pytest uses a tests directory as root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.evaluators.abstention import evaluate_abstention
from evaluation.evaluators.citations import evaluate_citations
from evaluation.evaluators.generation import required_fact_coverage
from evaluation.evaluators.retrieval import (
    evaluate_ranking,
    hit_at_k,
    ndcg_at_k,
    reciprocal_rank,
)


def test_retrieval_metrics():
    relevant = {"chunk-b"}
    ranked = ["chunk-a", "chunk-b", "chunk-c"]

    assert hit_at_k(relevant, ranked, 1) == 0.0
    assert hit_at_k(relevant, ranked, 2) == 1.0
    assert reciprocal_rank(relevant, ranked) == 0.5
    assert ndcg_at_k(relevant, ranked, 3) == pytest.approx(1 / 1.5849625007)

    metrics = evaluate_ranking(relevant, ranked)
    assert metrics["hit_at_3"] == 1.0
    assert metrics["mrr"] == 0.5


def test_retrieval_metrics_reject_nonpositive_k():
    with pytest.raises(ValueError):
        hit_at_k({"a"}, ["a"], 0)

    with pytest.raises(ValueError):
        ndcg_at_k({"a"}, ["a"], -1)


def test_required_fact_coverage():
    result = required_fact_coverage(
        "Use Depends to share a database session.",
        ["Depends", "database session", "OAuth2PasswordBearer"],
    )

    assert result["applicable"] is True
    assert result["coverage"] == pytest.approx(2 / 3)
    assert result["missing_facts"] == ["OAuth2PasswordBearer"]


def test_required_fact_coverage_not_applicable_when_empty():
    result = required_fact_coverage("Any answer", [])

    assert result["applicable"] is False
    assert result["coverage"] is None


def test_citations_are_checked_against_context_evidence():
    citations = [
        {"evidence_id": "chunk-1"},
        {"evidence_id": "chunk-missing"},
    ]
    context = [{"evidence_id": "chunk-1"}, {"evidence_id": "chunk-2"}]

    result = evaluate_citations(citations, context)

    assert result["citation_count"] == 2
    assert result["valid_citation_count"] == 1
    assert result["invalid_citation_ids"] == ["chunk-missing"]
    assert result["all_citations_valid"] is False


def test_expected_abstention_passes_without_citations():
    result = evaluate_abstention(
        expect_abstention=True,
        actually_abstained=True,
        citation_count=0,
    )

    assert result["passed"] is True


def test_expected_abstention_fails_if_answer_has_citations():
    result = evaluate_abstention(
        expect_abstention=True,
        actually_abstained=True,
        citation_count=1,
    )

    assert result["passed"] is False


def test_unexpected_abstention_fails():
    result = evaluate_abstention(
        expect_abstention=False,
        actually_abstained=True,
        citation_count=0,
    )

    assert result["passed"] is False


from evaluation.evaluators.retrieval import evaluate_context_retention


def test_context_retention_metrics():
    relevant = {"chunk_id:a", "chunk_id:b", "chunk_id:c"}
    retrieved = ["chunk_id:a", "chunk_id:x", "chunk_id:b"]
    context = ["chunk_id:b", "chunk_id:x"]

    result = evaluate_context_retention(relevant, retrieved, context)

    assert result["relevant_retrieved_count"] == 2
    assert result["relevant_in_context_count"] == 1
    assert result["retrieval_recall"] == pytest.approx(2 / 3)
    assert result["context_recall"] == pytest.approx(1 / 3)
    assert result["retention_of_retrieved_relevant"] == pytest.approx(1 / 2)


def test_ranking_rejects_missing_relevance_labels():
    with pytest.raises(ValueError, match="without relevance labels"):
        evaluate_ranking(set(), ["chunk_id:a"])


def test_context_retention_rejects_missing_relevance_labels():
    with pytest.raises(ValueError, match="without relevance labels"):
        evaluate_context_retention(set(), [], [])


def test_missing_citations_fail_when_required():
    result = evaluate_citations(
        citations=[],
        context_evidence=[{"evidence_id": "chunk-1"}],
    )

    assert result["citation_count"] == 0
    assert result["citations_present"] is False
    assert result["citations_complete"] is False
    assert result["all_citations_valid"] is False


def test_missing_citations_are_allowed_when_not_required():
    result = evaluate_citations(
        citations=[],
        context_evidence=[{"evidence_id": "chunk-1"}],
        require_citation=False,
    )

    assert result["citations_complete"] is True
    assert result["all_citations_valid"] is True
