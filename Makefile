# One call = the whole quality gate; CI calls the same target.
PYTEST_ARGS ?=

.PHONY: check check-fast format

check:
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy src/prismql
	uv run pytest $(PYTEST_ARGS)

check-fast:
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy src/prismql
	uv run pytest -m "not slow" $(PYTEST_ARGS)

format:
	uv run ruff format . && uv run ruff check . --fix
