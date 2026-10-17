import asyncio

from langchain_core.documents import Document

from app.generation.answer_generation import generate_answer
from app.retrieval.context_assembly import assemble_context


async def main() -> None:
    documents = [
        Document(
            page_content=(
                "FastAPI middleware can be added using "
                "the @app.middleware('http') decorator."
            ),
            metadata={
                "chunk_id": "test-middleware-001",
                "page_title": "Middleware",
                "section_url": "https://fastapi.tiangolo.com/tutorial/middleware/",
                "heading_path": "Advanced Middleware",
                "dense_score": 0.9,
            },
        )
    ]

    assembled_context = assemble_context(documents)

    result = await generate_answer(
        question="How do I add HTTP middleware in FastAPI?",
        assembled_context=assembled_context,
        model="rag-answer-generation",
    )

    print("\nANSWER\n")
    print(result.answer)

    print("\nCITATION METADATA\n")
    for citation in result.citations:
        print(citation)


if __name__ == "__main__":
    asyncio.run(main())
