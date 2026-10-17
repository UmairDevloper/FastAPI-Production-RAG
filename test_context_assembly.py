
import asyncio

from app.indexing.dense_indexing.reranker2 import CrossEncoderCompressor
from app.retrieval.context_assembly import assemble_context
from app.retrieval.orchestrator import RetrievalOrchestrator
from app.retrieval.retriever import build_dense_retriever


async def main() -> None:
    query = "How do I read JSON data sent by the client in a POST request?"

    retriever = build_dense_retriever(k=20)
    orchestrator = RetrievalOrchestrator(
        retriever,
        rrf_k=60,
        max_concurrency=4,
    )

    result = await orchestrator.retrieve(query)
    print("\n--- TOP 20 CANDIDATES BEFORE ASSEMBLY ---")


    for index, doc in enumerate(result.candidates, start=1):
        metadata = doc.metadata

        print(f"\n{index}. {metadata.get('page_title', 'Untitled')}")
        print(f"   Heading: {metadata.get('heading_path', 'N/A')}")
        print(f"   URL: {metadata.get('section_url') or metadata.get('url', 'N/A')}")
        print(f"   Fusion score: {metadata.get('fusion_score', 'N/A')}")
        print(f"   Dense score: {metadata.get('dense_score', 'N/A')}")
        print(f"   Chunk ID: {metadata.get('chunk_id', 'N/A')}")
        
    reranker = CrossEncoderCompressor(
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        top_n=8,
        batch_size=16,
        max_length=512,
        fail_open=True,
    )

    reranked_candidates = reranker.compress_documents(
        result.candidates,
        query=query,
    )

    print("\n--- TOP DOCUMENTS AFTER RERANKING ---")


    for i, doc in enumerate(reranked_candidates, start=1):
        print(f"\n{i}. {doc.metadata.get('page_title', 'Unknown')}")
        print(f"   Heading: {doc.metadata.get('heading_path')}")
        print(f"   Rerank score: {doc.metadata.get('rerank_score')}")
        print(f"   Dense score: {doc.metadata.get('dense_score')}")
        print(f"   URL: {doc.metadata.get('section_url') or doc.metadata.get('url')}")
        
    assembled = assemble_context(
        list(reranked_candidates),
        max_tokens=4000,
        max_documents=8,
    )

    print(f"\nQuery: {query}")
    print(f"Strategy: {result.diagnostics.strategy}")
    print(f"Retrieved candidates: {len(result.candidates)}")
    print(f"Selected evidence: {len(assembled.evidence)}")
    print(f"Estimated context tokens: {assembled.estimated_tokens}")
    print(f"Omitted documents: {assembled.omitted_documents}")

    print("\n--- ASSEMBLED CONTEXT ---")
    print(assembled.context)

    print("\n--- EVIDENCE SOURCES ---")
    for index, evidence in enumerate(assembled.evidence, start=1):
        print(f"{index}. {evidence.page_title or 'Untitled'}")
        print(f"   Heading: {evidence.heading_path or 'N/A'}")
        print(f"   URL: {evidence.source_url or 'N/A'}")
        print(f"   Score: {evidence.score}")
        

if __name__ == "__main__":
    asyncio.run(main())
