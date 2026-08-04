.PHONY: install test lint format typecheck check

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src tests

format:
	ruff format src tests
	ruff check --fix src tests

typecheck:
	mypy src/pytest_pubsub

check: lint typecheck test
