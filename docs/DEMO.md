# Demo Runbook (Story 7)

This runbook provides a 60-120 second, interview-ready demo path using only
synthetic data and local/stub providers.

## Prerequisites

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Demo in 3 commands

```bash
re-rag create-sample-data --output-dir ./sample_data
re-rag index --input-dir ./sample_data --vector-db-path ./vector_db --collection valuation_chunks --embedding-provider local --embedding-dimensions 12
re-rag ask --question "What cap rate evidence exists?" --vector-db-path ./vector_db --collection valuation_chunks --embedding-provider local --embedding-dimensions 12 --llm-provider stub --top-k 3
```

Expected output shape for `ask`:
- `ANSWER:`
- `INSUFFICIENT_EVIDENCE: <true|false>`
- `CITATIONS:`
- citation lines containing `chunk_id`, `doc_id`, and `page_span`

## Example questions (fictional only)

1. `What cap rate evidence exists?`
2. `What occupancy signals are present in offering memos?`

## Fallback path (API disabled)

Use local/stub defaults:
- `EMBEDDING_PROVIDER=local`
- `LLM_PROVIDER=stub`

This path requires no paid API keys and is deterministic enough for rehearsal.

## Screen-share hygiene

- Share a single terminal or browser tab, not the full desktop.
- Keep personal notes in a separate non-shared window/device.
- Avoid opening confidential apps, customer files, or messaging tools during demo.
