# Real Estate RAG Valuation Assistant

This repository contains a fictional, non-confidential prototype for a custom
real estate valuation RAG assistant. The current implementation includes:
- Story 1 foundations
- Story 2 PDF ingestion with page-level extraction metadata
- Story 3 custom cleaning and normalization pipeline

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
pytest
```

## Design and Architecture Docs

- `DESIGN.md` - design decisions and architecture baseline updated through Story 2
- `docs/ARCHITECTURE.md` - architecture notes and ingestion contract

## Next Stories

- Story 4+: chunking, embeddings, vector DB, RAG orchestration, demo
