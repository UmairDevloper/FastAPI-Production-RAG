"""Deterministic checks for required answer facts."""

import re
from collections.abc import Sequence


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def required_fact_coverage(
    answer: str,
    required_facts: Sequence[str],
) -> dict[str, object]:
    if not required_facts:
        return {
            "applicable": False,
            "coverage": None,
            "matched_facts": [],
            "missing_facts": [],
        }

    normalized_answer = normalize(answer)
    matched = [fact for fact in required_facts if normalize(fact) in normalized_answer]
    missing = [fact for fact in required_facts if fact not in matched]

    return {
        "applicable": True,
        "coverage": len(matched) / len(required_facts),
        "matched_facts": matched,
        "missing_facts": missing,
    }
