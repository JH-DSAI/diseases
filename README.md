# Disease Dashboard

A FastAPI web application for visualizing and analyzing US disease surveillance data.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121.0-009688.svg)](https://fastapi.tiangolo.com/)
[![UV](https://img.shields.io/badge/Package%20Manager-UV-blueviolet)](https://docs.astral.sh/uv/)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.1.3+-yellow.svg)](https://duckdb.org/)
[![HTMX](https://img.shields.io/badge/HTMX-2.0.8-3366CC.svg)](https://htmx.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-4-38B2AC.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

<!-- Pytest Coverage Comment:Begin -->
<!-- Pytest Coverage Comment:End -->

## Features

- **Interactive Dashboard**: Beautiful data visualizations using D3.js
- **Modern UI**: Built with Tailwind CSS, DaisyUI 5, HTMX, and Alpine.js
- **Fast Data Processing**: DuckDB for efficient querying of disease data
- **JSON API**: RESTful API for programmatic access to disease statistics
- **Authentication**: API key-based authentication for secure access
- **Extensible**: Designed for easy addition of new visualizations and data sources

## Tech Stack

- **Backend**: FastAPI 0.121.0, Python 3.11+
- **Database**: DuckDB (in-memory analytics database)
- **Frontend**:
  - HTMX 2.0.8 (dynamic HTML)
  - Alpine.js 3.15.0 (reactive components)
  - Tailwind CSS + DaisyUI 5.0.0 (styling)
  - D3.js v7 (data visualizations)
- **Package Manager**: uv (fast Python package installer)

## Project Structure

```
disease-dashboard/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── auth.py              # Authentication middleware
│   ├── database.py          # DuckDB connection & data loading
│   ├── models.py            # Pydantic models
│   ├── routers/
│   │   ├── api.py           # JSON API endpoints
│   │   └── pages.py         # HTML page routes
│   ├── static/
│   │   ├── css/             # Custom CSS
│   │   └── js/              # Custom JavaScript
│   └── templates/           # Jinja2 HTML templates
├── us_disease_tracker_data/ # Disease data (CSV files)
├── pyproject.toml           # Project configuration & scripts
├── .env.example             # Environment variable template
├── QUICKSTART.md            # Quick start guide
└── README.md                # This file
```

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package installer

### Installation

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and configure:
   - Generate a secure `SECRET_KEY`
   - Add your API keys to `API_KEYS` (comma-separated)

4. **Generate an API key** (optional, for production):
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Copy the output and add it to your `.env` file.

### Running the Application

**Development mode** (with auto-reload, listens on all interfaces):
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production mode**:
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The application will be available at:
- **Web UI**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

### Authentication

The application uses API key authentication. To access protected endpoints:

1. **Web Browser**: The application will check for API keys in the Authorization header
2. **API Requests**: Include the API key in the Authorization header:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/api/diseases
   ```

**Development Mode**: If no API keys are configured in `.env`, the application allows all access.

## API Endpoints

### Public Endpoints

- `GET /health` - Basic health check (unauthenticated)

### Protected Endpoints (require API key)

- `GET /` - Landing page with disease overview
- `GET /disease/{disease_name}` - Disease-specific detail page
- `GET /api/health` - Detailed health check with database status
- `GET /api/diseases` - List all tracked diseases
- `GET /api/stats` - Summary statistics across all data

## Data

The application loads disease surveillance data from CSV files in the `us_disease_tracker_data/data/states/` directory. Currently tracking:

- **Measles**: Viral respiratory infection
- **Pertussis**: Whooping cough
- **Meningococcus**: Bacterial meningitis

Data includes:
- Temporal trends (weekly/monthly)
- Geographic distribution (state, regional, county levels)
- Age group stratification
- Case confirmation status
- Disease subtypes (e.g., meningococcus serotypes)

## Development

### Adding New Visualizations

1. Create D3.js chart functions in `app/static/js/app.js`
2. Add API endpoints in `app/routers/api.py` to serve the data
3. Update templates in `app/templates/` to include the visualizations
4. Use Alpine.js for reactive data fetching and HTMX for dynamic updates

### Database Queries

Add custom queries in `app/database.py`:

```python
def get_disease_timeseries(self, disease_name: str):
    """Get time series data for a specific disease"""
    return self.conn.execute("""
        SELECT report_period_start, SUM(count) as total_cases
        FROM disease_data
        WHERE disease_name = ?
        GROUP BY report_period_start
        ORDER BY report_period_start
    """, [disease_name]).fetchall()
```

### Testing

Run the test suite:
```bash
uv run pytest
```

Run tests with verbose output:
```bash
uv run pytest -v
```

Run tests with coverage report:
```bash
uv run pytest --cov=app --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

Current test coverage: **85%**

The test suite includes:
- **API endpoint tests**: Authentication, diseases, statistics, health checks
- **Page rendering tests**: Landing page, disease detail pages, error handling
- **Database tests**: Connection, data loading, queries, error scenarios

### Code Quality

Run the linter:
```bash
uv run ruff check .
```

Auto-fix issues:
```bash
uv run ruff check --fix .
```

Format code:
```bash
uv run ruff format .
```

Run both linting and tests:
```bash
uv run ruff check . && uv run pytest
```

## Future Enhancements

- [ ] Additional data visualizations (time series, maps, demographic breakdowns)
- [ ] MCP server for conversational data queries
- [ ] Export functionality (PDF, CSV, JSON)
- [ ] User management and authentication UI
- [ ] Real-time data updates
- [ ] Historical trend analysis
- [ ] Predictive modeling

## License

MIT License

## Support

For issues and questions, please open a GitHub issue.
