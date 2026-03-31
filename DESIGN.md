# Design Decisions and Project Architecture (Stories 1-2)

This document captures baseline design decisions and the Story 2 ingestion
implementation contract.

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
