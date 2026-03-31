from __future__ import annotations

from pathlib import Path

import pytest

from real_estate_rag.chunking import ChunkingConfig, chunk_segments
from real_estate_rag.cleaning import CleanSegment
from real_estate_rag.embedding import LocalHashEmbeddingClient
from real_estate_rag.vector_store import ChromaVectorStore


def _segments() -> tuple[CleanSegment, ...]:
    return (
        CleanSegment(
            text="Downtown office NOI 1200000 and cap rate 6.1%",
            doc_id="doc-a",
            page_span=(1, 1),
            silo="comps",
            content_type="narrative",
            normalized_fields={"cap_rate": "6.1%"},
            warnings=(),
        ),
        CleanSegment(
            text="Suburban retail occupancy 94% with recent lease activity",
            doc_id="doc-b",
            page_span=(2, 2),
            silo="offering_memo",
            content_type="narrative",
            normalized_fields={},
            warnings=(),
        ),
    )


def test_persistence_across_store_reinstantiation(tmp_path: Path) -> None:
    chunks = chunk_segments(_segments(), ChunkingConfig(max_chunk_chars=120, overlap_chars=20))
    embedder = LocalHashEmbeddingClient(dimensions=10)
    vectors = embedder.embed([chunk.text for chunk in chunks])
    vector_path = tmp_path / "chroma"

    store = ChromaVectorStore(str(vector_path), "test_collection")
    store.upsert(chunks, vectors)

    # Simulate new process by new store instance over same persist path.
    reloaded = ChromaVectorStore(str(vector_path), "test_collection")
    query_vec = embedder.embed(["Downtown office NOI"])[0]
    results = reloaded.query(query_vec, top_k=3)
    assert len(results) >= 1


def test_metadata_filter_narrows_results(tmp_path: Path) -> None:
    chunks = chunk_segments(_segments(), ChunkingConfig(max_chunk_chars=120, overlap_chars=20))
    embedder = LocalHashEmbeddingClient(dimensions=10)
    vectors = embedder.embed([chunk.text for chunk in chunks])
    store = ChromaVectorStore(str(tmp_path / "chroma"), "filter_collection")
    store.upsert(chunks, vectors)

    query_vec = embedder.embed(["occupancy and lease activity"])[0]
    all_results = store.query(query_vec, top_k=5)
    filtered_results = store.query(
        query_vec,
        top_k=5,
        metadata_filter={"silo": "offering_memo"},
    )
    assert len(all_results) >= len(filtered_results)
    assert len(filtered_results) >= 1
    assert all(hit.metadata.get("silo") == "offering_memo" for hit in filtered_results)


def test_upsert_is_idempotent_and_no_duplicates(tmp_path: Path) -> None:
    chunks = chunk_segments((_segments()[0],), ChunkingConfig(max_chunk_chars=120, overlap_chars=20))
    embedder = LocalHashEmbeddingClient(dimensions=10)
    vectors = embedder.embed([chunk.text for chunk in chunks])
    store = ChromaVectorStore(str(tmp_path / "chroma"), "idempotent_collection")
    store.upsert(chunks, vectors)
    store.upsert(chunks, vectors)

    query_vec = embedder.embed(["NOI cap rate"])[0]
    results = store.query(query_vec, top_k=10)
    unique_ids = {result.chunk_id for result in results}
    assert len(unique_ids) == len(results)


def test_dimension_mismatch_raises_clear_error(tmp_path: Path) -> None:
    chunks = chunk_segments((_segments()[0],), ChunkingConfig(max_chunk_chars=120, overlap_chars=20))
    store = ChromaVectorStore(str(tmp_path / "chroma"), "dimension_collection")

    small = LocalHashEmbeddingClient(dimensions=8).embed([chunks[0].text])
    store.upsert(chunks, small)

    large = LocalHashEmbeddingClient(dimensions=12).embed([chunks[0].text])
    with pytest.raises(ValueError, match="Embedding dimension mismatch"):
        store.upsert(chunks, large)


def test_stored_embeddings_align_with_adapter_output(tmp_path: Path) -> None:
    chunks = chunk_segments((_segments()[0],), ChunkingConfig(max_chunk_chars=120, overlap_chars=20))
    embedder = LocalHashEmbeddingClient(dimensions=10)
    vectors = embedder.embed([chunks[0].text])
    store = ChromaVectorStore(str(tmp_path / "chroma"), "alignment_collection")
    store.upsert(chunks, vectors)

    stored = store.get_embeddings([chunks[0].chunk_id])
    assert len(stored) == 1
    assert pytest.approx(stored[0], rel=1e-6, abs=1e-6) == vectors[0]
