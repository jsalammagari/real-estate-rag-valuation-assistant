"""PDF ingestion and page-level extraction.

Story 2 scope:
- discover PDFs by directory walk
- assign stable document IDs
- extract page text with page-level metadata
- emit machine-readable scan-like warnings for low-text pages
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class PageExtraction:
    """Extraction result for a single page."""

    page_index: int
    text: str
    char_count: int
    scan_suspected: bool
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class IngestedDocument:
    """Extraction result for a single PDF document."""

    doc_id: str
    file_path: str
    relative_path: str
    file_name: str
    silo: str
    total_pages: int
    pages: tuple[PageExtraction, ...]
    warnings: tuple[str, ...] = ()


def discover_pdf_files(input_dir: Path | str) -> list[Path]:
    """Recursively discover PDF files under an input directory."""
    root = Path(input_dir).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Input directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {root}")
    return sorted(root.rglob("*.pdf"))


def compute_doc_id(file_path: Path | str) -> str:
    """Create a stable doc_id from file bytes using SHA-256."""
    path = Path(file_path).expanduser().resolve()
    digest = sha256(path.read_bytes()).hexdigest()
    return digest


def infer_silo(
    file_path: Path | str,
    root_dir: Path | str,
    silo_mapping: dict[str, str] | None = None,
) -> str:
    """Infer silo from the top-level subfolder beneath root_dir.

    Example:
      root_dir=/tmp/data
      file_path=/tmp/data/comps/doc1.pdf
      => silo='comps'
    """
    path = Path(file_path).expanduser().resolve()
    root = Path(root_dir).expanduser().resolve()
    relative_parts = path.relative_to(root).parts
    inferred = relative_parts[0] if len(relative_parts) > 1 else "default"
    if silo_mapping:
        return silo_mapping.get(inferred, inferred)
    return inferred


def extract_pdf_document(
    file_path: Path | str,
    *,
    root_dir: Path | str,
    low_text_threshold: int = 25,
    silo_mapping: dict[str, str] | None = None,
) -> IngestedDocument:
    """Extract page-level text and metadata from one PDF."""
    path = Path(file_path).expanduser().resolve()
    root = Path(root_dir).expanduser().resolve()
    reader = PdfReader(str(path))

    pages: list[PageExtraction] = []
    doc_warnings: list[str] = []

    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        char_count = len(text)
        page_warnings: list[str] = []

        if char_count == 0:
            page_warnings.append("empty_page_text")
        if char_count < low_text_threshold:
            page_warnings.append("low_text_scan_suspected")

        scan_suspected = "low_text_scan_suspected" in page_warnings
        pages.append(
            PageExtraction(
                page_index=index,
                text=text,
                char_count=char_count,
                scan_suspected=scan_suspected,
                warnings=tuple(page_warnings),
            )
        )

    if any(page.scan_suspected for page in pages):
        doc_warnings.append("contains_scan_suspected_pages")

    return IngestedDocument(
        doc_id=compute_doc_id(path),
        file_path=str(path),
        relative_path=str(path.relative_to(root)),
        file_name=path.name,
        silo=infer_silo(path, root, silo_mapping=silo_mapping),
        total_pages=len(pages),
        pages=tuple(pages),
        warnings=tuple(doc_warnings),
    )


def ingest_pdf_directory(
    input_dir: Path | str,
    *,
    low_text_threshold: int = 25,
    silo_mapping: dict[str, str] | None = None,
) -> tuple[IngestedDocument, ...]:
    """Ingest all PDFs under a directory with page-level extraction."""
    root = Path(input_dir).expanduser().resolve()
    documents: list[IngestedDocument] = []
    for pdf_path in discover_pdf_files(root):
        document = extract_pdf_document(
            pdf_path,
            root_dir=root,
            low_text_threshold=low_text_threshold,
            silo_mapping=silo_mapping,
        )
        documents.append(document)
    return tuple(documents)
