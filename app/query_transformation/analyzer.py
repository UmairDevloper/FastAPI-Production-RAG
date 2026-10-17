
import json

from app.llm_gateway.client import complete
from app.query_transformation.schemas import QueryAnalysis

SYSTEM_PROMPT = """
You are a query-routing classifier for a RAG application covering
FastAPI documentation.

Choose exactly one strategy:

- direct: A clear question, technical keyword, API name, code snippet,
  error message, configuration value, or documentation phrase searchable
  as written.
- rewrite: A relevant query that is poorly phrased or messy.
- multi_query: A single concept that benefits from distinct search formulations.
- decompose: A question containing multiple independent subquestions.
- hyde: A query that benefits from a hypothetical documentation passage.
- clarify: Essential information is missing and cannot reasonably be inferred.
- out_of_scope: The query is clearly unrelated to FastAPI documentation.

Rules:
1. Short queries are not automatically ambiguous.
2. Prefer direct for recognizable technical terms, API names, code,
   errors, exception text, configuration values, and related keywords.
3. Never clarify merely because a query lacks grammatical structure.
4. Never invent API names, versions, or facts.
5. Retrieval evidence determines whether relevant documentation exists.

Return ONLY a valid JSON object with these fields:
strategy, reason, search_query, needs_clarification
"""


ALLOWED_STRATEGIES = {
    "direct",
    "rewrite",
    "multi_query",
    "decompose",
    "hyde",
    "clarify",
    "out_of_scope",
}


async def analyze_query(query: str) -> QueryAnalysis:
    try:
        raw = await complete(
            model="rag-query-transform",
            system=SYSTEM_PROMPT,
            user=f"User question:\n{query}",
        )

        data = json.loads(raw)

        if not isinstance(data, dict):
            raise ValueError("Analyzer output was not a JSON object")  # noqa: TRY004

        strategy = data.get("strategy")

        if strategy not in ALLOWED_STRATEGIES:
            raise ValueError("Unknown strategy")

        search_query = data.get("search_query", query)

        if not isinstance(search_query, str) or not search_query.strip():
            search_query = query

        needs_clarification = data.get("needs_clarification", False)

        if not isinstance(needs_clarification, bool):
            needs_clarification = strategy == "clarify"

        return QueryAnalysis(
            strategy=strategy,
            reason=str(data.get("reason", "")),
            search_query=search_query.strip(),
            needs_clarification=needs_clarification,
        )

    except (ValueError, TypeError, KeyError):
        return QueryAnalysis(
            strategy="direct",
            reason="Analyzer output was invalid; using original query.",
            search_query=query,
            needs_clarification=False,
        )
