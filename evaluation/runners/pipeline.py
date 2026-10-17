"""Run deterministic evaluations against the real RAG pipeline."""

import argparse
import asyncio
import json
import time
from datetime import UTC, datetime

from app.generation.rag_pipeline import build_rag_pipeline
from app.retrieval.deduplication import get_document_id
from evaluation.config.settings import REPORTS_DIR
from evaluation.datasets.loader import load_cases
from evaluation.evaluators.abstention import evaluate_abstention
from evaluation.evaluators.citations import evaluate_citations
from evaluation.evaluators.generation import required_fact_coverage
from evaluation.evaluators.retrieval import (
    evaluate_context_retention,
    evaluate_ranking,
)


def _evidence_ids(evidence: list[object]) -> list[str]:
    ids = []
    for item in evidence:
        if isinstance(item, dict):
            value = item.get("evidence_id")
        else:
            value = getattr(item, "evidence_id", None)

        if value is not None:
            ids.append(str(value))
    return ids


def _mean_metric_dict(results: list[dict], field: str) -> dict | None:
    """Average numeric metrics across cases that have valid metric dictionaries."""
    metric_dicts = [
        result[field] for result in results if isinstance(result.get(field), dict)
    ]

    if not metric_dicts:
        return None

    metric_names = metric_dicts[0].keys()

    return {
        name: round(
            sum(metrics[name] for metrics in metric_dicts) / len(metric_dicts),
            4,
        )
        for name in metric_names
        if all(
            isinstance(metrics.get(name), (int, float))
            and not isinstance(metrics.get(name), bool)
            for metrics in metric_dicts
        )
    }


async def _evaluate_case(pipeline, case) -> dict:
    started = time.perf_counter()

    try:
        response = await pipeline.answer(case.question)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

        evidence = list(response.context.evidence)
        citations = list(response.citations)

        citation_metrics = evaluate_citations(citations, evidence)
        fact_metrics = required_fact_coverage(response.answer, case.required_facts)

        abstention_metrics = evaluate_abstention(
            expect_abstention=case.expect_abstention,
            actually_abstained=bool(response.insufficient_evidence),
            citation_count=len(citations),
        )

        retrieval = response.retrieval

        retrieval = response.retrieval
        diagnostics = getattr(retrieval, "diagnostics", None)
        strategy = getattr(diagnostics, "strategy", None)

        retrieval_metrics = None
        context_metrics = None

        if not case.relevant_chunk_ids:
            retrieval_evaluation_status = "unlabeled"
        elif retrieval is None:
            retrieval_evaluation_status = "unavailable"
        elif strategy in {"clarify", "out_of_scope"}:
            retrieval_evaluation_status = "skipped_non_retrieval_strategy"
        else:
            relevant_ids = set(case.relevant_chunk_ids)
            retrieved_ids = [get_document_id(doc) for doc in retrieval.candidates]
            context_ids = _evidence_ids(evidence)

            retrieval_metrics = evaluate_ranking(relevant_ids, retrieved_ids)
            context_metrics = evaluate_context_retention(
                relevant_ids, retrieved_ids, context_ids
            )
            retrieval_evaluation_status = "evaluated"

        return {
            "case_id": case.case_id,
            "question": case.question,
            "status": "completed",
            "answer": response.answer,
            "expected_abstention": case.expect_abstention,
            "actual_abstention": bool(response.insufficient_evidence),
            "required_fact_coverage": fact_metrics,
            "citation_integrity": citation_metrics,
            "abstention": abstention_metrics,
            "evidence_ids": _evidence_ids(evidence),
            "cited_evidence_ids": [
                getattr(citation, "evidence_id", None) for citation in citations
            ],
            "retrieval_strategy": strategy,
            "latency_ms": {
                **response.latency_ms,
                "evaluation_total": elapsed_ms,
            },
            "error": None,
            "retrieval_evaluation_status": retrieval_evaluation_status,
            "retrieval_metrics": retrieval_metrics,
            "context_metrics": context_metrics,
        }

    except (ValueError, RuntimeError, TimeoutError) as exc:
        return {
            "case_id": case.case_id,
            "question": case.question,
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
            "latency_ms": {
                "evaluation_total": round((time.perf_counter() - started) * 1000, 2)
            },
        }


async def run_pipeline_evaluation(limit: int | None = 1) -> dict:
    cases = load_cases()
    if limit is not None:
        if limit < 1:
            raise ValueError("limit must be positive, or None for all cases")
        cases = cases[:limit]

    pipeline = build_rag_pipeline()
    results = []

    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {case.case_id}: {case.question}")
        result = await _evaluate_case(pipeline, case)
        results.append(result)

        if result["status"] == "error":
            print(f"  ERROR: {result['error']}")
        else:
            coverage = result["required_fact_coverage"]["coverage"]
            print(
                f"  done | coverage={coverage} | "
                f"latency={result['latency_ms'].get('total', 'n/a')} ms"
            )

    completed = [r for r in results if r["status"] == "completed"]
    errors = [r for r in results if r["status"] == "error"]

    labeled_cases = [
        result
        for result in completed
        if result.get("retrieval_evaluation_status") != "unlabeled"
    ]

    evaluated_cases = [
        result
        for result in completed
        if result.get("retrieval_evaluation_status") == "evaluated"
    ]

    skipped_cases = [
        result
        for result in completed
        if result.get("retrieval_evaluation_status")
        in {"skipped_non_retrieval_strategy", "unavailable"}
    ]

    retrieval_aggregates = _mean_metric_dict(evaluated_cases, "retrieval_metrics")
    context_aggregates = _mean_metric_dict(evaluated_cases, "context_metrics")

    fact_scores = [
        r["required_fact_coverage"]["coverage"]
        for r in completed
        if r["required_fact_coverage"]["coverage"] is not None
    ]

    report = {
        "suite": "pipeline",
        "created_at": datetime.now(UTC).isoformat(),
        "requested_cases": len(cases),
        "completed_cases": len(completed),
        "error_cases": len(errors),
        "mean_required_fact_coverage": (
            round(sum(fact_scores) / len(fact_scores), 4) if fact_scores else None
        ),
        "citation_integrity_pass_rate": (
            round(
                sum(r["citation_integrity"]["all_citations_valid"] for r in completed)
                / len(completed),
                4,
            )
            if completed
            else None
        ),
        "retrieval_evaluation": {
            "labeled_cases": len(labeled_cases),
            "evaluated_cases": len(evaluated_cases),
            "skipped_or_unavailable_cases": len(skipped_cases),
            "unlabeled_cases": sum(
                result.get("retrieval_evaluation_status") == "unlabeled"
                for result in completed
            ),
            "mean_metrics": retrieval_aggregates,
        },
        "context_retention_evaluation": {
            "evaluated_cases": len(evaluated_cases),
            "mean_metrics": context_aggregates,
        },
        "results": results,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / "pipeline_latest.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\nEvaluation summary")
    print(f"Completed: {len(completed)}/{len(cases)}")
    print(f"Errors: {len(errors)}")
    print(f"Report: {report_path}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the real RAG pipeline.")
    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Number of evaluation cases to run (default: 1).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Evaluate all available cases.",
    )
    args = parser.parse_args()

    asyncio.run(run_pipeline_evaluation(limit=None if args.all else args.limit))


if __name__ == "__main__":
    main()
