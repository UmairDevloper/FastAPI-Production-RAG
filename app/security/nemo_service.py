import logging
from pathlib import Path

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.rails.llm.options import RailType

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "nemo_guardrails"

_rails: LLMRails | None = None


def get_nemo_rails() -> LLMRails:
    """Initialize NeMo lazily."""
    global _rails

    if _rails is None:
        config = RailsConfig.from_path(str(CONFIG_PATH))
        _rails = LLMRails(config)

    return _rails


async def check_nemo_input(question: str) -> bool:
    """Allow input only when NeMo explicitly reports passed."""
    try:
        result = await get_nemo_rails().check_async(
            messages=[{"role": "user", "content": question}],
            rail_types=[RailType.INPUT],
        )
        status = getattr(result.status, "value", result.status)
        return str(status).lower() == "passed"
    except Exception:
        logger.exception("NeMo input check failed")
        return False
