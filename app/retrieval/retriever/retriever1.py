"""
R0: dense retriever as a LangChain retriever
============================================

Wraps your existing Qdrant collection (built by the ingestion phase) as a
standard LangChain retriever. ``retriever.invoke("question")`` returns a list
of LangChain ``Document`` objects, best match first. Results equal your
ingestion baseline, but any LangChain component (rerankers, query
transformers, LangGraph nodes, ...) can now be plugged in around it.

Pieces
------
    ModelEmbeddings        adapts your ActiveModel (Qwen3 / BGE-M3) to LangChain's
                           ``Embeddings`` interface (query prompts are applied correctly)
    QdrantDenseRetriever   embeds the question, searches Qdrant, returns Documents
    build_dense_retriever  picks the first model that has a collection AND passes
                           its health check (retries with backoff), which is the
                           same failover idea as the ingestion phase

Document layout
---------------
    page_content        the chunk text
    metadata            every payload field (chunk_id, url, section_url, page_title,
                        category, heading_path, code_languages, links, images, ...)
                        plus ``dense_score`` (cosine similarity from Qdrant)

The model is chosen once when the retriever is built. Switching models per
request, if one fails while serving, belongs to the service layer (R7).

Smoke test (run from the project root)
--------------------------------------
    uv run python -m app.retrieval.retriever "how do I declare a request body"
"""

import logging
import sys
from typing import Any

import logfire
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict

from app.ingestion.embedding4.embedder import collection_name, get_client
from app.ingestion.embedding4.models_config import (
    MODELS,
    ActiveModel,
    ModelFailure,
    configure_logfire,
    health_check,
    with_retries,
)

log = logging.getLogger("retrieval.retriever")

DEFAULT_K = 20        # candidates fetched from Qdrant (the reranker later keeps the best few)
LOG_QUERIES = True    # send the question text to Logfire; set False if users may type sensitive text


# ---------------------------------------------------------------------------
# Embeddings adapter
# ---------------------------------------------------------------------------

class ModelEmbeddings(Embeddings):
    """
    Adapter that exposes an ``ActiveModel`` through LangChain's ``Embeddings`` interface.

    ``embed_query`` uses the model's query prompt and ``embed_documents`` its
    document prompt (for Qwen3 the question gets an instruction prefix), so
    results match what the ingestion phase measured.
    """

    def __init__(self, active: ActiveModel) -> None:
        """
        Args:
            active: A healthy model returned by ``health_check``.
        """
        self.active = active

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embed chunk texts.

        Args:
            texts: The texts to embed.

        Returns:
            One normalized vector per text.
        """
        return self.active.embed(texts, is_query=False)

    def embed_query(self, text: str) -> list[float]:
        """
        Embed a user question.

        Args:
            text: The question.

        Returns:
            A normalized vector.
        """
        return self.active.embed([text], is_query=True)[0]


# ---------------------------------------------------------------------------
# The retriever
# ---------------------------------------------------------------------------

class QdrantDenseRetriever(BaseRetriever):
    """
    Dense-vector search over one Qdrant collection, returning LangChain Documents.

    Attributes:
        client: Qdrant client.
        collection: Collection name (``<prefix>__<model name>``).
        embeddings: Embeddings adapter built from the selected model.
        model_name: Short model name, recorded in traces.
        k: Number of chunks to return.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: Any
    collection: str
    embeddings: Any
    model_name: str
    k: int = DEFAULT_K

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        """
        Embed the question, search Qdrant and convert the hits to Documents.

        The Qdrant call is retried (2s, 4s) on temporary network errors.

        Args:
            query: The user's question.
            run_manager: LangChain callback manager (required by the interface).

        Returns:
            Up to ``k`` Documents, best first, each with a ``dense_score``.
        """
        attributes = {"query": query} if LOG_QUERIES else {}
        with logfire.span("dense retrieval", model=self.model_name, k=self.k, **attributes):
            vector = self.embeddings.embed_query(query)

            points = with_retries(
                lambda: self.client.query_points(
                    collection_name=self.collection,
                    query=vector,
                    limit=self.k,
                    with_payload=True,
                ).points,
                "Qdrant search",
            )

            docs = [
                Document(
                    page_content=point.payload["text"],
                    metadata={
                        **{key: value for key, value in point.payload.items() if key != "text"},
                        "dense_score": point.score,
                    },
                )
                for point in points
            ]
            logfire.info(
                "retrieved {count} chunks",
                count=len(docs),
                top_score=docs[0].metadata["dense_score"] if docs else None,
            )
        return docs


def build_dense_retriever(k: int = DEFAULT_K) -> QdrantDenseRetriever:
    """
    Build the retriever with the first usable model.

    Walks ``MODELS`` in priority order and takes the first model that has a
    collection in Qdrant and passes its health check (load plus a probe
    embedding, with retries). A model that fails is skipped with a warning,
    so a broken primary falls back to the next model's collection.

    Args:
        k: How many chunks the retriever returns per question.

    Returns:
        A ready-to-use ``QdrantDenseRetriever``.

    Raises:
        RuntimeError: If no model has both a collection and a working model.
    """
    client = get_client()

    for cfg in MODELS:
        name = collection_name(cfg["name"])
        if not with_retries(lambda: client.collection_exists(name), "Qdrant collection check"):
            log.info("No collection '%s' for model '%s', skipping", name, cfg["name"])
            continue
        try:
            active = health_check(cfg)
        except ModelFailure as exc:
            log.error("%s. Trying the next model.", exc)
            logfire.warn("retrieval model {model} unusable", model=cfg["name"], reason=str(exc))
            continue

        log.info("Retriever uses model '%s' (collection '%s')", cfg["name"], name)
        return QdrantDenseRetriever(
            client=client,
            collection=name,
            embeddings=ModelEmbeddings(active),
            model_name=cfg["name"],
            k=k,
        )

    raise RuntimeError("No usable collection and model found. Run the embedding stage first.")


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python -m app.retrieval.retriever "your question"')

    logging.basicConfig(level=logging.WARNING)
    configure_logfire("fastapi-rag-retrieval")
    try:
        results = build_dense_retriever(k=5).invoke(" ".join(sys.argv[1:]))
        for rank, doc in enumerate(results, start=1):
            heading = " > ".join(doc.metadata["heading_path"]) or doc.metadata["page_title"]
            print(f"{rank}. {doc.metadata['dense_score']:.3f}  {heading}\n      {doc.metadata['section_url']}")
    finally:
        logfire.shutdown()