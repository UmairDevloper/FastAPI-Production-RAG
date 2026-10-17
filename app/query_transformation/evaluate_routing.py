
import asyncio
import json
from collections import Counter

from app.query_transformation.analyzer import analyze_query
from app.query_transformation.messy_cases import MESSY_CASES


async def main():
    correct = 0
    category_totals = Counter()
    category_correct = Counter()
    results = []

    for index, case in enumerate(MESSY_CASES, start=1):
        query = case["query"]
        expected = case["expected_strategy"]

        try:
            result = await analyze_query(query)
            actual = result.strategy
            passed = actual == expected

            correct += int(passed)
            category_totals[case["category"]] += 1
            category_correct[case["category"]] += int(passed)

            row = {
                "query": query,
                "category": case["category"],
                "expected_strategy": expected,
                "actual_strategy": actual,
                "correct": passed,
                "reason": result.reason,
                "search_query": result.search_query,
                "needs_clarification": result.needs_clarification,
            }
            results.append(row)

            print(f"\n[{index}/{len(MESSY_CASES)}] {query}")
            print(f"Expected: {expected} | Actual: {actual}")
            print(f"Result: {'PASS' if passed else 'REVIEW'}")
            print(f"Search query: {result.search_query}")
            print(f"Reason: {result.reason}")

        except Exception as exc:
            print(f"\n[{index}] ERROR: {type(exc).__name__}: {exc}")

    print("\n--- Routing summary ---")
    print(f"Correct strategy labels: {correct}/{len(MESSY_CASES)}")
    print(f"Label accuracy: {correct / len(MESSY_CASES):.1%}")

    for category, total in sorted(category_totals.items()):
        passed = category_correct[category]
        print(f"{category}: {passed}/{total}")

    with open(
        "reports/query_transformation/routing_messy_results.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(results, file, indent=2, ensure_ascii=False)

    print("\nSaved routing results to:")
    print("reports/query_transformation/routing_messy_results.json")


if __name__ == "__main__":
    asyncio.run(main())