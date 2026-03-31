# Design Decisions and Project Architecture (Stories 1-7)

This document captures baseline design decisions and the implemented contracts
through Story 7.

## Story 1 Objectives

- Provide an installable, versioned Python package.
- Create a package layout that cleanly maps to planned RAG pipeline stages.
- Add a placeholder CLI entrypoint for future operator workflows.
- Set git and environment hygiene to prevent secrets/cached artifacts in source.
- Record technical decisions so Story 2+ can implement consistently.

## Story 2 Objectives

- Discover PDFs recursively from configured input directories.
- Extract page-level text with strict page boundaries.
- Emit stable `doc_id` and provenance metadata for downstream stages.
- Flag low-text pages via machine-readable warnings for future OCR routing.

## Story 3 Objectives

- Convert raw page text into cleaner, deduplicated, metadata-rich segments.
- Apply conservative normalization for valuation-relevant formats.
- Preserve source traceability (`doc_id`, `page_span`, `silo`, warnings).
- Produce deterministic `CleanSegment` output contract for Story 4 chunking.

## Story 4 Objectives

- Convert cleaned segments into deterministic retrieval-sized chunks.
- Preserve full source metadata per chunk for downstream traceability.
- Add overlap-aware chunk boundaries to reduce context loss at splits.
- Provide pluggable embedding adapters with local CI-safe default.

## Story 5 Objectives

- Persist chunk embeddings in a real local vector database.
- Support top-k similarity search with optional metadata filters.
- Guarantee idempotent re-index behavior via stable chunk identity.
- Keep integration testable with local ephemeral paths and no secrets.

## Story 6 Objectives

- Implement retrieval-augmented generation orchestration end-to-end.
- Enforce grounded answer generation with explicit citation outputs.
- Provide safe no-evidence behavior for valuation-risk scenarios.
- Keep default test path offline with deterministic embedding + stub LLM.

## Story 7 Objectives

- Expose a stable CLI demo path for ingest -> index -> ask.
- Ensure deterministic stub-mode rehearsal without paid APIs.
- Provide concise demo runbook with screen-share-safe instructions.
- Return explicit non-zero CLI exits for common operator errors.

## Design Decisions

### 1) Language and runtime

- **Decision:** Python 3.10+
- **Why:** Fast iteration for data pipelines and strong ecosystem for PDF, NLP,
  vector indexing, and prototyping.

### 2) Packaging and dependency management

- **Decision:** `pyproject.toml` with `setuptools` build backend.
- **Why:** Standards-based packaging with editable install support and minimal
  bootstrap complexity for early-stage prototype work.

### 3) CLI strategy

- **Decision:** Expose a single installable command `re-rag`.
- **Why:** Gives one stable operator surface from day one and avoids ad hoc
  scripts; future stories add subcommands for ingest/index/query.

### 4) Module boundaries

- **Decision:** Use `src/real_estate_rag/` with dedicated packages:
  `ingestion`, `cleaning`, `chunking`, `embedding`, `vector_store`, `rag`,
  `cli`.
- **Why:** Keeps concerns isolated and traceable to assignment deliverables:
  custom ingestion/cleaning pipeline + vector DB + RAG orchestration.

### 5) Provider abstraction direction

- **Decision:** Plan pluggable adapters for embeddings, LLM, and vector DB.
- **Why:** Enables local/stub development without API keys and allows later
  switch to managed cloud providers without rewriting pipeline logic.

### 6) Data and confidentiality posture

- **Decision:** Use synthetic/publicly shareable sample inputs only.
- **Why:** Meets assignment confidentiality constraints and keeps repo safe for
  interview sharing.

### 7) Stable document identity

- **Decision:** Use SHA-256 hash of file bytes for `doc_id`.
- **Why:** Deterministic identity across repeated ingestions supports idempotent
  indexing in later stories.

### 8) Page indexing convention

- **Decision:** Use 1-based page indexing in extraction output.
- **Why:** Aligns with how users reference page numbers in documents and demos.

### 9) Cleaning strategy

- **Decision:** Use deterministic, pure-function pipeline stages.
- **Why:** Ensures reproducible output and unit-testability without external
  services, APIs, embeddings, or model dependencies.

### 10) Normalization policy

- **Decision:** Normalize only conservative, low-risk patterns (currency spacing,
  date formats, area-unit variants, cap-rate hint extraction).
- **Why:** Improves retrieval consistency while avoiding semantic invention.

### 11) Dedupe policy

- **Decision:** Suppress near-duplicate segments within a document using token
  similarity threshold.
- **Why:** Reduces index noise and redundant retrieval context for later stages.

### 12) Chunking strategy

- **Decision:** Use deterministic character-based splitting with overlap.
- **Why:** Predictable behavior across environments and model-agnostic control
  over chunk size before introducing tokenizer-coupled behavior.

### 13) Chunk identity strategy

- **Decision:** Build `chunk_id` as SHA-256 over source metadata + chunk index
  + chunk text.
- **Why:** Stable IDs improve idempotent indexing and traceability in later
  vector-store stories.

### 14) Embedding abstraction strategy

- **Decision:** Introduce `EmbeddingClient` interface with local deterministic
  adapter plus optional remote HTTP adapter.
- **Why:** Keeps Story 4 testable without secrets/network while preserving a
  path to cloud provider integration.

### 15) Vector database backend choice

- **Decision:** Use persistent local Chroma for Story 5.
- **Why:** Real vector indexing/retrieval with durable on-disk persistence and
  straightforward local setup suitable for interview prototype constraints.

### 16) Index idempotency policy

- **Decision:** Upsert vectors by deterministic `chunk_id`.
- **Why:** Re-running index pipelines updates existing points instead of creating
  duplicate records.

### 17) Query filtering policy

- **Decision:** Support metadata equality filters (`silo`, `doc_id`, etc.) in
  vector query path.
- **Why:** Enables scoped retrieval over siloed corpora and improves precision.

### 18) Citation contract strategy

- **Decision:** Return structured citation objects from retrieval metadata
  (`chunk_id`, `doc_id`, `page_span`, `score`) rather than free-form citation
  text only.
- **Why:** Keeps outputs machine-parseable and auditable for technical review.

### 19) No-evidence safety policy

- **Decision:** If no qualifying retrieval context exists, skip LLM generation
  and return explicit `insufficient_evidence=True` with a safe message.
- **Why:** Reduces hallucination risk in valuation-oriented usage.

### 20) Context budget policy

- **Decision:** Rank-ordered chunk inclusion under a character budget with
  top-hit trimming fallback.
- **Why:** Deterministic and simple context control before advanced reranking.

### 21) Demo UX strategy

- **Decision:** Keep a terminal-first CLI as the primary demo surface.
- **Why:** Lower operational complexity and stronger live keyboard-skill signal
  for interview scenarios.

## Planned Technical Stack (for Story 2+)

- **PDF extraction:** `pymupdf` primary path, OCR fallback interface for
  scan-heavy pages.
- **Embeddings:** Local/stub default adapter with optional remote provider via
  env config.
- **LLM generation:** Stub default adapter with optional remote provider via
  env config.
- **Vector database (dev):** Local-first vector store for fast iteration.
- **Vector database (production target):** To be finalized in roadmap docs in
  later stories.

## Architecture (Target State)

```text
PDF Sources
   |
   v
Ingestion (extract pages + metadata)
   |
   v
Custom Cleaning (normalize + quality gates)
   |
   v
Chunking (overlap + traceable provenance)
   |
   v
Embedding Adapter
   |
   v
Vector Store (index + retrieve)
   |
   v
RAG Orchestration (retrieve context + grounded response + citations)
   |
   v
CLI / Demo Surface
```

## Current Story 1 Implementation Status

Implemented in Story 1:
- Package scaffold and module layout
- Placeholder CLI (`re-rag --help`, `re-rag --version`)
- `.gitignore` and `.env.example` hygiene
- Initial docs scaffold (`README.md`, `docs/ARCHITECTURE.md`, this file)
- Basic smoke test setup with `pytest`

Out of scope for Story 1:
- PDF parsing, cleaning, chunking, embeddings, vector indexing, RAG responses

## Story 2 Implementation Status

Implemented in Story 2:
- `discover_pdf_files`: recursive, deterministic PDF discovery
- `extract_pdf_document`: page-level extraction with warning signals
- `ingest_pdf_directory`: directory-level ingestion orchestration
- dataclass output contracts: `IngestedDocument`, `PageExtraction`
- tests for discovery, silo inference, page boundaries, stable `doc_id`, and
  low-text scan suspicion behavior

Out of scope in Story 2:
- OCR execution, cleaning, normalization, deduplication, chunking, embeddings,
  vector DB integration, and response generation

## Story 3 Implementation Status

Implemented in Story 3:
- `CleanSegment` and `CleaningConfig` contracts
- deterministic cleaning stage pipeline
- repeated header/footer and page-number suppression
- conservative normalization for currency/date/area units and cap-rate hint
- content-type heuristic (`narrative` vs `table_like`)
- quality gate for short/noisy text and near-duplicate suppression
- warning propagation from ingestion to cleaned segments
- unit tests for noise handling, normalization, quality gates, dedupe, and
  metadata/warning passthrough

Out of scope in Story 3:
- chunking overlap policies, embeddings, vector index integration, retrieval,
  and generation

## Story 4 Implementation Status

Implemented in Story 4:
- `TextChunk` and `ChunkingConfig` contracts
- deterministic, overlap-aware chunking pipeline (`chunk_segments`)
- stable chunk id generation
- metadata inheritance from `CleanSegment` to every chunk
- embedding adapter interface (`EmbeddingClient`)
- local deterministic hash embedding adapter for CI/tests
- optional remote HTTP embedding adapter guarded by runtime config
- unit tests for chunk boundaries, overlap, determinism, metadata carryover,
  and embedding shape/determinism

Out of scope in Story 4:
- vector DB indexing/retrieval, ranking, and LLM generation

## Story 5 Implementation Status

Implemented in Story 5:
- `VectorStore` abstraction (`upsert`, `clear`, `query`)
- `ChromaVectorStore` persistent backend
- dimension validation guard for embedding mismatch
- metadata persistence and filter-based retrieval support
- integration tests for persistence, filter narrowing, idempotent upsert, and
  embedding alignment
- minimal CLI hooks:
  - `re-rag index-local`
  - `re-rag query-local`

Out of scope in Story 5:
- hybrid retrieval ranking and RAG answer generation

## Story 6 Implementation Status

Implemented in Story 6:
- `RagEngine`, `RagConfig`, `RagResponse`, `Citation`
- LLM adapter interface with `StubLlmClient` and optional `RemoteHTTPLlmClient`
- grounded prompt construction including context metadata and snippet text
- context budgeting and minimum score filtering
- explicit no-evidence refusal path with `insufficient_evidence` flag
- unit tests validating grounding, citation linkage, filter passthrough, and
  no-evidence safety behavior

Out of scope in Story 6:
- production auth/rate limiting/caching/streaming and UI polish

## Story 7 Implementation Status

Implemented in Story 7:
- CLI subcommands: `create-sample-data`, `ingest`, `index`, `ask`
- alias compatibility for legacy commands (`index-local`, `query-local`)
- formatted answer + citation output in `ask`
- non-zero error exits for missing index path, empty collections, and invalid
  input conditions
- demo runbook (`docs/DEMO.md`) with 3-command flow and screen-share hygiene
- CLI smoke tests for subcommand discovery, end-to-end stub run, and error path

Out of scope in Story 7:
- web UI polishing, authentication, analytics, and deployment manifests
