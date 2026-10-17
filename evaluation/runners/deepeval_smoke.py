from deepeval.metrics import BaseMetric

from evaluation.evaluators.deepevals_metrics import (
    build_metrics,
    build_test_case,
)


def main() -> None:
    test_case = build_test_case(
        question="How does FastAPI middleware work?",
        answer=(
            "FastAPI middleware runs for requests before they reach "
            "the path operation and for responses before they are returned."
        ),
        retrieval_context=[
            (
                "Middleware is a function that works with every request "
                "before it is processed by any specific path operation. "
                "It also works with every response before it is returned."
            )
        ],
    )

    metrics: list[BaseMetric] = build_metrics(threshold=0.7)

    for metric in metrics:
        metric.measure(test_case)
        print(
            f"{type(metric).__name__}: "
            f"score={metric.score:.3f}, "
            f"success={metric.success}, "
            f"reason={metric.reason}"
        )


if __name__ == "__main__":
    main()
