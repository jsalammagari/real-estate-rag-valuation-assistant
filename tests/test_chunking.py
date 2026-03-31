from __future__ import annotations

from real_estate_rag.chunking import ChunkingConfig, chunk_segments
from real_estate_rag.cleaning import CleanSegment


def _segment(text: str) -> CleanSegment:
    return CleanSegment(
        text=text,
        doc_id="doc-001",
        page_span=(3, 3),
        silo="comps",
        content_type="narrative",
        normalized_fields={"date_example": "2025-03-07"},
        warnings=("source_warning",),
    )


def test_long_segment_splits_with_bounds_and_overlap() -> None:
    text = "A" * 120 + "B" * 120 + "C" * 120
    config = ChunkingConfig(max_chunk_chars=100, overlap_chars=20)
    chunks = chunk_segments((_segment(text),), config)
    assert len(chunks) > 1
    assert all(len(chunk.text) <= 100 for chunk in chunks)
    for index in range(1, len(chunks)):
        prev = chunks[index - 1].text
        current = chunks[index].text
        assert prev[-20:] == current[:20]


def test_metadata_is_preserved_and_chunk_ids_are_stable() -> None:
    config = ChunkingConfig(max_chunk_chars=50, overlap_chars=10)
    segments = (_segment("x" * 140),)
    first = chunk_segments(segments, config)
    second = chunk_segments(segments, config)
    assert [c.chunk_id for c in first] == [c.chunk_id for c in second]
    assert first[0].doc_id == "doc-001"
    assert first[0].page_span == (3, 3)
    assert first[0].silo == "comps"
    assert first[0].content_type == "narrative"
    assert first[0].normalized_fields["date_example"] == "2025-03-07"
    assert first[0].source_warnings == ("source_warning",)


def test_deterministic_order_for_multiple_segments() -> None:
    segments = (_segment("alpha " * 30), _segment("beta " * 30))
    config = ChunkingConfig(max_chunk_chars=60, overlap_chars=15)
    first = chunk_segments(segments, config)
    second = chunk_segments(segments, config)
    assert [c.text for c in first] == [c.text for c in second]
