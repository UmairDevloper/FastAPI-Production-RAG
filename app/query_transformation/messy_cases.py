
"""
Messy-query evaluation cases for FastAPI documentation RAG.

Expected strategies are hypotheses for evaluation, not absolute truths.
"""

MESSY_CASES = [
    # 1. Typos and informal wording -> rewrite
    {
        "query": "how fastapi depnd injction wrks n how use it",
        "expected_strategy": "rewrite",
        "category": "typos",
    },
    {
        "query": "fastapi req body not coming proper how fix",
        "expected_strategy": "rewrite",
        "category": "informal",
    },
    {
        "query": "whats diff betwen async def and def in fast api",
        "expected_strategy": "rewrite",
        "category": "typos",
    },
    {
        "query": "how do i stop user frm accesing endpoint without login",
        "expected_strategy": "rewrite",
        "category": "informal",
    },
    {
        "query": "pydantic schema response_model thing not validating why",
        "expected_strategy": "rewrite",
        "category": "fragment",
    },

    # 2. Synonyms and alternative terminology -> multi_query
    {
        "query": "how does fastapi inject dependencies into endpoints",
        "expected_strategy": "multi_query",
        "category": "terminology",
    },
    {
        "query": "ways to handle errors exceptions and failed requests in fastapi",
        "expected_strategy": "multi_query",
        "category": "terminology",
    },
    {
        "query": "how can i run startup and shutdown tasks when app begins or stops",
        "expected_strategy": "multi_query",
        "category": "terminology",
    },

    # 3. Multiple independent information needs -> decompose
    {
        "query": (
            "how do i configure middleware, implement oauth2 "
            "authentication, and write tests for endpoints"
        ),
        "expected_strategy": "decompose",
        "category": "multi_part",
    },
    {
        "query": (
            "show me how to define request models, configure database "
            "dependencies, and handle validation errors"
        ),
        "expected_strategy": "decompose",
        "category": "multi_part",
    },
    {
        "query": (
            "how do i upload files, serve static files, "
            "and return downloadable responses"
        ),
        "expected_strategy": "decompose",
        "category": "multi_part",
    },

    # 4. Underspecified intent -> clarify
    {
        "query": "it doesnt work in fastapi",
        "expected_strategy": "clarify",
        "category": "ambiguous",
    },
    {
        "query": "which one should i use",
        "expected_strategy": "clarify",
        "category": "missing_context",
    },
    {
        "query": "why am i getting this error",
        "expected_strategy": "clarify",
        "category": "missing_context",
    },

    # 5. Clearly outside the documentation domain -> out_of_scope
    {
        "query": "who won the last fifa world cup",
        "expected_strategy": "out_of_scope",
        "category": "out_of_scope",
    },
    {
        "query": "write me a poem about the moon",
        "expected_strategy": "out_of_scope",
        "category": "out_of_scope",
    },

    # 6. Clear controls -> direct
    {
        "query": "How do I use Depends in FastAPI?",
        "expected_strategy": "direct",
        "category": "control_clear",
    },
    {
        "query": "How do I declare a path parameter in FastAPI?",
        "expected_strategy": "direct",
        "category": "control_clear",
    },
]