"""Page-aware deterministic chunking for Story 4."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from real_estate_rag.cleaning import CleanSegment


@dataclass(frozen=True)
class ChunkingConfig:
    """Configuration for character-based chunk splitting."""

    max_chunk_chars: int = 300
    overlap_chars: int = 40


@dataclass(frozen=True)
class TextChunk:
    """Chunk contract for embedding and retrieval."""

    chunk_id: str
    text: str
    doc_id: str
    page_span: tuple[int, int]
    silo: str
    content_type: str
    normalized_fields: dict[str, str]
    source_warnings: tuple[str, ...] = ()
    chunk_index: int = 0
    total_chunks_for_segment: int = 1


def chunk_segments(
    segments: tuple[CleanSegment, ...],
    config: ChunkingConfig | None = None,
) -> tuple[TextChunk, ...]:
    """Chunk cleaned segments into bounded, overlapping units."""
    cfg = config or ChunkingConfig()
    if cfg.max_chunk_chars <= 0:
        raise ValueError("max_chunk_chars must be > 0")
    if cfg.overlap_chars < 0:
        raise ValueError("overlap_chars must be >= 0")
    if cfg.overlap_chars >= cfg.max_chunk_chars:
        raise ValueError("overlap_chars must be smaller than max_chunk_chars")

    output: list[TextChunk] = []
    for segment in segments:
        windows = _split_with_overlap(segment.text, cfg.max_chunk_chars, cfg.overlap_chars)
        total = len(windows)
        for index, text in enumerate(windows):
            output.append(
                TextChunk(
                    chunk_id=_build_chunk_id(segment, index, text),
                    text=text,
                    doc_id=segment.doc_id,
                    page_span=segment.page_span,
                    silo=segment.silo,
                    content_type=segment.content_type,
                    normalized_fields=dict(segment.normalized_fields),
                    source_warnings=segment.warnings,
                    chunk_index=index,
                    total_chunks_for_segment=total,
                )
            )
    return tuple(output)


def _split_with_overlap(text: str, max_chars: int, overlap_chars: int) -> tuple[str, ...]:
    value = text.strip()
    if not value:
        return ()
    if len(value) <= max_chars:
        return (value,)

    chunks: list[str] = []
    step = max_chars - overlap_chars
    start = 0
    text_len = len(value)
    while start < text_len:
        end = min(start + max_chars, text_len)
        chunks.append(value[start:end])
        if end >= text_len:
            break
        start += step
    return tuple(chunks)


def _build_chunk_id(segment: CleanSegment, chunk_index: int, chunk_text: str) -> str:
    payload = "|".join(
        [
            segment.doc_id,
            str(segment.page_span[0]),
            str(segment.page_span[1]),
            segment.silo,
            segment.content_type,
            str(chunk_index),
            chunk_text,
        ]
    )
    return sha256(payload.encode("utf-8")).hexdigest()
