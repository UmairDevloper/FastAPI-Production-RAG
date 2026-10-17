import json

from app.llm_gateway.client import complete

"""
Query analysis for routing questions to the appropriate retrieval strategy."""

async def generate_query_variants(
    query: str,
    count: int = 3,
) -> list[str]:
    raw = await complete(
        model="rag-query-transform",
        system=(
            "Generate distinct search queries for retrieving "
            "relevant FastAPI documentation. Preserve the user's "
            "intent; do not answer the question. Return a JSON "
            "array of strings only."
        ),
        user=f"Question: {query}\nGenerate at most {count} variants.",
    )

    try:
        variants = json.loads(raw)
        if not isinstance(variants, list):
            return [query]

        clean = []
        for item in variants:
            if isinstance(item, str) and item.strip():
                candidate = item.strip()
                if candidate not in clean and candidate != query:
                    clean.append(candidate)

        return clean[:count] or [query]

    except (ValueError, TypeError):
        return [query]