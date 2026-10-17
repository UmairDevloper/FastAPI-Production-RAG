import asyncio

from app.query_transformation.service import transform_query

CASES = [
    ("What is the current weather in Multan?", "out_of_scope"),
    ("What is the latest stock price of Microsoft?", "out_of_scope"),
    ("Write a poem about the ocean.", "out_of_scope"),
    ("Who won the latest FIFA World Cup?", "out_of_scope"),
    ("How do I add HTTP middleware in FastAPI?", "direct"),
]


async def main():
    failed = False

    for question, expected in CASES:
        result = await transform_query(question)
        actual = result.analysis.strategy
        passed = actual == expected

        print(
            f"{'PASS' if passed else 'FAIL'} | "
            f"Expected: {expected} | Actual: {actual} | {question}"
        )

        if not passed:
            failed = True

    if failed:
        raise SystemExit("Scope routing checks failed.")

    print(f"\nAll {len(CASES)} scope-routing checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
