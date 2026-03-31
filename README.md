# Real Estate RAG Valuation Assistant

This repository contains a fictional, non-confidential prototype for a custom
real estate valuation RAG assistant. The current implementation includes Story
1 foundations and Story 2 PDF ingestion with page-level extraction metadata.

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

## Basic Checks

```bash
pytest
```

## Design and Architecture Docs

- `DESIGN.md` - design decisions and architecture baseline updated through Story 2
- `docs/ARCHITECTURE.md` - architecture notes and ingestion contract

## Next Stories

- Story 3: custom cleaning and normalization pipeline
- Story 4+: chunking, embeddings, vector DB, RAG orchestration, demo
