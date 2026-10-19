from __future__ import annotations

import hashlib
import time

import logfire
from langchain_core.documents import Document


def get_document_id(doc: Document) -> str:
    """Return a stable identifier for a retrieved chunk."""
    metadata = doc.metadata

    for field in ("chunk_id", "point_id", "id"):
        value = metadata.get(field)
        if value is not None and str(value).strip():
            return f"{field}:{value}"

    # Prefer a source-based identifier when available.
    source = metadata.get("section_url") or metadata.get("url")
    heading = metadata.get("heading_path")

    if source:
        return f"source:{source}|heading:{heading or ''}"

    # Last-resort fallback for documents without identifying metadata.
    digest = hashlib.sha256(doc.page_content.encode("utf-8")).hexdigest()

    return f"content:{digest}"


def deduplicate_documents(
    documents: list[Document],
) -> list[Document]:
    """Keep the first occurrence of each chunk, preserving its order."""
    started = time.perf_counter()
    unique: dict[str, Document] = {}
    duplicate_count = 0

    with logfire.span(
        "retrieval.deduplicate_documents",
        input_document_count=len(documents),
    ) as span:
        for doc in documents:
            document_id = get_document_id(doc)

            if document_id not in unique:
                unique[document_id] = doc
            else:
                duplicate_count += 1

        result = list(unique.values())
        latency_ms = round(
            (time.perf_counter() - started) * 1000,
            2,
        )

        span.set_attribute("deduplication.output_count", len(result))
        span.set_attribute("deduplication.duplicate_count", duplicate_count)
        span.set_attribute("deduplication.latency_ms", latency_ms)

        logfire.info(
            "retrieval.deduplication_completed",
            input_count=len(documents),
            output_count=len(result),
            duplicate_count=duplicate_count,
            latency_ms=latency_ms,
        )

        return result
