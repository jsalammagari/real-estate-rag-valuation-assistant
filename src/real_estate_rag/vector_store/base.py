"""Vector store interfaces and data contracts."""

from __future__ import annotations

from dataclasses import dataclass

from real_estate_rag.chunking import TextChunk


@dataclass(frozen=True)
class SearchResult:
    """Vector search hit."""

    chunk_id: str
    text: str
    score: float
    metadata: dict[str, object]


class VectorStore:
    """Vector store abstraction for Story 5."""

    def upsert(self, chunks: tuple[TextChunk, ...], embeddings: list[list[float]]) -> None:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError

    def query(
        self,
        vector: list[float],
        top_k: int,
        metadata_filter: dict[str, object] | None = None,
    ) -> tuple[SearchResult, ...]:
        raise NotImplementedError

    def count(self) -> int:
        raise NotImplementedError
