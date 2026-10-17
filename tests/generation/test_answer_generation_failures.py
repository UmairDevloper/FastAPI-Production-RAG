from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from app.generation.answer_generation import generate_answer
from app.retrieval.context_assembly import AssembledContext

EMPTY_CONTEXT = AssembledContext(
    context="",
    evidence=[],
    estimated_tokens=0,
    omitted_documents=0,
)


async def test_empty_question_is_rejected() -> None:
    try:
        await generate_answer(
            question="   ",
            assembled_context=EMPTY_CONTEXT,
            model="rag-generation",
        )
    except ValueError:
        return

    raise AssertionError("Expected an empty question to raise ValueError.")


async def test_empty_evidence_does_not_call_llm() -> None:
    with patch(
        "app.generation.answer_generation.complete",
        new_callable=AsyncMock,
    ) as mock_complete:
        result = await generate_answer(
            question="How do I add HTTP middleware?",
            assembled_context=EMPTY_CONTEXT,
            model="rag-generation",
        )

    assert result.insufficient_evidence is True
    assert result.citations == []
    mock_complete.assert_not_awaited()


async def test_gateway_error_propagates() -> None:
    context = AssembledContext(
        context="[chunk_id:test-001]\nExample FastAPI documentation.",
        evidence=[],
        estimated_tokens=10,
        omitted_documents=0,
    )

    # Use a nonempty evidence list so generation reaches the LLM.
    from app.retrieval.context_assembly import Evidence

    evidence = Evidence(
        evidence_id="chunk_id:test-001",
        content="Example FastAPI documentation.",
        source_url=None,
        page_title="Test",
        heading_path=None,
        score=None,
    )
    context = AssembledContext(
        context=context.context,
        evidence=[evidence],
        estimated_tokens=context.estimated_tokens,
        omitted_documents=0,
    )

    with patch(
        "app.generation.answer_generation.complete",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Gateway unavailable"),
    ):
        try:
            await generate_answer(
                question="Explain this documentation.",
                assembled_context=context,
                model="rag-generation",
            )
        except RuntimeError as exc:
            assert "Gateway unavailable" in str(exc)
            return

    raise AssertionError("Expected gateway error to propagate.")


def main() -> None:
    asyncio.run(test_empty_question_is_rejected())
    asyncio.run(test_empty_evidence_does_not_call_llm())
    asyncio.run(test_gateway_error_propagates())
    print("All answer-generation failure tests passed.")


if __name__ == "__main__":
    main()
