import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from app.generation.rag_pipeline import RAGPipeline, build_rag_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing RAG pipeline...")
    app.state.rag_pipeline = build_rag_pipeline()
    logger.info("RAG pipeline initialized.")
    yield
    logger.info("RAG API shutting down.")


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
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
async def ask(
    payload: AskRequest,
    request: Request,
) -> AskResponse:
    question = payload.question.strip()
    if not question:
        raise HTTPException(
            status_code=422,
            detail="Question cannot be empty or whitespace.",
        )

    pipeline: RAGPipeline = request.app.state.rag_pipeline

    try:
        result = await pipeline.answer(question)
    except ValueError as exc:
        logger.warning("RAG request rejected: %s", exc)
        raise HTTPException(
            status_code=422,
            detail="The question could not be processed.",
        ) from exc
    except Exception as exc:
        logger.exception("RAG request failed")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing the question.",
        ) from exc

    return AskResponse(
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
