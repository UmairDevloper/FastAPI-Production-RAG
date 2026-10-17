from __future__ import annotations

import hashlib

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
    digest = hashlib.sha256(
        doc.page_content.encode("utf-8")
    ).hexdigest()

    return f"content:{digest}"


def deduplicate_documents(
    documents: list[Document],
) -> list[Document]:
    """Keep the first occurrence of each chunk, preserving its order."""
    unique: dict[str, Document] = {}

    for doc in documents:
        document_id = get_document_id(doc)

        if document_id not in unique:
            unique[document_id] = doc

    return list(unique.values())
