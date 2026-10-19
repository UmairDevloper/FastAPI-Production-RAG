# FastAPI Documentation RAG --- Architecture

> **Purpose:** A portfolio-grade Retrieval-Augmented Generation (RAG)
> application that answers questions about the official FastAPI
> documentation, grounds answers in retrieved evidence, validates
> citations, and exposes the pipeline through a FastAPI API and Swagger
> UI.
>
> **Architecture style:** Modular, layered, asynchronous Python
> application with a retrieval pipeline and an LLM gateway. The system
> uses a local open-weight language model for generation, a hosted
> vector database for retrieval, and distributed tracing/structured
> observability for debugging.
>
> **Repository note:** This document reflects the project details
> established so far. Some implementation choices may evolve; check the
> actual configuration files before treating optional fallbacks or every
> listed stage as active in a particular run.

## 1. System overview

The project ingests FastAPI documentation, converts it into clean
structured chunks, embeds the chunks, and stores vectors in Qdrant
Cloud. At query time, it transforms and retrieves the question as
configured, combines/deduplicates candidate evidence, assembles a
context within a token budget, and asks an LLM to generate a cited
answer. Citation IDs are checked against the evidence supplied to the
model before the API returns the result.

### High-level wireframe

``` mermaid
flowchart TD
    U[User / Developer] -->|Question| SW[Swagger UI /docs]
    SW -->|POST /ask| API[FastAPI application]
    API --> VAL[Request validation<br/>Pydantic models]
    VAL --> PIPE[RAG pipeline orchestration]

    PIPE --> QT[Query transformation<br/>direct / rewrite / multi-query / decomposition / HyDE / clarify / out-of-scope]
    QT --> RET[Retrieval orchestration]
    RET --> EMB[Qwen3 Embedding 0.6B<br/>1024 dimensions]
    EMB --> QD[(Qdrant Cloud<br/>FastAPI_RAG__qwen3)]
    QD --> RET
    RET --> RER[Optional reranking<br/>BGE / MiniLM / configured reranker]
    RER --> FUS[Deduplication + result fusion<br/>RRF, k=60 where configured]
    FUS --> CTX[Context assembly<br/>evidence IDs + source metadata + token budget]

    CTX --> GUARD[Configured input/security checks]
    GUARD --> GEN[Answer generation]
    GEN --> GW[LLM gateway<br/>OpenAI-compatible AsyncOpenAI client]
    GW --> LIT[LiteLLM proxy<br/>Docker, port 4000]
    LIT --> OLL[Ollama on host<br/>qwen3:8b, Q4_K_M]
    OLL --> LIT
    LIT --> GW
    GW --> GEN

    GEN --> CIT[Citation validation<br/>match IDs to supplied evidence]
    CIT --> RES[Structured answer + citations + latency metrics]
    RES --> API
    API --> SW
    SW --> U

    API -. traces / spans .-> LF[Logfire observability]
    PIPE -. traces / spans .-> LF
    RET -. traces / spans .-> LF
    GEN -. traces / spans .-> LF
    GW -. request diagnostics .-> LF
```

## 2. Main technology stack

  ---------------------------------------------------------------------------------------
  Area                    Technology                              Role
  ----------------------- --------------------------------------- -----------------------
  Language                Python                                  Application, ingestion,
                                                                  retrieval, evaluation
                                                                  and API code

  API framework           FastAPI                                 HTTP API, request
                                                                  handling and
                                                                  lifecycle/startup

  API schema / validation Pydantic                                Validates request and
                                                                  response models; powers
                                                                  the OpenAPI schema

  Interactive API testing Swagger UI (`/docs`)                    Manual requests against
                                                                  the API

  ASGI server             Uvicorn                                 Runs the FastAPI
                                                                  application

  LLM interface           OpenAI Python SDK (`AsyncOpenAI`)       Async chat-completions
                                                                  client using an
                                                                  OpenAI-compatible base
                                                                  URL

  LLM routing / proxy     LiteLLM Proxy in Docker                 Model alias routing,
                                                                  provider integration,
                                                                  fallbacks and request
                                                                  timeout configuration

  Local inference         Ollama                                  Serves the local
                                                                  `qwen3:8b` model

  Generation model        Qwen3 8B, quantized Q4_K_M              Local answer
                                                                  generation; model is
                                                                  CPU-capable on the
                                                                  current machine

  Embeddings              `Qwen/Qwen3-Embedding-0.6B`             Creates
                                                                  1024-dimensional dense
                                                                  vectors for
                                                                  documentation chunks
                                                                  and queries

  Vector database         Qdrant Cloud                            Stores and searches the
                                                                  documentation vectors

  Retrieval framework     LangChain document abstractions         Common document
                          (`langchain_core.documents.Document`)   representation in parts
                                                                  of the retrieval
                                                                  pipeline

  Reranking               Configured reranker options such as BGE Reorders retrieved
                          reranker / MiniLM; exact active model   candidates to improve
                          depends on configuration                relevance

  Ingestion / crawling    Crawl4AI (used in the ingestion         Crawls documentation
                          workflow)                               pages for conversion to
                                                                  Markdown

  Data format             Markdown and JSONL                      Cleaned source pages
                                                                  and chunk records

  Observability           Logfire                                 Spans, timings,
                                                                  diagnostics and
                                                                  pipeline error
                                                                  investigation

  Configuration           `.env`, `python-dotenv`, YAML           Environment settings
                                                                  and LiteLLM
                                                                  model-routing
                                                                  configuration

  Packaging / commands    `uv`                                    Runs project commands
                                                                  and manages the Python
                                                                  environment

  Code quality / tests    Ruff, pytest                            Linting and automated
                                                                  tests

  Containerization        Docker                                  Runs the LiteLLM proxy

  Evaluation              Project-specific evaluation runners and Measures
                          JSON reports                            retrieval/generation
                                                                  behavior and
                                                                  citation/fact checks

  Optional safety layer   NeMo Guardrails / project security      Input screening and
                          checks                                  configured security
                                                                  validation
  ---------------------------------------------------------------------------------------

**Important:** The table lists technologies known from the project
history. Optional fallback providers, rerankers, and safety checks are
only active when the current code/configuration invokes them
successfully.

## 3. Repository responsibilities

The following describes the observed module layout and its
responsibilities. It is a conceptual map, not a guarantee that every
possible subdirectory is required at runtime.

``` text
FastAPI RAG/
├── app/
│   ├── main.py
│   │   └── FastAPI app, lifespan/startup, /health and /ask endpoints
│   ├── ingestion/
│   │   └── Embedding/model configuration and ingestion-related code
│   ├── indexing/
│   │   └── Dense indexing and evaluation-related indexing utilities
│   ├── retrieval/
│   │   ├── Retrieval orchestration
│   │   ├── Deduplication and document IDs
│   │   ├── Fusion / Reciprocal Rank Fusion (RRF)
│   │   └── Context assembly and evidence metadata
│   ├── query_transformation/
│   │   └── Direct, rewrite, multi-query, decomposition, HyDE and routing strategies
│   ├── generation/
│   │   ├── rag_pipeline.py
│   │   │   └── Coordinates the end-to-end answer pipeline
│   │   ├── answer_generation.py
│   │   │   └── Builds the generation prompt and validates citation IDs
│   │   └── prompts.py
│   │       └── System prompt(s) for grounded answer generation
│   ├── llm_gateway/
│   │   └── client.py — async OpenAI-compatible client to LiteLLM
│   ├── security/
│   │   └── Input/security validation helpers and configured safety integration
│   └── docker/
│       └── litellm/
│           └── litellm_config.yaml — model aliases, routing, fallbacks and timeout
├── evaluation/
│   ├── runners/
│   │   └── Evaluation entry points
│   └── reports/
│       └── Generated evaluation reports (JSON)
├── tests/
│   └── Automated tests, including RAG pipeline/generation tests
├── app/data/fastapi_docs/
│   └── JSONL chunk data (project data path)
├── .env
│   └── Local secrets/configuration; must never be committed
├── pyproject.toml
│   └── Project dependencies and tool configuration
└── architecture.md
    └── This architecture document
```

Directory names and responsibilities can differ slightly as the codebase
evolves. Keep this diagram aligned with the actual repository when
moving or renaming modules.

## 4. Offline / ingestion and indexing flow

``` mermaid
flowchart LR
    DOCS[Official FastAPI documentation] --> CRAWL[Crawl4AI crawler]
    CRAWL --> MD[Markdown pages]
    MD --> CLEAN[Clean and normalize content]
    CLEAN --> CHUNK[Structure-aware chunking]
    CHUNK --> JSONL[JSONL chunk records]
    JSONL --> EMB[Qwen3 Embedding 0.6B]
    EMB --> VEC[1024-dimensional vectors]
    VEC --> QDRANT[(Qdrant Cloud collection)]
    JSONL -. source text and metadata .-> QDRANT
```

Known data/indexing details:

-   Source material: official FastAPI documentation.
-   Crawled content is converted to Markdown, cleaned, and chunked with
    document structure in mind.
-   Chunk records are stored as JSONL under `app/data/fastapi_docs` in
    the current project layout.
-   Embeddings use `Qwen/Qwen3-Embedding-0.6B`, with 1024 dimensions.
-   The current collection name recorded for the project is
    `FastAPI_RAG__qwen3`.
-   The latest reported corpus size was approximately **2,201 chunks**.
    Re-run the indexing/count script to confirm the live count.
-   The vector store is Qdrant Cloud, so connection details and
    credentials are supplied through environment/configuration rather
    than hard-coded into source.

## 5. Online question-answering flow

1.  **Request:** The user submits a question in Swagger UI or sends
    `POST /ask`.
2.  **Validation:** FastAPI/Pydantic validates the request shape and
    question length. The endpoint rejects blank questions after
    trimming.
3.  **Pipeline orchestration:** `RAGPipeline.answer()` coordinates the
    stages.
4.  **Query transformation:** Depending on configuration and the
    question, the pipeline can use direct querying, rewriting,
    multi-query generation, decomposition, HyDE, clarification or
    out-of-scope handling.
5.  **Retrieval:** The retriever embeds the query and searches the
    Qdrant collection for relevant documentation chunks.
6.  **Reranking (if enabled):** A configured reranker scores candidate
    chunks and selects a smaller, more relevant set.
7.  **Fusion and deduplication:** Candidate lists can be merged using
    Reciprocal Rank Fusion (RRF; `k=60` where configured), and duplicate
    chunks are removed.
8.  **Context assembly:** Selected evidence is packaged with an evidence
    ID, text, source URL, page title, heading path and score. Context is
    assembled within the configured budget.
9.  **Safety checks (where configured):** Input and security checks run
    at their designated pipeline boundaries.
10. **Generation:** `answer_generation.py` combines the question,
    assembled context and `ANSWER_SYSTEM_PROMPT`, then calls the async
    LLM client.
11. **LLM gateway:** `app/llm_gateway/client.py` uses `AsyncOpenAI` with
    the LiteLLM base URL and master key. LiteLLM maps the
    `rag-generation` alias to Ollama's `qwen3:8b` model according to
    `app/docker/litellm/litellm_config.yaml`.
12. **Citation validation:** Citation IDs in the model output are
    checked against the exact evidence supplied. Unknown or ambiguous
    citation IDs raise an error instead of being silently accepted.
13. **Response:** The API returns the question, answer, citations,
    insufficient-evidence flag and latency metrics.

## 6. API surface

  Endpoint              Purpose
  --------------------- -------------------------------------------------------
  `GET /health`         Basic health response
  `POST /ask`           Runs the RAG pipeline and returns a structured answer
  `GET /docs`           Swagger UI generated by FastAPI
  `GET /openapi.json`   OpenAPI schema generated by FastAPI

Example request:

``` json
{
  "question": "How does middleware work in FastAPI?"
}
```

The response model contains:

-   `question`
-   `answer`
-   `citations` --- each includes `evidence_id`, `source_url`,
    `page_title`, and `heading_path`
-   `insufficient_evidence`
-   `latency_ms` --- pipeline stage timing data

Run locally from the repository root:

``` powershell
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then open <http://127.0.0.1:8000/docs>.

## 7. LLM gateway and local inference

``` mermaid
flowchart LR
    AG[Answer generation] --> CLIENT[AsyncOpenAI client]
    CLIENT -->|HTTP /v1/chat/completions| PROXY[LiteLLM Proxy in Docker<br/>127.0.0.1:4000]
    PROXY -->|Docker host route| OLLAMA[Ollama on host<br/>port 11434]
    OLLAMA --> MODEL[Qwen3 8B<br/>Q4_K_M]
    MODEL --> OLLAMA --> PROXY --> CLIENT --> AG
```

Known configuration:

-   LiteLLM proxy endpoint used by the Python client:
    `http://127.0.0.1:4000/v1` or the configured equivalent.
-   From inside the Docker container, Ollama is addressed through
    `http://host.docker.internal:11434`.
-   Model alias `rag-generation` maps to `ollama_chat/qwen3:8b`.
-   `LITELLM_MASTER_KEY` authenticates requests to LiteLLM. The key
    belongs in local environment configuration and must not be
    published.
-   The Python client currently uses a 180-second timeout and
    `max_retries=0`; LiteLLM configuration has `request_timeout: 180`
    and `num_retries: 1` in the reported configuration.
-   Fallback aliases/providers are declared in the LiteLLM YAML. A
    configured fallback is not proof that a fallback call will succeed;
    provider credentials, limits and model availability still matter.
-   Ollama model files are stored on the `D:` drive in the current setup
    (reported path: `D:\OllamaModels`).

### Generation performance note

The short direct LiteLLM tests completed successfully, while full RAG
requests have timed out during answer generation. This indicates that
the gateway can work for small prompts but does not establish that
full-context generation is reliable. Use Logfire to compare
prompt/context size, generation duration and failures; inspect LiteLLM
logs after a failure. Avoid claiming that timeout behavior has been
permanently fixed until repeated full-pipeline tests pass.

## 8. Observability

Logfire is used to instrument key boundaries so slow stages and
exceptions can be traced through the pipeline.

Areas instrumented or discussed include:

-   API startup, health checks and `/ask` requests.
-   RAG pipeline execution.
-   Retrieval orchestration, fusion, deduplication and context assembly.
-   Answer generation, LLM completion and citation validation.
-   Evaluation runs and selected security checks.
-   LLM request diagnostics such as model alias, elapsed time, finish
    reason, token usage when returned, prompt/context character counts
    and errors.

Useful generation measurements:

-   `context_chars` and `evidence_count`
-   `system_chars` and `user_chars`
-   LLM completion elapsed time
-   answer length and finish reason
-   exception type and request latency

Never log secrets, authorization headers, or the contents of `.env`.
Treat user questions and retrieved documents as potentially sensitive
data when configuring telemetry retention.

## 9. Retrieval quality and evaluation

The project includes evaluation runners and generated JSON reports. The
latest reported evaluation snapshot included a three-case generation
test with all three cases completed, required facts satisfied, and valid
citations. This is a small smoke-test result, not a claim of broad
benchmark performance.

Previously reported retrieval baseline (use as a historical snapshot,
not a live guarantee):

  Metric     Dense retrieval   Dense + MiniLM reranking
  -------- ----------------- --------------------------
  Hit@1                  48%                        55%
  Hit@3                  73%                        82%
  Hit@5                  82%                        92%
  Hit@10                 93%                        95%
  Hit@20                 97%                        97%
  MRR                   0.64                       0.70
  NDCG                  0.45                       0.50

These results came from the project's earlier reported evaluation run.
Re-run the evaluation suite before publishing current quality claims.

Typical local checks used in the project:

``` powershell
uv run ruff check .
uv run pytest -q
uv run python -m evaluation.runners.pipeline --limit 3
```

Check the actual runner/module name in the repository if it has changed.

## 10. Security and reliability boundaries

-   Keep `.env`, `LITELLM_MASTER_KEY`, Qdrant credentials, and any
    provider API keys out of Git.
-   Validate request input with Pydantic and application-level checks.
-   Keep citation validation strict: generated citations should refer to
    evidence IDs that were actually supplied.
-   Treat retrieved documentation as data, not as trusted instructions
    for the model.
-   Configure guardrails and out-of-scope handling according to the
    current implementation; don't assume a guardrail is active merely
    because a dependency is installed.
-   Use generic client-facing error messages and detailed server-side
    diagnostics.
-   Avoid unlimited request concurrency on CPU-only local inference; if
    concurrent requests cause contention, add a measured concurrency
    limit at the generation boundary.
-   Keep model/proxy credentials and provider fallbacks in
    environment/configuration files, not source code.

## 11. Deployment topology

The current development/portfolio topology is:

-   FastAPI and Swagger UI run on the host.
-   LiteLLM runs in a Docker container and publishes port `4000` on
    localhost.
-   Ollama runs on the host at port `11434`, serving the local Qwen3
    model.
-   Qdrant Cloud is remote.
-   Logfire receives application telemetry.
-   The machine must remain powered on and the relevant processes must
    remain running for the locally hosted model to answer requests.

This is suitable for a low-cost portfolio demonstration where downtime
is acceptable. It is not a fully managed, always-on production
deployment.

## 12. End-to-end flow summary

``` mermaid
sequenceDiagram
    actor User
    participant API as FastAPI
    participant RAG as RAGPipeline
    participant RET as Retrieval / Qdrant
    participant CTX as Context assembly
    participant GW as LiteLLM gateway
    participant O as Ollama / Qwen3
    participant LOG as Logfire

    User->>API: POST /ask
    API->>LOG: Trace request
    API->>RAG: answer(question)
    RAG->>RET: Transform query and retrieve chunks
    RET-->>RAG: Ranked / fused evidence
    RAG->>CTX: Assemble evidence context
    CTX-->>RAG: Context + evidence metadata
    RAG->>GW: Generate grounded answer
    GW->>O: Chat completion request
    O-->>GW: Model response
    GW-->>RAG: Answer text
    RAG->>RAG: Validate citation IDs
    RAG-->>API: Answer, citations, latency
    API-->>User: JSON response
    RAG-->>LOG: Spans, timings and errors
```

## 13. Before publishing this document

Review these items against the current repository:

-   Confirm actual filenames and directory names.
-   Confirm which reranker, query transformation strategies and
    guardrails are enabled by default.
-   Confirm the active LiteLLM aliases, fallback providers and timeout
    values.
-   Confirm the current Qdrant collection name and chunk count.
-   Do not commit `.env`, API keys, local model files, virtual
    environments, or large generated artifacts.
-   Keep the Mermaid diagrams in fenced `mermaid` blocks. GitHub renders
    these diagrams directly in Markdown views.

------------------------------------------------------------------------

**Architecture pattern in one sentence:** a modular, asynchronous
FastAPI RAG service with structure-aware document ingestion, dense
vector retrieval, optional reranking and fusion, evidence-based context
assembly, a LiteLLM gateway to local Ollama/Qwen3 generation, strict
citation validation, evaluation and Logfire observability.
