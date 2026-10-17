import logging
import re

logger = logging.getLogger(__name__)

from dataclasses import dataclass

from app.generation.prompts import ANSWER_SYSTEM_PROMPT
from app.llm_gateway.client import complete  # Change to the actual module path.
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

    if not question.strip():
        raise ValueError("question must not be empty.")

    evidence = assembled_context.evidence

    if not evidence:
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

    answer = await complete(
        model=model,
        system=ANSWER_SYSTEM_PROMPT,
        user=user_prompt,
        temperature=0,
        max_tokens=512,
    )

    # Build a lookup from the evidence supplied to the LLM.
    evidence_by_id = {item.evidence_id: item for item in evidence}

    # Extract bracketed references, accepting either the exact evidence ID
    # or its raw metadata value (e.g. [chunk_id:test-001] or [test-001]).
    cited_ids = []

    # Build a lookup from the evidence supplied to the LLM.
    evidence_by_id = {item.evidence_id: item for item in evidence}

    # Accept canonical IDs and unprefixed IDs only when they uniquely match
    # supplied evidence. Reject unknown or ambiguous references.
    cited_ids = []
    for raw_id in CITATION_PATTERN.findall(answer):
        if raw_id in evidence_by_id:
            evidence_id = raw_id
        else:
            matches = [
                evidence_id
                for evidence_id in evidence_by_id
                if evidence_id.rsplit(":", 1)[-1] == raw_id
            ]
            if len(matches) != 1:
                logger.error(
                    "Invalid citation ID generated: %s; available IDs: %s",
                    raw_id,
                    list(evidence_by_id),
                )
                raise ValueError(
                    f"Generated answer contains unknown or ambiguous "
                    f"citation ID: {raw_id}"
                )
            evidence_id = matches[0]

        if evidence_id not in cited_ids:
            cited_ids.append(evidence_id)
        else:
            matches = [
                evidence_id
                for evidence_id in evidence_by_id
                if evidence_id.rsplit(":", 1)[-1] == raw_id
            ]
            if len(matches) != 1:
                continue
            evidence_id = matches[0]

        if evidence_id not in cited_ids:
            cited_ids.append(evidence_id)
    # Reject citations that were not present in the supplied evidence.
    invalid_ids = [
        evidence_id for evidence_id in cited_ids if evidence_id not in evidence_by_id
    ]

    if invalid_ids:
        logger.error(
            "Invalid citation IDs generated. invalid_ids=%s available_evidence_ids=%s",
            invalid_ids,
            list(evidence_by_id.keys()),
        )
        raise ValueError(
            f"Generated answer contains unknown citation IDs: {invalid_ids}"
        )

    # Return metadata only for evidence actually cited.
    citations = [
        Citation(
            evidence_id=evidence_id,
            source_url=evidence_by_id[evidence_id].source_url,
            page_title=evidence_by_id[evidence_id].page_title,
            heading_path=evidence_by_id[evidence_id].heading_path,
        )
        for evidence_id in cited_ids
    ]

    return GeneratedAnswer(
        answer=answer,
        citations=citations,
        insufficient_evidence=False,
    )
