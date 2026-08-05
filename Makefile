.PHONY: install test lint format format-check typecheck check

install:
	uv sync --all-extras

test:
	uv run pytest --cov=pytest_pubsub

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

typecheck:
	uv run mypy src

check: lint format-check typecheck test
