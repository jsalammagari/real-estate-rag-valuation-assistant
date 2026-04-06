# Real Estate RAG Valuation Assistant

This repository contains a prototype for a custom real estate valuation RAG assistant, built for a **Google Cloud Practice Customer Engineer interview**.

## The Problem

> A large real estate customer has valuable property data trapped in siloed, unstructured PDF documents (appraisals, offering memos, lease abstracts, comparable sales). Standard RAG tools can't properly parse this messy data.

## The Solution

A custom RAG (Retrieval-Augmented Generation) system that:
1. **Ingests PDFs** from different "silos" (folders representing data sources)
2. **Cleans and normalizes** messy real estate data (dates, currencies, areas)
3. **Indexes** the cleaned content into a vector database
4. **Answers questions** grounded in the actual documents
5. **Provides citations** pointing back to exact documents and pages

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER QUESTION                                      │
│                    "What cap rate evidence exists?"                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EMBEDDING CLIENT                                    │
│                    (converts question to vector)                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          VECTOR DATABASE                                     │
│              (finds similar chunks via cosine similarity)                    │
│                         ChromaDB (local)                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RAG ENGINE                                         │
│           (assembles context + generates grounded answer)                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ANSWER + CITATIONS                                      │
│         "Based on [CONTEXT 1], cap rate is 6.1%..."                         │
│         Citations: doc_id, page_span, score                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Data Pipeline (How PDFs Become Searchable)

```
PDF Files                 INGESTION              CLEANING               CHUNKING
───────────              ──────────             ─────────              ─────────

┌──────────┐            ┌──────────┐           ┌──────────┐          ┌──────────┐
│ comp.pdf │            │ Extract  │           │ Remove   │          │ Split    │
│ memo.pdf │  ────────► │ pages +  │ ────────► │ noise +  │ ───────► │ into     │
│ lease.pdf│            │ metadata │           │ normalize│          │ chunks   │
└──────────┘            └──────────┘           └──────────┘          └──────────┘
                              │                      │                     │
                              ▼                      ▼                     ▼
                         • doc_id             • Headers removed      • 300 char chunks
                         • page_index         • Dates: 2025-03-07    • 40 char overlap
                         • silo               • Currency: $1,250,000 • chunk_id
                         • warnings           • Area: sqft           • metadata preserved


CHUNKING                  EMBEDDING              VECTOR STORE
─────────                ──────────             ─────────────

┌──────────┐            ┌──────────┐           ┌──────────┐
│ Text     │            │ Convert  │           │ Store    │
│ chunks   │  ────────► │ to       │ ────────► │ vectors  │
│ + meta   │            │ vectors  │           │ + meta   │
└──────────┘            └──────────┘           └──────────┘
                              │                      │
                              ▼                      ▼
                         [0.23, 0.87, ...]     ChromaDB
                         (12-dim for local)    (persistent)
```

---

## Tools and Technologies

### Core Stack

| Technology | Purpose | File |
|------------|---------|------|
| **Python 3.10+** | Runtime language | - |
| **pypdf** | PDF text extraction | `ingestion/pdf_ingestion.py` |
| **ChromaDB** | Vector database (local, persistent) | `vector_store/chroma_store.py` |
| **ReportLab** | Generate sample PDFs for testing | `cli/main.py`, `scripts/` |

### Project Structure

```
src/real_estate_rag/
├── ingestion/          # PDF discovery and extraction
│   └── pdf_ingestion.py
├── cleaning/           # Data normalization and deduplication
│   └── pipeline.py
├── chunking/           # Split text into retrieval-sized pieces
│   └── pipeline.py
├── embedding/          # Convert text to vectors
│   └── adapters.py
├── vector_store/       # Store and query vectors
│   ├── base.py
│   └── chroma_store.py
├── rag/                # Retrieval-augmented generation
│   ├── engine.py
│   └── llm.py
└── cli/                # Command-line interface
    └── main.py
```

---

## How Each Component Works

### 1. Ingestion (`ingestion/pdf_ingestion.py`)

**Purpose:** Extract text from PDFs with metadata

```python
# What it does:
# - Discovers all PDFs recursively in a directory
# - Extracts text page-by-page using pypdf
# - Generates stable doc_id via SHA-256 hash of file bytes
# - Infers "silo" from folder structure (comps/, leases/, etc.)
# - Flags low-text pages as potential scans

# Key output:
IngestedDocument(
    doc_id="abc123...",      # Stable hash ID
    file_path="/path/to/doc.pdf",
    silo="comps",            # From folder name
    total_pages=3,
    pages=(PageExtraction(...), ...),
    warnings=("contains_scan_suspected_pages",)
)
```

### 2. Cleaning (`cleaning/pipeline.py`)

**Purpose:** Remove noise and normalize formats

This is the **"secret sauce"** — why off-the-shelf RAG tools fail:

```python
# What it removes:
# - Repeated headers/footers ("CONFIDENTIAL REPORT" on every page)
# - Page numbers ("Page 1 of 2")
# - Near-duplicate content

# What it normalizes:
# - Dates: "3/7/2025" → "2025-03-07"
# - Currency: "$ 1,250,000" → "$1,250,000"
# - Area: "12500 SF", "sq ft" → "12500 sqft"
# - Cap rates: extracts "6.1%" as metadata
```

**Before vs After:**
```
BEFORE (raw):                          AFTER (cleaned):
─────────────                          ────────────────
CONFIDENTIAL REPORT                    NOI noted on 2025-03-07 at
NOI noted on 3/7/2025 at               $1,250,000 for 12500 sqft
$ 1,250,000 for 12500 SF
Page 1 of 2
```

### 3. Chunking (`chunking/pipeline.py`)

**Purpose:** Split cleaned text into retrieval-sized pieces

```python
# Configuration:
max_chunk_chars = 300    # Maximum chunk size
overlap_chars = 40       # Overlap between chunks (context continuity)

# What it produces:
TextChunk(
    chunk_id="def456...",    # Stable hash ID
    text="NOI noted on...",
    doc_id="abc123...",      # Links back to source
    page_span=(1, 1),        # Source page(s)
    silo="comps",
    content_type="narrative" # or "table_like"
)
```

### 4. Embedding (`embedding/adapters.py`)

**Purpose:** Convert text to numerical vectors for similarity search

**Two modes:**

| Mode | Class | Use Case |
|------|-------|----------|
| **Local (offline)** | `LocalHashEmbeddingClient` | Testing, demos, CI |
| **Remote (API)** | `RemoteHTTPEmbeddingClient` | Production (Vertex AI, OpenAI) |

```python
# Local mode (deterministic, no API):
client = LocalHashEmbeddingClient(dimensions=12)
vectors = client.embed(["What is cap rate?"])
# Returns: [[0.23, 0.87, 0.45, ...]]  (12 floats from SHA-256 hash)

# Remote mode (real semantic embeddings):
client = RemoteHTTPEmbeddingClient(
    endpoint="https://api.openai.com/v1/embeddings",
    model="text-embedding-3-small",
    api_key="sk-..."
)
```

### 5. Vector Store (`vector_store/chroma_store.py`)

**Purpose:** Store vectors and find similar ones

```python
# Store chunks:
store = ChromaVectorStore("./vector_db", "valuation_chunks")
store.upsert(chunks, vectors)

# Query:
results = store.query(
    query_vector,
    top_k=5,
    metadata_filter={"silo": "comps"}  # Optional filtering
)
# Returns chunks ranked by similarity score
```

**Storage:** Local SQLite database + binary files in `./vector_db/`

### 6. RAG Engine (`rag/engine.py`)

**Purpose:** Orchestrate retrieval + generation

```python
# Flow:
# 1. Embed the user's question
# 2. Query vector store for similar chunks
# 3. Filter by minimum score threshold
# 4. Assemble context within budget (max_context_chars)
# 5. Build grounded prompt for LLM
# 6. Generate answer (or return "insufficient evidence")
# 7. Return answer + citations
```

**Key safety features:**
- **Grounding:** LLM is instructed to use ONLY provided context
- **No-evidence handling:** Returns explicit `insufficient_evidence=True` instead of hallucinating
- **Citations:** Every answer includes source references

### 7. CLI (`cli/main.py`)

**Purpose:** User-facing commands

| Command | What It Does |
|---------|--------------|
| `re-rag create-sample-data` | Generate synthetic test PDFs |
| `re-rag ingest` | Inspect ingestion output |
| `re-rag index` | Full pipeline: ingest → clean → chunk → embed → store |
| `re-rag ask` | Query the indexed data |

---

## Why This Architecture?

### The Problem with Standard RAG Tools

Standard tools (LangChain loaders, LlamaIndex) do:
```
PDF → Extract text → Chunk → Embed → Store
```

But they **don't handle**:
- Repeated headers on every page ("CONFIDENTIAL")
- Inconsistent date formats (`3/7/2025` vs `2025-03-07`)
- Currency variations (`$ 1,250,000` vs `$1.25M`)
- Near-duplicate paragraphs
- Low-quality/scanned pages

This creates **noisy retrieval** — the vector search returns irrelevant chunks.

### This Solution

```
PDF → Extract → CUSTOM CLEANING → Chunk → Embed → Store
              ─────────────────
              (The differentiator)
```

The custom cleaning pipeline:
1. Removes noise before it enters the index
2. Normalizes formats for consistent matching
3. Deduplicates repetitive content
4. Preserves provenance for citations

---

## Quick Start

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Demo in 3 Commands

```bash
# 1. Generate sample data (50 PDFs)
python scripts/generate_50_samples.py

# 2. Index the documents
re-rag index --input-dir ./sample_data_50 \
  --vector-db-path ./vector_db_50 \
  --collection valuation_50 \
  --embedding-provider local \
  --embedding-dimensions 12

# 3. Ask questions
re-rag ask --question "What cap rate evidence exists?" \
  --vector-db-path ./vector_db_50 \
  --collection valuation_50 \
  --embedding-provider local \
  --embedding-dimensions 12 \
  --llm-provider stub \
  --top-k 5
```

**All offline, no API keys needed.**

### Query with Silo Filtering

```bash
# Only search lease documents
re-rag ask --question "Show me lease terms" \
  --silo leases \
  --vector-db-path ./vector_db_50 \
  --collection valuation_50 \
  --embedding-provider local \
  --embedding-dimensions 12 \
  --llm-provider stub \
  --top-k 5
```

---

## Interview Context

This prototype demonstrates:

| Assessment Criteria | How It's Demonstrated |
|--------------------|----------------------|
| **Domain-specific technical acumen** | Real estate cleaning logic (cap rates, NOI, dates) |
| **Hands-on keyboard skills** | Live CLI demo |
| **Identifying customer solutions** | Custom pipeline solves "data trapped in silos" |
| **Conveying business value** | Auditable citations, reduced manual processing |
| **Handling questions** | Architecture docs, trade-off decisions |

---

## Implemented Scope

### Story 1-8 (Complete)

- **Story 1:** Installable package layout, placeholder CLI, environment hygiene
- **Story 2:** PDF ingestion with page-level extraction metadata
- **Story 3:** Custom cleaning and normalization pipeline
- **Story 4:** Page-aware chunking and embedding adapters
- **Story 5:** Persistent vector indexing and metadata-filtered retrieval
- **Story 6:** RAG orchestration with grounding, citations, and safe no-evidence behavior
- **Story 7:** Demo-ready CLI surface and runbook
- **Story 8:** Test hardening, automation commands, and CI smoke checks

---

## API Reference

### Ingestion API

```python
from pathlib import Path
from real_estate_rag.ingestion import ingest_pdf_directory

docs = ingest_pdf_directory(Path("./sample_data"), low_text_threshold=25)
for doc in docs:
    print(doc.doc_id, doc.silo, doc.total_pages, doc.warnings)
```

### Cleaning API

```python
from real_estate_rag.cleaning import CleaningConfig, clean_documents
from real_estate_rag.ingestion import ingest_pdf_directory

docs = ingest_pdf_directory("./sample_data")
segments = clean_documents(docs, CleaningConfig(min_text_length=20))
for segment in segments:
    print(segment.doc_id, segment.page_span, segment.silo, segment.content_type)
```

### Chunking API

```python
from real_estate_rag.chunking import ChunkingConfig, chunk_segments

chunks = chunk_segments(
    segments,
    ChunkingConfig(max_chunk_chars=300, overlap_chars=40),
)
```

### RAG API

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

---

## Running Tests

```bash
# Lint
make lint

# Unit tests (fast, offline)
make test

# End-to-end tests
make test-e2e

# All checks (lint + test + e2e)
make ci
```

---

## Documentation

- `docs/ARCHITECTURE.md` - End-to-end architecture, data flow, and decision log
- `docs/ROADMAP.md` - Prototype-to-production plan with GCP-forward options
- `docs/COMPLIANCE.md` - Confidentiality/data handling dos and don'ts
- `docs/DEMO.md` - Demo script and screen-share-safe runbook
- `docs/FAQ.md` - Short technical Q&A primer for likely reviewer questions
- `CONTRIBUTING.md` - Test/lint/CI commands and marker policy
- `DESIGN.md` - Design decisions and architecture baseline

---

## Embedding Provider Configuration

### Local (Offline - Default)

```bash
--embedding-provider local --embedding-dimensions 12
```

No API keys needed. Uses deterministic hash-based vectors.

### Remote (Production)

```bash
export EMBEDDING_PROVIDER=remote_http
export EMBEDDING_API_BASE_URL=https://api.openai.com/v1/embeddings
export EMBEDDING_MODEL=text-embedding-3-small
export EMBEDDING_API_KEY=sk-...

re-rag index --embedding-provider remote_http ...
```

---

## LLM Provider Configuration

### Stub (Offline - Default)

```bash
--llm-provider stub
```

Returns static response. No API keys needed.

### Remote (Production)

```bash
export LLM_PROVIDER=remote_http
export LLM_API_BASE_URL=https://api.openai.com/v1/chat/completions
export LLM_MODEL=gpt-4
export LLM_API_KEY=sk-...

re-rag ask --llm-provider remote_http ...
```

---

## License

This is an educational prototype for interview demonstration purposes.