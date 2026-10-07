"""
Retrieval evaluation with LlamaIndex
====================================

Measures how well the Qdrant index finds the right content, using
LlamaIndex's ``RetrieverEvaluator`` (hit rate, MRR, NDCG, precision, recall)
instead of hand-written metrics.

How it works
------------
1. ``QdrantChunkRetriever`` wraps your Qdrant search as a LlamaIndex
   ``BaseRetriever``. Retrieved nodes carry the chunk id, so they can be
   compared with the expected ids.
2. For each question the expected chunk ids are derived from ``chunks.jsonl``:
       page level   every chunk on the expected page(s)
       chunk level  only the chunks on those pages that contain a keyword
                    (a proxy for "this chunk holds the answer")
3. ``RetrieverEvaluator.evaluate(query, expected_ids)`` scores each question
   at several cut-offs (top 1, 3, 5, 10). Results are averaged with pandas.

Reading the result
    page high, chunk low   right page found, answer chunk missed -> chunk size / boundaries
    both low               embedding / retrieval problem -> hybrid search, reranker, better model
    exact < natural        identifier questions lag -> keyword (hybrid) search will help

Out-of-scope questions
    A few questions the docs cannot answer. Their top similarity score should
    be clearly lower than the scores of in-scope questions; the gap tells you
    where to put a "not found in the docs" threshold.

Commands (run from the project root)
------------------------------------
    uv run python -m app.ingestion.embedding4.evaluate validate
        Checks that the expected pages and keywords exist in your chunks.
        RUN THIS FIRST: a wrong expectation looks like a retrieval failure.

    uv run python -m app.ingestion.embedding4.evaluate run
    uv run python -m app.ingestion.embedding4.evaluate run --model qwen3
    uv run python -m app.ingestion.embedding4.evaluate run --model all

Extending it
------------
Any other retriever (hybrid, reranked, a LlamaIndex or LangChain pipeline) only
has to be a ``BaseRetriever`` returning nodes whose ``id_`` is the chunk id.
Then the same questions and metrics compare it with this baseline. To grow the
question set automatically, LlamaIndex's ``generate_question_context_pairs``
creates synthetic questions per chunk once an LLM is configured.

Setup:  uv add llama-index-core
"""

import argparse
import logging
import sys
import time
from dataclasses import dataclass

import logfire
import pandas as pd
from llama_index.core import QueryBundle
from llama_index.core.evaluation import RetrieverEvaluator
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, TextNode

from app.ingestion.embedding4.embedder import collection_name, get_client, load_chunks
from app.ingestion.embedding4.models_config import (
    MODELS,
    ActiveModel,
    configure_logfire,
    load_model,
    unload_model,
)

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

KS = (1, 3, 5, 10)   # cut-offs: the retriever returns the top k results
MAIN_K = 5           # the cut-off used for the headline numbers and the failure list
METRICS = ["hit_rate", "mrr", "ndcg", "precision", "recall"]   # LlamaIndex metric names


# ---------------------------------------------------------------------------
# Evaluation set
# ---------------------------------------------------------------------------

@dataclass
class Case:
    """
    One evaluation question with its expected answer location.

    Attributes:
        question: The question as a user would type it.
        pages: URL fragments; a chunk is on the right page if its URL
            contains any of them (for example ``"/tutorial/body/"``).
        keywords: Words that should appear in the right chunk (case-insensitive).
        kind: ``"natural"`` (plain language) or ``"exact"`` (identifier-based).
    """

    question: str
    pages: list[str]
    keywords: list[str]
    kind: str = "natural"


CASES = [
    # --- natural-language questions ----------------------------------------
    Case("How do I read JSON data sent by the client in a POST request?",
         ["/tutorial/body/"], ["BaseModel", "request body"]),
    Case("How can I make a query parameter optional with a default value?",
         ["/tutorial/query-params/"], ["str | None", "default", "optional"]),
    Case("How do I limit the maximum length of a query string?",
         ["/tutorial/query-params-str-validations/"], ["max_length"]),
    Case("How do I declare a path parameter with a type like int?",
         ["/tutorial/path-params/"], ["item_id"]),
    Case("How do I share logic between several endpoints?",
         ["/tutorial/dependencies/"], ["Depends"]),
    Case("How do I return an error with a specific status code to the client?",
         ["/tutorial/handling-errors/"], ["HTTPException"]),
    Case("How do I allow requests from another website's frontend?",
         ["/tutorial/cors/"], ["CORSMiddleware", "origins"]),
    Case("How do I run a task after sending the response, like sending an email?",
         ["/tutorial/background-tasks/"], ["BackgroundTasks"]),
    Case("How do I split a large app into multiple files?",
         ["/tutorial/bigger-applications/"], ["APIRouter"]),
    Case("How do I write automated tests for my API?",
         ["/tutorial/testing/"], ["TestClient"]),
    Case("How do I connect FastAPI to a relational database?",
         ["/tutorial/sql-databases/"], ["SQLModel", "Session"]),
    Case("How do I accept file uploads?",
         ["/tutorial/request-files/"], ["UploadFile"]),
    Case("How do I serve static files such as images or CSS?",
         ["/tutorial/static-files/"], ["StaticFiles"]),
    Case("How can I hide a field like the password from the response?",
         ["/tutorial/response-model/"], ["response_model"]),
    Case("How do I set the HTTP status code for a successful creation?",
         ["/tutorial/response-status-code/"], ["status_code", "201"]),
    Case("How do I read fields from an HTML form?",
         ["/tutorial/request-forms/"], ["Form"]),
    Case("How do I read cookies sent by the browser?",
         ["/tutorial/cookie-params/"], ["Cookie"]),
    Case("How do I read a custom request header?",
         ["/tutorial/header-params/"], ["Header"]),
    Case("How do I protect endpoints with a username and password flow?",
         ["/tutorial/security/"], ["OAuth2PasswordBearer", "OAuth2"]),
    Case("How do I create and verify JWT access tokens?",
         ["/tutorial/security/oauth2-jwt/"], ["jwt"]),
    Case("How do I get the current logged in user inside an endpoint?",
         ["/tutorial/security/get-current-user/"], ["get_current_user"]),
    Case("How do I run code when the application starts and stops?",
         ["/advanced/events/"], ["lifespan"]),
    Case("How do I build a WebSocket endpoint?",
         ["/advanced/websockets/"], ["WebSocket"]),
    Case("How do I return HTML instead of JSON?",
         ["/advanced/custom-response/"], ["HTMLResponse"]),
    Case("How do I load configuration from environment variables?",
         ["/advanced/settings/"], ["BaseSettings", "environment variable"]),
    Case("How do I package my app in a Docker container?",
         ["/deployment/docker/"], ["Dockerfile"]),
    Case("When should I use async def instead of def?",
         ["/async/"], ["async def"]),
    Case("How do I add custom code that runs for every request?",
         ["/tutorial/middleware/"], ["middleware"]),
    Case("How do I run cleanup code after a dependency finishes?",
         ["/tutorial/dependencies/dependencies-with-yield/"], ["yield"]),
    Case("How do I set a title and version for the generated API docs?",
         ["/tutorial/metadata/"], ["description", "version"]),
    Case("How do I declare a nested Pydantic model inside a request body?",
         ["/tutorial/body-nested-models/"], ["BaseModel"]),
    Case("How do I add validation rules like a minimum value to a model field?",
         ["/tutorial/body-fields/"], ["Field("]),

    # --- exact-identifier questions (test keyword matching) ----------------
    Case("What does Depends do?",
         ["/tutorial/dependencies/"], ["Depends"], "exact"),
    Case("How do I raise HTTPException with custom headers?",
         ["/tutorial/handling-errors/"], ["HTTPException", "headers"], "exact"),
    Case("CORSMiddleware allow_origins configuration",
         ["/tutorial/cors/"], ["allow_origins"], "exact"),
    Case("What is dependency_overrides used for?",
         ["/advanced/testing-dependencies/"], ["dependency_overrides"], "exact"),
    Case("How does response_model_exclude_unset work?",
         ["/tutorial/response-model/"], ["response_model_exclude_unset"], "exact"),
    Case("How do I use OAuth2PasswordRequestForm?",
         ["/tutorial/security/simple-oauth2/"], ["OAuth2PasswordRequestForm"], "exact"),
    Case("How do I pass lifespan to FastAPI?",
         ["/advanced/events/"], ["lifespan"], "exact"),
    Case("How do I use include_router with a prefix?",
         ["/tutorial/bigger-applications/"], ["include_router", "prefix"], "exact"),
]

# Questions the FastAPI docs cannot answer (used for the score-gap check)
OUT_OF_SCOPE = [
    "What is the best pizza recipe?",
    "How do I train a neural network with PyTorch?",
    "What is the capital of France?",
    "How do I fix a leaking kitchen tap?",
]


# ---------------------------------------------------------------------------
# Ground truth from the chunks
# ---------------------------------------------------------------------------

def expected_ids(case: Case, chunks: list[dict], require_keyword: bool) -> list[str]:
    """
    Find the chunk ids that count as a correct answer for a question.

    Args:
        case: The question with its expected pages and keywords.
        chunks: All chunks from ``chunks.jsonl``.
        require_keyword: If True (chunk level), the chunk text must also
            contain one of the keywords. If False (page level), being on the
            right page is enough.

    Returns:
        The ``chunk_id`` of every matching chunk.
    """
    ids = []
    for chunk in chunks:
        if not any(page in chunk["url"] for page in case.pages):
            continue
        if require_keyword and case.keywords:
            text = chunk["text"].lower()
            if not any(k.lower() in text for k in case.keywords):
                continue
        ids.append(chunk["chunk_id"])
    return ids


def validate() -> bool:
    """
    Check that every expectation in ``CASES`` can actually be met.

    Each question needs at least one chunk on its expected page(s), and at
    least one of those chunks must contain a keyword. A failing expectation
    would otherwise be counted as a retrieval failure.

    Returns:
        True if every case is consistent with the chunks, False otherwise.
    """
    chunks = load_chunks()
    problems = 0

    for case in CASES:
        if not expected_ids(case, chunks, require_keyword=False):
            problems += 1
            print(f"[NO PAGE]     {case.question}\n              none of {case.pages} matches a chunk URL")
        elif not expected_ids(case, chunks, require_keyword=True):
            problems += 1
            print(f"[NO KEYWORD]  {case.question}\n              none of {case.keywords} appears on {case.pages}")

    print(f"\n{len(CASES)} questions checked, {problems} problem(s).")
    if problems:
        print("Fix the page paths / keywords above (look at the 'url' values in chunks.jsonl) before running the evaluation.")
    return problems == 0


# ---------------------------------------------------------------------------
# The retriever under test
# ---------------------------------------------------------------------------

class QdrantChunkRetriever(BaseRetriever):
    """
    Your Qdrant dense search, wrapped as a LlamaIndex retriever.

    Each result is a ``NodeWithScore`` whose node id is the ``chunk_id``, so
    ``RetrieverEvaluator`` can compare retrieved ids with expected ids.
    Question vectors are cached, so evaluating the same question at several
    cut-offs embeds it only once.

    Attributes:
        top_k: How many chunks to return. The evaluation changes it per cut-off.
        latencies: Milliseconds per uncached query (question embedding + search).
    """

    def __init__(self, model_name: str, top_k: int = MAIN_K) -> None:
        """
        Connect to the model's collection and load the model.

        Args:
            model_name: Short model name from ``MODELS`` (for example ``"qwen3"``).
            top_k: Initial number of results per query.

        Raises:
            RuntimeError: If the model is unknown or has no collection in Qdrant.
        """
        super().__init__()
        cfg = next((m for m in MODELS if m["name"] == model_name), None)
        if cfg is None:
            raise RuntimeError(f"Unknown model '{model_name}'. Known: {[m['name'] for m in MODELS]}")

        self.client = get_client()
        self.collection = collection_name(model_name)
        if not self.client.collection_exists(self.collection):
            raise RuntimeError(f"Collection '{self.collection}' does not exist. Run the embedding stage first.")

        self.cfg = cfg
        self.active = ActiveModel(cfg=cfg, model=load_model(cfg))
        self.top_k = top_k
        self.latencies: list[float] = []
        self._vector_cache: dict[str, list[float]] = {}

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        """
        Embed the question, search Qdrant and return LlamaIndex nodes.

        Args:
            query_bundle: LlamaIndex wrapper around the question text.

        Returns:
            Up to ``top_k`` nodes, best first, each with its similarity score.
        """
        question = query_bundle.query_str
        started = time.perf_counter()

        vector = self._vector_cache.get(question)
        fresh = vector is None
        if fresh:
            vector = self.active.embed([question], is_query=True)[0]
            self._vector_cache[question] = vector

        points = self.client.query_points(
            collection_name=self.collection, query=vector, limit=self.top_k, with_payload=True
        ).points

        if fresh:
            self.latencies.append((time.perf_counter() - started) * 1000)

        return [
            NodeWithScore(
                node=TextNode(
                    id_=p.payload["chunk_id"],
                    text=p.payload["text"],
                    metadata={"url": p.payload["url"]},
                ),
                score=p.score,
            )
            for p in points
        ]


# ---------------------------------------------------------------------------
# Running the evaluation
# ---------------------------------------------------------------------------

def evaluate_model(model_name: str) -> dict:
    """
    Evaluate one model's collection with ``RetrieverEvaluator``.

    For every question, at every cut-off in ``KS`` and at both levels (page
    and chunk), LlamaIndex computes the metrics in ``METRICS``. The rows are
    collected in a pandas DataFrame and summarized.

    Args:
        model_name: Short model name from ``MODELS``.

    Returns:
        A dict with the per-question DataFrame, the summary table, the
        headline numbers, latency figures, similarity scores for in-scope and
        out-of-scope questions, and the number of skipped questions.
    """
    chunks = load_chunks()
    url_of = {c["chunk_id"]: c["url"] for c in chunks}

    retriever = QdrantChunkRetriever(model_name)
    retriever.retrieve("warm up")      # the first call is slow; keep it out of the timings
    retriever.latencies.clear()

    evaluator = RetrieverEvaluator.from_metric_names(METRICS, retriever=retriever)

    rows: list[dict] = []
    in_scope_scores: list[float] = []
    skipped = 0

    with logfire.span("retrieval evaluation {model}", model=model_name, questions=len(CASES)):
        for case in CASES:
            levels = {
                "page": expected_ids(case, chunks, require_keyword=False),
                "chunk": expected_ids(case, chunks, require_keyword=True),
            }
            if not levels["page"] or not levels["chunk"]:
                skipped += 1   # nothing to find; run `validate` to see why
                continue

            for k in KS:
                retriever.top_k = k
                for level, ids in levels.items():
                    result = evaluator.evaluate(query=case.question, expected_ids=ids)
                    rows.append({
                        "level": level, "k": k, "kind": case.kind, "question": case.question,
                        **result.metric_vals_dict, "retrieved": result.retrieved_ids,
                    })

            retriever.top_k = 1
            top = retriever.retrieve(case.question)
            in_scope_scores.append(top[0].score if top else 0.0)

        retriever.top_k = 1
        out_scores = [retriever.retrieve(q)[0].score for q in OUT_OF_SCOPE]

        df = pd.DataFrame(rows)
        summary = df.groupby(["level", "k"])[METRICS].mean()
        main_chunk = summary.loc[("chunk", MAIN_K)]
        main_page = summary.loc[("page", MAIN_K)]
        avg_latency = sum(retriever.latencies) / len(retriever.latencies)

        # One record per run in Logfire, so runs can be compared over time
        logfire.info(
            "evaluation {model}: chunk hit@{k} {hit}, mrr {mrr}, ndcg {ndcg}, avg latency {latency} ms",
            model=model_name, k=MAIN_K,
            hit=round(float(main_chunk["hit_rate"]), 3),
            mrr=round(float(main_chunk["mrr"]), 3),
            ndcg=round(float(main_chunk["ndcg"]), 3),
            page_hit=round(float(main_page["hit_rate"]), 3),
            latency=round(avg_latency),
            skipped=skipped,
        )

    unload_model(retriever.cfg)   # free memory before the next model loads
    return {
        "model": model_name, "collection": retriever.collection, "df": df, "summary": summary,
        "chunk": main_chunk, "page": main_page, "latency_avg_ms": avg_latency,
        "latency_p95_ms": sorted(retriever.latencies)[int(0.95 * (len(retriever.latencies) - 1))],
        "in_scores": in_scope_scores, "out_scores": out_scores, "skipped": skipped, "url_of": url_of,
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_report(r: dict) -> None:
    """
    Print the report for one model: tables, diagnosis and failed questions.

    Args:
        r: The dict returned by :func:`evaluate_model`.
    """
    df, summary = r["df"], r["summary"]
    print(f"\n=== Retrieval evaluation (LlamaIndex): {r['model']} (collection {r['collection']}) ===")
    print(f"Questions: {df['question'].nunique()} in scope ({r['skipped']} skipped), {len(OUT_OF_SCOPE)} out of scope")

    for level, label in (("page", "Page level (right page found)"), ("chunk", "Chunk level (answer chunk found)")):
        print(f"\n{label}")
        print(summary.loc[level].round(3).to_string())
    print("\nNote: precision and recall are low by design when several chunks count as correct; "
          "compare hit_rate, mrr and ndcg first.")

    main = df[(df["level"] == "chunk") & (df["k"] == MAIN_K)]
    print(f"\nChunk-level hit rate @{MAIN_K} by question type:")
    by_kind = main.groupby("kind")["hit_rate"].agg(["mean", "count"])
    for kind, row in by_kind.iterrows():
        print(f"  {kind:<10} n={int(row['count']):<3} {row['mean']:6.0%}")

    print(f"\nSpeed: avg {r['latency_avg_ms']:.0f} ms, p95 {r['latency_p95_ms']:.0f} ms per new question "
          "(question embedding + search)")

    in_s, out_s = r["in_scores"], r["out_scores"]
    print("\nTop-1 similarity scores:")
    print(f"  in-scope questions:     avg {sum(in_s) / len(in_s):.2f}   min {min(in_s):.2f}")
    print(f"  out-of-scope questions: avg {sum(out_s) / len(out_s):.2f}   max {max(out_s):.2f}")
    if max(out_s) < min(in_s):
        print(f"  -> clean separation: a 'not found in the docs' threshold between {max(out_s):.2f} and {min(in_s):.2f} works")
    else:
        print("  -> the ranges overlap: one score threshold would misclassify some questions "
              "(a reranker score or an LLM check separates them better)")

    # Plain-language diagnosis
    hit = lambda level, k: float(summary.loc[(level, k), "hit_rate"])   # noqa: E731
    hints = []
    if hit("page", MAIN_K) - hit("chunk", MAIN_K) >= 0.15:
        hints.append("Right pages are found but the answer chunk is often missing: review chunk size and boundaries.")
    kinds = by_kind["mean"].to_dict()
    if "exact" in kinds and "natural" in kinds:
        if kinds["natural"] - kinds["exact"] >= 0.15:
            hints.append("Identifier questions lag behind natural ones: hybrid (keyword) search should help.")
        elif kinds["exact"] - kinds["natural"] >= 0.15:
            hints.append("Natural-language questions lag behind: try a stronger model, query rewriting or a reranker.")
    if hit("chunk", 10) - hit("chunk", MAIN_K) >= 0.10:
        hints.append("The right chunk is often at ranks 6-10: a reranker should help.")
    if hit("chunk", MAIN_K) < 0.70:
        hints.append(f"Chunk-level hit rate @{MAIN_K} is below 70%: check the failures below before adding features.")
    print("\nWhat the numbers suggest:")
    print("  " + "\n  ".join(hints) if hints else "  No obvious weakness. Compare against hybrid search and a reranker next.")

    failures = main[main["hit_rate"] == 0]
    if len(failures):
        print(f"\nFailed questions (answer chunk not in the top {MAIN_K}): {len(failures)}")
        for _, row in failures.iterrows():
            print(f"\n  Q: {row['question']}")
            for chunk_id in row["retrieved"][:3]:
                print(f"     got: {r['url_of'].get(chunk_id, chunk_id)}")


def print_comparison(results: list[dict]) -> None:
    """
    Print a side-by-side table when several models were evaluated.

    Args:
        results: One dict per model, as returned by :func:`evaluate_model`.
    """
    print("\n=== Model comparison ===")
    print(f"{'model':<12}{'chunk hit@' + str(MAIN_K):>14}{'chunk mrr':>11}{'chunk ndcg':>12}{'page hit@' + str(MAIN_K):>13}{'avg ms':>9}")
    for r in results:
        print(f"{r['model']:<12}{float(r['chunk']['hit_rate']):>14.0%}{float(r['chunk']['mrr']):>11.2f}"
              f"{float(r['chunk']['ndcg']):>12.2f}{float(r['page']['hit_rate']):>13.0%}{r['latency_avg_ms']:>9.0f}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def models_with_collection() -> list[str]:
    """
    List the model names that already have a collection in Qdrant.

    Returns:
        Model names in priority order (the order of ``MODELS``).
    """
    client = get_client()
    return [m["name"] for m in MODELS if client.collection_exists(collection_name(m["name"]))]


def main() -> None:
    """Parse the command line and run ``validate`` or ``run``."""
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality of the Qdrant index.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="check that the expected pages and keywords exist in the chunks")
    run = sub.add_parser("run", help="run the evaluation")
    run.add_argument("--model", default=None, help="model name, or 'all' (default: first model with a collection)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
    configure_logfire("fastapi-rag-evaluation")

    try:
        if args.command == "validate":
            sys.exit(0 if validate() else 1)

        available = models_with_collection()
        if not available:
            raise SystemExit("No collection found in Qdrant. Run the embedding stage first.")

        names = available if args.model == "all" else [args.model or available[0]]
        results = []
        for name in names:
            results.append(evaluate_model(name))
            print_report(results[-1])
        if len(results) > 1:
            print_comparison(results)
    finally:
        logfire.shutdown()


if __name__ == "__main__":
    main()