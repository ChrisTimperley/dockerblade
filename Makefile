.PHONY: check install test lint publish

lint:
	poetry run ruff check src
	poetry run mypy src

test:
	poetry run pytest

install:
	poetry install --with dev

publish:
	poetry publish --build

check: lint test
