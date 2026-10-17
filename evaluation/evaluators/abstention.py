"""Deterministic expected-abstention checks."""


def evaluate_abstention(
    *,
    expect_abstention: bool,
    actually_abstained: bool,
    citation_count: int,
) -> dict[str, object]:
    abstention_matches = expect_abstention == actually_abstained
    no_citations_when_abstaining = not actually_abstained or citation_count == 0

    return {
        "applicable": expect_abstention,
        "expected_abstention": expect_abstention,
        "actually_abstained": actually_abstained,
        "abstention_matches": abstention_matches,
        "no_citations_when_abstaining": no_citations_when_abstaining,
        "passed": abstention_matches and no_citations_when_abstaining,
    }
