# Real Estate RAG Valuation Assistant

This repository contains a fictional, non-confidential prototype scaffold for a
custom real estate valuation RAG assistant. It is intentionally structured for
incremental delivery of ingestion, cleaning, vector retrieval, and grounded
answer generation in later stories.

## Story 1 Scope

Story 1 only bootstraps project foundations:
- installable package layout
- placeholder CLI entrypoint
- environment and git hygiene
- architecture and technical decisions stub

No PDF extraction, cleaning, indexing, or RAG logic is implemented yet.

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

## CLI (placeholder)

```bash
re-rag --help
re-rag --version
```

## Basic Checks

```bash
pytest
```

## Design and Architecture Docs

- `DESIGN.md` - Story 1 design decisions and target architecture
- `docs/ARCHITECTURE.md` - architecture planning stub for upcoming stories

## Next Stories

- Story 2: PDF ingestion and page-level extraction
- Story 3: custom cleaning and normalization pipeline
- Story 4+: chunking, embeddings, vector DB, RAG orchestration, demo
