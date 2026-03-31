# Architecture (Story 1 Stub)

This is a planning stub that records baseline decisions before implementation.
Detailed component behavior will be expanded in later stories.

## Planned Pipeline

1. PDF ingestion from siloed document folders
2. Custom cleaning and normalization pipeline
3. Chunking and metadata enrichment
4. Embedding generation
5. Vector index upsert and retrieval
6. RAG response generation with citations

## Planned Modules

- `real_estate_rag.ingestion`: PDF discovery and extraction
- `real_estate_rag.cleaning`: text normalization and quality gating
- `real_estate_rag.chunking`: chunk creation and overlap strategy
- `real_estate_rag.embedding`: embedding provider adapters
- `real_estate_rag.vector_store`: vector index and retrieval adapters
- `real_estate_rag.rag`: retrieval-to-generation orchestration
- `real_estate_rag.cli`: operator entrypoints for indexing and querying

## Non-Confidentiality Rule

All example inputs must be synthetic or publicly shareable. Do not commit any
real customer names, logos, screenshots, proprietary documents, or secrets.
