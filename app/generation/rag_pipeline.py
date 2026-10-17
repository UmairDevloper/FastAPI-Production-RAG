from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass

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

    async def answer(self, question: str) -> RAGResponse:
        question = question.strip()
        if not question:
            raise ValueError("Question cannot be empty.")

        
        timings: dict[str, float] = {}
        total_started = time.perf_counter()

        empty_context = AssembledContext(
            context="",
            evidence=[],
            estimated_tokens=0,
            omitted_documents=0,
        )

        security_started = time.perf_counter()
        decision = validate_input(question)
        timings["security"] = round(
            (time.perf_counter() - security_started) * 1000, 2
        )

        if not decision.allowed:
            logger.warning(
                "Request blocked by input security: reason=%s",
                decision.reason,
            )
            timings["total"] = round(
                (time.perf_counter() - total_started) * 1000, 2
            )

            return RAGResponse(
                question=question,
                answer="Your request was blocked by the input security policy.",
                citations=[],
                insufficient_evidence=True,
                retrieval=None,
                context=empty_context,
                latency_ms=timings,
            )

        # Second layer: NeMo jailbreak detection.
        nemo_started = time.perf_counter()
        nemo_allowed = await check_nemo_input(question)
        timings["nemo_security"] = round((time.perf_counter() - nemo_started) * 1000, 2)

        if not nemo_allowed:
            logger.warning("Request blocked by NeMo input security.")
            timings["total"] = round((time.perf_counter() - total_started) * 1000, 2)

            return RAGResponse(
                question=question,
                answer="Your request was blocked by the input security policy.",
                citations=[],
                insufficient_evidence=True,
                retrieval=None,
                context=empty_context,
                latency_ms=timings,
            )
            
        # 1. Query transformation + retrieval + fusion.
        started = time.perf_counter()
        retrieval = await self.orchestrator.retrieve(question)
        timings["retrieval"] = round((time.perf_counter() - started) * 1000, 2)


        # 2. Handle requests that should not reach the LLM.
        if retrieval.diagnostics.strategy == "clarify":
            return RAGResponse(
                question=question,
                answer=(
                    "Could you clarify your question so I can identify "
                    "the relevant FastAPI documentation?"
                ),
                citations=[],
                insufficient_evidence=True,
                retrieval=retrieval,
                context=empty_context,
                latency_ms={
                    **timings,
                    "total": round((time.perf_counter() - total_started) * 1000, 2),
                },
            )

        if retrieval.diagnostics.strategy == "out_of_scope":
            return RAGResponse(
                question=question,
                answer=(
                    "I can help with questions about FastAPI "
                    "documentation. This question appears to be outside "
                    "that scope."
                ),
                citations=[],
                insufficient_evidence=True,
                retrieval=retrieval,
                context=empty_context,
                latency_ms={
                    **timings,
                    "total": round((time.perf_counter() - total_started) * 1000, 2),
                },
            )

        # 3. Rerank candidates. Run synchronous model inference off-loop.
        started = time.perf_counter()
        if retrieval.candidates:
            reranked = await asyncio.to_thread(
                self.reranker.compress_documents,
                retrieval.candidates,
                question,
            )
        else:
            reranked = []

        timings["reranking"] = round((time.perf_counter() - started) * 1000, 2)

        # 4. Assemble context exactly once, after reranking.
        started = time.perf_counter()
        assembled = assemble_context(
            list(reranked),
            max_tokens=self.max_context_tokens,
            max_documents=self.max_context_documents,
        )
        timings["context_assembly"] = round((time.perf_counter() - started) * 1000, 2)

        # 5. Generate an answer grounded in the assembled evidence.
        started = time.perf_counter()
        generated: GeneratedAnswer = await generate_answer(
            question=question,
            assembled_context=assembled,
            model=self.generation_model,
        )

        timings["generation"] = round((time.perf_counter() - started) * 1000, 2)

        # 6. Validate generated output before returning it.
        output_decision = validate_output(generated.answer)

        answer = generated.answer
        citations = generated.citations
        insufficient_evidence = generated.insufficient_evidence

        if not output_decision.allowed:
            logger.warning(
                "Generated answer blocked by output security: reason=%s",
                output_decision.reason,
            )
            answer = "The generated answer was withheld by the output security policy."
            citations = []
            insufficient_evidence = True

        timings["total"] = round((time.perf_counter() - total_started) * 1000, 2)

        logger.info(
            "RAG request completed | strategy=%s | candidates=%d | "
            "context_documents=%d | context_tokens=%d | latency_ms=%s",
            retrieval.diagnostics.strategy,
            len(retrieval.candidates),
            len(assembled.evidence),
            assembled.estimated_tokens,
            timings,
        )

        return RAGResponse(
            question=question,
            answer=answer,
            citations=citations,
            insufficient_evidence=insufficient_evidence,
            retrieval=retrieval,
            context=assembled,
            latency_ms=timings,
        )


def build_rag_pipeline() -> RAGPipeline:
    orchestrator = build_retrieval_orchestrator(k=20)

    reranker = CrossEncoderCompressor(
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        top_n=8,
        batch_size=16,
        max_length=512,
        fail_open=True,
    )

    return RAGPipeline(
        orchestrator=orchestrator,
        reranker=reranker,
        generation_model="rag-generation",
        max_context_tokens=4000,
        max_context_documents=8,
    )
