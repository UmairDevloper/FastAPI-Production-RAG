import asyncio
import json
import logging

from app.ingestion.embedding4.models_config import configure_logfire
from app.retrieval.orchestrator import build_retrieval_orchestrator

async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    configure_logfire("fastapi-rag-orchestration")

    try:
        orchestrator = build_retrieval_orchestrator(k=20)

        result = await orchestrator.retrieve(
            "How do I configure middleware, implement OAuth2 authentication, "
            "and test FastAPI endpoints?"
        )

        print(json.dumps(result.to_dict(), indent=2))

        for rank, doc in enumerate(result.candidates[:10], start=1):
            heading = doc.metadata.get("heading_path", "")
            print(f"\n{rank}. {heading}")
            print(f"   ID: {doc.metadata.get('retrieval_id')}")
            print(f"   Score: {doc.metadata.get('fusion_score', doc.metadata.get('dense_score'))}")
            print(f"   URL: {doc.metadata.get('section_url') or doc.metadata.get('url')}")

    finally:
        import logfire
        logfire.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
