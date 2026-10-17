from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from app.generation.answer_generation import generate_answer
from app.retrieval.context_assembly import AssembledContext, Evidence


def make_context() -> AssembledContext:
    evidence = Evidence(
        evidence_id="chunk_id:test-001",
        content="Use @app.middleware('http') to define HTTP middleware.",
        source_url="https://fastapi.tiangolo.com/tutorial/middleware/",
        page_title="Middleware",
        heading_path="Create a middleware",
        score=0.95,
    )

    return AssembledContext(
        context="[chunk_id:test-001]\nUse @app.middleware('http') to define HTTP middleware.",
        evidence=[evidence],
        estimated_tokens=30,
        omitted_documents=0,
    )


async def test_valid_citation_is_accepted() -> None:
    context = make_context()

    with patch(
        "app.generation.answer_generation.complete",
        new_callable=AsyncMock,
        return_value="Use @app.middleware('http'). [chunk_id:test-001]",
    ):
        result = await generate_answer(
            question="How do I add HTTP middleware?",
            assembled_context=context,
            model="rag-generation",
        )

    assert result.citations
    assert result.citations[0].evidence_id == "chunk_id:test-001"


async def test_fabricated_citation_is_rejected() -> None:
    context = make_context()

    with patch(
        "app.generation.answer_generation.complete",
        new_callable=AsyncMock,
        return_value="Use middleware. [chunk_id:fake-999]",
    ):
        try:
            await generate_answer(
                question="How do I add HTTP middleware?",
                assembled_context=context,
                model="rag-generation",
            )
        except ValueError:
            return

    raise AssertionError("Expected fabricated citation to be rejected.")


async def test_no_evidence_returns_insufficient_evidence() -> None:
    context = AssembledContext(
        context="",
        evidence=[],
        estimated_tokens=0,
        omitted_documents=0,
    )

    result = await generate_answer(
        question="How do I add HTTP middleware?",
        assembled_context=context,
        model="rag-generation",
    )

    assert result.insufficient_evidence is True
    assert result.citations == []


async def test_unprefixed_citation_matches_supplied_evidence() -> None:
    context = make_context()

    with patch(
        "app.generation.answer_generation.complete",
        new_callable=AsyncMock,
        return_value="Use middleware. [test-001]",
    ):
        result = await generate_answer(
            question="How do I add HTTP middleware?",
            assembled_context=context,
            model="rag-generation",
        )

    assert len(result.citations) == 1
    assert result.citations[0].evidence_id == "chunk_id:test-001"


def main() -> None:
    asyncio.run(test_valid_citation_is_accepted())
    asyncio.run(test_fabricated_citation_is_rejected())
    asyncio.run(test_no_evidence_returns_insufficient_evidence())
    asyncio.run(test_unprefixed_citation_matches_supplied_evidence())
    print("All answer-generation validation tests passed.")


if __name__ == "__main__":
    main()
