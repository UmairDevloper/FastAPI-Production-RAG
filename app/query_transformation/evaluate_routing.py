import asyncio
import json
import time
from collections import Counter
from pathlib import Path

import logfire

from app.query_transformation.analyzer import analyze_query
from app.query_transformation.messy_cases import MESSY_CASES

OUTPUT_FILE = Path("reports/query_transformation/routing_messy_results.json")


async def main():
    run_started = time.perf_counter()

    correct = 0
    category_totals = Counter()
    category_correct = Counter()
    results = []
    error_count = 0

    with logfire.span(
        "evaluation.messy_query_routing",
        case_count=len(MESSY_CASES),
    ):
        for index, case in enumerate(MESSY_CASES, start=1):
            query = case["query"]
            expected = case["expected_strategy"]
            category = case["category"]
            case_started = time.perf_counter()

            with logfire.span(
                "evaluation.routing_case",
                case_index=index,
                category=category,
                expected_strategy=expected,
                query_chars=len(query),
            ):
                try:
                    result = await analyze_query(query)
                    actual = result.strategy
                    passed = actual == expected

                    correct += int(passed)
                    category_totals[category] += 1
                    category_correct[category] += int(passed)

                    row = {
                        "query": query,
                        "category": category,
                        "expected_strategy": expected,
                        "actual_strategy": actual,
                        "correct": passed,
                        "reason": result.reason,
                        "search_query": result.search_query,
                        "needs_clarification": result.needs_clarification,
                    }
                    results.append(row)

                    elapsed_ms = round(
                        (time.perf_counter() - case_started) * 1000,
                        2,
                    )

                    logfire.info(
                        "Routing evaluation case completed",
                        case_index=index,
                        category=category,
                        expected_strategy=expected,
                        actual_strategy=actual,
                        passed=passed,
                        elapsed_ms=elapsed_ms,
                    )

                    print(f"\n[{index}/{len(MESSY_CASES)}] {query}")
                    print(f"Expected: {expected} | Actual: {actual}")
                    print(f"Result: {'PASS' if passed else 'REVIEW'}")
                    print(f"Search query: {result.search_query}")
                    print(f"Reason: {result.reason}")

                except Exception as exc:
                    error_count += 1

                    logfire.exception(
                        "Routing evaluation case failed",
                        case_index=index,
                        category=category,
                        expected_strategy=expected,
                        error_type=type(exc).__name__,
                        elapsed_ms=round(
                            (time.perf_counter() - case_started) * 1000,
                            2,
                        ),
                    )

                    print(f"\n[{index}] ERROR: {type(exc).__name__}: {exc}")

        print("\n--- Routing summary ---")
        print(f"Correct strategy labels: {correct}/{len(MESSY_CASES)}")

        accuracy = correct / len(MESSY_CASES) if MESSY_CASES else 0.0
        print(f"Label accuracy: {accuracy:.1%}")

        for category, total in sorted(category_totals.items()):
            passed = category_correct[category]
            print(f"{category}: {passed}/{total}")

        logfire.info(
            "Routing evaluation summary",
            total_cases=len(MESSY_CASES),
            correct_labels=correct,
            label_accuracy=accuracy,
            failed_cases=error_count,
            category_totals=dict(category_totals),
            category_correct=dict(category_correct),
            elapsed_ms=round(
                (time.perf_counter() - run_started) * 1000,
                2,
            ),
        )

        with logfire.span(
            "evaluation.save_routing_results",
            output_file=str(OUTPUT_FILE),
            result_count=len(results),
        ):
            OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

            import json

            import aiofiles

            async with aiofiles.open(
                OUTPUT_FILE,
                mode="w",
                encoding="utf-8",
            ) as file:
                await file.write(
                    json.dumps(
                        results,
                        indent=2,
                        ensure_ascii=False,
                    )
                )

        print("\nSaved routing results to:")
        print(str(OUTPUT_FILE))

        logfire.info(
            "Routing evaluation report saved",
            output_file=str(OUTPUT_FILE),
            result_count=len(results),
        )


if __name__ == "__main__":
    asyncio.run(main())
