"""Validate citations against evidence assembled for the response."""

from collections.abc import Iterable


def evaluate_citations(
    citations: Iterable[object],
    context_evidence: Iterable[object],
    *,
    require_citation: bool = True,
) -> dict[str, object]:
    def evidence_id(item: object) -> str | None:
        if isinstance(item, dict):
            value = item.get("evidence_id")
        else:
            value = getattr(item, "evidence_id", None)

        return str(value) if value is not None else None

    valid_ids = {
        value for item in context_evidence if (value := evidence_id(item)) is not None
    }
    cited_ids = [
        value for item in citations if (value := evidence_id(item)) is not None
    ]

    invalid_ids = [value for value in cited_ids if value not in valid_ids]
    citations_present = bool(cited_ids)
    citations_complete = citations_present or not require_citation

    return {
        "citation_count": len(cited_ids),
        "valid_citation_count": len(cited_ids) - len(invalid_ids),
        "invalid_citation_ids": invalid_ids,
        "citations_present": citations_present,
        "citations_complete": citations_complete,
        "all_citations_valid": not invalid_ids and citations_complete,
    }
