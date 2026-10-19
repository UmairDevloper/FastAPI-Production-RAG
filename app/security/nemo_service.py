from __future__ import annotations

import logging
import time
from pathlib import Path

import logfire
from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.rails.llm.options import RailType

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "nemo_guardrails"

_rails: LLMRails | None = None


def get_nemo_rails() -> LLMRails:
    """Initialize NeMo lazily."""
    global _rails

    if _rails is None:
        with logfire.span("security.nemo.initialize"):
            started = time.perf_counter()

            try:
                config = RailsConfig.from_path(str(CONFIG_PATH))
                rails = LLMRails(config)
                _rails = rails

                logfire.info(
                    "security.nemo.initialized",
                    latency_ms=round(
                        (time.perf_counter() - started) * 1000,
                        2,
                    ),
                )
            except Exception as exc:
                logfire.error(
                    "security.nemo.initialization_failed",
                    error_type=type(exc).__name__,
                )
                raise

    return _rails


async def check_nemo_input(question: str) -> bool:
    """Allow input only when NeMo explicitly reports passed."""
    started = time.perf_counter()

    with logfire.span(
        "security.nemo.input_check",
        input_chars=len(question),
    ):
        try:
            result = await get_nemo_rails().check_async(
                messages=[{"role": "user", "content": question}],
                rail_types=[RailType.INPUT],
            )

            status = getattr(result.status, "value", result.status)
            passed = str(status).lower() == "passed"

            logfire.info(
                "security.nemo.input_check_completed",
                passed=passed,
                status=str(status),
                latency_ms=round(
                    (time.perf_counter() - started) * 1000,
                    2,
                ),
            )

            return passed

        except Exception as exc:
            logger.exception("NeMo input check failed")

            logfire.error(
                "security.nemo.input_check_failed",
                error_type=type(exc).__name__,
                latency_ms=round(
                    (time.perf_counter() - started) * 1000,
                    2,
                ),
            )

            return False
