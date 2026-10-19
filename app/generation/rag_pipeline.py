from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass

import logfire

from app.generation.answer_generation import (
    Citation,
    GeneratedAnswer,
    generate_answer,
)
from app.indexing.dense_indexing.reranker2 import CrossEncoderCompressor
from app.retrieval.context_assembly import (
    AssembledContext,
    assemble_context,
)
from app.retrieval.orchestrator import (
    RetrievalOrchestrator,
    build_retrieval_orchestrator,
)
from app.security.guardrails import validate_input, validate_output
from app.security.nemo_service import check_nemo_input

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RAGResponse:
    question: str
    answer: str
    citations: list[Citation]
    insufficient_evidence: bool
    retrieval: object
    context: AssembledContext
    latency_ms: dict[str, float]


class RAGPipeline:
    def __init__(
        self,
        orchestrator: RetrievalOrchestrator,
        reranker: CrossEncoderCompressor,
        *,
        generation_model: str = "rag-generation",
        max_context_tokens: int = 4000,
        max_context_documents: int = 8,
    ) -> None:
        self.orchestrator = orchestrator
        self.reranker = reranker
        self.generation_model = generation_model
        self.max_context_tokens = max_context_tokens
        self.max_context_documents = max_context_documents

        logfire.info(
            "RAG pipeline initialized",
            generation_model=generation_model,
            max_context_tokens=max_context_tokens,
            max_context_documents=max_context_documents,
        )

    async def answer(self, question: str) -> RAGResponse:
        request_id = uuid.uuid4().hex[:12]
        total_started = time.perf_counter()
        timings: dict[str, float] = {}
        current_stage = "input_validation"

        question = question.strip()

        # Do not record the question itself: it may contain sensitive data.
        with logfire.span(
            "rag.request",
            request_id=request_id,
            question_chars=len(question),
            generation_model=self.generation_model,
        ):
            logfire.info(
                "RAG request started",
                request_id=request_id,
                question_chars=len(question),
            )

            empty_context = AssembledContext(
                context="",
                evidence=[],
                estimated_tokens=0,
                omitted_documents=0,
            )

            def elapsed_ms(started: float) -> float:
                return round((time.perf_counter() - started) * 1000, 2)

            def record_timing(stage: str, started: float) -> None:
                timings[stage] = elapsed_ms(started)

            def finish_early(
                *,
                answer_text: str,
                retrieval: object,
                reason: str,
            ) -> RAGResponse:
                timings["total"] = elapsed_ms(total_started)

                logfire.info(
                    "RAG request completed early",
                    request_id=request_id,
                    reason=reason,
                    total_ms=timings["total"],
                    timings_ms=timings,
                )

                return RAGResponse(
                    question=question,
                    answer=answer_text,
                    citations=[],
                    insufficient_evidence=True,
                    retrieval=retrieval,
                    context=empty_context,
                    latency_ms=dict(timings),
                )

            try:
                if not question:
                    logfire.warn(
                        "Empty question rejected",
                        request_id=request_id,
                    )
                    raise ValueError("Question cannot be empty.")

                # 1. Input guardrails.
                current_stage = "input_security"
                started = time.perf_counter()

                with logfire.span(
                    "rag.input_security",
                    request_id=request_id,
                ):
                    decision = validate_input(question)

                record_timing(current_stage, started)

                logfire.info(
                    "Input security completed",
                    request_id=request_id,
                    allowed=decision.allowed,
                    duration_ms=timings[current_stage],
                )

                if not decision.allowed:
                    logfire.warn(
                        "Request blocked by input security",
                        request_id=request_id,
                        reason=str(decision.reason),
                    )
                    return finish_early(
                        answer_text=(
                            "Your request was blocked by the input security policy."
                        ),
                        retrieval=None,
                        reason="input_security_blocked",
                    )

                # 2. NeMo jailbreak detection.
                current_stage = "nemo_security"
                started = time.perf_counter()

                with logfire.span(
                    "rag.nemo_security",
                    request_id=request_id,
                ):
                    nemo_allowed = await check_nemo_input(question)

                record_timing(current_stage, started)

                logfire.info(
                    "NeMo input security completed",
                    request_id=request_id,
                    allowed=nemo_allowed,
                    duration_ms=timings[current_stage],
                )

                if not nemo_allowed:
                    logfire.warn(
                        "Request blocked by NeMo input security",
                        request_id=request_id,
                    )
                    return finish_early(
                        answer_text=(
                            "Your request was blocked by the input security policy."
                        ),
                        retrieval=None,
                        reason="nemo_security_blocked",
                    )

                # 3. Query transformation, retrieval, and fusion.
                current_stage = "retrieval"
                started = time.perf_counter()

                with logfire.span(
                    "rag.retrieval",
                    request_id=request_id,
                ):
                    retrieval = await self.orchestrator.retrieve(question)

                record_timing(current_stage, started)

                strategy = retrieval.diagnostics.strategy
                candidate_count = len(retrieval.candidates)

                logfire.info(
                    "Retrieval completed",
                    request_id=request_id,
                    strategy=strategy,
                    candidates=candidate_count,
                    duration_ms=timings[current_stage],
                )

                # 4. Requests that should not reach the LLM.
                if strategy == "clarify":
                    return finish_early(
                        answer_text=(
                            "Could you clarify your question so I can identify "
                            "the relevant FastAPI documentation?"
                        ),
                        retrieval=retrieval,
                        reason="clarification_required",
                    )

                if strategy == "out_of_scope":
                    return finish_early(
                        answer_text=(
                            "I can help with questions about FastAPI "
                            "documentation. This question appears to be outside "
                            "that scope."
                        ),
                        retrieval=retrieval,
                        reason="out_of_scope",
                    )

                # 5. Rerank candidates without blocking the event loop.
                current_stage = "reranking"
                started = time.perf_counter()

                with logfire.span(
                    "rag.reranking",
                    request_id=request_id,
                    input_documents=candidate_count,
                ):
                    if retrieval.candidates:
                        reranked = await asyncio.to_thread(
                            self.reranker.compress_documents,
                            retrieval.candidates,
                            question,
                        )
                    else:
                        reranked = []

                record_timing(current_stage, started)

                logfire.info(
                    "Reranking completed",
                    request_id=request_id,
                    input_documents=candidate_count,
                    output_documents=len(reranked),
                    duration_ms=timings[current_stage],
                )

                # 6. Assemble context after reranking.
                current_stage = "context_assembly"
                started = time.perf_counter()

                with logfire.span(
                    "rag.context_assembly",
                    request_id=request_id,
                    max_tokens=self.max_context_tokens,
                    max_documents=self.max_context_documents,
                ):
                    assembled = assemble_context(
                        list(reranked),
                        max_tokens=self.max_context_tokens,
                        max_documents=self.max_context_documents,
                    )

                record_timing(current_stage, started)

                logfire.info(
                    "RAG context assembled",
                    request_id=request_id,
                    estimated_tokens=assembled.estimated_tokens,
                    documents=len(assembled.evidence),
                    omitted_documents=assembled.omitted_documents,
                    context_chars=len(assembled.context),
                    duration_ms=timings[current_stage],
                )

                # 7. Generate an answer grounded in the assembled evidence.
                current_stage = "generation"
                started = time.perf_counter()

                with logfire.span(
                    "rag.generation",
                    request_id=request_id,
                    model=self.generation_model,
                    context_tokens=assembled.estimated_tokens,
                    context_documents=len(assembled.evidence),
                ):
                    generated: GeneratedAnswer = await generate_answer(
                        question=question,
                        assembled_context=assembled,
                        model=self.generation_model,
                    )

                record_timing(current_stage, started)

                logfire.info(
                    "Answer generation completed",
                    request_id=request_id,
                    model=self.generation_model,
                    answer_chars=len(generated.answer),
                    citations=len(generated.citations),
                    insufficient_evidence=generated.insufficient_evidence,
                    duration_ms=timings[current_stage],
                )

                # 8. Validate generated output.
                current_stage = "output_security"
                started = time.perf_counter()

                with logfire.span(
                    "rag.output_security",
                    request_id=request_id,
                ):
                    output_decision = validate_output(generated.answer)

                record_timing(current_stage, started)

                logfire.info(
                    "Output security completed",
                    request_id=request_id,
                    allowed=output_decision.allowed,
                    duration_ms=timings[current_stage],
                )

                answer = generated.answer
                citations = generated.citations
                insufficient_evidence = generated.insufficient_evidence

                if not output_decision.allowed:
                    logfire.warn(
                        "Generated answer blocked by output security",
                        request_id=request_id,
                        reason=str(output_decision.reason),
                    )
                    answer = (
                        "The generated answer was withheld by the output "
                        "security policy."
                    )
                    citations = []
                    insufficient_evidence = True

                timings["total"] = elapsed_ms(total_started)

                logfire.info(
                    "RAG request completed",
                    request_id=request_id,
                    strategy=strategy,
                    candidates=candidate_count,
                    reranked_documents=len(reranked),
                    context_documents=len(assembled.evidence),
                    context_tokens=assembled.estimated_tokens,
                    citations=len(citations),
                    insufficient_evidence=insufficient_evidence,
                    total_ms=timings["total"],
                    timings_ms=timings,
                )

                return RAGResponse(
                    question=question,
                    answer=answer,
                    citations=citations,
                    insufficient_evidence=insufficient_evidence,
                    retrieval=retrieval,
                    context=assembled,
                    latency_ms=dict(timings),
                )

            except Exception:
                timings["total"] = elapsed_ms(total_started)

                # Logfire records this exception on the active request span.
                logfire.error(
                    "RAG request failed",
                    request_id=request_id,
                    stage=current_stage,
                    total_ms=timings["total"],
                    timings_ms=timings,
                    exc_info=True,
                )
                raise


def build_rag_pipeline() -> RAGPipeline:
    with logfire.span("rag.build_pipeline"):
        logfire.info("Building RAG pipeline dependencies")

        try:
            orchestrator = build_retrieval_orchestrator(k=20)

            reranker = CrossEncoderCompressor(
                model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
                top_n=8,
                batch_size=16,
                max_length=512,
                fail_open=True,
            )

            pipeline = RAGPipeline(
                orchestrator=orchestrator,
                reranker=reranker,
                generation_model="rag-generation",
                max_context_tokens=4000,
                max_context_documents=8,
            )

            logfire.info("RAG pipeline dependencies built successfully")
            return pipeline

        except Exception:
            logfire.error(
                "Failed to build RAG pipeline dependencies",
                exc_info=True,
            )
            raise
