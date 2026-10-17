import asyncio

from app.generation.rag_pipeline import build_rag_pipeline


async def main() -> None:
    pipeline = build_rag_pipeline()

    question = "How do I add HTTP middleware in FastAPI?"
    result = await pipeline.answer(question)

    print("\nQUESTION")
    print(result.question)

    print("\nANSWER")
    print(result.answer)

    print("\nCITATIONS")
    for citation in result.citations:
        print(
            citation.evidence_id,
            citation.page_title,
            citation.heading_path,
            citation.source_url,
        )

    print("\nDIAGNOSTICS")
    print("Strategy:", result.retrieval.diagnostics.strategy)
    print("Candidates:", len(result.retrieval.candidates))
    print("Context documents:", len(result.context.evidence))
    print("Context tokens:", result.context.estimated_tokens)
    print("Insufficient evidence:", result.insufficient_evidence)
    print("Latency (ms):", result.latency_ms)


if __name__ == "__main__":
    asyncio.run(main())
