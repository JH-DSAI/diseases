# Disease Dashboard - Just Commands

# Run development server
dev:
    uv run uvicorn app.main:app --reload --reload-exclude '*.duckdb' --host 0.0.0.0 --port 8000

# Run tests
test:
    uv run pytest

# Build frontend assets
build:
    npm run build

# Run linter and tests
check:
    uv run ruff check .
    uv run pytest
