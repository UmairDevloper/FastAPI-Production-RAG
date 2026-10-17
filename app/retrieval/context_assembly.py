from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.documents import Document

from app.retrieval.deduplication import (
    deduplicate_documents,
    get_document_id,
)


@dataclass(frozen=True, slots=True)
class Evidence:
    """A selected document and its source information."""

    evidence_id: str
    content: str
    source_url: str | None
    page_title: str | None
    heading_path: str | None
    score: float | None


@dataclass(frozen=True, slots=True)
class AssembledContext:
    """Context prepared for the answer-generation stage."""

    context: str
    evidence: list[Evidence]
    estimated_tokens: int
    omitted_documents: int


def estimate_tokens(text: str) -> int:
    """Estimate token count without an additional tokenizer dependency.

    This is a rough budget estimate, not an exact model token count.
    """
    return max(1, (len(text) + 3) // 4) if text else 0


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None

    result = str(value).strip()
    return result or None


def _format_evidence(item: Evidence) -> str:
    """Format one evidence item with explicit source information."""
    lines = [f"[{item.evidence_id}]"]

    if item.page_title:
        lines.append(f"Title: {item.page_title}")

    if item.heading_path:
        lines.append(f"Section: {item.heading_path}")

    if item.source_url:
        lines.append(f"Source: {item.source_url}")

    lines.extend(["Content:", item.content])

    return "\n".join(lines)


def assemble_context(
    documents: list[Document],
    *,
    max_tokens: int = 4000,
    max_documents: int = 8,
) -> AssembledContext:
    """Deduplicate and pack retrieved documents into a bounded context.

    Documents are considered in their incoming order, so the caller should
    provide them in retrieval/fusion relevance order.
    """
    if max_tokens < 1:
        raise ValueError("max_tokens must be at least 1.")

    if max_documents < 1:
        raise ValueError("max_documents must be at least 1.")

    unique_documents = deduplicate_documents(documents)
    selected: list[Evidence] = []
    formatted_blocks: list[str] = []
    estimated_tokens = 0
    omitted_documents = 0

    for doc in unique_documents:
        content = doc.page_content.strip()

        if not content:
            omitted_documents += 1
            continue

        metadata = doc.metadata
        evidence = Evidence(
            evidence_id=get_document_id(doc),
            content=content,
            source_url=_optional_string(
                metadata.get("section_url") or metadata.get("url")
            ),
            page_title=_optional_string(metadata.get("page_title")),
            heading_path=_optional_string(metadata.get("heading_path")),
            score=(
                float(metadata["fusion_score"])
                if metadata.get("fusion_score") is not None
                else (
                    float(metadata["dense_score"])
                    if metadata.get("dense_score") is not None
                    else None
                )
            ),
        )

        block = _format_evidence(evidence)
        separator = "\n\n---\n\n" if formatted_blocks else ""
        block_tokens = estimate_tokens(separator + block)

        if len(selected) >= max_documents:
            omitted_documents += 1
            continue

        if estimated_tokens + block_tokens > max_tokens:
            omitted_documents += 1
            continue

        selected.append(evidence)
        formatted_blocks.append(block)
        estimated_tokens += block_tokens

    return AssembledContext(
        context="\n\n---\n\n".join(formatted_blocks),
        evidence=selected,
        estimated_tokens=estimated_tokens,
        omitted_documents=omitted_documents,
    )
