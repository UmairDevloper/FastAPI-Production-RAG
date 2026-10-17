from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from pathlib import Path

from app.generation.evaluate_cases import CASES
from app.generation.rag_pipeline import build_rag_pipeline

logger = logging.getLogger(__name__)

OUTPUT_PATH = Path("tests/generation/generation_eval_results.json")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


async def main() -> None:
    pipeline = build_rag_pipeline()
    results: list[dict[str, object]] = []

    target = "How do I share a database session using dependencies?"
    selected_cases = [case for case in CASES if case.question == target]

    print(f"Matched cases: {len(selected_cases)}", flush=True)

    for case in selected_cases:
        print(f"Testing: {case.question}", flush=True)
        started = time.perf_counter()

        try:
            response = await pipeline.answer(case.question)
            answer = response.answer
            normalized_answer = normalize(answer)

            missing_facts = [
                fact
                for fact in case.required_facts
                if normalize(fact) not in normalized_answer
            ]

            normalized_answer = normalize(response.answer)

            abstention_pass = (
                response.insufficient_evidence
                and not response.citations
                and any(
                    phrase in normalized_answer
                    for phrase in (
                        "outside",
                        "cannot help",
                        "can't help",
                        "unable to answer",
                    )
                )
                if case.expect_abstention
                else True
            )

            cited_ids = {citation.evidence_id for citation in response.citations}
            supplied_ids = {item.evidence_id for item in response.context.evidence}

            results.append(
                {
                    "question": case.question,
                    "answer": answer,
                    "missing_required_facts": missing_facts,
                    "required_facts_pass": not missing_facts,
                    "citations_present": bool(cited_ids),
                    "citations_valid": cited_ids.issubset(supplied_ids),
                    "citation_count": len(cited_ids),
                    "insufficient_evidence": response.insufficient_evidence,
                    "expect_abstention": case.expect_abstention,
                    "abstention_pass": abstention_pass,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                    "error": None,
                }
            )

        except Exception as exc:
            logger.exception("Evaluation failed for: %s", case.question)
            results.append(
                {
                    "question": case.question,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    completed = [item for item in results if item.get("error") is None]
    failed = [item for item in results if item.get("error") is not None]
    total = len(results)

    fact_passes = sum(item.get("required_facts_pass") is True for item in completed)

    citation_passes = sum(item.get("citations_valid") is True for item in completed)

    abstention_cases = [
        item for item in completed if item.get("expect_abstention") is True
    ]

    abstention_passes = sum(
        item.get("abstention_pass") is True for item in abstention_cases
    )

    print(f"\nCases: {total}")
    print(f"Completed: {len(completed)}/{total}")
    print(f"Failed: {len(failed)}/{total}")
    print(f"Required-fact pass rate: {fact_passes}/{total} total cases")
    print(f"Valid-citation pass rate: {citation_passes}/{total} total cases")

    print(
        f"Abstention pass rate: "
        f"{abstention_passes}/{len(abstention_cases)} expected-abstention cases"
    )

    if failed:
        print("\nFailed cases:")
        for item in failed:
            print(f"- {item['question']}: {item['error']}")

    print(f"Required-fact pass rate: {fact_passes}/{len(completed)} completed cases")
    print(
        f"Valid-citation pass rate: {citation_passes}/{len(completed)} completed cases"
    )
    print(f"\nCases: {total}")
    print(f"Completed: {len(completed)}/{total}")
    print(f"Failed: {len(failed)}/{total}")
    print(f"Required-fact pass rate: {fact_passes}/{len(completed)} completed cases")
    print(f"Valid-citation rate: {citation_passes}/{len(completed)} completed cases")

    if failed:
        print("\nFailed cases:")
        for item in failed:
            print(f"- {item['question']}: {item['error']}")

    print(f"\nResults saved to: {OUTPUT_PATH}")
