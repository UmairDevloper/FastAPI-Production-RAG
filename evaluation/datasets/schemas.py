"""Schema for evaluation golden cases."""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GoldenCase:
    case_id: str
    question: str
    required_facts: tuple[str, ...] = ()
    expected_source_terms: tuple[str, ...] = ()
    expected_output: str | None = None
    expect_abstention: bool = False
    # Optional stable IDs for relevant source chunks, when labeled.
    relevant_chunk_ids: tuple[str, ...] = ()
