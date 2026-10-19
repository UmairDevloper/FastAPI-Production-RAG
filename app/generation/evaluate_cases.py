from __future__ import annotations

from dataclasses import dataclass

import logfire


@dataclass(frozen=True, slots=True)
class GenerationCase:
    question: str
    required_facts: tuple[str, ...]
    expected_source_terms: tuple[str, ...]
    expect_abstention: bool = False


CASES: list[GenerationCase] = [
    # Middleware and CORS (4)
    GenerationCase(
        "How do I add HTTP middleware in FastAPI?",
        ("@app.middleware", "call_next"),
        ("middleware",),
    ),
    GenerationCase(
        "How do I enable CORS in FastAPI?",
        ("CORSMiddleware", "allow_origins"),
        ("cors", "middleware"),
    ),
    GenerationCase(
        "How do I redirect HTTP requests to HTTPS?",
        ("HTTPSRedirectMiddleware",),
        ("middleware", "https"),
    ),
    GenerationCase(
        "Can middleware modify a response header?",
        ("response.headers",),
        ("middleware",),
    ),
    # Parameters and request bodies (5)
    GenerationCase(
        "How do I declare a path parameter?",
        ("path parameter",),
        ("path parameters",),
    ),
    GenerationCase(
        "How do I define an optional query parameter?",
        ("None",),
        ("query parameters",),
    ),
    GenerationCase(
        "How do I receive JSON in a POST request?",
        ("BaseModel",),
        ("request body",),
    ),
    GenerationCase(
        "How do I receive multiple body parameters?",
        ("Body",),
        ("multiple body parameters",),
    ),
    GenerationCase(
        "How do I upload a file?",
        ("UploadFile",),
        ("request files",),
    ),
    # Responses and status codes (4)
    GenerationCase(
        "How do I define a response model?",
        ("response_model",),
        ("response model",),
    ),
    GenerationCase(
        "How do I return HTTP status code 201?",
        ("status_code", "201"),
        ("response status code",),
    ),
    GenerationCase(
        "How do I return a custom response?",
        ("Response",),
        ("custom response",),
    ),
    GenerationCase(
        "How do I exclude fields from a response?",
        ("response_model_exclude",),
        ("response model",),
    ),
    # Errors and dependencies (5)
    GenerationCase(
        "How do I raise an HTTP error?",
        ("HTTPException",),
        ("handling errors",),
    ),
    GenerationCase(
        "How do I create a custom exception handler?",
        ("exception_handler",),
        ("handling errors",),
    ),
    GenerationCase(
        "What is FastAPI dependency injection?",
        ("Depends",),
        ("dependencies",),
    ),
    GenerationCase(
        "How do I share a database session using dependencies?",
        ("Depends",),
        ("dependencies", "database"),
    ),
    GenerationCase(
        "Can dependencies have sub-dependencies?",
        ("Depends",),
        ("dependencies",),
    ),
    # Security and authentication (4)
    GenerationCase(
        "How do I use OAuth2 password bearer authentication?",
        ("OAuth2PasswordBearer",),
        ("security", "oauth2"),
    ),
    GenerationCase(
        "How do I extract a bearer token?",
        ("Authorization",),
        ("security",),
    ),
    GenerationCase(
        "How do I configure HTTP Basic authentication?",
        ("HTTPBasic",),
        ("security",),
    ),
    GenerationCase(
        "How do I hash passwords securely?",
        ("password",),
        ("security",),
    ),
    # Async and database integration (4)
    GenerationCase(
        "When should I use async def for a path operation?",
        ("async def",),
        ("async",),
    ),
    GenerationCase(
        "Can I use def instead of async def?",
        ("def",),
        ("async",),
    ),
    GenerationCase(
        "How do I integrate SQL databases with FastAPI?",
        ("SQL",),
        ("sql databases",),
    ),
    GenerationCase(
        "How do I run code at application startup?",
        ("lifespan",),
        ("lifespan",),
    ),
    # Out-of-scope / abstention (4)
    GenerationCase(
        "What is the current weather in Multan?",
        (),
        (),
        expect_abstention=True,
    ),
    GenerationCase(
        "What is the latest stock price of Microsoft?",
        (),
        (),
        expect_abstention=True,
    ),
    GenerationCase(
        "Write a poem about the ocean.",
        (),
        (),
        expect_abstention=True,
    ),
    GenerationCase(
        "Who won the latest FIFA World Cup?",
        (),
        (),
        expect_abstention=True,
    ),
]


def validate_generation_cases(
    cases: list[GenerationCase],
) -> dict[str, int]:
    """Validate the static evaluation dataset and report aggregate metadata."""
    with logfire.span(
        "evaluation.dataset.validate",
        dataset="generation_cases",
        case_count=len(cases),
    ):
        if not cases:
            logfire.error("Generation evaluation dataset is empty")
            raise ValueError("Generation evaluation dataset cannot be empty.")

        seen_questions: set[str] = set()
        duplicate_count = 0
        abstention_count = 0
        required_fact_count = 0
        source_term_count = 0

        for index, case in enumerate(cases):
            with logfire.span(
                "evaluation.dataset.validate_case",
                case_index=index,
                expect_abstention=case.expect_abstention,
            ):
                if not case.question.strip():
                    logfire.error(
                        "Evaluation case has an empty question",
                        case_index=index,
                    )
                    raise ValueError(
                        f"Generation case at index {index} has an empty question."
                    )

                normalized_question = case.question.strip().casefold()

                if normalized_question in seen_questions:
                    duplicate_count += 1
                    logfire.warn(
                        "Duplicate evaluation question detected",
                        case_index=index,
                    )

                seen_questions.add(normalized_question)

                if case.expect_abstention:
                    abstention_count += 1

                    if case.required_facts or case.expected_source_terms:
                        logfire.error(
                            "Abstention case unexpectedly has required facts "
                            "or source terms",
                            case_index=index,
                        )
                        raise ValueError(
                            f"Abstention case at index {index} must not define "
                            "required facts or expected source terms."
                        )

                required_fact_count += len(case.required_facts)
                source_term_count += len(case.expected_source_terms)

        summary = {
            "cases": len(cases),
            "unique_questions": len(seen_questions),
            "duplicate_questions": duplicate_count,
            "abstention_cases": abstention_count,
            "answerable_cases": len(cases) - abstention_count,
            "required_facts": required_fact_count,
            "expected_source_terms": source_term_count,
        }

        logfire.info(
            "Generation evaluation dataset validated",
            **summary,
        )

        return summary


# Validate once when this dataset module is imported.
DATASET_SUMMARY = validate_generation_cases(CASES)
