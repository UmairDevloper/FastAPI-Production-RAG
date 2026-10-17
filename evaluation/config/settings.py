"""Evaluation suite configuration."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVALUATION_ROOT = PROJECT_ROOT / "evaluation"
DATASET_PATH = EVALUATION_ROOT / "datasets" / "golden_cases.jsonl"
REPORTS_DIR = EVALUATION_ROOT / "reports"

# Fast, deterministic checks should run before expensive LLM judging.
DEFAULT_SMOKE_CASES = 1
DEFAULT_FULL_CASES = 30

JUDGE_MODEL = "rag-generation"
JUDGE_BASE_URL = "http://localhost:4000/v1"
JUDGE_TIMEOUT_SECONDS = 120.0

# These are initial guardrails, not claims that the system already meets them.
THRESHOLDS = {
    "retrieval_hit_at_5": 0.80,
    "faithfulness": 0.80,
    "answer_relevancy": 0.80,
    "citation_validity": 1.00,
}
