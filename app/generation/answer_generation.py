import re
import time
from dataclasses import dataclass

import logfire

from app.generation.prompts import ANSWER_SYSTEM_PROMPT
from app.llm_gateway.client import complete
from app.retrieval.context_assembly import AssembledContext

CITATION_PATTERN = re.compile(r"\[((?:chunk_id:)?[A-Za-z0-9][A-Za-z0-9:_-]*-\d{3,})\]")


@dataclass(frozen=True, slots=True)
class Citation:
    evidence_id: str
    source_url: str | None
    page_title: str | None
    heading_path: str | None


@dataclass(frozen=True, slots=True)
class GeneratedAnswer:
    answer: str
    citations: list[Citation]
    insufficient_evidence: bool


async def generate_answer(
    *,
    question: str,
    assembled_context: AssembledContext,
    model: str,
) -> GeneratedAnswer:
    """Generate an answer using assembled evidence from the RAG pipeline."""

    started_at = time.perf_counter()
    evidence = assembled_context.evidence

    with logfire.span(
        "rag.answer_generation",
        model=model,
        evidence_count=len(evidence),
        question_chars=len(question),
        context_chars=len(assembled_context.context),
    ):
        if not question.strip():
            logfire.warn("Answer generation rejected an empty question")
            raise ValueError("question must not be empty.")

        if not evidence:
            logfire.info(
                "Answer generation skipped: no evidence supplied",
                model=model,
            )
            return GeneratedAnswer(
                answer=(
                    "I could not find sufficient relevant documentation "
                    "to answer this question."
                ),
                citations=[],
                insufficient_evidence=True,
            )

        user_prompt = (
            f"User question:\n{question.strip()}\n\n"
            "Documentation context:\n"
            f"<context>\n{assembled_context.context}\n</context>\n\n"
            "Answer the question using the supplied evidence. "
            "Cite sources using their exact evidence identifiers."
        )

        generation_started = time.perf_counter()

        with logfire.span(
            "rag.llm_completion",
            model=model,
            temperature=0,
            max_tokens=512,
            evidence_count=len(evidence),
        ):
            answer = await complete(
                model=model,
                system=ANSWER_SYSTEM_PROMPT,
                user=user_prompt,
                temperature=0,
                max_tokens=512,
            )

        generation_ms = (time.perf_counter() - generation_started) * 1000

        logfire.info(
            "LLM completion finished",
            model=model,
            generation_ms=round(generation_ms, 2),
            answer_chars=len(answer),
        )

        with logfire.span(
            "rag.citation_validation",
            evidence_count=len(evidence),
        ):
            evidence_by_id = {item.evidence_id: item for item in evidence}
            cited_ids: list[str] = []
            raw_citation_ids = CITATION_PATTERN.findall(answer)

            for raw_id in raw_citation_ids:
                if raw_id in evidence_by_id:
                    evidence_id = raw_id
                else:
                    matches = [
                        supplied_id
                        for supplied_id in evidence_by_id
                        if supplied_id.rsplit(":", 1)[-1] == raw_id
                    ]

                    if len(matches) != 1:
                        logfire.error(
                            "Generated citation is unknown or ambiguous",
                            raw_citation_id=raw_id,
                            available_evidence_ids=list(evidence_by_id),
                        )
                        raise ValueError(
                            "Generated answer contains unknown or ambiguous "
                            f"citation ID: {raw_id}"
                        )

                    evidence_id = matches[0]

                if evidence_id not in cited_ids:
                    cited_ids.append(evidence_id)

            invalid_ids = [
                evidence_id
                for evidence_id in cited_ids
                if evidence_id not in evidence_by_id
            ]

            if invalid_ids:
                logfire.error(
                    "Generated answer contains invalid citation IDs",
                    invalid_ids=invalid_ids,
                    available_evidence_ids=list(evidence_by_id),
                )
                raise ValueError(
                    f"Generated answer contains unknown citation IDs: {invalid_ids}"
                )

            citations = [
                Citation(
                    evidence_id=evidence_id,
                    source_url=evidence_by_id[evidence_id].source_url,
                    page_title=evidence_by_id[evidence_id].page_title,
                    heading_path=evidence_by_id[evidence_id].heading_path,
                )
                for evidence_id in cited_ids
            ]

        total_ms = (time.perf_counter() - started_at) * 1000

        logfire.info(
            "Answer generation completed",
            model=model,
            evidence_count=len(evidence),
            citations_found=len(raw_citation_ids),
            unique_citations=len(citations),
            answer_chars=len(answer),
            generation_ms=round(generation_ms, 2),
            total_ms=round(total_ms, 2),
            insufficient_evidence=False,
        )

        return GeneratedAnswer(
            answer=answer,
            citations=citations,
            insufficient_evidence=False,
        )
