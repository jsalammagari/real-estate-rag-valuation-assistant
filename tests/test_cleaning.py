from __future__ import annotations

import pytest

from real_estate_rag.cleaning import CleaningConfig, clean_ingested_document
from real_estate_rag.ingestion import IngestedDocument, PageExtraction

pytestmark = pytest.mark.unit


def _doc(pages: tuple[PageExtraction, ...]) -> IngestedDocument:
    return IngestedDocument(
        doc_id="doc-123",
        file_path="/tmp/comps/mock.pdf",
        relative_path="comps/mock.pdf",
        file_name="mock.pdf",
        silo="comps",
        total_pages=len(pages),
        pages=pages,
        warnings=("contains_scan_suspected_pages",),
    )


def test_noise_reduction_removes_repeated_header_footer() -> None:
    page_one = PageExtraction(
        page_index=1,
        text="CONFIDENTIAL REPORT\nProperty Revenue is $ 1,200,000\nPage 1 of 2",
        char_count=64,
        scan_suspected=False,
        warnings=(),
    )
    page_two = PageExtraction(
        page_index=2,
        text="CONFIDENTIAL REPORT\nProperty Revenue is $1,200,000\nPage 2 of 2",
        char_count=63,
        scan_suspected=False,
        warnings=(),
    )
    segments = clean_ingested_document(_doc((page_one, page_two)), CleaningConfig(min_text_length=10))
    assert len(segments) == 1
    assert "CONFIDENTIAL REPORT" not in segments[0].text
    assert "Page 1 of 2" not in segments[0].text
    assert "removed_repeated_header_footer" in segments[0].warnings


def test_currency_and_date_normalization_preserves_other_text() -> None:
    page = PageExtraction(
        page_index=1,
        text="NOI noted on 3/7/2025 at $ 1,250,000 and location Midtown",
        char_count=70,
        scan_suspected=False,
        warnings=(),
    )
    segments = clean_ingested_document(_doc((page,)), CleaningConfig(min_text_length=10))
    assert len(segments) == 1
    text = segments[0].text
    assert "2025-03-07" in text
    assert "$1,250,000" in text
    assert "Midtown" in text
    assert segments[0].normalized_fields["date_example"] == "2025-03-07"


def test_quality_gate_drops_short_fragments() -> None:
    short = PageExtraction(
        page_index=1,
        text="x",
        char_count=1,
        scan_suspected=True,
        warnings=("low_text_scan_suspected",),
    )
    segments = clean_ingested_document(_doc((short,)), CleaningConfig(min_text_length=15))
    assert segments == ()


def test_near_duplicate_pages_retain_single_segment() -> None:
    p1 = PageExtraction(
        page_index=1,
        text="Cap rate is 6.2% for subject property",
        char_count=40,
        scan_suspected=False,
        warnings=(),
    )
    p2 = PageExtraction(
        page_index=2,
        text="Cap rate is 6.2% for subject property",
        char_count=40,
        scan_suspected=False,
        warnings=(),
    )
    segments = clean_ingested_document(_doc((p1, p2)), CleaningConfig(min_text_length=10))
    assert len(segments) == 1
    assert segments[0].normalized_fields["cap_rate"] == "6.2%"


def test_silo_and_warning_passthrough() -> None:
    page = PageExtraction(
        page_index=1,
        text="Building area 12500 SF",
        char_count=22,
        scan_suspected=True,
        warnings=("low_text_scan_suspected",),
    )
    segments = clean_ingested_document(_doc((page,)), CleaningConfig(min_text_length=10))
    assert len(segments) == 1
    segment = segments[0]
    assert segment.doc_id == "doc-123"
    assert segment.page_span == (1, 1)
    assert segment.silo == "comps"
    assert "scan_suspected" in segment.warnings
    assert "contains_scan_suspected_pages" in segment.warnings
    assert "sqft" in segment.text
