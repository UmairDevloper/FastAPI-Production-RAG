"""
Retrieval-phase evaluation: dense baseline vs dense + reranker
==============================================================

Runs the SAME questions as the ingestion evaluation against retrieval
configurations built with LangChain, and prints one comparison table.

How it works
------------
    - Configurations: ``dense`` (plain search) plus one entry per reranker.
      Every configuration returns the same 20 candidates, so Hit@20 is the
      same for all: it is the CEILING a reranker cannot exceed. The reranker
      only changes the ORDER inside those 20.
    - ``LangChainAsLlamaRetriever`` is a thin adapter that lets LlamaIndex's
      ``RetrieverEvaluator`` score any LangChain retriever, so the metrics are
      computed by the same code as the ingestion baseline and the numbers are
      directly comparable.
    - Ground truth: the chunk ids derived from ``CASES`` (the chunk level:
      right page AND a keyword in the chunk text).

Output
------
    1. Table: Hit@1/3/5/10/20, MRR, NDCG@10 and latency per configuration
    2. Which questions a reranker FIXED or BROKEN compared with dense (Hit@5)
    3. Score separation: in-scope vs out-of-scope top scores. A reranker score
       often separates "answerable" from "not in the docs" better than a cosine
       score, which is how the R5 "not found" gate will be built.

Commands (run from the project root)
------------------------------------
    uv run python -m app.retrieval.evaluate run
    uv run python -m app.retrieval.evaluate run --rerankers bge-base,minilm
    uv run python -m app.retrieval.evaluate run --rerankers all
"""

import argparse
import logging
import sys
import time

import logfire
import pandas as pd
from langchain_core.retrievers import BaseRetriever as LangChainRetriever
from llama_index.core import QueryBundle
from llama_index.core.evaluation import RetrieverEvaluator
from llama_index.core.retrievers import BaseRetriever as LlamaRetriever
from llama_index.core.schema import NodeWithScore, TextNode

from app.ingestion.embedding4.embedder import load_chunks
from app.ingestion.embedding4.models_config import configure_logfire
from app.ingestion.evaluate import CASES, OUT_OF_SCOPE, expected_ids   # same questions as the baseline
from app.retrieval.retriever.pipelineRetriever import RERANKERS, build_pipeline

KS = (1, 3, 5, 10, 20)     # cut-offs; 20 is the number of candidates (the ceiling)
CANDIDATES = 10       # chunks fetched from Qdrant for every configuration
METRICS = ["hit_rate", "mrr", "ndcg"]


# ---------------------------------------------------------------------------
# Adapter: LangChain retriever -> LlamaIndex retriever
# ---------------------------------------------------------------------------

class LangChainAsLlamaRetriever(LlamaRetriever):
    """
    Let LlamaIndex's evaluator score a LangChain retriever.

    The LangChain retriever is invoked once per question (results are cached),
    and ``top_k`` slices the ranked list, so one call serves every cut-off in
    ``KS``. Node ids are the chunk ids, so they can be compared with the
    expected ids.

    Attributes:
        top_k: How many of the ranked documents to expose.
        latencies: Milliseconds per uncached question (the whole pipeline).
    """

    def __init__(self, retriever: LangChainRetriever) -> None:
        """
        Args:
            retriever: Any LangChain retriever whose Documents carry ``chunk_id`` and ``url`` metadata.
        """
        super().__init__()
        self.retriever = retriever
        self.top_k = max(KS)
        self.latencies: list[float] = []
        self._cache: dict[str, list] = {}

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        """
        Run the LangChain retriever (once per question) and convert to nodes.

        Args:
            query_bundle: LlamaIndex wrapper around the question.

        Returns:
            The first ``top_k`` documents as nodes. The score is the rerank
            score when present, otherwise the dense score.
        """
        question = query_bundle.query_str
        docs = self._cache.get(question)
        if docs is None:
            started = time.perf_counter()
            docs = self.retriever.invoke(question)
            self.latencies.append((time.perf_counter() - started) * 1000)
            self._cache[question] = docs

        return [
            NodeWithScore(
                node=TextNode(
                    id_=doc.metadata["chunk_id"],
                    text=doc.page_content,
                    metadata={"url": doc.metadata["url"]},
                ),
                score=float(doc.metadata.get("rerank_score", doc.metadata.get("dense_score", 0.0))),
            )
            for doc in docs[: self.top_k]
        ]


# ---------------------------------------------------------------------------
# Evaluating one configuration
# ---------------------------------------------------------------------------

def evaluate_config(label: str, retriever: LangChainRetriever, chunks: list[dict]) -> dict:
    """
    Evaluate one retrieval configuration on all questions.

    Args:
        label: Name shown in the report (``dense``, ``dense+bge-base``, ...).
        retriever: The LangChain retriever to test.
        chunks: All chunks (to derive the expected ids).

    Returns:
        A dict with the summary table (chunk and page level), the per-question
        Hit@5 at chunk level, latency figures and top-1 scores for in-scope
        and out-of-scope questions.
    """
    adapter = LangChainAsLlamaRetriever(retriever)
    adapter.retrieve("warm up")        # loads the models; keep this out of the timings
    adapter.latencies.clear()
    evaluator = RetrieverEvaluator.from_metric_names(METRICS, retriever=adapter)

    rows: list[dict] = []
    in_scores: list[float] = []

    with logfire.span("retrieval evaluation {config}", config=label, questions=len(CASES)):
        for case in CASES:
            levels = {
                "page": expected_ids(case, chunks, require_keyword=False),
                "chunk": expected_ids(case, chunks, require_keyword=True),
            }
            if not levels["page"] or not levels["chunk"]:
                continue   # nothing to find; run the ingestion `validate` command to see why

            for k in KS:
                adapter.top_k = k
                for level, ids in levels.items():
                    result = evaluator.evaluate(query=case.question, expected_ids=ids)
                    rows.append({"level": level, "k": k, "question": case.question, **result.metric_vals_dict})

            adapter.top_k = 1
            in_scores.append(adapter.retrieve(case.question)[0].score)

        out_scores = [adapter.retrieve(question)[0].score for question in OUT_OF_SCOPE]

        df = pd.DataFrame(rows)
        summary = df.groupby(["level", "k"])[METRICS].mean()
        ordered = sorted(adapter.latencies)

        logfire.info(
            "evaluation {config}: chunk hit@5 {hit5}, mrr@20 {mrr}, avg latency {latency} ms",
            config=label,
            hit5=round(float(summary.loc[("chunk", 5), "hit_rate"]), 3),
            mrr=round(float(summary.loc[("chunk", 20), "mrr"]), 3),
            latency=round(sum(ordered) / len(ordered)),
        )

    return {
        "label": label,
        "summary": summary,
        "hit5": df[(df["level"] == "chunk") & (df["k"] == 5)].set_index("question")["hit_rate"],
        "latency_avg_ms": sum(ordered) / len(ordered),
        "latency_p95_ms": ordered[int(0.95 * (len(ordered) - 1))],
        "in_scores": in_scores,
        "out_scores": out_scores,
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_report(results: list[dict]) -> None:
    """
    Print the comparison table, the fixed/broken questions and the score separation.

    The first result is the baseline (``dense``); every other one is compared with it.

    Args:
        results: One dict per configuration, as returned by :func:`evaluate_config`.
    """
    print("\n=== Retrieval phase: chunk-level comparison ===")
    header = f"{'config':<20}" + "".join(f"{'Hit@' + str(k):>8}" for k in KS)
    print(header + f"{'MRR@20':>9}{'NDCG@10':>9}{'avg ms':>9}{'p95 ms':>9}")
    for r in results:
        chunk = r["summary"].loc["chunk"]
        hits = "".join(f"{float(chunk.loc[k, 'hit_rate']):>8.0%}" for k in KS)
        print(f"{r['label']:<20}{hits}{float(chunk.loc[20, 'mrr']):>9.2f}{float(chunk.loc[10, 'ndcg']):>9.2f}"
              f"{r['latency_avg_ms']:>9.0f}{r['latency_p95_ms']:>9.0f}")
    print(f"\nHit@{max(KS)} is the ceiling: a reranker only reorders the {CANDIDATES} candidates, "
          "so it cannot find what the first search missed.")

    baseline = results[0]
    for r in results[1:]:
        fixed = [q for q in baseline["hit5"].index if baseline["hit5"][q] == 0 and r["hit5"].get(q, 0) == 1]
        broken = [q for q in baseline["hit5"].index if baseline["hit5"][q] == 1 and r["hit5"].get(q, 0) == 0]
        print(f"\n{r['label']} vs {baseline['label']} at Hit@5: {len(fixed)} fixed, {len(broken)} broken")
        for question in fixed:
            print(f"  + {question}")
        for question in broken:
            print(f"  - {question}")

    print("\n=== Score separation (top-1 score: answerable vs not in the docs) ===")
    for r in results:
        low_in, high_out = min(r["in_scores"]), max(r["out_scores"])
        verdict = "clean gap" if high_out < low_in else "OVERLAP"
        print(f"{r['label']:<20} in-scope min {low_in:.2f}   out-of-scope max {high_out:.2f}   -> {verdict}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse the command line, evaluate each configuration and print the report."""
    parser = argparse.ArgumentParser(description="Compare retrieval configurations.")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run the comparison")
    DEFAULT_RERANKER_ARG = "bge-base"
    run.add_argument(
        "--rerankers",
        default=DEFAULT_RERANKER_ARG,
        help=f"comma-separated presets from {list(RERANKERS)}, or 'all' (default: {DEFAULT_RERANKER_ARG})",
    )
    args = parser.parse_args()

    names = list(RERANKERS) if args.rerankers == "all" else [n.strip() for n in args.rerankers.split(",") if n.strip()]
    unknown = [n for n in names if n not in RERANKERS]
    if unknown:
        raise SystemExit(f"Unknown reranker(s) {unknown}. Choose from {list(RERANKERS)} or 'all'.")

    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
    configure_logfire("fastapi-rag-retrieval-evaluation")

    try:
        chunks = load_chunks()
        results = [evaluate_config("dense", build_pipeline(rerank=None, top_n=CANDIDATES), chunks)]
        for name in names:
            pipeline = build_pipeline(rerank=name, candidates=CANDIDATES, top_n=CANDIDATES)
            results.append(evaluate_config(f"dense+{name}", pipeline, chunks))
        print_report(results)
    finally:
        logfire.shutdown()


if __name__ == "__main__":
    sys.exit(main())