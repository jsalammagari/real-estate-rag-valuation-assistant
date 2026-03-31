"""CLI entrypoint for demo-ready ingestion, indexing, and asking."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from real_estate_rag import __version__
from real_estate_rag.chunking import ChunkingConfig, chunk_segments
from real_estate_rag.cleaning import CleaningConfig, clean_documents
from real_estate_rag.embedding import create_embedding_client_from_env
from real_estate_rag.ingestion import ingest_pdf_directory
from real_estate_rag.rag import RagConfig, RagEngine, create_llm_client_from_env
from real_estate_rag.vector_store import ChromaVectorStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="re-rag",
        description="Real Estate RAG Valuation Assistant CLI.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("help", help="Show CLI help.")

    ingest_parser = subparsers.add_parser("ingest", help="Inspect ingestion output only.")
    ingest_parser.add_argument("--input-dir", required=True, help="Directory containing source PDFs.")

    index_parser = subparsers.add_parser(
        "index",
        aliases=["index-local"],
        help="Run ingestion->clean->chunk->embed->index pipeline.",
    )
    index_parser.add_argument("--input-dir", required=True, help="Directory containing source PDFs.")
    index_parser.add_argument(
        "--vector-db-path",
        default=os.getenv("VECTOR_DB_PATH", "./vector_db"),
        help="Persistent Chroma path.",
    )
    index_parser.add_argument(
        "--collection",
        default=os.getenv("VECTOR_DB_COLLECTION", "valuation_chunks"),
        help="Collection name.",
    )
    index_parser.add_argument(
        "--embedding-provider",
        default=os.getenv("EMBEDDING_PROVIDER", "local"),
        choices=["local", "remote_http"],
        help="Embedding provider.",
    )
    index_parser.add_argument(
        "--embedding-dimensions",
        type=int,
        default=int(os.getenv("EMBEDDING_DIMENSIONS", "12")),
        help="Vector dimensions for local provider.",
    )

    ask_parser = subparsers.add_parser(
        "ask",
        aliases=["query-local"],
        help="Ask a valuation question and print grounded answer with citations.",
    )
    ask_parser.add_argument("--question", required=True, help="Query text.")
    ask_parser.add_argument(
        "--vector-db-path",
        default=os.getenv("VECTOR_DB_PATH", "./vector_db"),
        help="Persistent Chroma path.",
    )
    ask_parser.add_argument(
        "--collection",
        default=os.getenv("VECTOR_DB_COLLECTION", "valuation_chunks"),
        help="Collection name.",
    )
    ask_parser.add_argument(
        "--top-k",
        type=int,
        default=int(os.getenv("RAG_TOP_K", "4")),
        help="Number of nearest chunks to return.",
    )
    ask_parser.add_argument(
        "--silo",
        default="",
        help="Optional silo filter.",
    )
    ask_parser.add_argument(
        "--embedding-provider",
        default=os.getenv("EMBEDDING_PROVIDER", "local"),
        choices=["local", "remote_http"],
        help="Embedding provider.",
    )
    ask_parser.add_argument(
        "--embedding-dimensions",
        type=int,
        default=int(os.getenv("EMBEDDING_DIMENSIONS", "12")),
        help="Vector dimensions for local provider.",
    )
    ask_parser.add_argument(
        "--llm-provider",
        default=os.getenv("LLM_PROVIDER", "stub"),
        choices=["stub", "remote_http"],
        help="LLM provider.",
    )
    ask_parser.add_argument(
        "--max-context-chars",
        type=int,
        default=int(os.getenv("RAG_MAX_CONTEXT_CHARS", "1400")),
        help="Maximum context character budget for prompt assembly.",
    )
    ask_parser.add_argument(
        "--min-score",
        type=float,
        default=float(os.getenv("RAG_MIN_SCORE", "-1.0")),
        help="Minimum retrieval score threshold.",
    )

    sample_parser = subparsers.add_parser(
        "create-sample-data",
        help="Generate synthetic PDFs for demos (non-confidential).",
    )
    sample_parser.add_argument("--output-dir", default="./sample_data", help="Output directory.")

    return parser


def app() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command in (None, "help"):
        parser.print_help()
        return 0

    try:
        if args.command == "create-sample-data":
            _create_sample_data(args.output_dir)
            print(json.dumps({"status": "ok", "output_dir": str(Path(args.output_dir).resolve())}))
            return 0

        if args.command == "ingest":
            docs = ingest_pdf_directory(args.input_dir)
            if not docs:
                raise ValueError("No PDF files found under input directory.")
            print(
                json.dumps(
                    {
                        "status": "ok",
                        "documents": len(docs),
                        "pages": sum(doc.total_pages for doc in docs),
                    }
                )
            )
            return 0

        embedding_client = create_embedding_client_from_env(
            args.embedding_provider,
            dimensions=args.embedding_dimensions,
            endpoint=os.getenv("EMBEDDING_API_BASE_URL", ""),
            model=os.getenv("EMBEDDING_MODEL", ""),
            api_key=os.getenv("EMBEDDING_API_KEY", ""),
        )
        store = ChromaVectorStore(args.vector_db_path, args.collection)

        if args.command in ("index", "index-local"):
            docs = ingest_pdf_directory(args.input_dir)
            if not docs:
                raise ValueError("No PDF files found under input directory.")
            cleaned = clean_documents(docs, CleaningConfig())
            if not cleaned:
                raise ValueError("No clean segments produced. Check source corpus quality.")
            chunks = chunk_segments(cleaned, ChunkingConfig())
            if not chunks:
                raise ValueError("No chunks produced for indexing.")
            vectors = embedding_client.embed([chunk.text for chunk in chunks])
            store.upsert(chunks, vectors)
            print(
                json.dumps(
                    {
                        "status": "ok",
                        "documents": len(docs),
                        "clean_segments": len(cleaned),
                        "chunks_indexed": len(chunks),
                        "vector_db_path": args.vector_db_path,
                        "collection": args.collection,
                    }
                )
            )
            return 0

        if args.command in ("ask", "query-local"):
            vector_db_path = Path(args.vector_db_path).expanduser().resolve()
            if not vector_db_path.exists():
                raise FileNotFoundError(f"Vector DB path does not exist: {vector_db_path}")
            if store.count() == 0:
                raise ValueError("Vector collection is empty. Run `re-rag index` first.")

            llm_client = create_llm_client_from_env(
                args.llm_provider,
                endpoint=os.getenv("LLM_API_BASE_URL", ""),
                model=os.getenv("LLM_MODEL", ""),
                api_key=os.getenv("LLM_API_KEY", ""),
            )
            engine = RagEngine(
                embedding_client=embedding_client,
                vector_store=store,
                llm_client=llm_client,
                config=RagConfig(
                    top_k=args.top_k,
                    max_context_chars=args.max_context_chars,
                    min_score=args.min_score,
                ),
            )
            metadata_filter = {"silo": args.silo} if args.silo else None
            response = engine.answer(args.question, metadata_filter=metadata_filter)

            print("ANSWER:")
            print(response.answer_text)
            print("")
            print(f"INSUFFICIENT_EVIDENCE: {response.insufficient_evidence}")
            print("CITATIONS:")
            if not response.citations:
                print("- none")
            for citation in response.citations:
                start_page, end_page = citation.page_span
                print(
                    f"- chunk_id={citation.chunk_id} doc_id={citation.doc_id} "
                    f"page_span={start_page}-{end_page} score={citation.score:.6f}"
                )
            return 0
    except (ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}")
        return 2
    except Exception as exc:  # pragma: no cover
        print(f"ERROR: unexpected failure: {exc}")
        return 1

    parser.print_help()
    return 0


def _create_sample_data(output_dir: str) -> None:
    from reportlab.pdfgen import canvas

    root = Path(output_dir).expanduser().resolve()
    comps_dir = root / "comps"
    memo_dir = root / "offering_memo"
    comps_dir.mkdir(parents=True, exist_ok=True)
    memo_dir.mkdir(parents=True, exist_ok=True)

    _write_pdf(
        comps_dir / "comp_downtown.pdf",
        [
            "CONFIDENTIAL REPORT\nDowntown Tower NOI: $ 1,200,000\nCap rate is 6.1%\nPage 1 of 2",
            "CONFIDENTIAL REPORT\nRent growth outlook stable for 2025\nPage 2 of 2",
        ],
    )
    _write_pdf(
        memo_dir / "memo_suburban.pdf",
        [
            "MEMO HEADER\nSuburban Retail occupancy at 94% on 3/7/2025\nPage 1 of 1",
        ],
    )


def _write_pdf(path: Path, page_texts: list[str]) -> None:
    from reportlab.pdfgen import canvas

    pdf = canvas.Canvas(str(path))
    for text in page_texts:
        y = 780
        for line in text.split("\n"):
            pdf.drawString(72, y, line)
            y -= 18
        pdf.showPage()
    pdf.save()


if __name__ == "__main__":
    raise SystemExit(app())
