"""RAG orchestration with grounding and citations for Story 6."""

from __future__ import annotations

from dataclasses import dataclass

from real_estate_rag.embedding import EmbeddingClient
from real_estate_rag.rag.llm import LlmClient
from real_estate_rag.vector_store import SearchResult, VectorStore


@dataclass(frozen=True)
class RagConfig:
    """Runtime config for retrieval and context assembly."""

    top_k: int = 4
    max_context_chars: int = 1400
    min_score: float = -1.0


@dataclass(frozen=True)
class Citation:
    """Citation emitted in RAG responses."""

    chunk_id: str
    doc_id: str
    page_span: tuple[int, int]
    score: float


@dataclass(frozen=True)
class RagResponse:
    """Response contract for Story 6."""

    answer_text: str
    citations: tuple[Citation, ...]
    insufficient_evidence: bool
    raw_retrieved_chunks: tuple[SearchResult, ...] = ()


class RagEngine:
    """Orchestrates embed -> retrieve -> context -> generate pipeline."""

    def __init__(
        self,
        *,
        embedding_client: EmbeddingClient,
        vector_store: VectorStore,
        llm_client: LlmClient,
        config: RagConfig | None = None,
    ) -> None:
        self._embedding_client = embedding_client
        self._vector_store = vector_store
        self._llm_client = llm_client
        self._config = config or RagConfig()

    def answer(
        self,
        question: str,
        metadata_filter: dict[str, object] | None = None,
    ) -> RagResponse:
        query_vector = self._embedding_client.embed([question])[0]
        retrieved = self._vector_store.query(
            query_vector,
            top_k=self._config.top_k,
            metadata_filter=metadata_filter,
        )
        filtered = tuple(item for item in retrieved if item.score >= self._config.min_score)
        selected = self._select_context_chunks(filtered)

        if not selected:
            return RagResponse(
                answer_text=(
                    "Insufficient evidence in the indexed documents to answer this question "
                    "reliably. Please ingest more relevant documents or adjust filters."
                ),
                citations=(),
                insufficient_evidence=True,
                raw_retrieved_chunks=filtered,
            )

        prompt = self._build_prompt(question, selected)
        answer_text = self._llm_client.generate(prompt)
        citations = tuple(self._build_citation(item) for item in selected)
        return RagResponse(
            answer_text=answer_text,
            citations=citations,
            insufficient_evidence=False,
            raw_retrieved_chunks=filtered,
        )

    def _select_context_chunks(self, hits: tuple[SearchResult, ...]) -> tuple[SearchResult, ...]:
        selected: list[SearchResult] = []
        used_chars = 0
        for hit in hits:
            chunk_size = len(hit.text)
            if used_chars + chunk_size <= self._config.max_context_chars:
                selected.append(hit)
                used_chars += chunk_size
            elif not selected:
                # If the highest-ranked hit is too large, include a trimmed version.
                trimmed = SearchResult(
                    chunk_id=hit.chunk_id,
                    text=hit.text[: self._config.max_context_chars],
                    score=hit.score,
                    metadata=hit.metadata,
                )
                selected.append(trimmed)
                break
            else:
                break
        return tuple(selected)

    def _build_prompt(self, question: str, hits: tuple[SearchResult, ...]) -> str:
        blocks: list[str] = []
        for idx, hit in enumerate(hits, start=1):
            doc_id = str(hit.metadata.get("doc_id", "unknown_doc"))
            page_start = int(hit.metadata.get("page_start", 0))
            page_end = int(hit.metadata.get("page_end", page_start))
            blocks.append(
                "\n".join(
                    [
                        f"[CONTEXT {idx}]",
                        f"chunk_id={hit.chunk_id}",
                        f"doc_id={doc_id}",
                        f"page_span={page_start}-{page_end}",
                        f"text={hit.text}",
                    ]
                )
            )

        context = "\n\n".join(blocks)
        return (
            "You are a valuation assistant. Use ONLY the provided context snippets.\n"
            "If evidence is incomplete, explicitly say so and avoid fabricating values.\n"
            "Return concise prose and reference context IDs when relevant.\n\n"
            f"Question: {question}\n\n"
            "Context snippets:\n"
            f"{context}\n"
        )

    @staticmethod
    def _build_citation(hit: SearchResult) -> Citation:
        doc_id = str(hit.metadata.get("doc_id", "unknown_doc"))
        page_start = int(hit.metadata.get("page_start", 0))
        page_end = int(hit.metadata.get("page_end", page_start))
        return Citation(
            chunk_id=hit.chunk_id,
            doc_id=doc_id,
            page_span=(page_start, page_end),
            score=hit.score,
        )
