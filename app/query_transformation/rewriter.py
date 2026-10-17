from app.llm_gateway.client import complete

"""
Query rewriter for transforming user questions into optimized search queries for FastAPI documentation.
"""

async def rewrite_query(
    original_query: str,
    *,
    context: str | None = None,
) -> str:
    system = """
Rewrite the user's question as one clear search query for
FastAPI documentation.

Preserve the original intent and technical constraints.
Keep API names, code identifiers, and version details intact.
Do not answer the question or add unsupported assumptions.
Return only the rewritten query.
"""

    user = f"Original question:\n{original_query}"
    if context:
        user += f"\n\nRelevant conversation context:\n{context}"

    rewritten = await complete(
        model="rag-query-transform",
        system=system,
        user=user,
    )

    return rewritten or original_query