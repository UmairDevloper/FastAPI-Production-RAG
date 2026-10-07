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

def ensure_collection(
    client: QdrantClient,
    active: ActiveModel,
) -> str:
    """
    Create the model's Qdrant collection if it does not already exist.

    IMPORTANT:
        We do NOT delete an existing collection.

    This makes indexing resumable. If the process stops after 1,000/2,200
    chunks, restarting the command will keep those 1,000 chunks and continue
    with the remaining chunks.

    Returns:
        The collection name.
    """
    name = collection_name(active.name)

    if client.collection_exists(name):
        log.info(
            "Collection '%s' already exists. Resuming indexing.",
            name,
        )
        return name

    log.info(
        "Creating new collection '%s' with model '%s' (dim=%d)",
        name,
        active.name,
        active.dim,
    )

    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(
            size=active.dim,
            distance=Distance.COSINE,
        ),
    )

    # Index for fast filtering by category.
    client.create_payload_index(
        name,
        field_name="category",
        field_schema=PayloadSchemaType.KEYWORD,
    )

    return name


def get_existing_point_ids(
    client: QdrantClient,
    collection_name_: str,
    chunks: list[dict],
) -> set[str]:
    """
    Find which deterministic point IDs already exist in Qdrant.

    Because point_id() is deterministic, the same chunk always gets
    the same Qdrant ID.

    This is what makes the indexing process resumable.

    Args:
        client:
            Qdrant client.
        collection_name_:
            Existing Qdrant collection.
        chunks:
            Chunks we are about to process.

    Returns:
        Set of point IDs that already exist in Qdrant.
    """
    ids = [
        point_id(chunk["chunk_id"])
        for chunk in chunks
    ]

    if not ids:
        return set()

    existing_ids: set[str] = set()

    # Retrieve in smaller groups so we don't create a huge request.
    retrieve_batch_size = 256

    for start in range(0, len(ids), retrieve_batch_size):
        batch_ids = ids[start:start + retrieve_batch_size]

        points = with_retries(
            lambda batch_ids=batch_ids: client.retrieve(
                collection_name=collection_name_,
                ids=batch_ids,
                with_payload=False,
                with_vectors=False,
            ),
            "Checking existing Qdrant points",
        )

        existing_ids.update(
            str(point.id)
            for point in points
        )

    return existing_ids


def build_collection(
    client: QdrantClient,
    active: ActiveModel,
    chunks: list[dict],
) -> None:
    """
    Resumably embed chunks with one model and store them in Qdrant.

    Pipeline:

        chunks
           ↓
        stable point IDs
           ↓
        check Qdrant
           ↓
        already exists? ── YES ──> skip
           │
           NO
           ↓
        embed batch
           ↓
        upsert batch
           ↓
        next batch

    Important:
        The collection is NOT deleted when this function starts.

    If the process stops at 1,280 / 2,200 chunks, restarting will skip
    the 1,280 existing points and continue with the remaining chunks.

    Raises:
        ModelFailure:
            If the embedding model fails after retries.

        Exception:
            If Qdrant fails after retries.
    """

    name = ensure_collection(client, active)

    total = len(chunks)

    # ---------------------------------------------------------------
    # STEP 1: Find already-indexed chunks
    # ---------------------------------------------------------------

    log.info(
        "[%s] Checking which of %d chunks are already indexed...",
        active.name,
        total,
    )

    existing_ids = get_existing_point_ids(
        client,
        name,
        chunks,
    )

    log.info(
        "[%s] Found %d/%d chunks already indexed.",
        active.name,
        len(existing_ids),
        total,
    )

    # ---------------------------------------------------------------
    # STEP 2: Remove already-indexed chunks from the work list
    # ---------------------------------------------------------------

    pending_chunks = [
        chunk
        for chunk in chunks
        if point_id(chunk["chunk_id"]) not in existing_ids
    ]

    pending_total = len(pending_chunks)

    if pending_total == 0:
        log.info(
            "[%s] All %d chunks are already indexed. Nothing to do.",
            active.name,
            total,
        )
        return

    log.info(
        "[%s] %d chunks remaining.",
        active.name,
        pending_total,
    )

    # ---------------------------------------------------------------
    # STEP 3: Embed + upload only missing chunks
    # ---------------------------------------------------------------

    for start in range(0, pending_total, UPSERT_BATCH):

        batch = pending_chunks[
            start:start + UPSERT_BATCH
        ]

        end = start + len(batch)

        log.info(
            "[%s] Processing pending chunks %d-%d/%d...",
            active.name,
            start + 1,
            end,
            pending_total,
        )

        # -----------------------------------------------------------
        # 3A. Embedding
        # -----------------------------------------------------------

        try:
            vectors = with_retries(
                lambda: active.embed(
                    [
                        c["contextual_text"]
                        for c in batch
                    ]
                ),
                (
                    f"Embedding batch "
                    f"{start}-{end} with '{active.name}'"
                ),
            )

        except Exception as exc:
            # This is considered an embedding-model failure.
            raise ModelFailure(
                f"'{active.name}' failed while embedding: {exc}"
            ) from exc

        # -----------------------------------------------------------
        # 3B. Validate embedding result
        # -----------------------------------------------------------

        if len(vectors) != len(batch):
            raise ModelFailure(
                f"Embedding model '{active.name}' returned "
                f"{len(vectors)} vectors for {len(batch)} chunks."
            )

        for i, vector in enumerate(vectors):
            if len(vector) != active.dim:
                raise ModelFailure(
                    f"Model '{active.name}' returned vector dimension "
                    f"{len(vector)} for chunk "
                    f"'{batch[i]['chunk_id']}', expected {active.dim}."
                )

        # -----------------------------------------------------------
        # 3C. Build Qdrant points
        # -----------------------------------------------------------

        points = [
            PointStruct(
                id=point_id(c["chunk_id"]),
                vector=v,
                payload={
                    k: val
                    for k, val in c.items()
                    if k != "contextual_text"
                },
            )
            for c, v in zip(batch, vectors)
        ]

        # -----------------------------------------------------------
        # 3D. Upload to Qdrant
        # -----------------------------------------------------------

        # If the network dies here:
        #
        # - Qdrant may have received some/all points.
        # - The client may not receive the response.
        # - The process can stop.
        #
        # On the next run, get_existing_point_ids() will discover
        # whatever Qdrant successfully stored.
        #
        # Therefore we don't need to re-embed those chunks.

        with_retries(
            lambda: client.upsert(
                collection_name=name,
                points=points,
            ),
            "Qdrant upsert",
        )

        log.info(
            "[%s] Stored %d/%d remaining chunks.",
            active.name,
            min(end, pending_total),
            pending_total,
        )

    log.info(
        "[%s] Indexing complete. %d total chunks available.",
        active.name,
        total,
    )


def index_chunks() -> str:
    """
    Run the embedding stage with automatic model failover.

    Resumability:
        If the process stops because of a network/Qdrant error,
        the existing collection is preserved.

        Running the command again will:
            1. Find the existing collection.
            2. Check which point IDs already exist.
            3. Skip completed chunks.
            4. Embed only missing chunks.

    Model failover:
        If the embedding model itself fails, its partial collection is
        deleted because vectors from different embedding models must
        never be mixed.

    Returns:
        Name of the model that completed the indexing.
    """

    client = get_client()
    chunks = load_chunks()

    log.info(
        "Loaded %d chunks. Models in order: %s",
        len(chunks),
        [m["name"] for m in MODELS],
    )

    failed: set[str] = set()

    while True:

        active = select_model(
            exclude=failed
        )

        try:

            with logfire.span(
                "embed with {model}",
                model=active.name,
                role=active.role,
                chunk_count=len(chunks),
            ):

                build_collection(
                    client,
                    active,
                    chunks,
                )

            log.info(
                "Done: all chunks embedded with '%s'.",
                active.name,
            )

            return active.name

        except ModelFailure as exc:

            # -------------------------------------------------------
            # MODEL FAILURE
            # -------------------------------------------------------
            #
            # The model itself is broken.
            #
            # We cannot continue using the partial collection because
            # switching models would create incompatible vectors.
            #

            failed.add(active.name)

            log.error(
                "%s. Switching to the next model.",
                exc,
            )

            logfire.warn(
                "model {failed_model} failed while embedding, "
                "switching to the next model",
                failed_model=active.name,
                reason=str(exc),
            )

            partial = collection_name(
                active.name
            )

            if client.collection_exists(partial):

                log.warning(
                    "Deleting incomplete collection '%s' "
                    "because the embedding model failed.",
                    partial,
                )

                client.delete_collection(
                    partial
                )

        finally:

            # Always release the model from memory.
            unload_model(
                active.cfg
            )

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