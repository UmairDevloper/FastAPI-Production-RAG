from app.llm_gateway.client import complete

"""
Query analysis for routing questions to the appropriate retrieval strategy."""

async def generate_hypothetical_document(query: str) -> str:
    return await complete(
        model="rag-hyde",
        system=(
            "Write a short hypothetical passage that could appear "
            "in technical FastAPI documentation and would address "
            "the question. Do not claim the passage is real or "
            "verified documentation. Do not invent exact API "
            "signatures when uncertain."
        ),
        user=query,
        temperature=0.2,
    )