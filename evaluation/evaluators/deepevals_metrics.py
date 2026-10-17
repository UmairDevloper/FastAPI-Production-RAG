import os

from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
)
from deepeval.models import OpenAIModel
from deepeval.test_case import LLMTestCase


def build_test_case(
    *,
    question: str,
    answer: str,
    retrieval_context: list[str],
) -> LLMTestCase:
    return LLMTestCase(
        input=question,
        actual_output=answer,
        retrieval_context=retrieval_context,
    )


def build_metrics(*, threshold: float = 0.7) -> list:
    judge = OpenAIModel(
        model="rag-generation",
        base_url="http://localhost:4000/v1",
        api_key=os.getenv("LITELLM_API_KEY", "local"),
        temperature=0,
    )

    return [
        FaithfulnessMetric(
            threshold=threshold,
            model=judge,
            include_reason=True,
        ),
        AnswerRelevancyMetric(
            threshold=threshold,
            model=judge,
            include_reason=True,
        ),
    ]
