import os
import time

from dotenv import load_dotenv
from fastapi import logger
from openai import AsyncOpenAI

load_dotenv()  # Load environment variables from .env file
"""
LLM client for handling asynchronous requests to the LiteLLM proxy.
"""

_client: AsyncOpenAI | None = None


def get_llm_client() -> AsyncOpenAI:
    global _client

    if _client is None:
        _client = AsyncOpenAI(
            base_url=os.getenv(
                "LITELLM_BASE_URL",
                "http://localhost:4000/v1",
            ),
            api_key=os.environ["LITELLM_MASTER_KEY"],
            timeout=180,
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
    started = time.perf_counter()

    response = await get_llm_client().chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    print(
        f"LLM HTTP request elapsed: "
        f"{time.perf_counter() - started:.2f}s"
    )
    print("LLM usage:", response.usage)

    content = response.choices[0].message.content

    if not content or not content.strip():
        logger.error(
            "LLM returned empty content | model=%s | finish_reason=%s | response_id=%s",
            model,
            response.choices[0].finish_reason,
            response.id,
        )
        raise RuntimeError(
            f"LLM returned empty content for model={model!r}; "
            f"finish_reason={response.choices[0].finish_reason!r}"
        )

    return content.strip()
