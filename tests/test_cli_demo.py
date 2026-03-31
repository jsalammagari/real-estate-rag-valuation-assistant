from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest


def _run_cli(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "real_estate_rag.cli.main", *args]
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(cmd, capture_output=True, text=True, env=merged_env, check=False)


pytestmark = pytest.mark.integration


def test_cli_help_lists_demo_subcommands() -> None:
    result = _run_cli(["--help"])
    assert result.returncode == 0
    assert "ingest" in result.stdout
    assert "index" in result.stdout
    assert "ask" in result.stdout
    assert "create-sample-data" in result.stdout


def test_end_to_end_stub_demo_flow(tmp_path: Path) -> None:
    sample_dir = tmp_path / "sample_data"
    vector_dir = tmp_path / "vector_db"

    create_result = _run_cli(["create-sample-data", "--output-dir", str(sample_dir)])
    assert create_result.returncode == 0

    ingest_result = _run_cli(["ingest", "--input-dir", str(sample_dir)])
    assert ingest_result.returncode == 0

    index_result = _run_cli(
        [
            "index",
            "--input-dir",
            str(sample_dir),
            "--vector-db-path",
            str(vector_dir),
            "--collection",
            "test_demo",
            "--embedding-provider",
            "local",
            "--embedding-dimensions",
            "12",
        ]
    )
    assert index_result.returncode == 0

    ask_result = _run_cli(
        [
            "ask",
            "--question",
            "What cap rate evidence exists?",
            "--vector-db-path",
            str(vector_dir),
            "--collection",
            "test_demo",
            "--embedding-provider",
            "local",
            "--embedding-dimensions",
            "12",
            "--llm-provider",
            "stub",
            "--top-k",
            "3",
        ]
    )
    assert ask_result.returncode == 0
    assert "ANSWER:" in ask_result.stdout
    assert "CITATIONS:" in ask_result.stdout
    assert "doc_id=" in ask_result.stdout


@pytest.mark.e2e
def test_e2e_smoke_stub_demo_flow_runtime_bound(tmp_path: Path) -> None:
    sample_dir = tmp_path / "sample_data"
    vector_dir = tmp_path / "vector_db"
    steps = [
        ["create-sample-data", "--output-dir", str(sample_dir)],
        [
            "index",
            "--input-dir",
            str(sample_dir),
            "--vector-db-path",
            str(vector_dir),
            "--collection",
            "test_smoke",
            "--embedding-provider",
            "local",
            "--embedding-dimensions",
            "12",
        ],
        [
            "ask",
            "--question",
            "What occupancy evidence exists?",
            "--vector-db-path",
            str(vector_dir),
            "--collection",
            "test_smoke",
            "--embedding-provider",
            "local",
            "--embedding-dimensions",
            "12",
            "--llm-provider",
            "stub",
            "--top-k",
            "3",
        ],
    ]
    for step in steps:
        result = _run_cli(step)
        assert result.returncode == 0


def test_ask_returns_non_zero_for_missing_vector_path(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing_db"
    result = _run_cli(
        [
            "ask",
            "--question",
            "What is the NOI?",
            "--vector-db-path",
            str(missing_path),
            "--collection",
            "unknown",
            "--embedding-provider",
            "local",
            "--embedding-dimensions",
            "12",
            "--llm-provider",
            "stub",
        ]
    )
    assert result.returncode != 0
    assert "ERROR:" in result.stdout


def test_index_returns_non_zero_for_empty_input_dir(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir(parents=True)
    result = _run_cli(
        [
            "index",
            "--input-dir",
            str(empty_dir),
            "--vector-db-path",
            str(tmp_path / "vector"),
            "--collection",
            "empty_case",
            "--embedding-provider",
            "local",
            "--embedding-dimensions",
            "12",
        ]
    )
    assert result.returncode != 0
    assert "No PDF files found" in result.stdout
