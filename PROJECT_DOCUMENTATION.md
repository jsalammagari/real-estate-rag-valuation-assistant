# Real Estate RAG Valuation Assistant - Complete Technical Documentation

## Document Purpose

This document serves as a comprehensive knowledge base for the Real Estate RAG Valuation Assistant project. It contains every technical detail, design decision, implementation specification, and operational procedure. Any LLM given this document should be able to answer any question about the project accurately and completely.

---

# TABLE OF CONTENTS

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Solution Architecture](#3-solution-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Project Structure](#5-project-structure)
6. [Data Models & Contracts](#6-data-models--contracts)
7. [Component Deep-Dive](#7-component-deep-dive)
8. [Configuration & Environment](#8-configuration--environment)
9. [CLI Reference](#9-cli-reference)
10. [API Reference](#10-api-reference)
11. [Testing](#11-testing)
12. [Deployment & Operations](#12-deployment--operations)
13. [Design Decisions & Trade-offs](#13-design-decisions--trade-offs)
14. [Production Roadmap](#14-production-roadmap)
15. [Troubleshooting](#15-troubleshooting)
16. [Glossary](#16-glossary)

---

# 1. PROJECT OVERVIEW

## 1.1 What Is This Project?

The Real Estate RAG Valuation Assistant is a custom Retrieval-Augmented Generation (RAG) prototype designed to help real estate analysts query property valuation data trapped in unstructured PDF documents. It was built as a demonstration for a Google Cloud Practice Customer Engineer interview.

## 1.2 Core Capabilities

1. **PDF Ingestion**: Recursively discovers and extracts text from PDF files organized in silo folders
2. **Custom Cleaning**: Removes noise (headers, footers, page numbers) and normalizes formats (dates, currencies, areas)
3. **Intelligent Chunking**: Splits cleaned text into retrieval-sized chunks with overlap for context continuity
4. **Vector Indexing**: Stores chunk embeddings in a persistent vector database with metadata
5. **Semantic Search**: Finds relevant chunks based on question similarity with optional metadata filtering
6. **Grounded Answers**: Generates responses using only retrieved context with full citations
7. **Safety Features**: Explicit handling of insufficient evidence to prevent hallucination

## 1.3 Key Differentiator

Unlike standard RAG tools (LangChain, LlamaIndex), this solution includes a **domain-specific cleaning pipeline** that processes documents BEFORE chunking. This removes noise and normalizes formats at the source, resulting in cleaner indexes and more accurate retrieval.

## 1.4 Target Users

- **Real Estate Analysts**: Query property valuation data quickly
- **Due Diligence Teams**: Find comparable sales and cap rate evidence
- **Compliance Officers**: Audit valuation decisions with citation trails

---

# 2. PROBLEM STATEMENT

## 2.1 The Business Challenge

A large real estate investment firm has decades of property valuation data stored in PDF documents. Their analysts spend 2-3 hours manually searching for cap rate evidence for a single property. They want to use AI to search this data, but standard tools fail.

## 2.2 The Technical Blocker

> "Our proprietary data is trapped in siloed, unstructured PDF formats that standard RAG tools can't parse correctly."

## 2.3 Why Standard RAG Tools Fail

| Issue | Example | Impact |
|-------|---------|--------|
| Repeated Headers | "CONFIDENTIAL REPORT" on every page | Pollutes search results |
| Page Numbers | "Page 1 of 2" embedded in content | Creates meaningless chunks |
| Inconsistent Dates | "3/7/2025" vs "2025-03-07" vs "March 7, 2025" | Queries miss matches |
| Currency Variations | "$ 1,250,000" vs "$1.25M" vs "$1,250,000.00" | Retrieval failures |
| Area Unit Formats | "12500 SF" vs "12,500 sq ft" vs "12500 sqft" | Inconsistent indexing |
| Near-Duplicates | Same boilerplate paragraph in 50 documents | Wastes context budget |

## 2.4 Document Types (Silos)

The customer's data is organized into these categories:

| Silo | Description | Typical Content |
|------|-------------|-----------------|
| `comps/` | Comparable Sales Reports | Sale prices, cap rates, property details |
| `offering_memo/` | Offering Memoranda | Property marketing materials, financials |
| `appraisals/` | Appraisal Reports | Formal valuations, income approaches |
| `leases/` | Lease Abstracts | Tenant info, rent terms, escalations |
| `financials/` | Financial Statements | NOI, operating expenses, rent rolls |

## 2.5 Success Criteria

- **Time to find evidence**: From 2-3 hours to under 30 seconds
- **Answer consistency**: Same question returns same results regardless of who asks
- **Auditability**: Every answer includes citations to source documents and pages
- **Safety**: System refuses to answer when evidence is insufficient

---

# 3. SOLUTION ARCHITECTURE

## 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA INGESTION PIPELINE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐          │
│  │  PDFs   │───▶│ Ingestion │───▶│ Cleaning │───▶│ Chunking │          │
│  │ (silos) │    │           │    │          │    │          │          │
│  └─────────┘    └───────────┘    └──────────┘    └──────────┘          │
│       │              │                │               │                 │
│       ▼              ▼                ▼               ▼                 │
│   Input dir     IngestedDoc      CleanSegment     TextChunk            │
│                 + PageExtract    + normalized     + chunk_id           │
│                 + doc_id         + deduplicated   + metadata           │
│                 + silo           + quality gated                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         INDEXING PIPELINE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐    ┌───────────────┐    ┌─────────────────┐              │
│  │ TextChunk│───▶│ EmbeddingClient│───▶│ ChromaVectorStore│             │
│  │          │    │               │    │                 │              │
│  └──────────┘    └───────────────┘    └─────────────────┘              │
│       │                │                      │                         │
│       ▼                ▼                      ▼                         │
│   chunk.text      [0.23, 0.87, ...]    Persistent storage              │
│                   (vector)              + metadata                      │
│                                         + similarity search             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           QUERY PIPELINE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐    ┌─────────┐    ┌───────────┐    ┌───────────┐         │
│  │ Question │───▶│ Embed   │───▶│ Vector    │───▶│ RAG       │         │
│  │          │    │         │    │ Search    │    │ Engine    │         │
│  └──────────┘    └─────────┘    └───────────┘    └───────────┘         │
│       │              │               │                │                 │
│       ▼              ▼               ▼                ▼                 │
│   "What cap      Query vector    Top-K chunks     Grounded answer      │
│    rate..."                      + scores         + citations          │
│                                  + metadata       + insufficient_evidence│
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 3.2 Data Flow Summary

1. **Input**: PDF files organized in silo folders (e.g., `comps/`, `leases/`)
2. **Ingestion**: Extract text page-by-page, generate stable `doc_id` from file hash
3. **Cleaning**: Remove headers/footers, normalize dates/currency/area, deduplicate
4. **Chunking**: Split into 300-char chunks with 40-char overlap, preserve metadata
5. **Embedding**: Convert chunks to vectors (local hash or remote API)
6. **Indexing**: Store vectors + metadata in persistent ChromaDB
7. **Query**: Embed question, find similar chunks, assemble context
8. **Response**: Generate grounded answer with citations or return "insufficient evidence"

## 3.3 Key Design Principles

1. **Clean Before Index**: Noise removal happens before data enters the vector store
2. **Preserve Provenance**: Every chunk traces back to source document and page
3. **Pluggable Adapters**: Swap embedding/LLM providers without code changes
4. **Offline First**: Default configuration works without API keys or network
5. **Safe by Default**: Explicit handling of insufficient evidence cases

---

# 4. TECHNOLOGY STACK

## 4.1 Core Dependencies

| Package | Version | Purpose | File |
|---------|---------|---------|------|
| Python | 3.10+ | Runtime language | - |
| pypdf | >=5.0.0 | PDF text extraction | `ingestion/pdf_ingestion.py` |
| chromadb | >=1.0.0 | Vector database | `vector_store/chroma_store.py` |
| reportlab | >=4.0.0 | Sample PDF generation (dev) | `cli/main.py` |
| pytest | >=8.0.0 | Testing framework (dev) | `tests/` |
| ruff | >=0.8.0 | Linting (dev) | - |

## 4.2 Why These Choices?

### Python 3.10+
- Rich ecosystem for ML and data processing
- Fast prototyping and iteration
- Strong typing support with dataclasses

### pypdf
- Pure Python, no system dependencies
- Page-level text extraction
- Handles most PDF formats reliably

### ChromaDB
- Persistent local storage (SQLite + binary files)
- Metadata filtering support
- Easy migration path to cloud vector databases
- No external service dependency for prototype

### ReportLab
- Generates synthetic PDFs for testing
- Creates realistic document structures
- Enables deterministic test data

## 4.3 Production-Ready Integrations (Optional)

| Service | Purpose | Integration Point |
|---------|---------|-------------------|
| Vertex AI Embeddings | Managed semantic vectors | `RemoteHTTPEmbeddingClient` |
| Vertex AI Gemini | Managed LLM generation | `RemoteHTTPLlmClient` |
| Vertex AI Vector Search | Scalable vector retrieval | `VectorStore` interface |
| AlloyDB + pgvector | SQL-native vector storage | `VectorStore` interface |
| Google Cloud Storage | Document storage | Ingestion input |
| Document AI | Advanced PDF parsing/OCR | Ingestion fallback |

---

# 5. PROJECT STRUCTURE

## 5.1 Directory Layout

```
real-estate-rag-valuation-assistant/
├── src/
│   └── real_estate_rag/
│       ├── __init__.py                 # Package version (__version__ = "0.1.0")
│       ├── ingestion/
│       │   ├── __init__.py             # Exports: ingest_pdf_directory, IngestedDocument, PageExtraction
│       │   └── pdf_ingestion.py        # PDF discovery and extraction
│       ├── cleaning/
│       │   ├── __init__.py             # Exports: clean_documents, CleanSegment, CleaningConfig
│       │   └── pipeline.py             # Normalization and deduplication
│       ├── chunking/
│       │   ├── __init__.py             # Exports: chunk_segments, TextChunk, ChunkingConfig
│       │   └── pipeline.py             # Text splitting with overlap
│       ├── embedding/
│       │   ├── __init__.py             # Exports: EmbeddingClient, LocalHashEmbeddingClient, create_embedding_client_from_env
│       │   └── adapters.py             # Embedding provider implementations
│       ├── vector_store/
│       │   ├── __init__.py             # Exports: VectorStore, ChromaVectorStore, SearchResult
│       │   ├── base.py                 # Abstract VectorStore interface
│       │   └── chroma_store.py         # ChromaDB implementation
│       ├── rag/
│       │   ├── __init__.py             # Exports: RagEngine, RagConfig, RagResponse, Citation, create_llm_client_from_env
│       │   ├── engine.py               # RAG orchestration
│       │   └── llm.py                  # LLM client implementations
│       └── cli/
│           ├── __init__.py
│           └── main.py                 # CLI commands (re-rag)
├── tests/
│   ├── __init__.py
│   ├── fixtures.py                     # Shared test fixtures
│   ├── test_ingestion.py               # Ingestion tests
│   ├── test_cleaning.py                # Cleaning tests
│   ├── test_chunking.py                # Chunking tests
│   ├── test_embedding.py               # Embedding tests
│   ├── test_vector_store.py            # Vector store tests
│   ├── test_rag.py                     # RAG engine tests
│   ├── test_smoke.py                   # CLI smoke tests
│   └── test_cli_demo.py                # End-to-end CLI tests
├── scripts/
│   └── generate_50_samples.py          # Generate 50 varied test PDFs
├── presentation/
│   ├── Real_Estate_RAG_Interview_Presentation.pptx
│   ├── SPEAKER_SCRIPT.md
│   └── generate_presentation.py
├── docs/
│   ├── ARCHITECTURE.md                 # Architecture documentation
│   ├── ROADMAP.md                      # Production roadmap
│   ├── COMPLIANCE.md                   # Data handling guidelines
│   ├── DEMO.md                         # Demo runbook
│   └── FAQ.md                          # Technical Q&A
├── .github/
│   └── workflows/
│       └── ci.yml                      # GitHub Actions CI
├── pyproject.toml                      # Package configuration
├── Makefile                            # Task runner
├── DESIGN.md                           # Design decisions
├── CONTRIBUTING.md                     # Contributor guide
├── README.md                           # Project overview
├── .gitignore                          # Git ignore rules
└── .env.example                        # Environment variable template
```

## 5.2 Package Exports Summary

### `real_estate_rag.ingestion`
- `ingest_pdf_directory(input_dir, low_text_threshold=25, silo_mapping=None) -> tuple[IngestedDocument, ...]`
- `IngestedDocument` - dataclass
- `PageExtraction` - dataclass

### `real_estate_rag.cleaning`
- `clean_documents(documents, config=None) -> tuple[CleanSegment, ...]`
- `CleanSegment` - dataclass
- `CleaningConfig` - dataclass

### `real_estate_rag.chunking`
- `chunk_segments(segments, config=None) -> tuple[TextChunk, ...]`
- `TextChunk` - dataclass
- `ChunkingConfig` - dataclass

### `real_estate_rag.embedding`
- `EmbeddingClient` - abstract base class
- `LocalHashEmbeddingClient` - deterministic hash-based embeddings
- `RemoteHTTPEmbeddingClient` - HTTP API embeddings
- `create_embedding_client_from_env(provider, dimensions, endpoint, model, api_key) -> EmbeddingClient`

### `real_estate_rag.vector_store`
- `VectorStore` - abstract base class
- `ChromaVectorStore` - ChromaDB implementation
- `SearchResult` - dataclass

### `real_estate_rag.rag`
- `RagEngine` - orchestration class
- `RagConfig` - dataclass
- `RagResponse` - dataclass
- `Citation` - dataclass
- `LlmClient` - abstract base class
- `StubLlmClient` - deterministic stub
- `RemoteHTTPLlmClient` - HTTP API LLM
- `create_llm_client_from_env(provider, endpoint, model, api_key) -> LlmClient`

---

# 6. DATA MODELS & CONTRACTS

## 6.1 Ingestion Stage

### PageExtraction
```python
@dataclass(frozen=True)
class PageExtraction:
    """Extraction result for a single page."""
    page_index: int           # 1-based page number
    text: str                 # Raw extracted text
    char_count: int           # Length of text
    scan_suspected: bool      # True if char_count < low_text_threshold
    warnings: tuple[str, ...] # e.g., ("empty_page_text", "low_text_scan_suspected")
```

### IngestedDocument
```python
@dataclass(frozen=True)
class IngestedDocument:
    """Extraction result for a single PDF document."""
    doc_id: str               # SHA-256 hash of file bytes (stable identifier)
    file_path: str            # Absolute path to PDF
    relative_path: str        # Path relative to input root
    file_name: str            # Just the filename
    silo: str                 # Top-level folder name (e.g., "comps", "leases")
    total_pages: int          # Number of pages
    pages: tuple[PageExtraction, ...]  # Per-page extractions
    warnings: tuple[str, ...] # e.g., ("contains_scan_suspected_pages",)
```

## 6.2 Cleaning Stage

### CleaningConfig
```python
@dataclass(frozen=True)
class CleaningConfig:
    """Configuration for deterministic text cleaning."""
    min_text_length: int = 20              # Skip segments shorter than this
    dedupe_similarity_threshold: float = 0.9  # Jaccard similarity for deduplication
```

### CleanSegment
```python
@dataclass(frozen=True)
class CleanSegment:
    """Cleaned segment contract consumed by downstream chunking."""
    text: str                              # Cleaned and normalized text
    doc_id: str                            # Source document ID
    page_span: tuple[int, int]             # (start_page, end_page) inclusive
    silo: str                              # Source silo
    content_type: str                      # "narrative" or "table_like"
    normalized_fields: dict[str, str]      # Extracted values (date_example, currency_example, cap_rate)
    warnings: tuple[str, ...]              # Combined warnings from all stages
```

## 6.3 Chunking Stage

### ChunkingConfig
```python
@dataclass(frozen=True)
class ChunkingConfig:
    """Configuration for character-based chunk splitting."""
    max_chunk_chars: int = 300   # Maximum chunk size
    overlap_chars: int = 40      # Overlap between consecutive chunks
```

### TextChunk
```python
@dataclass(frozen=True)
class TextChunk:
    """Chunk contract for embedding and retrieval."""
    chunk_id: str                          # SHA-256 hash of source metadata + chunk text
    text: str                              # Chunk text content
    doc_id: str                            # Source document ID
    page_span: tuple[int, int]             # Source page range
    silo: str                              # Source silo
    content_type: str                      # "narrative" or "table_like"
    normalized_fields: dict[str, str]      # Inherited from CleanSegment
    source_warnings: tuple[str, ...]       # Inherited warnings
    chunk_index: int = 0                   # Position within segment (0-based)
    total_chunks_for_segment: int = 1      # Total chunks from this segment
```

## 6.4 Vector Store Stage

### SearchResult
```python
@dataclass(frozen=True)
class SearchResult:
    """Single result from vector similarity search."""
    chunk_id: str              # Chunk identifier
    text: str                  # Chunk text
    score: float               # Similarity score (1 - distance)
    metadata: dict[str, Any]   # All chunk metadata
```

## 6.5 RAG Stage

### RagConfig
```python
@dataclass(frozen=True)
class RagConfig:
    """Runtime config for retrieval and context assembly."""
    top_k: int = 4                    # Number of chunks to retrieve
    max_context_chars: int = 1400     # Maximum context budget
    min_score: float = -1.0           # Minimum similarity threshold
```

### Citation
```python
@dataclass(frozen=True)
class Citation:
    """Citation emitted in RAG responses."""
    chunk_id: str                     # Chunk identifier
    doc_id: str                       # Source document ID
    page_span: tuple[int, int]        # Source page range
    score: float                      # Similarity score
```

### RagResponse
```python
@dataclass(frozen=True)
class RagResponse:
    """Response contract for RAG queries."""
    answer_text: str                          # Generated answer
    citations: tuple[Citation, ...]           # Source citations
    insufficient_evidence: bool               # True if no relevant context found
    raw_retrieved_chunks: tuple[SearchResult, ...] = ()  # All retrieved chunks
```

---

# 7. COMPONENT DEEP-DIVE

## 7.1 Ingestion Component

### Location
`src/real_estate_rag/ingestion/pdf_ingestion.py`

### Functions

#### `discover_pdf_files(input_dir: Path | str) -> list[Path]`
- Recursively finds all `.pdf` files under input directory
- Returns sorted list (deterministic order)
- Raises `FileNotFoundError` if directory doesn't exist
- Raises `NotADirectoryError` if path is not a directory

#### `compute_doc_id(file_path: Path | str) -> str`
- Reads file bytes and computes SHA-256 hash
- Returns 64-character hex string
- Stable: same file always produces same ID

#### `infer_silo(file_path: Path | str, root_dir: Path | str, silo_mapping: dict | None = None) -> str`
- Extracts top-level folder name relative to root
- Example: `/data/comps/file.pdf` with root `/data/` → silo = "comps"
- Returns "default" if file is directly in root
- Optional `silo_mapping` dict for custom silo names

#### `extract_pdf_document(file_path, root_dir, low_text_threshold=25, silo_mapping=None) -> IngestedDocument`
- Uses `pypdf.PdfReader` for extraction
- Iterates pages with 1-based indexing
- Flags pages with `char_count < low_text_threshold` as `scan_suspected`
- Adds document-level warning if any pages are scan-suspected

#### `ingest_pdf_directory(input_dir, low_text_threshold=25, silo_mapping=None) -> tuple[IngestedDocument, ...]`
- Main entry point for ingestion
- Discovers all PDFs, extracts each one
- Returns tuple of IngestedDocument objects

### Warnings Emitted
- `empty_page_text` - Page has zero characters
- `low_text_scan_suspected` - Page has fewer than threshold characters
- `contains_scan_suspected_pages` - Document has at least one suspected scan page

## 7.2 Cleaning Component

### Location
`src/real_estate_rag/cleaning/pipeline.py`

### Regular Expressions Used

```python
# Page number detection - matches "Page 1 of 2", "page 1/2", "1 of 2", etc.
_PAGE_NUMBER_RE = re.compile(r"^(?:page\s*)?\d+(?:\s*(?:of|/)\s*\d+)?$", re.IGNORECASE)

# Collapse multiple spaces/tabs to single space
_MULTISPACE_RE = re.compile(r"[ \t]{2,}")

# Area unit normalization - matches "sq ft", "sqft", "SF", "sq. ft", etc.
_AREA_UNIT_RE = re.compile(r"\b(?:sq\.?\s*ft|sqft|sf)\b", re.IGNORECASE)

# Currency detection - matches "$ 1,250,000", "$1.25M", etc.
_CURRENCY_TEXT_RE = re.compile(r"\$\s*(\d[\d,]*(?:\.\d+)?)\s*([kmb])?\b", re.IGNORECASE)

# US date format - matches "3/7/2025", "03/07/2025"
_DATE_SLASH_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")

# ISO date format - matches "2025-03-07"
_DATE_DASH_RE = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")

# Cap rate extraction - matches "cap rate: 6.1%", "Cap Rate is 6.5%", etc.
_CAP_RATE_RE = re.compile(
    r"\bcap\s*rate\b(?:\s*[:=]\s*|\s+is\s+|\s+of\s+)?([0-9]+(?:\.[0-9]+)?%)",
    re.IGNORECASE,
)

# Token extraction for similarity comparison
_TOKEN_RE = re.compile(r"\w+")
```

### Cleaning Pipeline Steps

1. **Detect Repeated Edge Lines**
   - Examine first and last lines of each page
   - Count occurrences across all pages
   - Lines appearing more than once are marked as repeated headers/footers

2. **Clean Page Text**
   - Remove lines that match repeated headers/footers
   - Remove lines that match page number pattern
   - Join remaining lines

3. **Normalize Text**
   - Collapse multiple spaces to single space
   - Normalize area units → "sqft"
   - Normalize currency → "$1,250,000" format
   - Convert US dates → ISO format (2025-03-07)
   - Extract cap rate as metadata

4. **Infer Content Type**
   - Check for table cues: `|` character, tabs, aligned columns
   - Returns "table_like" if cues found, otherwise "narrative"

5. **Quality Gate**
   - Skip segments shorter than `min_text_length`

6. **Near-Duplicate Suppression**
   - Tokenize text (lowercase words)
   - Compare Jaccard similarity with previously seen segments
   - Skip if similarity >= `dedupe_similarity_threshold`

### Functions

#### `clean_documents(documents: tuple[IngestedDocument, ...], config: CleaningConfig | None = None) -> tuple[CleanSegment, ...]`
- Main entry point
- Processes all documents, maintains order
- Returns deduplicated, normalized segments

#### `clean_ingested_document(document: IngestedDocument, config: CleaningConfig | None = None) -> tuple[CleanSegment, ...]`
- Processes single document
- Called by `clean_documents` for each document

### Warnings Added
- `removed_repeated_header_footer` - Line was removed as repeated header/footer
- `removed_page_number_line` - Line was removed as page number
- `scan_suspected` - Inherited from page if applicable

## 7.3 Chunking Component

### Location
`src/real_estate_rag/chunking/pipeline.py`

### Algorithm

**Character-based splitting with overlap:**

```
Input text: "ABCDEFGHIJKLMNOPQRSTUVWXYZ" (26 chars)
Config: max_chunk_chars=10, overlap_chars=3

Step = max_chunk_chars - overlap_chars = 10 - 3 = 7

Chunk 0: chars 0-10  → "ABCDEFGHIJ"
Chunk 1: chars 7-17  → "HIJKLMNOPQ"
Chunk 2: chars 14-24 → "OPQRSTUVWX"
Chunk 3: chars 21-26 → "VWXYZ"
```

### Chunk ID Generation

```python
def _build_chunk_id(segment: CleanSegment, chunk_index: int, chunk_text: str) -> str:
    payload = "|".join([
        segment.doc_id,
        str(segment.page_span[0]),
        str(segment.page_span[1]),
        segment.silo,
        segment.content_type,
        str(chunk_index),
        chunk_text,
    ])
    return sha256(payload.encode("utf-8")).hexdigest()
```

This ensures:
- Same content from same source → same chunk_id
- Different position → different chunk_id
- Idempotent re-indexing

### Functions

#### `chunk_segments(segments: tuple[CleanSegment, ...], config: ChunkingConfig | None = None) -> tuple[TextChunk, ...]`
- Main entry point
- Validates config (max > 0, overlap >= 0, overlap < max)
- Returns all chunks with full metadata

### Metadata Inheritance

Every `TextChunk` inherits from its source `CleanSegment`:
- `doc_id` - unchanged
- `page_span` - unchanged
- `silo` - unchanged
- `content_type` - unchanged
- `normalized_fields` - deep copied
- `source_warnings` - unchanged

## 7.4 Embedding Component

### Location
`src/real_estate_rag/embedding/adapters.py`

### Interface

```python
class EmbeddingClient:
    """Embedding adapter interface."""
    
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Convert texts to vectors."""
        raise NotImplementedError
```

### Implementations

#### LocalHashEmbeddingClient
```python
@dataclass(frozen=True)
class LocalHashEmbeddingClient(EmbeddingClient):
    """Deterministic local embedding adapter for tests and CI."""
    dimensions: int = 12
    
    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            values = []
            for i in range(self.dimensions):
                byte = digest[i % len(digest)]
                values.append(round(byte / 255.0, 6))
            vectors.append(values)
        return vectors
```

**Properties:**
- Deterministic: same text → same vector
- Offline: no network required
- Fast: pure computation
- NOT semantic: similar texts don't produce similar vectors

#### RemoteHTTPEmbeddingClient
```python
@dataclass(frozen=True)
class RemoteHTTPEmbeddingClient(EmbeddingClient):
    """Optional HTTP embedding adapter."""
    endpoint: str
    model: str
    api_key: str
    timeout_seconds: int = 20
```

**Expected API:**
- Request: `POST {"model": "...", "texts": ["..."]}`
- Response: `{"embeddings": [[...], [...]]}`
- Auth: `Authorization: Bearer <api_key>`

### Factory Function

```python
def create_embedding_client_from_env(
    provider: str,          # "local" or "remote_http"
    dimensions: int = 12,   # For local provider
    endpoint: str = "",     # For remote provider
    model: str = "",        # For remote provider
    api_key: str = "",      # For remote provider
) -> EmbeddingClient:
```

## 7.5 Vector Store Component

### Location
`src/real_estate_rag/vector_store/base.py` - Interface
`src/real_estate_rag/vector_store/chroma_store.py` - Implementation

### Interface

```python
class VectorStore:
    """Abstract vector store interface."""
    
    def upsert(self, chunks: tuple[TextChunk, ...], embeddings: list[list[float]]) -> None:
        """Insert or update chunks with their embeddings."""
        raise NotImplementedError
    
    def clear(self) -> None:
        """Remove all data from the store."""
        raise NotImplementedError
    
    def query(
        self,
        vector: list[float],
        top_k: int,
        metadata_filter: dict[str, object] | None = None,
    ) -> tuple[SearchResult, ...]:
        """Find similar chunks."""
        raise NotImplementedError
```

### ChromaVectorStore Implementation

```python
class ChromaVectorStore(VectorStore):
    def __init__(self, persist_path: str, collection_name: str = "valuation_chunks"):
        path = Path(persist_path).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(path))
        self._collection = self._client.get_or_create_collection(name=collection_name)
```

**Key Features:**

1. **Persistent Storage**
   - Uses `PersistentClient` with disk path
   - Data survives process restarts
   - Storage format: SQLite metadata + binary vector files

2. **Idempotent Upsert**
   - Uses `chunk_id` as primary key
   - Re-running index updates existing records
   - No duplicate chunks

3. **Metadata Storage**
   - Flattens `TextChunk` to metadata dict
   - Converts `page_span` tuple to `page_start`, `page_end`, `page_span` string
   - Converts `source_warnings` tuple to pipe-separated string
   - Prefixes `normalized_fields` with `norm_`

4. **Dimension Validation**
   - Checks incoming vector dimensions against existing data
   - Raises `ValueError` on mismatch
   - Prevents corrupted indexes

5. **Score Computation**
   - ChromaDB returns distances (lower = more similar)
   - Converts to scores: `score = 1.0 - distance`

### Metadata Filter Format

```python
# Single value filter
metadata_filter = {"silo": "comps"}

# Multiple filters (AND)
metadata_filter = {"silo": "comps", "content_type": "narrative"}
```

## 7.6 RAG Engine Component

### Location
`src/real_estate_rag/rag/engine.py` - Orchestration
`src/real_estate_rag/rag/llm.py` - LLM clients

### RagEngine Class

```python
class RagEngine:
    def __init__(
        self,
        embedding_client: EmbeddingClient,
        vector_store: VectorStore,
        llm_client: LlmClient,
        config: RagConfig | None = None,
    ):
```

### Query Flow

```python
def answer(self, question: str, metadata_filter: dict | None = None) -> RagResponse:
    # 1. Embed the question
    query_vector = self._embedding_client.embed([question])[0]
    
    # 2. Retrieve similar chunks
    retrieved = self._vector_store.query(
        query_vector,
        top_k=self._config.top_k,
        metadata_filter=metadata_filter,
    )
    
    # 3. Filter by minimum score
    filtered = tuple(item for item in retrieved if item.score >= self._config.min_score)
    
    # 4. Select chunks within context budget
    selected = self._select_context_chunks(filtered)
    
    # 5. Handle no-evidence case
    if not selected:
        return RagResponse(
            answer_text="Insufficient evidence...",
            citations=(),
            insufficient_evidence=True,
            raw_retrieved_chunks=filtered,
        )
    
    # 6. Build grounded prompt
    prompt = self._build_prompt(question, selected)
    
    # 7. Generate answer
    answer_text = self._llm_client.generate(prompt)
    
    # 8. Build citations
    citations = tuple(self._build_citation(item) for item in selected)
    
    return RagResponse(
        answer_text=answer_text,
        citations=citations,
        insufficient_evidence=False,
        raw_retrieved_chunks=filtered,
    )
```

### Context Selection

```python
def _select_context_chunks(self, hits: tuple[SearchResult, ...]) -> tuple[SearchResult, ...]:
    selected = []
    used_chars = 0
    
    for hit in hits:
        chunk_size = len(hit.text)
        if used_chars + chunk_size <= self._config.max_context_chars:
            selected.append(hit)
            used_chars += chunk_size
        elif not selected:
            # First chunk too large - trim it
            trimmed = SearchResult(
                chunk_id=hit.chunk_id,
                text=hit.text[:self._config.max_context_chars],
                score=hit.score,
                metadata=hit.metadata,
            )
            selected.append(trimmed)
            break
        else:
            break
    
    return tuple(selected)
```

### Prompt Template

```python
def _build_prompt(self, question: str, hits: tuple[SearchResult, ...]) -> str:
    blocks = []
    for idx, hit in enumerate(hits, start=1):
        doc_id = hit.metadata.get("doc_id", "unknown_doc")
        page_start = hit.metadata.get("page_start", 0)
        page_end = hit.metadata.get("page_end", page_start)
        blocks.append(
            f"[CONTEXT {idx}]\n"
            f"chunk_id={hit.chunk_id}\n"
            f"doc_id={doc_id}\n"
            f"page_span={page_start}-{page_end}\n"
            f"text={hit.text}"
        )
    
    context = "\n\n".join(blocks)
    
    return (
        "You are a valuation assistant. Use ONLY the provided context snippets.\n"
        "If evidence is incomplete, explicitly say so and avoid fabricating values.\n"
        "Return concise prose and reference context IDs when relevant.\n\n"
        f"Question: {question}\n\n"
        "Context snippets:\n"
        f"{context}\n"
    )
```

### LLM Clients

#### StubLlmClient
```python
class StubLlmClient(LlmClient):
    def generate(self, prompt: str) -> str:
        return "STUB_ANSWER: grounded response generated from provided context."
```

#### RemoteHTTPLlmClient
```python
@dataclass(frozen=True)
class RemoteHTTPLlmClient(LlmClient):
    endpoint: str
    model: str
    api_key: str
    timeout_seconds: int = 30
```

---

# 8. CONFIGURATION & ENVIRONMENT

## 8.1 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VECTOR_DB_PATH` | `./vector_db` | Path to vector database directory |
| `VECTOR_DB_COLLECTION` | `valuation_chunks` | Collection name |
| `EMBEDDING_PROVIDER` | `local` | `local` or `remote_http` |
| `EMBEDDING_DIMENSIONS` | `12` | Vector dimensions (local mode) |
| `EMBEDDING_API_BASE_URL` | - | Embedding API endpoint |
| `EMBEDDING_MODEL` | - | Embedding model name |
| `EMBEDDING_API_KEY` | - | Embedding API key |
| `LLM_PROVIDER` | `stub` | `stub` or `remote_http` |
| `LLM_API_BASE_URL` | - | LLM API endpoint |
| `LLM_MODEL` | - | LLM model name |
| `LLM_API_KEY` | - | LLM API key |
| `RAG_TOP_K` | `4` | Number of chunks to retrieve |
| `RAG_MAX_CONTEXT_CHARS` | `1400` | Maximum context size |
| `RAG_MIN_SCORE` | `-1.0` | Minimum similarity threshold |

## 8.2 .env.example

```bash
# Vector Database
VECTOR_DB_PATH=./vector_db
VECTOR_DB_COLLECTION=valuation_chunks

# Embedding Configuration
EMBEDDING_PROVIDER=local
EMBEDDING_DIMENSIONS=12
# For remote embeddings:
# EMBEDDING_PROVIDER=remote_http
# EMBEDDING_API_BASE_URL=https://api.openai.com/v1/embeddings
# EMBEDDING_MODEL=text-embedding-3-small
# EMBEDDING_API_KEY=sk-your-key-here

# LLM Configuration
LLM_PROVIDER=stub
# For remote LLM:
# LLM_PROVIDER=remote_http
# LLM_API_BASE_URL=https://api.openai.com/v1/chat/completions
# LLM_MODEL=gpt-4
# LLM_API_KEY=sk-your-key-here

# RAG Configuration
RAG_TOP_K=4
RAG_MAX_CONTEXT_CHARS=1400
RAG_MIN_SCORE=-1.0
```

## 8.3 pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "real-estate-rag-valuation-assistant"
version = "0.1.0"
description = "Prototype scaffold for a real estate valuation RAG assistant."
readme = "README.md"
requires-python = ">=3.10"
authors = [{ name = "Project Team" }]
dependencies = ["pypdf>=5.0.0", "chromadb>=1.0.0"]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "reportlab>=4.0.0", "ruff>=0.8.0"]

[project.scripts]
re-rag = "real_estate_rag.cli.main:app"

[tool.setuptools]
package-dir = { "" = "src" }

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
markers = [
    "unit: fast deterministic unit tests",
    "integration: integration tests over real local components",
    "e2e: end-to-end smoke tests over CLI pipeline",
    "network: tests that require external network access (opt-in)",
]
```

---

# 9. CLI REFERENCE

## 9.1 Available Commands

| Command | Description |
|---------|-------------|
| `re-rag --help` | Show help message |
| `re-rag --version` | Show version (0.1.0) |
| `re-rag create-sample-data` | Generate synthetic test PDFs |
| `re-rag ingest` | Inspect ingestion output (no indexing) |
| `re-rag index` | Full pipeline: ingest → clean → chunk → embed → index |
| `re-rag ask` | Query indexed data |
| `re-rag index-local` | Alias for `index` |
| `re-rag query-local` | Alias for `ask` |

## 9.2 Command Details

### `re-rag create-sample-data`

```bash
re-rag create-sample-data --output-dir ./sample_data
```

**Options:**
- `--output-dir` (default: `./sample_data`) - Output directory

**Creates:**
- `comps/comp_downtown.pdf` - 2-page comparable sales report
- `offering_memo/memo_suburban.pdf` - 1-page offering memo

### `re-rag ingest`

```bash
re-rag ingest --input-dir ./sample_data
```

**Options:**
- `--input-dir` (required) - Directory containing PDFs

**Output:** JSON with document and page counts
```json
{"status": "ok", "documents": 2, "pages": 3}
```

### `re-rag index`

```bash
re-rag index \
  --input-dir ./sample_data \
  --vector-db-path ./vector_db \
  --collection valuation_chunks \
  --embedding-provider local \
  --embedding-dimensions 12
```

**Options:**
- `--input-dir` (required) - Directory containing PDFs
- `--vector-db-path` (default: `./vector_db`) - Vector database path
- `--collection` (default: `valuation_chunks`) - Collection name
- `--embedding-provider` (default: `local`) - `local` or `remote_http`
- `--embedding-dimensions` (default: `12`) - Dimensions for local provider

**Output:** JSON with pipeline statistics
```json
{
  "status": "ok",
  "documents": 50,
  "clean_segments": 90,
  "chunks_indexed": 165,
  "vector_db_path": "./vector_db",
  "collection": "valuation_chunks"
}
```

### `re-rag ask`

```bash
re-rag ask \
  --question "What cap rate evidence exists?" \
  --vector-db-path ./vector_db \
  --collection valuation_chunks \
  --embedding-provider local \
  --embedding-dimensions 12 \
  --llm-provider stub \
  --top-k 5 \
  --silo comps
```

**Options:**
- `--question` (required) - Query text
- `--vector-db-path` (default: `./vector_db`) - Vector database path
- `--collection` (default: `valuation_chunks`) - Collection name
- `--top-k` (default: `4`) - Number of results
- `--silo` (optional) - Filter by silo
- `--embedding-provider` (default: `local`) - Embedding provider
- `--embedding-dimensions` (default: `12`) - Dimensions for local
- `--llm-provider` (default: `stub`) - `stub` or `remote_http`
- `--max-context-chars` (default: `1400`) - Context budget
- `--min-score` (default: `-1.0`) - Minimum similarity

**Output:**
```
ANSWER:
STUB_ANSWER: grounded response generated from provided context.

INSUFFICIENT_EVIDENCE: False
CITATIONS:
- chunk_id=abc123... doc_id=def456... page_span=1-1 score=0.847000
- chunk_id=ghi789... doc_id=jkl012... page_span=2-2 score=0.723000
```

## 9.3 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Unexpected error |
| 2 | User error (missing files, empty corpus, invalid config) |

---

# 10. API REFERENCE

## 10.1 Full Pipeline Example

```python
from pathlib import Path
from real_estate_rag.ingestion import ingest_pdf_directory
from real_estate_rag.cleaning import CleaningConfig, clean_documents
from real_estate_rag.chunking import ChunkingConfig, chunk_segments
from real_estate_rag.embedding import LocalHashEmbeddingClient
from real_estate_rag.vector_store import ChromaVectorStore
from real_estate_rag.rag import RagConfig, RagEngine, StubLlmClient

# 1. Ingest PDFs
documents = ingest_pdf_directory(
    Path("./sample_data"),
    low_text_threshold=25,
)

# 2. Clean and normalize
segments = clean_documents(
    documents,
    CleaningConfig(min_text_length=20, dedupe_similarity_threshold=0.9),
)

# 3. Chunk with overlap
chunks = chunk_segments(
    segments,
    ChunkingConfig(max_chunk_chars=300, overlap_chars=40),
)

# 4. Create embedding client
embedding_client = LocalHashEmbeddingClient(dimensions=12)

# 5. Embed chunks
vectors = embedding_client.embed([chunk.text for chunk in chunks])

# 6. Create vector store and index
vector_store = ChromaVectorStore("./vector_db", "valuation_chunks")
vector_store.upsert(chunks, vectors)

# 7. Create RAG engine
engine = RagEngine(
    embedding_client=embedding_client,
    vector_store=vector_store,
    llm_client=StubLlmClient(),
    config=RagConfig(top_k=4, max_context_chars=1400, min_score=0.0),
)

# 8. Query
response = engine.answer(
    "What cap rate evidence exists?",
    metadata_filter={"silo": "comps"},
)

# 9. Process response
print(f"Answer: {response.answer_text}")
print(f"Insufficient Evidence: {response.insufficient_evidence}")
for citation in response.citations:
    print(f"  - {citation.doc_id[:16]}... page {citation.page_span} score={citation.score:.4f}")
```

## 10.2 Individual Component Examples

### Ingestion Only
```python
from real_estate_rag.ingestion import ingest_pdf_directory

docs = ingest_pdf_directory("./pdfs", low_text_threshold=25)
for doc in docs:
    print(f"{doc.file_name}: {doc.total_pages} pages, silo={doc.silo}")
    for page in doc.pages:
        print(f"  Page {page.page_index}: {page.char_count} chars")
```

### Cleaning Only
```python
from real_estate_rag.cleaning import CleaningConfig, clean_documents

segments = clean_documents(docs, CleaningConfig(min_text_length=20))
for seg in segments:
    print(f"doc={seg.doc_id[:16]} pages={seg.page_span} type={seg.content_type}")
    print(f"  normalized: {seg.normalized_fields}")
```

### Vector Store Direct Access
```python
from real_estate_rag.vector_store import ChromaVectorStore

store = ChromaVectorStore("./vector_db", "my_collection")

# Check count
print(f"Stored chunks: {store.count()}")

# Query with filter
results = store.query(
    vector=[0.1, 0.2, 0.3, ...],
    top_k=5,
    metadata_filter={"silo": "leases", "content_type": "table_like"},
)
```

---

# 11. TESTING

## 11.1 Test Structure

| File | Coverage | Markers |
|------|----------|---------|
| `test_ingestion.py` | PDF discovery, extraction, doc_id, silo inference | unit, integration |
| `test_cleaning.py` | Normalization, deduplication, quality gates | unit |
| `test_chunking.py` | Splitting, overlap, chunk_id, metadata | unit |
| `test_embedding.py` | Local client determinism, dimension consistency | unit |
| `test_vector_store.py` | Persistence, upsert, query, filtering | integration |
| `test_rag.py` | Grounding, citations, no-evidence handling | unit, integration |
| `test_smoke.py` | CLI parsing, version | unit |
| `test_cli_demo.py` | End-to-end CLI flow | e2e |
| `fixtures.py` | Shared test utilities | - |

## 11.2 Test Markers

```python
# pytest.ini_options markers:
# unit - Fast deterministic unit tests
# integration - Integration tests over real local components
# e2e - End-to-end smoke tests over CLI pipeline
# network - Tests requiring external network (opt-in)
```

## 11.3 Running Tests

```bash
# All tests (excludes e2e and network by default)
make test
# or
pytest -q

# E2E tests
make test-e2e
# or
pytest -m e2e

# Specific file
pytest tests/test_cleaning.py -v

# Specific test
pytest tests/test_cleaning.py::test_date_normalization -v

# Full CI suite
make ci
# Runs: lint + test + test-e2e
```

## 11.4 Test Fixtures

```python
# tests/fixtures.py

def create_temp_pdf(tmp_path: Path, name: str, pages: list[str]) -> Path:
    """Create a temporary PDF for testing."""
    from reportlab.pdfgen import canvas
    path = tmp_path / name
    pdf = canvas.Canvas(str(path))
    for text in pages:
        y = 750
        for line in text.split("\n"):
            pdf.drawString(50, y, line)
            y -= 15
        pdf.showPage()
    pdf.save()
    return path

def create_sample_documents(tmp_path: Path) -> tuple[IngestedDocument, ...]:
    """Create sample IngestedDocument objects for testing."""
    ...

def create_sample_segments() -> tuple[CleanSegment, ...]:
    """Create sample CleanSegment objects for testing."""
    ...
```

## 11.5 Test Count

**Total: 30 tests**
- Ingestion: 6 tests
- Cleaning: 8 tests
- Chunking: 5 tests
- Embedding: 3 tests
- Vector Store: 4 tests
- RAG: 3 tests
- CLI: 1 test

---

# 12. DEPLOYMENT & OPERATIONS

## 12.1 Local Development Setup

```bash
# Clone repository
git clone <repository-url>
cd real-estate-rag-valuation-assistant

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Verify installation
re-rag --version
pytest -q
```

## 12.2 Demo Workflow

```bash
# Generate sample data
python scripts/generate_50_samples.py

# Index documents
re-rag index \
  --input-dir ./sample_data_50 \
  --vector-db-path ./vector_db_50 \
  --collection valuation_50 \
  --embedding-provider local \
  --embedding-dimensions 12

# Query
re-rag ask \
  --question "What cap rate evidence exists?" \
  --vector-db-path ./vector_db_50 \
  --collection valuation_50 \
  --embedding-provider local \
  --embedding-dimensions 12 \
  --llm-provider stub \
  --top-k 5
```

## 12.3 Vector Database Location

```
./vector_db/
├── chroma.sqlite3              # Metadata storage
└── <collection-uuid>/          # Collection data
    ├── data_level0.bin         # Vector embeddings
    ├── header.bin              # Index header
    ├── index_metadata.json     # Index config
    └── length.bin              # Lengths
```

## 12.4 Clearing the Index

```python
from real_estate_rag.vector_store import ChromaVectorStore

store = ChromaVectorStore("./vector_db", "valuation_chunks")
store.clear()  # Deletes and recreates collection
```

Or delete the directory:
```bash
rm -rf ./vector_db
```

## 12.5 Makefile Targets

```makefile
lint:
	ruff check src tests

test:
	pytest -m "not e2e and not network" -q

test-e2e:
	pytest -m e2e -q

ci: lint test test-e2e
```

---

# 13. DESIGN DECISIONS & TRADE-OFFS

## 13.1 Decision Log

### D1: Language Choice - Python 3.10+

**Decision:** Use Python 3.10+ as the runtime language.

**Alternatives Considered:**
- TypeScript/Node.js
- Go
- Rust

**Rationale:**
- Rich ecosystem for ML, NLP, and data processing
- Excellent PDF libraries (pypdf, pdfplumber)
- Strong typing with dataclasses
- Fast prototyping iteration
- Team familiarity

**Trade-offs:**
- Slower than compiled languages
- GIL limits true parallelism
- Acceptable for prototype; production can optimize hot paths

### D2: PDF Extraction - pypdf

**Decision:** Use pypdf for PDF text extraction.

**Alternatives Considered:**
- pdfplumber (more features, heavier)
- PyMuPDF (C bindings, faster)
- Document AI (cloud-based, costly)

**Rationale:**
- Pure Python, no system dependencies
- Reliable page-level extraction
- Lightweight for prototype
- Handles most PDF formats

**Trade-offs:**
- Limited OCR support (flagged, not handled)
- No table extraction (handled by content_type heuristic)
- Production may need Document AI fallback

### D3: Vector Database - ChromaDB

**Decision:** Use ChromaDB for vector storage.

**Alternatives Considered:**
- Pinecone (managed, cloud-only)
- Qdrant (self-hosted or cloud)
- Weaviate (self-hosted or cloud)
- FAISS (in-memory, no persistence by default)
- Vertex AI Vector Search (managed, GCP-only)

**Rationale:**
- Persistent local storage
- No external service dependency
- Metadata filtering support
- Easy migration path to production DBs
- Good for prototyping

**Trade-offs:**
- Not horizontally scalable
- Single-node only
- Production needs Vector Search or AlloyDB

### D4: Chunking Strategy - Character-Based

**Decision:** Use deterministic character-based chunking with fixed size and overlap.

**Alternatives Considered:**
- Tokenizer-based chunking
- Semantic chunking (sentence/paragraph boundaries)
- Recursive splitters (LangChain-style)

**Rationale:**
- Deterministic: same input → same chunks
- Model-agnostic: no tokenizer dependency
- Predictable: easy to reason about boundaries
- Testable: reproducible results

**Trade-offs:**
- May split mid-sentence
- Not optimized for token limits
- Overlap mitigates context loss

### D5: Embedding Strategy - Pluggable Adapters

**Decision:** Use adapter pattern with local default and optional remote.

**Alternatives Considered:**
- Always use managed embeddings
- Always use local models (sentence-transformers)
- Hardcode single provider

**Rationale:**
- Demo reliability: no API failures
- Development speed: no API costs during iteration
- Production flexibility: easy provider swap
- Testing: deterministic results

**Trade-offs:**
- Local embeddings not semantic
- Production requires configuration change
- Additional abstraction layer

### D6: Document Identity - SHA-256 Hash

**Decision:** Use SHA-256 hash of file bytes as stable document ID.

**Alternatives Considered:**
- UUID (random)
- File path (mutable)
- Database auto-increment

**Rationale:**
- Stable: same file → same ID
- Content-addressed: detects duplicates
- Idempotent: re-indexing works correctly
- No coordination needed

**Trade-offs:**
- Same content, different files → same ID (feature or bug?)
- Modified file → new ID (breaks references)
- Acceptable for prototype scope

### D7: Cleaning Approach - Domain-Specific Rules

**Decision:** Use explicit regex patterns for real estate document cleaning.

**Alternatives Considered:**
- ML-based header detection
- Generic boilerplate removal
- No cleaning (raw extraction)

**Rationale:**
- Interpretable: can explain every transformation
- Deterministic: same input → same output
- Domain-optimized: targets known patterns
- No training data required

**Trade-offs:**
- May miss novel patterns
- Requires maintenance as patterns evolve
- Not generalizable to other domains

### D8: Safety Strategy - Explicit No-Evidence Handling

**Decision:** Return `insufficient_evidence=True` when no relevant context found.

**Alternatives Considered:**
- Always generate answer (let LLM handle)
- Return error
- Return empty response

**Rationale:**
- Explicit signal for downstream handling
- Prevents hallucination at source
- Clear contract for consumers
- Auditable decision

**Trade-offs:**
- May refuse when human would find answer
- Threshold tuning required
- Additional code path to maintain

---

# 14. PRODUCTION ROADMAP

## 14.1 Phase 1: Pilot Hardening (Weeks 1-6)

### Goals
- Deploy prototype to cloud environment
- Integrate real document sources
- Establish evaluation baseline

### Actions
1. Provision GCP project with IAM roles
2. Deploy application to Cloud Run
3. Move documents to Cloud Storage
4. Integrate Document AI for OCR fallback
5. Create evaluation test set (questions + expected answers)
6. Set up Secret Manager for API keys

### Deliverables
- Running Cloud Run service
- Document pipeline from Cloud Storage
- Baseline quality metrics

## 14.2 Phase 2: Production Rollout (Weeks 6-12)

### Goals
- Production-grade ML services
- Scalable vector storage
- Operational monitoring

### Actions
1. Integrate Vertex AI Embeddings
2. Integrate Vertex AI Gemini for generation
3. Choose and deploy vector backend:
   - Option A: Vertex AI Vector Search (managed)
   - Option B: AlloyDB + pgvector (SQL-native)
4. Define SLOs:
   - p95 latency < 3 seconds
   - Availability > 99.5%
   - Citation accuracy > 95%
5. Set up Cloud Monitoring and alerting
6. Implement incremental indexing

### Deliverables
- Production ML pipeline
- Scalable vector search
- Monitoring dashboard

## 14.3 Phase 3: Enterprise Scale (Weeks 12+)

### Goals
- Enterprise security controls
- Disaster recovery
- Continuous quality assurance

### Actions
1. Implement VPC Service Controls
2. Set up multi-zone deployment
3. Create DR runbooks and test procedures
4. Build continuous quality regression suite
5. Add policy gates for high-stakes queries
6. Implement audit logging

### Deliverables
- Security-hardened deployment
- Tested DR procedures
- Quality regression pipeline

## 14.4 Cost Estimation

### Initial Indexing (10,000 documents)
- Embedding API calls: $50-100
- Compute (Cloud Run): $10-20
- Storage (Vector DB): $5-10
- **Total one-time: ~$75-150**

### Monthly Operations (1,000 queries)
- Vector storage: $10-20
- Query embeddings: $5-10
- LLM generation: $20-50
- Compute: $20-30
- **Total monthly: ~$55-110**

### Cost Optimization Levers
- Chunk size: larger chunks = fewer embeddings
- Context budget: smaller context = fewer LLM tokens
- Re-index frequency: incremental vs full
- Caching: repeated queries

---

# 15. TROUBLESHOOTING

## 15.1 Common Issues

### "ModuleNotFoundError: No module named 'real_estate_rag'"

**Cause:** Package not installed in editable mode.

**Solution:**
```bash
pip install -e ".[dev]"
```

### "ValueError: Embedding dimension mismatch"

**Cause:** Trying to add vectors with different dimensions to existing collection.

**Solution:**
```bash
# Clear the collection
rm -rf ./vector_db

# Or use different collection name
re-rag index --collection new_collection ...
```

### "FileNotFoundError: Vector DB path does not exist"

**Cause:** Trying to query before indexing.

**Solution:**
```bash
# Index first
re-rag index --input-dir ./sample_data ...

# Then query
re-rag ask --question "..." ...
```

### "ValueError: No PDF files found"

**Cause:** Input directory is empty or contains no PDFs.

**Solution:**
```bash
# Check directory contents
ls -la ./sample_data

# Generate sample data if needed
re-rag create-sample-data --output-dir ./sample_data
```

### Pytest import errors

**Cause:** Virtual environment not activated or package not installed.

**Solution:**
```bash
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

### Conda/venv conflict

**Cause:** Both conda and venv active, pytest using wrong Python.

**Solution:**
```bash
conda deactivate
source .venv/bin/activate
pytest -q
```

## 15.2 Debug Mode

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check chunk contents
for chunk in chunks[:5]:
    print(f"ID: {chunk.chunk_id[:16]}")
    print(f"Text: {chunk.text[:100]}...")
    print(f"Metadata: {chunk.silo}, {chunk.page_span}")
    print("---")

# Check retrieval results
response = engine.answer("test query")
for result in response.raw_retrieved_chunks:
    print(f"Score: {result.score:.4f}")
    print(f"Text: {result.text[:100]}...")
```

---

# 16. GLOSSARY

| Term | Definition |
|------|------------|
| **RAG** | Retrieval-Augmented Generation - technique that retrieves relevant context before generating answers |
| **Chunk** | A fixed-size piece of text suitable for embedding and retrieval |
| **Embedding** | Vector representation of text for similarity comparison |
| **Vector Store** | Database optimized for storing and querying vector embeddings |
| **Silo** | Organizational category for documents (e.g., comps, leases) |
| **doc_id** | Stable document identifier (SHA-256 hash of file contents) |
| **chunk_id** | Stable chunk identifier (SHA-256 hash of source + text) |
| **page_span** | Range of pages a chunk or segment originates from |
| **CleanSegment** | Intermediate representation after cleaning, before chunking |
| **TextChunk** | Final representation ready for embedding and indexing |
| **Citation** | Reference linking an answer to its source document and page |
| **Grounding** | Technique ensuring LLM answers use only provided context |
| **ChromaDB** | Open-source embedding database used for vector storage |
| **Vertex AI** | Google Cloud's AI/ML platform |
| **Cap Rate** | Capitalization rate - key real estate valuation metric |
| **NOI** | Net Operating Income - property's income minus operating expenses |
| **Offering Memo** | Marketing document for property sale |
| **Comparable Sales** | Similar property transactions used for valuation |

---

# APPENDIX A: Sample Data Generator

The `scripts/generate_50_samples.py` script creates realistic test data:

**Document Types Generated:**
- Comparable Sales Reports (2 pages): Property details, transaction summary
- Offering Memoranda (3 pages): Executive summary, financials, market overview
- Appraisal Reports (2 pages): Value opinion, income/sales approaches
- Lease Abstracts (1 page): Tenant, terms, rent details
- Financial Statements (1 page): Operating statement, NOI

**Variations Included:**
- Date formats: US (3/7/2025), ISO (2025-03-07), spelled (March 7, 2025)
- Currency formats: spaced ($  1,250,000), compact ($1,250,000), abbreviated ($1.25M)
- Area formats: SF, sq ft, sqft, sq. ft., square feet
- Headers: CONFIDENTIAL, PROPRIETARY, DRAFT, INTERNAL USE ONLY
- Footers: Various legal disclaimers
- Property types: Office, Retail, Industrial, Multifamily, Mixed-Use, etc.
- Locations: 15 different US markets

---

# APPENDIX B: Presentation Materials

**Location:** `presentation/`

**Files:**
- `Real_Estate_RAG_Interview_Presentation.pptx` - 28-slide PowerPoint
- `SPEAKER_SCRIPT.md` - 30-minute speaker script with pause markers
- `generate_presentation.py` - Script to regenerate presentation

**Presentation Structure:**
1. Introduction (3 slides)
2. The Challenge (4 slides)
3. The Solution (4 slides)
4. Live Demo (6 slides)
5. Architecture (4 slides)
6. Business Value (4 slides)
7. Summary & Close (3 slides)

---

# APPENDIX C: Interview Q&A Reference

**Technical Questions:**

Q: "Why not LangChain/LlamaIndex?"
A: Generic loaders don't handle domain-specific noise. Custom cleaning removes headers, normalizes formats.

Q: "How do you handle scanned PDFs?"
A: Flag as scan_suspected, route to Document AI for OCR in production.

Q: "Why local embeddings?"
A: Demo reliability. Same architecture supports Vertex AI via config change.

Q: "What about hallucination?"
A: Grounded prompts + citation tracking + no-evidence handling + score thresholds.

Q: "How does it scale?"
A: Stateless pipeline, parallelizable ingestion, Vertex AI Vector Search for production.

**Business Questions:**

Q: "What's the ROI?"
A: 99% reduction in search time, 20x analyst throughput, automatic audit trail.

Q: "Timeline to production?"
A: 6 weeks pilot, 12 weeks production, 12+ weeks enterprise scale.

Q: "Cost estimate?"
A: $75-150 initial indexing, $55-110/month operations (10K docs, 1K queries).

---

*Document Version: 1.0*
*Last Updated: 2026-04-05*
*Total Sections: 16 + 3 Appendices*
*Estimated Reading Time: 45-60 minutes*
