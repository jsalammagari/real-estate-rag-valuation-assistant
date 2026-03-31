from __future__ import annotations

from pathlib import Path

import pytest

from real_estate_rag.ingestion import (
    discover_pdf_files,
    extract_pdf_document,
    ingest_pdf_directory,
)
from tests.fixtures import write_pdf


pytestmark = pytest.mark.unit


def test_discovery_and_silo_inference(tmp_path: Path) -> None:
    comps_dir = tmp_path / "comps"
    memo_dir = tmp_path / "offering_memo"
    comps_dir.mkdir(parents=True)
    memo_dir.mkdir(parents=True)

    pdf_a = comps_dir / "comp_1.pdf"
    pdf_b = memo_dir / "memo_1.pdf"
    write_pdf(pdf_a, ["Comp A page 1", "Comp A page 2"])
    write_pdf(pdf_b, ["Memo A page 1"])

    discovered = discover_pdf_files(tmp_path)
    assert discovered == [pdf_a, pdf_b]

    docs = ingest_pdf_directory(tmp_path)
    assert len(docs) == 2
    silos = {doc.file_name: doc.silo for doc in docs}
    assert silos["comp_1.pdf"] == "comps"
    assert silos["memo_1.pdf"] == "offering_memo"


def test_page_count_and_no_cross_page_merge(tmp_path: Path) -> None:
    source_dir = tmp_path / "comps"
    source_dir.mkdir(parents=True)
    pdf_path = source_dir / "property.pdf"
    write_pdf(pdf_path, ["First page text", "Second page text"])

    document = extract_pdf_document(pdf_path, root_dir=tmp_path)
    assert document.total_pages == 2
    assert document.pages[0].text == "First page text"
    assert document.pages[1].text == "Second page text"
    assert document.pages[0].text != document.pages[1].text


def test_doc_id_is_stable_for_same_file(tmp_path: Path) -> None:
    source_dir = tmp_path / "leases"
    source_dir.mkdir(parents=True)
    pdf_path = source_dir / "lease.pdf"
    write_pdf(pdf_path, ["Lease page 1"])

    first = extract_pdf_document(pdf_path, root_dir=tmp_path)
    second = extract_pdf_document(pdf_path, root_dir=tmp_path)
    assert first.doc_id == second.doc_id


def test_low_text_pages_are_flagged_as_scan_suspected(tmp_path: Path) -> None:
    source_dir = tmp_path / "comps"
    source_dir.mkdir(parents=True)
    pdf_path = source_dir / "low_text.pdf"
    write_pdf(pdf_path, ["x", ""])

    document = extract_pdf_document(pdf_path, root_dir=tmp_path, low_text_threshold=5)
    assert document.total_pages == 2
    assert document.pages[0].scan_suspected is True
    assert "low_text_scan_suspected" in document.pages[0].warnings
    assert document.pages[1].scan_suspected is True
    assert "empty_page_text" in document.pages[1].warnings
    assert "contains_scan_suspected_pages" in document.warnings
