from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass

import logfire

logger = logging.getLogger(__name__)

MAX_QUESTION_LENGTH = 8_000

JAILBREAK_PATTERNS = (
    re.compile(
        r"reveal\s+(your\s+)?(system|hidden)\s+prompt",
        re.IGNORECASE,
    ),
    re.compile(
        r"bypass\s+(all\s+)?safety\s+(rules|filters)",
        re.IGNORECASE,
    ),
    re.compile(
        r"act\s+as\s+if\s+you\s+have\s+no\s+restrictions",
        re.IGNORECASE,
    ),
    re.compile(
        r"ignore\s+(all\s+)?previous\s+instructions",
        re.IGNORECASE,
    ),
)

# Candidate payment-card numbers: 13–19 digits, optionally
# separated by spaces or hyphens. Luhn validation follows.
PAYMENT_CARD_CANDIDATE_PATTERN = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")


@dataclass(frozen=True, slots=True)
class SecurityDecision:
    allowed: bool
    reason: str | None = None


def validate_input(question: str) -> SecurityDecision:
    """Apply inexpensive input checks before retrieval."""
    started = time.perf_counter()
    reason: str | None = None

    if not question or not question.strip():
        reason = "empty_input"
    elif len(question) > MAX_QUESTION_LENGTH:
        reason = "input_too_long"
    elif any(pattern.search(question) for pattern in JAILBREAK_PATTERNS):
        reason = "suspected_jailbreak"

    decision = SecurityDecision(
        allowed=reason is None,
        reason=reason,
    )

    latency_ms = round(
        (time.perf_counter() - started) * 1000,
        2,
    )

    logfire.info(
        "security.input_validation",
        allowed=decision.allowed,
        reason=decision.reason,
        input_chars=len(question) if question else 0,
        latency_ms=latency_ms,
    )

    if not decision.allowed:
        logger.warning(
            "Input guardrail rejected input: reason=%s",
            decision.reason,
        )

    return decision


def _passes_luhn(value: str) -> bool:
    """Return whether a digit string passes the Luhn checksum."""
    digits = [int(char) for char in value if char.isdigit()]

    if not 13 <= len(digits) <= 19:
        return False

    checksum = 0
    parity = len(digits) % 2

    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit

    return checksum % 10 == 0


def validate_output(answer: str) -> SecurityDecision:
    """
    Block likely payment-card numbers, not ordinary emails,
    Python decorators, or documentation examples.

    Email addresses are intentionally permitted in output.
    Luhn is a heuristic, not proof that a number is a real card.
    """
    started = time.perf_counter()
    candidate_count = 0

    for match in PAYMENT_CARD_CANDIDATE_PATTERN.finditer(answer):
        digits = "".join(char for char in match.group(0) if char.isdigit())

        if not _passes_luhn(digits):
            continue

        candidate_count += 1

        logger.warning(
            "Output guardrail matched payment_card_candidate; "
            "match_length=%d; match_start=%d",
            len(digits),
            match.start(),
        )

        decision = SecurityDecision(
            False,
            "possible_payment_card",
        )

        logfire.warning(
            "security.output_validation",
            allowed=False,
            reason=decision.reason,
            answer_chars=len(answer),
            latency_ms=round(
                (time.perf_counter() - started) * 1000,
                2,
            ),
        )

        return decision

    decision = SecurityDecision(True)

    logfire.info(
        "security.output_validation",
        allowed=True,
        reason=None,
        answer_chars=len(answer),
        matched_card_candidates=candidate_count,
        latency_ms=round(
            (time.perf_counter() - started) * 1000,
            2,
        ),
    )

    return decision
