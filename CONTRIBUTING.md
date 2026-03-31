# Contributing and Test Commands

This project is designed to run fully offline in default test mode using
synthetic data and stub/local providers.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Local quality commands

- `make lint`  
  Runs static checks (`ruff check src tests`).

- `make test`  
  Runs default offline unit/integration suite (`pytest -m "not e2e and not network"`).

- `make test-e2e`  
  Runs CLI smoke e2e tests (`pytest -m "e2e and not network"`).

- `make ci`  
  Aggregates `lint + test + test-e2e`.

## Test marker policy

- `unit`: fast deterministic unit tests
- `integration`: local integration tests (no external network)
- `e2e`: full pipeline smoke tests
- `network`: external-network tests (opt-in only, skipped in CI by default)

## Failure interpretation

- Lint failures: style/static issues; fix before commit.
- Unit/integration failures: functional regressions in module logic.
- E2E failures: demo-path breakages (`create-sample-data -> index -> ask`).

## Confidentiality

Contributions must use synthetic/non-confidential fixtures only. Do not commit
customer names, proprietary documents, secrets, or logos.
