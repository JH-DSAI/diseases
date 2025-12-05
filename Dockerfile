# Stage 1: Build frontend assets
FROM node:20-alpine AS frontend-builder

WORKDIR /build

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source files needed for build
COPY vite.config.js tailwind.config.js ./
COPY app/static ./app/static
COPY app/templates ./app/templates

# Build frontend assets
RUN npm run build

# Stage 2: Python application
FROM python:3.11-slim

WORKDIR /app

# Install uv for faster dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# Copy dependency files and README (required by hatchling)
COPY pyproject.toml README.md ./

# Install dependencies (production only, no dev dependencies)
RUN uv pip install --no-cache -e .

# Copy application code
COPY app ./app
COPY us_disease_tracker_data ./us_disease_tracker_data

# Copy built frontend assets from stage 1
COPY --from=frontend-builder /build/app/static/dist ./app/static/dist

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
# --proxy-headers trusts X-Forwarded-* headers from Azure/load balancer
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
