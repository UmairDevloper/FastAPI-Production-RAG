"""Asynchronous LLM client for the LiteLLM proxy."""

import os
import time

import logfire
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

_client: AsyncOpenAI | None = None


def get_llm_client() -> AsyncOpenAI:
    """Return the lazily initialized LiteLLM client."""
    global _client

    if _client is None:
        with logfire.span("llm_client.initialize"):
            base_url = os.getenv(
                "LITELLM_BASE_URL",
                "http://localhost:4000/v1",
            )

            _client = AsyncOpenAI(
                base_url=base_url,
                api_key=os.environ["LITELLM_MASTER_KEY"],
                timeout=120,
                max_retries=0,
            )

            logfire.info(
                "LLM client initialized",
                base_url=base_url,
                timeout_seconds=180,
                max_retries=0,
            )

    return _client


async def complete(
    *,
    model: str,
    system: str,
    user: str,
    temperature: float = 0,
    max_tokens: int | None = None,
) -> str:
    """Call the configured LLM and return its non-empty text response."""
    started = time.perf_counter()

    with logfire.span(
        "llm.completion",
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        system_chars=len(system),
        user_chars=len(user),
    ):
        response = await get_llm_client().chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        elapsed_ms = (time.perf_counter() - started) * 1000
        choice = response.choices[0]
        content = choice.message.content

        usage = response.usage
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)

        logfire.info(
            "LLM request completed",
            model=model,
            elapsed_ms=round(elapsed_ms, 2),
            response_id=response.id,
            finish_reason=choice.finish_reason,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        if not content or not content.strip():
            logfire.error(
                "LLM returned empty content",
                model=model,
                finish_reason=choice.finish_reason,
                response_id=response.id,
                elapsed_ms=round(elapsed_ms, 2),
            )
            raise RuntimeError(
                f"LLM returned empty content for model={model!r}; "
                f"finish_reason={choice.finish_reason!r}"
            )

        return content.strip()
