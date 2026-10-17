"""Load and validate the evaluation dataset."""
import json
from pathlib import Path

from evaluation.config.settings import DATASET_PATH
from evaluation.datasets.schemas import GoldenCase


def load_cases(path: Path = DATASET_PATH) -> list[GoldenCase]:
    if not path.exists():
        raise FileNotFoundError(
            f"Golden dataset not found: {path}. "
            "Create the JSONL dataset before running evaluation."
        )

    cases: list[GoldenCase] = []
    seen_ids: set[str] = set()

    with path.open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                item = json.loads(line)
                case = GoldenCase(
                    case_id=str(item["case_id"]),
                    question=str(item["question"]),
                    required_facts=tuple(item.get("required_facts", [])),
                    expected_source_terms=tuple(
                        item.get("expected_source_terms", [])
                    ),
                    expected_output=item.get("expected_output"),
                    expect_abstention=bool(item.get("expect_abstention", False)),
                    relevant_chunk_ids=tuple(item.get("relevant_chunk_ids", [])),
                )
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                raise ValueError(
                    f"Invalid dataset record at line {line_number}: {exc}"
                ) from exc

            if not case.case_id.strip() or not case.question.strip():
                raise ValueError(
                    f"case_id and question must be non-empty (line {line_number})"
                )
            if case.case_id in seen_ids:
                raise ValueError(f"Duplicate case_id: {case.case_id}")

            seen_ids.add(case.case_id)
            cases.append(case)

    if not cases:
        raise ValueError(f"Dataset is empty: {path}")

    return cases
