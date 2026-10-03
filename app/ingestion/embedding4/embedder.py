"""
Embedder: embed the chunks with the selected model and store them in Qdrant
===========================================================================

``models.py`` decides WHICH model works. This file receives that model and
does the work:

    select_model()  ->  ActiveModel  ->  build_collection()  ->  Qdrant

Failover
--------
``index_chunks()`` asks ``models.py`` for a healthy model, then embeds ALL
chunks with it. If the model keeps failing after its retries (at any batch),
the partial collection is deleted, the model is marked as failed, and
``select_model()`` is asked again, which now skips it. The next model starts
again from the first chunk. A collection is NEVER filled by two different
models, because vectors from different models are not comparable.

Qdrant errors are retried the same way but do NOT switch models; they are
raised, because another embedding model cannot fix a database problem.

Settings
--------
Read from the ``settings`` object in ``app/config.py`` (loaded from ``.env``):
    settings.qdrant_url               Qdrant cluster URL
    settings.qdrant_api_key           Qdrant API key
    settings.qdrant_collection_name   prefix of the collection names
    settings.logfire_token            used by configure_logfire() in models.py

Collections
-----------
One per model: ``<qdrant_collection_name>__<model name>``, for example
``fastapi_docs__qwen3``. At search time the first model (in priority order)
that has a collection and works is used, and the question is embedded with
that same model.

Commands
--------
    uv run python -m app.ingestion.embedding.embedder index
    uv run python -m app.ingestion.embedding.embedder search "how do I declare a request body"
"""

import json
import logging
import sys
import uuid
from pathlib import Path

import logfire
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from app.config import settings
from app.ingestion.embedding4.models_config import (
    MODELS,
    ActiveModel,
    ModelFailure,
    configure_logfire,
    load_model,
    secret_value,
    select_model,
    unload_model,
    with_retries,
)

log = logging.getLogger("embedding.embedder")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# <project root>/data/fastapi_docs  (this file lives in app/ingestion/embedding/)
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "fastapi_docs"
CHUNKS_PATH = DATA_DIR / "chunks.jsonl"

UPSERT_BATCH = 64   # chunks embedded and sent to Qdrant per step


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_client() -> QdrantClient:
    """
    Create a Qdrant client from ``settings``.

    Returns:
        A connected ``QdrantClient``.

    Raises:
        RuntimeError: If the Qdrant URL or API key is missing in the settings.
    """
    url = settings.QDRANT_ENDPOINT
    api_key = secret_value(settings.QDRANT_API_KEY)
    if not url or not api_key:
        raise RuntimeError("Qdrant URL / API key are missing. Check your .env file.")
    return QdrantClient(url=str(url), api_key=api_key, timeout=60)


def collection_name(model_name: str) -> str:
    """
    Build the collection name of a model, e.g. ``fastapi_docs__qwen3``.

    Args:
        model_name: Short model name from ``MODELS``.

    Returns:
        ``<settings.QDRANT_COLLECTION_NAME>__<model_name>``.
    """
    return f"{settings.QDRANT_COLLECTION_NAME}__{model_name}"


def point_id(chunk_id: str) -> str:
    """
    Turn a chunk id into a UUID, because Qdrant ids must be integers or UUIDs.

    The conversion is deterministic, so re-running the pipeline overwrites the
    same points instead of creating duplicates.

    Args:
        chunk_id: Chunk id such as ``"a1b2c3d4e5f6-0003"``.

    Returns:
        A UUID string.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def load_chunks(path: Path = CHUNKS_PATH) -> list[dict]:
    """
    Read all chunks from the chunking step.

    Args:
        path: Path to ``chunks.jsonl``.

    Returns:
        A list of chunk dicts.

    Raises:
        FileNotFoundError: If the chunking step has not been run yet.
    """
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run the chunking step first.")
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

def build_collection(client: QdrantClient, active: ActiveModel, chunks: list[dict]) -> None:
    """
    Embed ALL chunks with one model and store them in that model's collection.

    Steps:
        1. Recreate the model's collection (vector size comes from the health check).
        2. For each batch: embed it (with retries), then upsert it (with retries).

    The text embedded is ``contextual_text`` (chunk + heading breadcrumb). The
    payload keeps ``text`` and all metadata for display and filtering.

    Args:
        client: Qdrant client.
        active: The healthy model received from ``models.py``.
        chunks: All chunks to embed.

    Raises:
        ModelFailure: If the embedding model fails during any batch.
        Exception: Qdrant errors after all retries (they do not switch models).
    """
    name = collection_name(active.name)
    log.info("Building collection '%s' with model '%s'", name, active.name)

    if client.collection_exists(name):
        client.delete_collection(name)
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=active.dim, distance=Distance.COSINE),
    )
    # Index for fast filtering by category (tutorial, advanced, reference, ...)
    client.create_payload_index(name, field_name="category", field_schema=PayloadSchemaType.KEYWORD)

    total = len(chunks)
    for start in range(0, total, UPSERT_BATCH):
        batch = chunks[start:start + UPSERT_BATCH]

        # 1) Embedding: retried; if it still fails, the MODEL is the problem
        try:
            vectors = with_retries(
                lambda: active.embed([c["contextual_text"] for c in batch]),
                f"Embedding batch {start}-{start + len(batch)} with '{active.name}'",
            )
        except Exception as exc:
            raise ModelFailure(f"'{active.name}' failed while embedding: {exc}") from exc

        points = [
            PointStruct(
                id=point_id(c["chunk_id"]),
                vector=v,
                payload={k: val for k, val in c.items() if k != "contextual_text"},
            )
            for c, v in zip(batch, vectors)
        ]

        # 2) Qdrant: retried; if it still fails, the error is raised (no model switch)
        with_retries(lambda: client.upsert(collection_name=name, points=points), "Qdrant upsert")
        log.info("[%s] %d/%d chunks stored", active.name, min(start + UPSERT_BATCH, total), total)


def index_chunks() -> str:
    """
    Run the embedding stage with automatic failover between models.

    Loop: ask ``select_model`` for a healthy model (skipping the ones that
    already failed), embed everything with it, and on ``ModelFailure`` drop the
    partial collection and try the next model. Each attempt is one Logfire
    span that records the model, its role, the start time and the duration.

    Returns:
        The name of the model that completed the run.

    Raises:
        RuntimeError: If every model failed.
    """
    client = get_client()
    chunks = load_chunks()
    log.info("Loaded %d chunks. Models in order: %s", len(chunks), [m["name"] for m in MODELS])

    failed: set[str] = set()
    while True:
        active = select_model(exclude=failed)   # raises RuntimeError when none is left
        try:
            with logfire.span(
                "embed with {model}", model=active.name, role=active.role, chunk_count=len(chunks)
            ):
                build_collection(client, active, chunks)
            log.info("Done: all chunks embedded with '%s'.", active.name)
            return active.name
        except ModelFailure as exc:
            failed.add(active.name)
            log.error("%s. Switching to the next model.", exc)
            logfire.warn(
                "model {failed_model} failed while embedding, switching to the next model",
                failed_model=active.name, reason=str(exc),
            )
            # Remove the partial collection so only complete ones exist
            partial = collection_name(active.name)
            if client.collection_exists(partial):
                client.delete_collection(partial)
        finally:
            unload_model(active.cfg)   # free memory before the next model loads


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search(query: str, limit: int = 5, category: str | None = None):
    """
    Search the docs with the first model that has a collection and works.

    The question must be embedded with the SAME model that built the
    collection, so models are tried in priority order among the existing
    collections. If embedding the question fails (after retries), the next
    available model is used. The model that served the search is logged.

    Args:
        query: The user's question.
        limit: Number of results.
        category: Optional filter, e.g. ``"tutorial"`` or ``"advanced"``.

    Returns:
        A list of Qdrant scored points (``.score`` and ``.payload``).

    Raises:
        RuntimeError: If no collection exists or no model can embed the query.
    """
    client = get_client()
    query_filter = (
        Filter(must=[FieldCondition(key="category", match=MatchValue(value=category))])
        if category
        else None
    )

    for cfg in MODELS:
        name = collection_name(cfg["name"])
        if not client.collection_exists(name):
            continue  # this model never completed an indexing run

        try:
            vector = with_retries(
                lambda: ActiveModel(cfg=cfg, model=load_model(cfg)).embed([query], is_query=True)[0],
                f"Embedding the query with '{cfg['name']}'",
            )
        except Exception as exc:
            log.error("Model '%s' failed for the query (%s). Trying the next model.", cfg["name"], exc)
            logfire.warn("model {model} failed for a search query", model=cfg["name"], reason=str(exc))
            continue

        # Qdrant errors are raised on purpose: another model cannot fix them
        points = client.query_points(
            collection_name=name,
            query=vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        ).points
        logfire.info("search served by model {model}", model=cfg["name"], results=len(points))
        return points

    raise RuntimeError("No usable collection or model found. Run the 'index' command first.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run ``index`` or ``search "<question>"`` from the command line."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    configure_logfire()

    args = sys.argv[1:]
    if args[:1] == ["index"]:
        print(f"\nIndexed with model: {index_chunks()}")
    elif args[:1] == ["search"] and len(args) > 1:
        for hit in search(" ".join(args[1:])):
            p = hit.payload
            print(f"\n{hit.score:.3f}  {' > '.join(p['heading_path']) or p['page_title']}")
            print(f"       {p['section_url']}")
            print(f"       {p['text'][:200].replace(chr(10), ' ')}...")
    else:
        print('Usage:\n  python -m app.ingestion.embedding.embedder index\n'
            '  python -m app.ingestion.embedding.embedder search "your question"')

    logfire.shutdown()


if __name__ == "__main__":
    main()