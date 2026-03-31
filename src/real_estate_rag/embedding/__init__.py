"""Embedding adapter exports."""

from .adapters import (
    EmbeddingClient,
    LocalHashEmbeddingClient,
    RemoteHTTPEmbeddingClient,
    create_embedding_client_from_env,
)

__all__ = [
    "EmbeddingClient",
    "LocalHashEmbeddingClient",
    "RemoteHTTPEmbeddingClient",
    "create_embedding_client_from_env",
]
