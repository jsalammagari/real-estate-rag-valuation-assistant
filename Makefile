.PHONY: install test test-e2e lint ci

install:
	python -m pip install -e ".[dev]"

test:
	pytest -m "not e2e and not network" -q

test-e2e:
	pytest -m "e2e and not network" -q

lint:
	ruff check src tests

ci: lint test test-e2e
