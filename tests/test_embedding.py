from __future__ import annotations

import pytest

from real_estate_rag.embedding import LocalHashEmbeddingClient, create_embedding_client_from_env


def test_local_hash_embedding_shape_and_determinism() -> None:
    client = LocalHashEmbeddingClient(dimensions=8)
    texts = ["Property A NOI", "Property B cap rate"]
    first = client.embed(texts)
    second = client.embed(texts)
    assert len(first) == len(texts)
    assert len(first[0]) == 8
    assert len(first[1]) == 8
    assert first == second


def test_embedding_factory_local_provider() -> None:
    client = create_embedding_client_from_env("local", dimensions=10)
    vectors = client.embed(["hello"])
    assert len(vectors) == 1
    assert len(vectors[0]) == 10


def test_embedding_factory_remote_requires_params() -> None:
    with pytest.raises(ValueError):
        create_embedding_client_from_env("remote_http")
