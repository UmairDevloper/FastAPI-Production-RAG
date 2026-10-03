"""
Embedding models: configuration, loading, health check and selection
====================================================================

This file answers one question: WHICH embedding model do we use right now?

How it works
------------
1. ``MODELS`` lists the models in priority order (first = primary).
2. ``select_model()`` walks that list. For each model it runs a health check
   (load the model and embed a probe text). The check is retried up to
   ``RETRY_ATTEMPTS`` times, sleeping 2s and then 4s between attempts.
3. The first model that passes is returned as a ready-to-use ``ActiveModel``.
   ``embedder.py`` receives it and does the actual embedding.

Everything is recorded in Logfire: one span per health check (red if it
failed), one warning per retry, one warning per model that is given up on.

Settings
--------
Secrets and names come from the ``settings`` object in ``app/config.py``
(loaded from your ``.env`` file). This file reads ``settings.logfire_token``
and, for testing only, ``settings.simulate_failure``.

Test all models without touching Qdrant
---------------------------------------
    uv run python -m app.ingestion.embedding.models
"""

import gc
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

import logfire
from sentence_transformers import SentenceTransformer

from app.config import settings

log = logging.getLogger("embedding.models")
T = TypeVar("T")

# ---------------------------------------------------------------------------
# Tuning constants (not secrets, so they live here and not in .env)
# ---------------------------------------------------------------------------

# Models in priority order: the first is the primary, the rest are fallbacks.
MODELS = [
    {"name": "qwen3", "hf_id": "Qwen/Qwen3-Embedding-0.6B"},
    {"name": "bge_m3", "hf_id": "BAAI/bge-m3"},
    # {"name": "gemma", "hf_id": "google/embeddinggemma-300m"},  # optional third model
]

# Retry policy: attempts per step, and the sleep between attempts
RETRY_ATTEMPTS = 3            # 1, 2 or 3 tries before giving up on a step
RETRY_BASE_DELAY_S = 2.0      # sleep after the first failure
RETRY_BACKOFF_FACTOR = 2.0    # each next sleep is this many times longer (2s, 4s, ...)

BATCH_SIZE = 16               # texts per model forward pass (lower it if RAM is tight)
MAX_SEQ_LEN = 1024            # tokens per text; chunks are ~450 tokens, code needs more

# Model names that must fail on purpose, to test the failover.
# Set SIMULATE_FAILURE=qwen3 in .env (and a matching optional field in Settings).
SIMULATE_FAILURE = {
    name.strip()
    for name in (getattr(settings, "SIMULATE_FAILURE", "") or "").split(",")
    if name.strip()
}

# Loaded models are cached so each model is loaded only once per process
_MODEL_CACHE: dict[str, SentenceTransformer] = {}


class ModelFailure(Exception):
    """
    Raised when an embedding model keeps failing after all retries.

    The failover loop in ``embedder.py`` catches ONLY this exception to switch
    to the next model. Other errors (for example Qdrant being unreachable)
    are not caught there, because another model cannot fix them.
    """


# ---------------------------------------------------------------------------
# Settings and observability helpers (shared with embedder.py)
# ---------------------------------------------------------------------------

def secret_value(value: Any) -> str | None:
    """
    Turn a settings value into a plain string.

    Pydantic stores secrets as ``SecretStr`` objects; this returns the real
    text for those and for ordinary strings alike.

    Args:
        value: A ``str``, a ``SecretStr`` or ``None``.

    Returns:
        The plain string, or ``None`` if the value is missing or empty.
    """
    if value is None:
        return None
    getter = getattr(value, "get_secret_value", None)
    text = getter() if getter else str(value)
    return text or None


def configure_logfire(service_name: str = "fastapi-rag-embedding") -> None:
    """
    Configure Logfire using the token from ``settings``.

    Data is sent only when ``settings.logfire_token`` is set. Without it the
    code still runs normally and nothing leaves your machine. Console output
    is switched off because the pipeline prints its own log lines.

    Args:
        service_name: Name shown in the Logfire dashboard for this process.
    """
    token = secret_value(settings.LOGFIRE_TOKEN)
    logfire.configure(
        token=token,
        send_to_logfire=bool(token),
        service_name=service_name,
        console=False,
    )


# ---------------------------------------------------------------------------
# Retry helper (also used by embedder.py)
# ---------------------------------------------------------------------------

def with_retries(action: Callable[[], T], label: str) -> T:
    """
    Run ``action`` and retry it with growing sleeps if it raises.

    Timeline with the defaults: try -> fail -> sleep 2s -> try -> fail ->
    sleep 4s -> try -> fail -> raise the last error. Every failed attempt is
    also sent to Logfire as a warning (label, attempt number, sleep, error).

    Args:
        action: A function with no arguments, for example a lambda.
        label: Text for the log lines, e.g. ``"Qdrant upsert"``.

    Returns:
        Whatever ``action`` returns on the first successful attempt.

    Raises:
        Exception: The last error, once all attempts have failed.
    """
    delay = RETRY_BASE_DELAY_S
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            return action()
        except Exception as exc:
            if attempt == RETRY_ATTEMPTS:
                raise
            log.warning(
                "%s failed (attempt %d/%d): %s. Retrying in %.0fs",
                label, attempt, RETRY_ATTEMPTS, exc, delay,
            )
            logfire.warn(
                "{label} failed (attempt {attempt}/{max_attempts}), retrying in {delay_s}s",
                label=label, attempt=attempt, max_attempts=RETRY_ATTEMPTS,
                delay_s=delay, error=str(exc),
            )
            time.sleep(delay)
            delay *= RETRY_BACKOFF_FACTOR
    raise RuntimeError("RETRY_ATTEMPTS must be at least 1")


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_model(cfg: dict) -> SentenceTransformer:
    """
    Load an embedding model (cached after the first successful load).

    Args:
        cfg: One entry of ``MODELS``.

    Returns:
        The loaded ``SentenceTransformer``.
    """
    if cfg["name"] not in _MODEL_CACHE:
        model = SentenceTransformer(cfg["hf_id"])
        model.max_seq_length = MAX_SEQ_LEN
        _MODEL_CACHE[cfg["name"]] = model
    return _MODEL_CACHE[cfg["name"]]


def unload_model(cfg: dict) -> None:
    """
    Remove a model from the cache and free its memory.

    Args:
        cfg: One entry of ``MODELS``.
    """
    _MODEL_CACHE.pop(cfg["name"], None)
    gc.collect()


@dataclass
class ActiveModel:
    """
    A model that passed its health check and is ready to embed text.

    This is the object ``embedder.py`` receives.

    Attributes:
        cfg: The model's entry in ``MODELS``.
        model: The loaded ``SentenceTransformer``.
        role: ``"primary"`` or ``"fallback"``.
        dim: Vector size, measured by the health check (0 until then).
    """

    cfg: dict
    model: SentenceTransformer
    role: str = "primary"
    dim: int = 0

    @property
    def name(self) -> str:
        """Short model name, e.g. ``"qwen3"``."""
        return self.cfg["name"]

    def embed(self, texts: list[str], is_query: bool = False) -> list[list[float]]:
        """
        Embed texts with the right prompt for this model.

        ``encode_query`` / ``encode_document`` (sentence-transformers >= 5)
        apply each model's own prompt, for example Qwen3's instruction for
        queries. Vectors are normalized, so cosine similarity works as a dot
        product.

        Args:
            texts: Texts to embed.
            is_query: True for search questions, False for documents (chunks).

        Returns:
            One vector (list of floats) per text.

        Raises:
            RuntimeError: If this model is listed in ``SIMULATE_FAILURE``.
        """
        if self.name in SIMULATE_FAILURE:
            raise RuntimeError(f"simulated failure of model '{self.name}'")

        encode = getattr(
            self.model, "encode_query" if is_query else "encode_document", self.model.encode
        )
        vectors = encode(
            texts, batch_size=BATCH_SIZE, normalize_embeddings=True, show_progress_bar=False
        )
        return vectors.tolist()


# ---------------------------------------------------------------------------
# Health check and selection
# ---------------------------------------------------------------------------

def health_check(cfg: dict) -> ActiveModel:
    """
    Test one model: load it and embed a probe text, with retries.

    The probe also measures the vector size, so no dimension has to be
    hard-coded in ``MODELS``.

    Args:
        cfg: One entry of ``MODELS``.

    Returns:
        A healthy ``ActiveModel``.

    Raises:
        ModelFailure: If the model cannot be loaded or used after all retries.
    """
    role = "primary" if cfg["name"] == MODELS[0]["name"] else "fallback"

    def probe() -> ActiveModel:
        active = ActiveModel(cfg=cfg, model=load_model(cfg), role=role)
        active.dim = len(active.embed(["health check"])[0])
        return active

    # The span is marked as failed automatically when ModelFailure is raised
    with logfire.span("health check {model}", model=cfg["name"], role=role):
        try:
            return with_retries(probe, f"Health check of '{cfg['name']}'")
        except Exception as exc:
            unload_model(cfg)
            raise ModelFailure(f"'{cfg['name']}' failed its health check: {exc}") from exc


def select_model(exclude: set[str] | None = None) -> ActiveModel:
    """
    Return the first healthy model, in priority order.

    Args:
        exclude: Model names to skip (models that already failed in this run).

    Returns:
        A healthy ``ActiveModel``, ready to be passed to ``embedder.py``.

    Raises:
        RuntimeError: If no model is left or every remaining model is unhealthy.
    """
    exclude = exclude or set()
    errors: list[str] = []

    for cfg in MODELS:
        if cfg["name"] in exclude:
            continue
        try:
            active = health_check(cfg)
        except ModelFailure as exc:
            log.error("%s. Trying the next model.", exc)
            logfire.warn("model {model} failed its health check", model=cfg["name"], reason=str(exc))
            errors.append(str(exc))
            continue

        log.info("Selected model '%s' (%s, %d dimensions)", active.name, active.role, active.dim)
        logfire.info(
            "selected model {model} ({role})", model=active.name, role=active.role, dim=active.dim
        )
        return active

    raise RuntimeError(
        f"No usable embedding model left (already failed: {sorted(exclude)}).\n  "
        + "\n  ".join(errors)
    )


# ---------------------------------------------------------------------------
# Test entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    configure_logfire()

    # Health-check EVERY model (not just the first healthy one) and print a table
    for model_cfg in MODELS:
        try:
            result = health_check(model_cfg)
            print(f"OK    {model_cfg['name']:<8} {model_cfg['hf_id']} ({result.dim} dimensions)")
        except ModelFailure as error:
            print(f"FAIL  {model_cfg['name']:<8} {error}")
        finally:
            unload_model(model_cfg)

    logfire.shutdown()