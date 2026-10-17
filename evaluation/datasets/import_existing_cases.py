"""Import existing generation cases into the evaluation JSONL dataset."""

import json

from app.generation.evaluate_cases import CASES
from evaluation.config.settings import DATASET_PATH


def main() -> None:
    records = []

    for index, case in enumerate(CASES, start=1):
        records.append({
            "case_id": f"fastapi-{index:03d}",
            "question": case.question,
            "required_facts": list(case.required_facts),
            "expected_source_terms": list(case.expected_source_terms),
            "expected_output": None,
            "expect_abstention": case.expect_abstention,
            "relevant_chunk_ids": [],
        })

    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)

    with DATASET_PATH.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Imported cases: {len(records)}")
    print(f"Dataset: {DATASET_PATH}")
    print("Reference answers and relevant chunk IDs remain unlabeled.")


if __name__ == "__main__":
    main()
