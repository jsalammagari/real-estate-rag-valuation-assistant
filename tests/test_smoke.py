from real_estate_rag.cli.main import build_parser


def test_cli_parser_builds() -> None:
    parser = build_parser()
    assert parser.prog == "re-rag"
