
import json

from app.llm_gateway.client import complete

"""
Query analysis for routing questions to the appropriate retrieval strategy.
This module provides functionality to decompose complex user queries into independent retrieval queries."""
SYSTEM_PROMPT = """
You decompose questions for a RAG application covering FastAPI
documentation.

Split a question into independent, concise retrieval queries only
when it contains multiple distinct information needs.

Rules:
- Preserve the user's intent and technical terminology.
- Do not invent API names, versions, or requirements.
- Keep dependent steps together when they form one connected task.
- Each query must be independently useful for retrieving documentation.
- If the question has only one information need, return one query.
- Return only a JSON object with this format:
  {"queries": ["first query", "second query"]}
"""


async def decompose_query(query: str) -> list[str]:
    raw = await complete(
        model="rag-query-transform",
        system=SYSTEM_PROMPT,
        user=f"Question to decompose:\n{query}",
    )

    try:
        data = json.loads(raw)
        queries = data["queries"]

        if not isinstance(queries, list):
            raise ValueError("Expected a list of queries.")

        cleaned = list(
            dict.fromkeys(
                item.strip()
                for item in queries
                if isinstance(item, str) and item.strip()
            )
        )

        if cleaned:
            return cleaned

    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        pass

    # Safe fallback: preserve the original information need.
    return [query.strip()]