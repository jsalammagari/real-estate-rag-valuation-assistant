# Real Estate RAG Valuation Assistant

This repository contains a fictional, non-confidential prototype for a custom
real estate valuation RAG assistant. The current implementation includes:
- Story 1 foundations
- Story 2 PDF ingestion with page-level extraction metadata
- Story 3 custom cleaning and normalization pipeline
- Story 4 page-aware chunking and embedding adapters
- Story 5 persistent vector indexing and metadata-filtered retrieval
- Story 6 RAG orchestration with grounding, citations, and safe no-evidence behavior
- Story 7 demo-ready CLI surface and runbook
- Story 8 test hardening, automation commands, and CI smoke checks

## Implemented Scope

### Story 1 (foundation)
- installable package layout
- placeholder CLI entrypoint
- environment and git hygiene
- architecture and technical decisions stub

### Story 2 (ingestion)
- recursive PDF discovery from a configured input directory
- stable SHA-256 `doc_id` generation from file bytes
- page-level extraction with 1-based page index and per-page text
- inferred `silo` metadata from top-level folder under input root
- machine-readable warnings for low-text or empty pages

### Story 3 (cleaning and normalization)
- repeated header/footer and page-number suppression (best effort)
- conservative normalization for currency/date/square-foot unit variants
- content typing heuristic (`narrative` vs `table_like`)
- quality gates (minimum text length) and near-duplicate suppression
- stable `CleanSegment` output contract for Story 4 chunking

### Story 4 (chunking and embedding)
- deterministic character-based chunking with configurable overlap
- stable chunk IDs derived from source metadata and chunk text
- full metadata inheritance from `CleanSegment` to each chunk
- pluggable embedding adapter interface with:
  - local deterministic hash-based embeddings (default for CI/tests)
  - optional `remote_http` adapter guarded by env configuration

### Story 5 (vector store)
- `VectorStore` abstraction for `upsert`, `clear`, and `query`
- persistent local Chroma backend (`ChromaVectorStore`)
- idempotent upsert behavior keyed by deterministic `chunk_id`
- metadata-filtered similarity search (`silo`, `doc_id`, etc.)
- dimension consistency validation to prevent mixed vector sizes

### Story 6 (RAG orchestration)
- `RagEngine.answer(question, metadata_filter=None)` end-to-end flow
- question embedding -> vector retrieval -> context assembly -> LLM generation
- explicit citation objects (`chunk_id`, `doc_id`, `page_span`, `score`)
- safe no-evidence path with `insufficient_evidence=True`
- context budget controls (`RAG_TOP_K`, `RAG_MAX_CONTEXT_CHARS`, `RAG_MIN_SCORE`)

### Story 7 (demo surface)
- interview-ready CLI flow: `create-sample-data` -> `index` -> `ask`
- `ingest` inspection command for quick data sanity checks
- non-zero CLI exits for missing index path / empty corpus / config issues
- demo runbook in `docs/DEMO.md` with screen-share-safe guidance

### Story 8 (test hardening and automation)
- standardized pytest markers: `unit`, `integration`, `e2e`, `network`
- centralized synthetic fixture helpers in `tests/fixtures.py`
- dedicated e2e smoke coverage for CLI demo path
- task runner targets via `Makefile`: `lint`, `test`, `test-e2e`, `ci`
- CI workflow at `.github/workflows/ci.yml` aligned with local commands

## Technical Decisions (Phase 0)

- **Language/runtime:** Python 3.10+
- **Dependency manager/build backend:** `pyproject.toml` with `setuptools`
- **PDF stack (planned for Story 2+):** `pymupdf` (primary), optional OCR
  fallback interface for scan-heavy pages
- **Embedding strategy (planned):** pluggable adapter with local stub/default
  and optional remote provider via env config
- **LLM strategy (planned):** pluggable adapter with local stub/default and
  optional remote provider via env config
- **Dev vector DB strategy (planned):** local-first provider for fast
  prototyping; production-target mapping will be documented in `docs/ROADMAP.md`

## Project Layout

```text
src/real_estate_rag/
  ingestion/
  cleaning/
  chunking/
  embedding/
  vector_store/
  rag/
  cli/
docs/
tests/
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## CLI Commands

```bash
re-rag --help
re-rag --version
re-rag ingest --help
re-rag index --help
re-rag ask --help
```

## Ingestion API (Story 2)

```python
from pathlib import Path
from real_estate_rag.ingestion import ingest_pdf_directory

docs = ingest_pdf_directory(Path("./sample_data"), low_text_threshold=25)
for doc in docs:
    print(doc.doc_id, doc.silo, doc.total_pages, doc.warnings)
    for page in doc.pages:
        print(page.page_index, page.char_count, page.scan_suspected)
```

### Ingestion Output Contract

- `IngestedDocument.doc_id`: stable SHA-256 hash of file bytes
- `IngestedDocument.file_path`: absolute file path
- `IngestedDocument.relative_path`: path relative to input root
- `IngestedDocument.silo`: top-level subfolder under input root (`default` if none)
- `IngestedDocument.total_pages`: extracted page count
- `PageExtraction.page_index`: 1-based page index
- `PageExtraction.text`: raw extracted page text (no cleaning in Story 2)
- `PageExtraction.scan_suspected`: `True` for low-text pages (routing signal for OCR in later stories)

## Cleaning API (Story 3)

```python
from real_estate_rag.cleaning import CleaningConfig, clean_documents
from real_estate_rag.ingestion import ingest_pdf_directory

docs = ingest_pdf_directory("./sample_data")
segments = clean_documents(docs, CleaningConfig(min_text_length=20))
for segment in segments:
    print(segment.doc_id, segment.page_span, segment.silo, segment.content_type)
```

### CleanSegment Output Contract

- `text`: cleaned and normalized segment text
- `doc_id`: source document id from ingestion
- `page_span`: inclusive source page range (Story 3 uses single-page spans)
- `silo`: source silo label from ingestion
- `content_type`: heuristic label (`narrative` or `table_like`)
- `normalized_fields`: extracted normalized hints (e.g., `date_example`, `currency_example`, `cap_rate`)
- `warnings`: combined stage + source warnings

## Chunking API (Story 4)

```python
from real_estate_rag.chunking import ChunkingConfig, chunk_segments

chunks = chunk_segments(
    segments,
    ChunkingConfig(max_chunk_chars=300, overlap_chars=40),
)
```

### TextChunk Output Contract

- `chunk_id`: deterministic SHA-256 id
- `text`: retrieval-sized chunk text
- `doc_id`, `page_span`, `silo`: source traceability fields
- `content_type`, `normalized_fields`: inherited content hints
- `source_warnings`: inherited warnings from cleaned source
- `chunk_index`, `total_chunks_for_segment`: position metadata

### Chunking defaults

- `max_chunk_chars=300`
- `overlap_chars=40`
- Character-based splitting for deterministic, model-agnostic behavior

## Embedding Adapter API (Story 4)

```python
from real_estate_rag.embedding import create_embedding_client_from_env

client = create_embedding_client_from_env(provider="local", dimensions=12)
vectors = client.embed([chunk.text for chunk in chunks])
```

### Embedding provider switch

- Local deterministic path (no secrets, default for tests):
  - `EMBEDDING_PROVIDER=local`
  - `EMBEDDING_DIMENSIONS=12`
- Optional remote HTTP path (when integrated with a provider endpoint):
  - `EMBEDDING_PROVIDER=remote_http`
  - `EMBEDDING_API_BASE_URL=<provider-endpoint>`
  - `EMBEDDING_MODEL=<model-name>`
  - `EMBEDDING_API_KEY=<secret>`

Remote configuration values must stay in local `.env` and never be committed.

## Vector Store API (Story 5)

```python
from real_estate_rag.vector_store import ChromaVectorStore

store = ChromaVectorStore("./vector_db", "valuation_chunks")
store.upsert(chunks, vectors)
hits = store.query(query_vector, top_k=3, metadata_filter={"silo": "comps"})
```

### Persistence behavior

`ChromaVectorStore` uses a persistent on-disk path (`VECTOR_DB_PATH`) so indexed
vectors remain available across process restarts when the same path and
collection name are reused.

### Minimal CLI hook (Story 5)

```bash
re-rag index-local --input-dir ./sample_data --vector-db-path ./vector_db --collection valuation_chunks
re-rag query-local --question "cap rate for downtown office" --vector-db-path ./vector_db --collection valuation_chunks --top-k 3
```

Optional metadata filter:

```bash
re-rag query-local --question "lease activity" --silo offering_memo --top-k 3
```

## RAG API (Story 6)

```python
from real_estate_rag.embedding import LocalHashEmbeddingClient
from real_estate_rag.rag import RagConfig, RagEngine, StubLlmClient
from real_estate_rag.vector_store import ChromaVectorStore

engine = RagEngine(
    embedding_client=LocalHashEmbeddingClient(dimensions=12),
    vector_store=ChromaVectorStore("./vector_db", "valuation_chunks"),
    llm_client=StubLlmClient(),
    config=RagConfig(top_k=4, max_context_chars=1400, min_score=0.0),
)
response = engine.answer("What cap rate evidence exists?", metadata_filter={"silo": "comps"})
```

### Citation format

Each `Citation` returned in `RagResponse.citations` includes:
- `chunk_id`
- `doc_id`
- `page_span` `(start_page, end_page)`
- `score`

This keeps answers auditable for technical stakeholders and allows business
stakeholders to trust that statements are grounded in indexed evidence.

### Trust boundaries and safety behavior

- RAG prompts instruct the model to use only provided snippets.
- If retrieval returns no usable evidence (or everything is below `RAG_MIN_SCORE`),
  `RagEngine` returns an explicit safe response with
  `insufficient_evidence=True` and no citations.
- Story 6 does not claim valuation certainty without supporting context.

## Demo in 3 Commands (Story 7)

```bash
re-rag create-sample-data --output-dir ./sample_data
re-rag index --input-dir ./sample_data --vector-db-path ./vector_db --collection valuation_chunks --embedding-provider local --embedding-dimensions 12
re-rag ask --question "What cap rate evidence exists?" --vector-db-path ./vector_db --collection valuation_chunks --embedding-provider local --embedding-dimensions 12 --llm-provider stub --top-k 3
```

See `docs/DEMO.md` for timing script, expected output format, fallback mode, and
screen-share hygiene.

### Why not off-the-shelf load-and-chunk only?

This corpus includes repeated report banners, page markers, short noisy pages,
and formatting inconsistency (`$ 1,250,000`, `3/7/2025`, `12500 SF`). A
chunk-only approach would index these artifacts as-is, increasing retrieval
noise. Story 3 removes repetitive boilerplate, normalizes conservative patterns,
and suppresses near duplicates before chunking so downstream retrieval quality
is more stable.

### Before vs After (synthetic example)

**Before (raw page text):**
```text
CONFIDENTIAL REPORT
NOI noted on 3/7/2025 at $ 1,250,000 for 12500 SF
Page 1 of 2
```

**After (clean segment text):**
```text
NOI noted on 2025-03-07 at $1,250,000 for 12500 sqft
```

## Basic Checks

```bash
make lint
make test
make test-e2e
make ci
```

## Test and CI Notes

- Default suite (`make test`) is offline and excludes `e2e` and `network` markers.
- E2E smoke (`make test-e2e`) validates `create-sample-data -> index -> ask` path.
- Network-marked tests are opt-in and skipped by default in CI.
- CI workflow runs lint + default suite + e2e smoke on push/PR.

## Design and Architecture Docs

- `DESIGN.md` - design decisions and architecture baseline updated through Story 7
- `docs/ARCHITECTURE.md` - architecture contracts through Story 8
- `docs/DEMO.md` - demo script and runbook for Story 7
- `CONTRIBUTING.md` - contributor commands, marker policy, and failure guidance

## Next Stories

- Story 9+: documentation deepening, presentation package, and readiness rehearsals
