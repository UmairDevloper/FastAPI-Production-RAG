from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Annotated

import logfire
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from app.generation.rag_pipeline import RAGPipeline, build_rag_pipeline
from app.ingestion.embedding4.models_config import configure_logfire

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logfire()

    logger.info("Initializing RAG pipeline...")
    with logfire.span("api.startup.initialize_rag_pipeline"):
        started = time.perf_counter()
        try:
            app.state.rag_pipeline = build_rag_pipeline()
            logfire.info(
                "api.rag_pipeline.initialized",
                latency_ms=round(
                    (time.perf_counter() - started) * 1000,
                    2,
                ),
            )
            logger.info("RAG pipeline initialized.")
        except Exception as exc:
            logfire.error(
                "api.rag_pipeline.initialization_failed",
                error_type=type(exc).__name__,
            )
            logger.exception("RAG pipeline initialization failed")
            raise

    try:
        yield
    finally:
        logger.info("RAG API shutting down.")
        logfire.info("api.shutdown")


app = FastAPI(
    title="FastAPI Documentation RAG",
    description="Question-answering API grounded in FastAPI documentation.",
    version="1.0.0",
    lifespan=lifespan,
)


class AskRequest(BaseModel):
    question: Annotated[str, Field(min_length=1, max_length=2000)]


class CitationResponse(BaseModel):
    evidence_id: str
    source_url: str | None
    page_title: str | None
    heading_path: str | None


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[CitationResponse]
    insufficient_evidence: bool
    latency_ms: dict[str, float]


@app.get("/health")
async def health():
    with logfire.span("api.health_check"):
        return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
async def ask(
    payload: AskRequest,
    request: Request,
) -> AskResponse:
    request_started = time.perf_counter()
    question = payload.question.strip()

    with logfire.span(
        "api.ask",
        question_chars=len(question),
    ) as span:
        if not question:
            logfire.warning(
                "api.ask.rejected",
                reason="empty_or_whitespace_question",
            )
            raise HTTPException(
                status_code=422,
                detail="Question cannot be empty or whitespace.",
            )

        pipeline: RAGPipeline = request.app.state.rag_pipeline

        try:
            result = await pipeline.answer(question)

        except ValueError as exc:
            logger.warning("RAG request rejected: %s", exc)
            logfire.warning(
                "api.ask.rejected",
                reason="value_error",
                error_type=type(exc).__name__,
                latency_ms=round(
                    (time.perf_counter() - request_started) * 1000,
                    2,
                ),
            )
            raise HTTPException(
                status_code=422,
                detail="The question could not be processed.",
            ) from exc

        except Exception as exc:
            logger.exception("RAG request failed")
            logfire.error(
                "api.ask.failed",
                error_type=type(exc).__name__,
                latency_ms=round(
                    (time.perf_counter() - request_started) * 1000,
                    2,
                ),
            )
            raise HTTPException(
                status_code=500,
                detail="An error occurred while processing the question.",
            ) from exc

        response = AskResponse(
            question=result.question,
            answer=result.answer,
            citations=[
                CitationResponse(
                    evidence_id=citation.evidence_id,
                    source_url=citation.source_url,
                    page_title=citation.page_title,
                    heading_path=citation.heading_path,
                )
                for citation in result.citations
            ],
            insufficient_evidence=result.insufficient_evidence,
            latency_ms=result.latency_ms,
        )

        total_latency_ms = round(
            (time.perf_counter() - request_started) * 1000,
            2,
        )

        span.set_attribute("api.citations_count", len(response.citations))
        span.set_attribute(
            "api.insufficient_evidence",
            response.insufficient_evidence,
        )
        span.set_attribute("api.total_latency_ms", total_latency_ms)

        logfire.info(
            "api.ask.completed",
            citations_count=len(response.citations),
            insufficient_evidence=response.insufficient_evidence,
            total_latency_ms=total_latency_ms,
            pipeline_latency_stages=len(response.latency_ms),
        )

        return response
