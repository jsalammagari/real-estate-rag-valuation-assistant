"""Chroma-backed persistent vector store implementation."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import chromadb

from real_estate_rag.chunking import TextChunk
from real_estate_rag.vector_store.base import SearchResult, VectorStore


class ChromaVectorStore(VectorStore):
    """Persistent local vector store via Chroma."""

    def __init__(self, persist_path: str, collection_name: str = "valuation_chunks") -> None:
        path = Path(persist_path).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(path))
        self._collection_name = collection_name
        self._collection = self._client.get_or_create_collection(name=collection_name)

    def upsert(self, chunks: tuple[TextChunk, ...], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        if not chunks:
            return

        dims = len(embeddings[0])
        if any(len(vec) != dims for vec in embeddings):
            raise ValueError("embedding vectors must all have identical dimensions")
        self._validate_dimension_consistency(dims)

        ids = [chunk.chunk_id for chunk in chunks]
        docs = [chunk.text for chunk in chunks]
        metadatas = [self._chunk_to_metadata(chunk) for chunk in chunks]

        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=docs,
            metadatas=metadatas,
        )

    def clear(self) -> None:
        self._client.delete_collection(self._collection_name)
        self._collection = self._client.get_or_create_collection(name=self._collection_name)

    def query(
        self,
        vector: list[float],
        top_k: int,
        metadata_filter: dict[str, object] | None = None,
    ) -> tuple[SearchResult, ...]:
        where = metadata_filter if metadata_filter else None
        result = self._collection.query(
            query_embeddings=[vector],
            n_results=top_k,
            where=where,
        )

        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        output: list[SearchResult] = []
        for chunk_id, text, metadata, distance in zip(ids, docs, metadatas, distances):
            score = 1.0 - float(distance)
            output.append(
                SearchResult(
                    chunk_id=chunk_id,
                    text=text or "",
                    score=score,
                    metadata=metadata or {},
                )
            )
        return tuple(output)

    def get_embeddings(self, chunk_ids: list[str]) -> list[list[float]]:
        """Return stored embeddings for test and validation flows."""
        result = self._collection.get(ids=chunk_ids, include=["embeddings"])
        embeddings = result.get("embeddings", [])
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()
        return embeddings if isinstance(embeddings, list) else []

    def _validate_dimension_consistency(self, incoming_dim: int) -> None:
        peek = self._collection.peek(limit=1)
        existing_embeddings = peek.get("embeddings", [])
        if existing_embeddings is None or len(existing_embeddings) == 0:
            return
        existing_dim = len(existing_embeddings[0])
        if existing_dim != incoming_dim:
            raise ValueError(
                f"Embedding dimension mismatch: existing={existing_dim}, incoming={incoming_dim}"
            )

    @staticmethod
    def _chunk_to_metadata(chunk: TextChunk) -> dict[str, Any]:
        metadata = asdict(chunk)
        metadata.pop("text", None)
        metadata.pop("page_span", None)
        metadata["page_start"] = chunk.page_span[0]
        metadata["page_end"] = chunk.page_span[1]
        metadata["page_span"] = f"{chunk.page_span[0]}-{chunk.page_span[1]}"
        metadata["source_warnings"] = "|".join(chunk.source_warnings)
        for key, value in chunk.normalized_fields.items():
            metadata[f"norm_{key}"] = value
        metadata.pop("normalized_fields", None)
        return metadata
