"""
R1: cross-encoder reranker as a LangChain document compressor
=============================================================

Why a reranker?
    The first search compares the question vector with chunk vectors that were
    created separately. It is fast but approximate. A cross-encoder reads the
    question and each candidate chunk TOGETHER and scores how well the chunk
    answers the question. It is more precise but slower, so it only runs on the
    ~20 candidates from the first search, and the best few are kept.

How it plugs in
    ``CrossEncoderCompressor`` implements LangChain's ``BaseDocumentCompressor``,
    so it works inside ``ContextualCompressionRetriever`` (see pipeline.py).

Custom on purpose
    LangChain's ready-made ``CrossEncoderReranker`` depends on the community
    package ``HuggingFaceCrossEncoder``, which is no longer maintained. This
    class uses sentence-transformers' ``CrossEncoder`` directly (already
    installed) and adds Logfire tracing and a safe fallback.

Fail-open
    If the reranker cannot load or crashes, the compressor logs a warning and
    returns the first ``top_n`` documents in the original dense order, so
    search keeps working with lower precision instead of failing.

Scores
    Every returned Document gets ``rerank_score`` (0 to 1, higher is better) in
    its metadata; the original ``dense_score`` is kept.
"""

import logging
from collections.abc import Sequence
from typing import Any

import logfire
from langchain_core.documents import BaseDocumentCompressor, Document
from pydantic import ConfigDict, PrivateAttr

log = logging.getLogger("retrieval.reranker")

def rerank_text(doc: Document) -> str:
    """
    Build the text the reranker reads for one candidate.

    Same breadcrumb logic as ingestion (``page title > headings``), so the
    reranker sees what the embedding model saw, not the bare chunk text.

    Args:
        doc: A candidate Document with ``page_title`` and ``heading_path`` metadata.

    Returns:
        The breadcrumb, a blank line, then the chunk text (just the text if there is no breadcrumb).
    """
    parts = [doc.metadata.get("page_title", ""), *doc.metadata.get("heading_path", [])]
    breadcrumb = " > ".join(dict.fromkeys(part for part in parts if part))
    return f"{breadcrumb}\n\n{doc.page_content}" if breadcrumb else doc.page_content

class CrossEncoderCompressor(BaseDocumentCompressor):
    """
    Rescore documents with a cross-encoder and keep the best ``top_n``.

    Attributes:
        model_name: Hugging Face id of the cross-encoder.
        top_n: How many documents to return.
        batch_size: Pairs scored per forward pass (lower it if RAM is tight).
        max_length: Token limit per (question + chunk) pair; longer pairs are truncated.
        fail_open: If True, a reranker failure returns the dense order instead of raising.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    model_name: str = "BAAI/bge-reranker-base"
    top_n: int = 5
    batch_size: int = 16
    max_length: int = 512
    fail_open: bool = True

    _model: Any = PrivateAttr(default=None)   # loaded on first use, then reused

    def _load(self):
        """
        Load the cross-encoder once (the first call downloads it if needed).

        Returns:
            The sentence-transformers ``CrossEncoder``.
        """
        if self._model is None:
            from sentence_transformers import CrossEncoder   # imported here to keep start-up fast

            self._model = CrossEncoder(self.model_name, max_length=self.max_length)
        return self._model

    def compress_documents(
        self, documents: Sequence[Document], query: str, callbacks: Any = None
    ) -> Sequence[Document]:
        """
        Rerank candidate documents for a question.

        Args:
            documents: Candidates from the first search (in dense order).
            query: The user's question.
            callbacks: LangChain callbacks (accepted for interface compatibility).

        Returns:
            Up to ``top_n`` documents, best first, each with a ``rerank_score``.

        Raises:
            Exception: Only if ``fail_open`` is False and the reranker fails.
        """
        docs = list(documents)
        if not docs:
            return []

        with logfire.span(
            "rerank", model=self.model_name, candidates=len(docs), top_n=self.top_n
        ):
            try:
                scores = self._load().predict(
                    [(query, rerank_text(doc)) for doc in docs],
                    batch_size=self.batch_size,
                    show_progress_bar=False,
                )
            except Exception as exc:
                if not self.fail_open:
                    raise
                log.error("Reranker '%s' failed (%s); keeping the dense order", self.model_name, exc)
                logfire.warn(
                    "reranker {model} failed, keeping the dense order",
                    model=self.model_name, reason=str(exc),
                )
                return docs[: self.top_n]

            ranked = sorted(zip(docs, scores), key=lambda pair: float(pair[1]), reverse=True)
            result = [
                Document(
                    page_content=doc.page_content,
                    metadata={**doc.metadata, "rerank_score": float(score)},
                )
                for doc, score in ranked[: self.top_n]
            ]
            logfire.info("reranked {count} chunks", count=len(result), top_score=result[0].metadata["rerank_score"])
        return result

class FlashRankCompressor(BaseDocumentCompressor):
    """
    Reranker based on the FlashRank library (small quantized models, built for CPU speed).

    Same contract as ``CrossEncoderCompressor``: returns up to ``top_n``
    documents, best first, each with a ``rerank_score``; on failure it can
    fall back to the dense order (``fail_open``).

    Attributes:
        model_name: A FlashRank model name, e.g. ``ms-marco-MiniLM-L-12-v2``.
        top_n: How many documents to return.
        max_length: Token limit per (question + chunk) pair. The library default
            is short and would cut most chunks, so it is raised here.
        fail_open: If True, a reranker failure returns the dense order instead of raising.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    model_name: str = "ms-marco-MiniLM-L-12-v2"
    top_n: int = 5
    max_length: int = 512
    fail_open: bool = True

    _ranker: Any = PrivateAttr(default=None)   # loaded on first use, then reused

    def _load(self):
        """
        Load the FlashRank model once.

        The model files are stored under ``HF_HOME`` (so they follow the
        Hugging Face cache to the drive with free space), in a ``flashrank`` folder.

        Returns:
            The FlashRank ``Ranker``.
        """
        if self._ranker is None:
            import os
            from pathlib import Path

            from flashrank import Ranker   # imported here to keep start-up fast

            cache_root = Path(os.environ.get("HF_HOME", Path.home() / ".cache")) / "flashrank"
            self._ranker = Ranker(
                model_name=self.model_name, cache_dir=str(cache_root), max_length=self.max_length
            )
        return self._ranker

    def compress_documents(
        self, documents: Sequence[Document], query: str, callbacks: Any = None
    ) -> Sequence[Document]:
        """
        Rerank candidate documents for a question.

        Args:
            documents: Candidates from the first search (in dense order).
            query: The user's question.
            callbacks: LangChain callbacks (accepted for interface compatibility).

        Returns:
            Up to ``top_n`` documents, best first, each with a ``rerank_score``.

        Raises:
            Exception: Only if ``fail_open`` is False and the reranker fails.
        """
        docs = list(documents)
        if not docs:
            return []

        with logfire.span("rerank (flashrank)", model=self.model_name, candidates=len(docs), top_n=self.top_n):
            try:
                from flashrank import RerankRequest

                request = RerankRequest(
                    query=query,
                    passages=[{"id": index, "text": rerank_text(doc)} for index, doc in enumerate(docs)],
                )
                ranked = self._load().rerank(request)   # list of dicts with "id" and "score", best first
            except Exception as exc:
                if not self.fail_open:
                    raise
                log.error("FlashRank '%s' failed (%s); keeping the dense order", self.model_name, exc)
                logfire.warn("flashrank {model} failed, keeping the dense order", model=self.model_name, reason=str(exc))
                return docs[: self.top_n]

            result = [
                Document(
                    page_content=docs[int(item["id"])].page_content,
                    metadata={**docs[int(item["id"])].metadata, "rerank_score": float(item["score"])},
                )
                for item in ranked[: self.top_n]
            ]
            logfire.info("reranked {count} chunks", count=len(result), top_score=result[0].metadata["rerank_score"])
        return result