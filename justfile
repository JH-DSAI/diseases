# Disease Dashboard - Just Commands

# Run development server (builds assets first)
dev:
    uv sync --extra dev
    just js-install
    just js-build
    uv run uvicorn app.main:app --reload --reload-exclude '*.duckdb' --host 0.0.0.0 --port 8000

# Run all tests
test:
    uv run pytest

# Run tests with verbose output
test-v:
    uv run pytest -v

# Run only API tests
test-api:
    uv run pytest tests/api/ -v

# Run only HTML tests
test-html:
    uv run pytest tests/html/ -v

# Run only ETL tests
test-etl:
    uv run pytest tests/etl/ -v

# Run tests without coverage (faster)
test-quick:
    uv run pytest --no-cov -q

# Run tests and generate HTML coverage report
test-cov:
    uv run pytest --cov-report=html
    @echo "Coverage report generated in htmlcov/"

# Build frontend assets (clean first)
js-build:
    rm -rf app/static/dist
    npm run build

js-install:
    npm install

# Run linter
lint:
    uv run ruff check .

# Run linter with auto-fix
lint-fix:
    uv run ruff check . --fix

# Run linter and tests
check:
    uv run ruff check .
    uv run pytest

# Run full CI suite (lint, format check, tests)
ci:
    uv run ruff check .
    uv run ruff format --check .
    uv run pytest -v

# Format code
fmt:
    uv run ruff format .
