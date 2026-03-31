from __future__ import annotations

from dataclasses import dataclass

from real_estate_rag.embedding import EmbeddingClient
from real_estate_rag.rag import LlmClient, RagConfig, RagEngine
from real_estate_rag.vector_store import SearchResult, VectorStore


@dataclass
class FakeEmbeddingClient(EmbeddingClient):
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


@dataclass
class RecordingLlmClient(LlmClient):
    called: bool = False
    last_prompt: str = ""

    def generate(self, prompt: str) -> str:
        self.called = True
        self.last_prompt = prompt
        return "Grounded response from model."


@dataclass
class FakeVectorStore(VectorStore):
    hits: tuple[SearchResult, ...]
    last_filter: dict[str, object] | None = None

    def upsert(self, chunks, embeddings) -> None:  # pragma: no cover - not used in this test
        return None

    def clear(self) -> None:  # pragma: no cover - not used in this test
        return None

    def query(self, vector, top_k, metadata_filter=None) -> tuple[SearchResult, ...]:
        self.last_filter = metadata_filter
        return self.hits[:top_k]


def test_rag_answer_includes_citations_and_grounded_prompt() -> None:
    hits = (
        SearchResult(
            chunk_id="chunk-1",
            text="NOI is 1200000 and cap rate is 6.1% for Property A.",
            score=0.92,
            metadata={"doc_id": "doc-a", "page_start": 3, "page_end": 3, "silo": "comps"},
        ),
    )
    llm = RecordingLlmClient()
    store = FakeVectorStore(hits=hits)
    engine = RagEngine(
        embedding_client=FakeEmbeddingClient(),
        vector_store=store,
        llm_client=llm,
        config=RagConfig(top_k=3, max_context_chars=500, min_score=0.0),
    )

    response = engine.answer("What is the cap rate?", metadata_filter={"silo": "comps"})
    assert llm.called is True
    assert "NOI is 1200000 and cap rate is 6.1% for Property A." in llm.last_prompt
    assert "[CONTEXT 1]" in llm.last_prompt
    assert response.insufficient_evidence is False
    assert len(response.citations) == 1
    assert response.citations[0].doc_id == "doc-a"
    assert response.citations[0].page_span == (3, 3)
    assert response.citations[0].chunk_id == "chunk-1"
    assert store.last_filter == {"silo": "comps"}


def test_no_evidence_path_skips_llm_and_returns_safe_response() -> None:
    llm = RecordingLlmClient()
    store = FakeVectorStore(hits=())
    engine = RagEngine(
        embedding_client=FakeEmbeddingClient(),
        vector_store=store,
        llm_client=llm,
        config=RagConfig(top_k=3, max_context_chars=500, min_score=0.0),
    )

    response = engine.answer("What is the valuation?")
    assert llm.called is False
    assert response.insufficient_evidence is True
    assert len(response.citations) == 0
    assert "Insufficient evidence" in response.answer_text


def test_context_budget_trims_to_fit() -> None:
    long_text = "x" * 500
    hits = (
        SearchResult(
            chunk_id="chunk-1",
            text=long_text,
            score=0.8,
            metadata={"doc_id": "doc-a", "page_start": 1, "page_end": 1},
        ),
        SearchResult(
            chunk_id="chunk-2",
            text="short",
            score=0.7,
            metadata={"doc_id": "doc-a", "page_start": 2, "page_end": 2},
        ),
    )
    llm = RecordingLlmClient()
    store = FakeVectorStore(hits=hits)
    engine = RagEngine(
        embedding_client=FakeEmbeddingClient(),
        vector_store=store,
        llm_client=llm,
        config=RagConfig(top_k=3, max_context_chars=100, min_score=0.0),
    )
    _ = engine.answer("Summarize context")
    assert len(llm.last_prompt) > 0
    assert "chunk-2" not in llm.last_prompt


def test_min_score_filter_can_trigger_insufficient_evidence() -> None:
    hits = (
        SearchResult(
            chunk_id="chunk-low",
            text="weak match",
            score=0.1,
            metadata={"doc_id": "doc-z", "page_start": 1, "page_end": 1},
        ),
    )
    llm = RecordingLlmClient()
    store = FakeVectorStore(hits=hits)
    engine = RagEngine(
        embedding_client=FakeEmbeddingClient(),
        vector_store=store,
        llm_client=llm,
        config=RagConfig(top_k=3, max_context_chars=200, min_score=0.5),
    )
    response = engine.answer("Any valuation?")
    assert response.insufficient_evidence is True
    assert llm.called is False
