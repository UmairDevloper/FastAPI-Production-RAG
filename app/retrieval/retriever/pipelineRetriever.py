"""
Retrieval pipeline: dense retriever (R0) + reranker (R1)
========================================================

    question -> dense search in Qdrant (20 candidates) -> cross-encoder rerank -> best 5

``build_pipeline`` returns a standard LangChain retriever:
``build_pipeline().invoke("question")`` gives the final Documents. Later
stages (hybrid search, query processing, context engineering, LangGraph) plug
into this same object.

Reranker presets (the first run downloads the model; keep the Hugging Face
cache on a drive with free space)
    bge-base   BAAI/bge-reranker-base                    about 1 GB, good quality (default)
    minilm     cross-encoder/ms-marco-MiniLM-L-6-v2     very small and fast, English only
    bge-m3     BAAI/bge-reranker-v2-m3                   about 2 GB, strongest, slowest on CPU
Any other Hugging Face cross-encoder id also works.

Demo (run from the project root): compares dense order and reranked order
    uv run python -m app.retrieval.pipeline "how do I return HTML instead of JSON"
    uv run python -m app.retrieval.pipeline "how do I write tests" --reranker minilm
"""

import argparse
import logging

import logfire
from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
# a) the import
from app.retrieval.retriever.reranker2 import CrossEncoderCompressor, FlashRankCompressor
from app.ingestion.embedding4.models_config import configure_logfire
from app.retrieval.retriever.reranker2 import CrossEncoderCompressor
from app.retrieval.retriever.retriever1 import build_dense_retriever

RERANKERS = {
    "bge-base": "BAAI/bge-reranker-base",
    "minilm": "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "bge-m3": "BAAI/bge-reranker-v2-m3",
    "flashrank": "flashrank:ms-marco-MiniLM-L-12-v2",
}

DEFAULT_RERANKER = "bge-base"
DEFAULT_CANDIDATES = 10   # chunks fetched from Qdrant
DEFAULT_TOP_N = 5         # chunks kept after reranking (what the LLM will later receive)


def build_pipeline(
    rerank: str | None = DEFAULT_RERANKER,
    candidates: int = DEFAULT_CANDIDATES,
    top_n: int = DEFAULT_TOP_N,
) -> BaseRetriever:
    """
    Assemble the retrieval pipeline.

    Args:
        rerank: A key of ``RERANKERS``, any Hugging Face cross-encoder id, or
            ``None`` for plain dense retrieval without reranking.
        candidates: How many chunks the dense search fetches.
        top_n: How many chunks are returned (after reranking if enabled).

    Returns:
        A LangChain retriever. Each returned Document carries ``dense_score``
        and, when reranking is on, ``rerank_score``.
    """
    if rerank is None:
        return build_dense_retriever(k=top_n)

    base = build_dense_retriever(k=candidates)
    model_id = RERANKERS.get(rerank, rerank)
    if model_id.startswith("flashrank:"):
        compressor = FlashRankCompressor(model_name=model_id.split(":", 1)[1], top_n=top_n)
    else:
        compressor = CrossEncoderCompressor(model_name=model_id, top_n=top_n)
    return ContextualCompressionRetriever(base_compressor=compressor, base_retriever=base)


def show(label: str, docs: list[Document], score_key: str) -> None:
    """
    Print a ranked list of Documents.

    Args:
        label: Heading for the list.
        docs: Documents in ranked order.
        score_key: Metadata key holding the score to display.
    """
    print(f"\n{label}")
    for rank, doc in enumerate(docs, start=1):
        heading = " > ".join(doc.metadata.get("heading_path", [])) or doc.metadata.get("page_title", "")
        print(f"  {rank}. {doc.metadata.get(score_key, 0):.3f}  {heading}")
        print(f"       {doc.metadata.get('section_url', doc.metadata['url'])}")


def main() -> None:
    """Run both the dense baseline and the reranked pipeline for one question and print them."""
    parser = argparse.ArgumentParser(description="Compare dense order and reranked order for a question.")
    parser.add_argument("question", nargs="+", help="the question to search for")
    parser.add_argument("--reranker", default=DEFAULT_RERANKER, help=f"preset {list(RERANKERS)} or a Hugging Face id")
    args = parser.parse_args()
    question = " ".join(args.question)

    logging.basicConfig(level=logging.WARNING)
    configure_logfire("fastapi-rag-retrieval")
    try:
        dense = build_pipeline(rerank=None)
        reranked = build_pipeline(rerank=args.reranker)
        show("Dense only (R0)", dense.invoke(question), "dense_score")
        show(f"Dense + reranker '{args.reranker}' (R0 + R1)", reranked.invoke(question), "rerank_score")
    finally:
        logfire.shutdown()


if __name__ == "__main__":
    main()