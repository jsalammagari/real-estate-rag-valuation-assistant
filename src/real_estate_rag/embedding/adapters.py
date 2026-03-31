"""Embedding adapters for Story 4."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from urllib import request


class EmbeddingClient:
    """Embedding adapter interface."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


@dataclass(frozen=True)
class LocalHashEmbeddingClient(EmbeddingClient):
    """Deterministic local embedding adapter for tests and CI.

    This uses hashed byte windows to produce stable pseudo-vectors.
    It is not semantic and is intended only for development/testing.
    """

    dimensions: int = 12

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            values: list[float] = []
            for i in range(self.dimensions):
                byte = digest[i % len(digest)]
                values.append(round(byte / 255.0, 6))
            vectors.append(values)
        return vectors


@dataclass(frozen=True)
class RemoteHTTPEmbeddingClient(EmbeddingClient):
    """Optional HTTP embedding adapter.

    Expected request shape:
      {"model": "...", "texts": ["..."]}
    Expected response shape:
      {"embeddings": [[...], [...]]}
    """

    endpoint: str
    model: str
    api_key: str
    timeout_seconds: int = 20

    def embed(self, texts: list[str]) -> list[list[float]]:
        payload = json.dumps({"model": self.model, "texts": texts}).encode("utf-8")
        req = request.Request(
            url=self.endpoint,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        with request.urlopen(req, timeout=self.timeout_seconds) as resp:  # nosec B310
            body = resp.read().decode("utf-8")
            data = json.loads(body)
        embeddings = data.get("embeddings")
        if not isinstance(embeddings, list):
            raise ValueError("Remote embedding response missing 'embeddings' list")
        return embeddings


def create_embedding_client_from_env(
    provider: str,
    *,
    dimensions: int = 12,
    endpoint: str = "",
    model: str = "",
    api_key: str = "",
) -> EmbeddingClient:
    """Factory for embedding adapter selection."""
    if provider == "local":
        return LocalHashEmbeddingClient(dimensions=dimensions)
    if provider == "remote_http":
        if not endpoint or not model or not api_key:
            raise ValueError("remote_http provider requires endpoint, model, and api_key")
        return RemoteHTTPEmbeddingClient(endpoint=endpoint, model=model, api_key=api_key)
    raise ValueError(f"Unsupported embedding provider: {provider}")
