# Architecture (Stories 1-2)

This document records the baseline design and implemented Story 2 ingestion
contract. Downstream stories (cleaning/chunking/retrieval/generation) extend
this architecture.

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

## Non-Confidentiality Rule

All example inputs must be synthetic or publicly shareable. Do not commit any
real customer names, logos, screenshots, proprietary documents, or secrets.
