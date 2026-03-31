"""CLI entrypoint for ingestion and local vector indexing."""

from __future__ import annotations

import argparse
import json
import os

from real_estate_rag import __version__
from real_estate_rag.chunking import ChunkingConfig, chunk_segments
from real_estate_rag.cleaning import CleaningConfig, clean_documents
from real_estate_rag.embedding import create_embedding_client_from_env
from real_estate_rag.ingestion import ingest_pdf_directory
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

    index_parser = subparsers.add_parser("index-local", help="Run local index pipeline.")
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

    query_parser = subparsers.add_parser("query-local", help="Query local vector store.")
    query_parser.add_argument("--question", required=True, help="Query text.")
    query_parser.add_argument(
        "--vector-db-path",
        default=os.getenv("VECTOR_DB_PATH", "./vector_db"),
        help="Persistent Chroma path.",
    )
    query_parser.add_argument(
        "--collection",
        default=os.getenv("VECTOR_DB_COLLECTION", "valuation_chunks"),
        help="Collection name.",
    )
    query_parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of nearest chunks to return.",
    )
    query_parser.add_argument(
        "--silo",
        default="",
        help="Optional silo filter.",
    )
    query_parser.add_argument(
        "--embedding-provider",
        default=os.getenv("EMBEDDING_PROVIDER", "local"),
        choices=["local", "remote_http"],
        help="Embedding provider.",
    )
    query_parser.add_argument(
        "--embedding-dimensions",
        type=int,
        default=int(os.getenv("EMBEDDING_DIMENSIONS", "12")),
        help="Vector dimensions for local provider.",
    )

    return parser


def app() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command in (None, "help"):
        parser.print_help()
        return 0

    embedding_client = create_embedding_client_from_env(
        args.embedding_provider,
        dimensions=args.embedding_dimensions,
        endpoint=os.getenv("EMBEDDING_API_BASE_URL", ""),
        model=os.getenv("EMBEDDING_MODEL", ""),
        api_key=os.getenv("EMBEDDING_API_KEY", ""),
    )

    store = ChromaVectorStore(args.vector_db_path, args.collection)

    if args.command == "index-local":
        docs = ingest_pdf_directory(args.input_dir)
        cleaned = clean_documents(docs, CleaningConfig())
        chunks = chunk_segments(cleaned, ChunkingConfig())
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

    if args.command == "query-local":
        query_vector = embedding_client.embed([args.question])[0]
        metadata_filter = {"silo": args.silo} if args.silo else None
        results = store.query(query_vector, top_k=args.top_k, metadata_filter=metadata_filter)
        for index, hit in enumerate(results, start=1):
            print(f"[{index}] score={hit.score:.6f} chunk_id={hit.chunk_id}")
            print(f"text={hit.text}")
            print(f"metadata={json.dumps(hit.metadata, sort_keys=True)}")
            print("---")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(app())
