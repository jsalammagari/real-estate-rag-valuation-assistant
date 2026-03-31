# Architecture (Stories 1-2)

This document records baseline design and implemented contracts through Story 8.
Downstream stories (presentation hardening and production concerns) extend this
architecture.

## Planned Pipeline

1. PDF ingestion from siloed document folders
2. Custom cleaning and normalization pipeline
3. Chunking and metadata enrichment
4. Embedding generation
5. Vector index upsert and retrieval
6. RAG response generation with citations

## Modules

- `real_estate_rag.ingestion`: PDF discovery and page-level extraction
- `real_estate_rag.cleaning`: text normalization and quality gating
- `real_estate_rag.chunking`: chunk creation and overlap strategy
- `real_estate_rag.embedding`: embedding provider adapters
- `real_estate_rag.vector_store`: vector index and retrieval adapters
- `real_estate_rag.rag`: retrieval-to-generation orchestration
- `real_estate_rag.cli`: operator entrypoints for indexing and querying

## Story 2 Ingestion Contract

Story 2 intentionally implements ingestion only. No cleaning/chunking or RAG
logic runs at this stage.

### Document schema

- `doc_id`: SHA-256 hash of raw file bytes (stable across repeated ingestions)
- `file_path`: absolute source path
- `relative_path`: source path relative to ingestion root
- `file_name`: basename of source file
- `silo`: inferred from top-level folder beneath root (or `default`)
- `total_pages`: number of pages in the PDF
- `warnings`: document-level warning codes

### Page schema

- `page_index`: 1-based page number
- `text`: raw extracted text for only that page
- `char_count`: extracted character count
- `scan_suspected`: low-text routing signal for OCR path in later stories
- `warnings`: page-level warning codes (e.g., `empty_page_text`,
  `low_text_scan_suspected`)

### Discovery behavior

- Discovery is recursive under the configured input directory using `*.pdf`.
- Files are returned in sorted order for deterministic processing.
- Silo simulation is driven by folder layout (example: `comps/`, `offering_memo/`).

### Known limits (by design in Story 2)

- No OCR execution in Story 2 (only machine-readable scan suspicion flags).
- No normalization or deduplication yet; raw text is intentionally preserved.
- No table reconstruction or layout repair yet.

## Story 3 Cleaning Contract

Story 3 consumes `IngestedDocument` records from Story 2 and outputs deterministic
`CleanSegment` records for chunking in Story 4.

### Pipeline stage order

1. Build repeated edge-line frequency map (header/footer candidates)
2. Remove repeated edge lines and page-number-only lines
3. Normalize conservative patterns (currency, date, area units, cap-rate hint)
4. Infer coarse content type (`narrative` vs `table_like`) via heuristic cues
5. Apply quality gates (min length) and near-duplicate suppression
6. Emit `CleanSegment` with source metadata and warnings

### CleanSegment schema

- `text`: cleaned normalized text
- `doc_id`: source document id
- `page_span`: inclusive page range tuple
- `silo`: source silo
- `content_type`: `narrative` or `table_like`
- `normalized_fields`: normalized hints dictionary
- `warnings`: combined warnings from source + cleaning stages

### Determinism guarantee

Given the same input extraction payload and config, the cleaner returns the same
ordered output segments. No randomness is used in v1.

### Why this custom path (instead of chunk-only ingestion)

Standard load-and-chunk indexing preserves repeated report banners, page number
lines, noisy short fragments, and inconsistent numeric/date/area formatting.
These artifacts dilute retrieval quality. Story 3 addresses this with targeted
noise suppression, conservative normalization, and dedupe before chunking.

## Story 4 Chunking and Embedding Contract

Story 4 converts `CleanSegment` outputs into deterministic, overlapping chunks
and provides pluggable embedding adapters.

### Chunking rules

- Character-based chunking with config:
  - `max_chunk_chars` (default: 300)
  - `overlap_chars` (default: 40)
- Deterministic boundaries and ordering for same input/config.
- No cross-segment merging in v1 (each segment chunked independently).
- Stable `chunk_id` derived from source metadata + chunk index + chunk text.

### TextChunk schema

- `chunk_id`
- `text`
- `doc_id`
- `page_span`
- `silo`
- `content_type`
- `normalized_fields`
- `source_warnings`
- `chunk_index`
- `total_chunks_for_segment`

### Citation granularity implication

Chunk boundaries set the granularity of future citations in Story 6. Smaller
chunks improve pinpoint traceability but may reduce contextual recall; overlap
mitigates boundary loss.

### Embedding adapter contract

- Interface: `embed(texts: list[str]) -> list[list[float]]`
- Local adapter (`LocalHashEmbeddingClient`): deterministic pseudo-vectors for
  CI and offline tests.
- Optional remote adapter (`RemoteHTTPEmbeddingClient`): HTTP POST to configured
  endpoint with model and API key from environment variables.

### Isolation boundary

Story 4 does not import or depend on vector DB, retrieval ranking, or LLM code.

## Story 5 Vector Index and Retrieval Contract

Story 5 introduces persistent vector indexing and similarity retrieval using a
local Chroma backend through a `VectorStore` abstraction.

### Vector store interface

- `upsert(chunks, embeddings)`: batch write/update vectors keyed by `chunk_id`
- `clear()`: reset collection for test isolation
- `query(vector, top_k, metadata_filter=None)`: nearest-neighbor retrieval with
  optional metadata filtering

### Backend choice

- Implemented backend: `ChromaVectorStore`
- Persistence: on-disk path (`VECTOR_DB_PATH`) reused across process restarts
- Collection configuration: `VECTOR_DB_COLLECTION`

### Idempotent indexing behavior

Upsert uses deterministic `chunk_id`; re-indexing the same chunks updates
existing points instead of creating unbounded duplicates.

### Metadata filters

Each vector point stores filterable metadata such as:
- `doc_id`
- `silo`
- `page_start`, `page_end`
- `content_type`
- derived normalized hints (`norm_*`)

### Dimension consistency guard

Incoming embeddings are validated for internal consistency and checked against
existing collection dimension to fail fast on mismatches.

### Scope limits

- No hybrid BM25 logic in Story 5 (deferred to later story if needed).
- No RAG prompt or LLM response generation yet (Story 6).

## Story 6 RAG Orchestration Contract

Story 6 adds the retrieval-to-generation path with explicit grounding and
citations.

### Core function

- `RagEngine.answer(question, metadata_filter=None) -> RagResponse`
- Returns:
  - `answer_text`
  - `citations` (`chunk_id`, `doc_id`, `page_span`, `score`)
  - `insufficient_evidence` flag
  - optional `raw_retrieved_chunks`

### Prompting and grounding

- Question is embedded using the active embedding adapter.
- Vector store returns top-k chunks with optional metadata filters.
- Prompt context includes:
  - context id
  - `chunk_id`
  - `doc_id`
  - `page_span`
  - snippet text
- Prompt instructs model to use only supplied snippets and avoid fabrication.

### Context budget algorithm

- Retrieval hits are processed in rank order.
- Chunks are included while cumulative characters stay <= `max_context_chars`.
- If top hit alone exceeds budget, it is trimmed and still included.
- Lower-ranked chunks are dropped when budget is exhausted.

### Safe no-evidence policy

- If retrieval yields no hits after score filtering (`min_score`), engine
  returns a safe message and sets `insufficient_evidence=True`.
- In this path, LLM generation is skipped and citations are empty.

### Scope limits

- No caching, streaming, auth, or rate-limiting in Story 6.
- No UI polish yet (Story 7).

## Story 7 Demo Surface Contract

Story 7 adds a stable operator-facing CLI for interview demos.

### Supported CLI commands

- `create-sample-data`: generate synthetic non-confidential demo PDFs
- `ingest`: run ingestion-only inspection and summary
- `index`: run ingestion -> cleaning -> chunking -> embedding -> vector upsert
- `ask`: run RAG answer path and print answer + structured citations

### Demo reliability boundaries

- Stub mode supported end-to-end (`EMBEDDING_PROVIDER=local`,
  `LLM_PROVIDER=stub`) with no paid APIs.
- `ask` returns non-zero on missing vector path, empty index, or bad config.
- Citation lines include `chunk_id`, `doc_id`, and `page_span` for auditability.

## Story 8 Test and Automation Contract

Story 8 standardizes confidence checks for local development and CI.

### Test markers

- `unit`: deterministic fast tests
- `integration`: local component integration tests
- `e2e`: end-to-end smoke tests over CLI flow
- `network`: external-network tests (opt-in only)

### Default execution policy

- Local default: `make test` (`not e2e and not network`)
- E2E smoke: `make test-e2e`
- Aggregate check: `make ci`

### CI policy

- Workflow file: `.github/workflows/ci.yml`
- Runs on push and pull_request
- Executes: install -> lint -> default tests -> e2e smoke

### Fixture strategy

Synthetic fixture builders are centralized in `tests/fixtures.py` to reduce
duplication and keep data non-confidential.

## Non-Confidentiality Rule

All example inputs must be synthetic or publicly shareable. Do not commit any
real customer names, logos, screenshots, proprietary documents, or secrets.
