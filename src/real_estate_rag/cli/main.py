"""CLI entrypoint for the project scaffold."""

from __future__ import annotations

import argparse

from real_estate_rag import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="re-rag",
        description="Real Estate RAG Valuation Assistant (scaffold).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="help",
        choices=["help"],
        help="Placeholder command for Story 1 bootstrap.",
    )
    return parser


def app() -> int:
    parser = build_parser()
    parser.parse_args()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(app())
