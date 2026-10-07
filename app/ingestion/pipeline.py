"""
Ingestion pipeline runner
=========================

Single entry point that runs the whole ingestion process in order:

    crawl  ->  parse  ->  chunk  ->  embed

and records every run in Logfire.

What you get in Logfire for each run
------------------------------------
    ingestion run <run_id>                    (root span: total time)
    ├── crawl      pages saved / empty / failed (each bad URL is a warning)
    ├── parse      pages in, sections out
    ├── chunk      sections in, chunks out, average chunk size, chunks with code
    └── embed      model used, fallback used or not
        ├── health check <model>              (red span if the model is unhealthy)
        ├── retry warnings                    (attempt number, sleep, error)
        ├── warning: model <x> failed ...     (when the pipeline switches model)
        └── embed with <model>                (start time and duration)

Only counts, names and timings are recorded, never page or chunk text.

Settings
--------
Logfire is configured through ``configure_logfire()`` (in
``embedding/models.py``), which reads ``settings.logfire_token`` from your
``app/config.py``. Without a token the pipeline still runs and nothing is sent.
Qdrant settings are read inside ``embedding/embedder.py``.

Commands (run from the project root)
------------------------------------
    uv run python -m app.ingestion.run_pipeline                 # all stages
    uv run python -m app.ingestion.run_pipeline --from parse    # reuse crawled pages
    uv run python -m app.ingestion.run_pipeline --from chunk    # reuse parsed sections
    uv run python -m app.ingestion.run_pipeline --from embed    # reuse chunks (re-embed only)

Exit code: 0 when every stage succeeded, 1 when a stage failed.
"""

import argparse
import asyncio
import json
import logging
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import logfire

from app.ingestion.crawler1 import web_crawler as crawler
from app.ingestion.chunking3 import get_chunk as chunking
from app.ingestion.data_parsing2 import parsing as parse_docs
from app.ingestion.embedding4 import embedder
from app.ingestion.embedding4.models_config import MODELS
from app.ingestion.embedding4.models_config import configure_logfire




log = logging.getLogger("pipeline")

# The stages, in the order they run
STAGES = ["crawl", "parse", "chunk", "embed"]


# ---------------------------------------------------------------------------
# Result record
# ---------------------------------------------------------------------------

@dataclass
class StageResult:
    """
    Outcome of one stage, used for the summary table at the end.

    Attributes:
        name: Stage name (``crawl``, ``parse``, ``chunk`` or ``embed``).
        status: ``"ok"``, ``"failed"`` or ``"skipped"``.
        seconds: How long the stage took (0 when skipped).
        details: Counts and names recorded for the stage (never text content).
    """

    name: str
    status: str
    seconds: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def count_lines(path: Path) -> int:
    """
    Count the lines (records) of a JSONL file.

    Args:
        path: Path to a ``.jsonl`` file.

    Returns:
        The number of lines in the file.
    """
    with open(path, encoding="utf-8") as f:
        return sum(1 for _ in f)


def require_file(path: Path, needed_by: str) -> None:
    """
    Fail early with a clear message if an input file is missing.

    Used when starting from a later stage (``--from parse`` and so on).

    Args:
        path: The file the stage needs.
        needed_by: Name of the stage that needs it.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"'{needed_by}' needs {path}, but it does not exist. "
            f"Run the earlier stages first (leave out --from)."
        )


def chunk_stats(path: Path) -> dict[str, Any]:
    """
    Summarize the chunk file: how many chunks, how big, how many contain code.

    Args:
        path: Path to ``chunks.jsonl``.

    Returns:
        ``{"chunks": int, "avg_chars": int, "chunks_with_code": int}``.
    """
    total = chars = with_code = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            chunk = json.loads(line)
            total += 1
            chars += chunk.get("char_count", 0)
            with_code += bool(chunk.get("has_code"))
    return {
        "chunks": total,
        "avg_chars": chars // total if total else 0,
        "chunks_with_code": with_code,
    }


# ---------------------------------------------------------------------------
# The four stages (each returns a dict of counts for Logfire and the summary)
# ---------------------------------------------------------------------------

def stage_crawl() -> dict[str, Any]:
    """
    Crawl the FastAPI docs and save the pages to disk.

    The crawler itself records every failed or empty URL as a Logfire warning.

    Returns:
        The crawler's counts: urls_in_sitemap, saved, empty, failed.

    Raises:
        RuntimeError: If no page could be saved (the later stages would have no input).
    """
    stats = asyncio.run(crawler.crawl_fastapi_docs())
    if stats["saved"] == 0:
        raise RuntimeError("The crawler saved 0 pages. Check your network and the sitemap URL.")
    return stats


def stage_parse() -> dict[str, Any]:
    """
    Clean the crawled pages and split them into structured sections.

    Returns:
        ``{"pages_in": int, "sections": int}``.

    Raises:
        RuntimeError: If parsing produced no sections.
    """
    require_file(parse_docs.INPUT_PATH, "parse")
    pages_in = count_lines(parse_docs.INPUT_PATH)

    parse_docs.main()

    sections = count_lines(parse_docs.OUTPUT_PATH)
    if sections == 0:
        raise RuntimeError("Parsing produced 0 sections. Inspect pages.jsonl.")
    return {"pages_in": pages_in, "sections": sections}


def stage_chunk() -> dict[str, Any]:
    """
    Split the sections into embedding-ready chunks.

    Returns:
        ``{"sections_in", "chunks", "avg_chars", "chunks_with_code"}``.

    Raises:
        RuntimeError: If chunking produced no chunks.
    """
    require_file(chunking.INPUT_PATH, "chunk")
    sections_in = count_lines(chunking.INPUT_PATH)

    chunking.main()

    stats = chunk_stats(chunking.OUTPUT_PATH)
    if stats["chunks"] == 0:
        raise RuntimeError("Chunking produced 0 chunks. Inspect parsed_sections.jsonl.")
    return {"sections_in": sections_in, **stats}


def stage_embed() -> dict[str, Any]:
    """
    Embed the chunks and store them in Qdrant, with retries and model failover.

    The retries, health checks and model switches are traced inside
    ``embedding/models.py`` and ``embedding/embedder.py`` and appear nested
    under this stage's span.

    Returns:
        ``{"model": str, "used_fallback": bool, "chunks": int}``.
    """
    require_file(embedder.CHUNKS_PATH, "embed")

    used_model = embedder.index_chunks()
    used_fallback = used_model != MODELS[0]["name"]

    if used_fallback:
        # Stands out in the Logfire live view: the primary model did not work
        logfire.warn(
            "primary model {primary} did not complete; the run used fallback {model}",
            primary=MODELS[0]["name"], model=used_model,
        )
    return {
        "model": used_model,
        "used_fallback": used_fallback,
        "chunks": count_lines(embedder.CHUNKS_PATH),
    }


# ---------------------------------------------------------------------------
# Running the stages
# ---------------------------------------------------------------------------

def run_stage(name: str, action: Callable[[], dict[str, Any]], results: list[StageResult]) -> None:
    """
    Run one stage inside its own Logfire span and record the outcome.

    On success the stage's counts are logged and stored. On failure the
    exception is recorded on the span (Logfire does this automatically), the
    stage is stored as ``failed`` and the exception is re-raised so the
    pipeline stops.

    Args:
        name: Stage name.
        action: The stage function; returns a dict of counts.
        results: List that collects one ``StageResult`` per stage.

    Raises:
        Exception: Whatever the stage raised.
    """
    log.info(">>> Stage '%s' started", name)
    started = time.perf_counter()

    try:
        with logfire.span("{stage}", stage=name):
            details = action()
            logfire.info("{stage} finished", stage=name, **details)
    except Exception as exc:
        results.append(StageResult(name, "failed", time.perf_counter() - started, {"error": str(exc)}))
        log.error("<<< Stage '%s' FAILED: %s", name, exc)
        raise

    elapsed = time.perf_counter() - started
    results.append(StageResult(name, "ok", elapsed, details))
    log.info("<<< Stage '%s' finished in %.1fs: %s", name, elapsed, details)


def run(run_id: str, from_stage: str, results: list[StageResult]) -> None:
    """
    Run the pipeline from ``from_stage`` to the end, inside one root span.

    Stages before ``from_stage`` are recorded as skipped.

    Args:
        run_id: Short id of this run (search for it in Logfire).
        from_stage: First stage to run (one of ``STAGES``).
        results: List that collects one ``StageResult`` per stage.

    Raises:
        Exception: The error of the first stage that failed.
    """
    actions: dict[str, Callable[[], dict[str, Any]]] = {
        "crawl": stage_crawl,
        "parse": stage_parse,
        "chunk": stage_chunk,
        "embed": stage_embed,
    }
    first = STAGES.index(from_stage)
    started = time.perf_counter()

    with logfire.span("ingestion run {run_id}", run_id=run_id, from_stage=from_stage):
        for index, name in enumerate(STAGES):
            if index < first:
                results.append(StageResult(name, "skipped"))
                logfire.info("{stage} skipped (starting from {from_stage})", stage=name, from_stage=from_stage)
                continue
            run_stage(name, actions[name], results)

        logfire.info(
            "run {run_id} finished in {seconds}s",
            run_id=run_id, seconds=round(time.perf_counter() - started, 1),
        )


# ---------------------------------------------------------------------------
# Summary and entry point
# ---------------------------------------------------------------------------

def print_summary(results: list[StageResult], run_id: str) -> None:
    """
    Print a table with the status, duration and counts of every stage.

    Printed even when a stage failed, so you see how far the run got.

    Args:
        results: Stage results collected during the run.
        run_id: Id of the run (same one you search for in Logfire).
    """
    print(f"\n=== Pipeline summary (run {run_id}) ===")
    for r in results:
        details = ", ".join(f"{k}={v}" for k, v in r.details.items())
        print(f"{r.name:<6} {r.status:<8} {r.seconds:6.1f}s  {details}")
    print(f"Total: {sum(r.seconds for r in results):.1f}s")


def main() -> None:
    """
    Parse the command line, configure Logfire, run the pipeline and report.

    Always flushes Logfire before exiting so the last spans are not lost.
    Exits with code 1 if a stage failed.
    """
    parser = argparse.ArgumentParser(description="Run the FastAPI docs ingestion pipeline.")
    parser.add_argument(
        "--from",
        dest="from_stage",
        choices=STAGES,
        default="crawl",
        help="first stage to run; earlier stages are skipped and their output files are reused",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    configure_logfire("fastapi-rag-ingestion")

    run_id = uuid.uuid4().hex[:8]
    results: list[StageResult] = []
    exit_code = 0

    try:
        run(run_id, args.from_stage, results)
    except Exception:
        exit_code = 1  # the span in Logfire already holds the exception details
        log.exception("Pipeline stopped because a stage failed")
    finally:
        print_summary(results, run_id)
        logfire.shutdown()  # make sure everything is sent before the script exits

    sys.exit(exit_code)


if __name__ == "__main__":
    main()