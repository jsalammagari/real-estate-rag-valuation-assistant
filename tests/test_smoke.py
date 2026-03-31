import pytest

from real_estate_rag.cli.main import build_parser

pytestmark = pytest.mark.unit


def test_cli_parser_builds() -> None:
    parser = build_parser()
    assert parser.prog == "re-rag"
