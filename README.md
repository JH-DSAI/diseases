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
<a href="https://github.com/JH-DSAI/diseases/blob/main/README.md"><img alt="Coverage" src="https://img.shields.io/badge/Coverage-91%25-brightgreen.svg" /></a><details><summary>Coverage Report </summary><table><tr><th>File</th><th>Stmts</th><th>Miss</th><th>Cover</th><th>Missing</th></tr><tbody><tr><td colspan="5"><b>app</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py">database.py</a></td><td>201</td><td>13</td><td>94%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L38-L39">38&ndash;39</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L98-L99">98&ndash;99</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L102-L103">102&ndash;103</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L112-L113">112&ndash;113</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L125-L126">125&ndash;126</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L295">295</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L354">354</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/database.py#L531">531</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/dependencies.py">dependencies.py</a></td><td>16</td><td>1</td><td>94%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/dependencies.py#L23">23</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/main.py">main.py</a></td><td>36</td><td>15</td><td>58%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/main.py#L31-L57">31&ndash;57</a></td></tr><tr><td colspan="5"><b>app/etl</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/base.py">base.py</a></td><td>51</td><td>6</td><td>88%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/base.py#L117">117</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/base.py#L130">130</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/base.py#L170-L173">170&ndash;173</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/config.py">config.py</a></td><td>13</td><td>1</td><td>92%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/config.py#L14">14</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/schema.py">schema.py</a></td><td>20</td><td>1</td><td>95%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/schema.py#L12">12</a></td></tr><tr><td colspan="5"><b>app/etl/transformers</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/nndss.py">nndss.py</a></td><td>119</td><td>8</td><td>93%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/nndss.py#L55">55</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/nndss.py#L106-L107">106&ndash;107</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/nndss.py#L147">147</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/nndss.py#L151">151</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/nndss.py#L179-L181">179&ndash;181</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/tracker.py">tracker.py</a></td><td>85</td><td>9</td><td>89%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/tracker.py#L55-L56">55&ndash;56</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/tracker.py#L69-L70">69&ndash;70</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/tracker.py#L73-L74">73&ndash;74</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/tracker.py#L115">115</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/tracker.py#L117">117</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/etl/transformers/tracker.py#L161">161</a></td></tr><tr><td colspan="5"><b>app/routers</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/api.py">api.py</a></td><td>78</td><td>18</td><td>77%</td><td><a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/api.py#L62-L64">62&ndash;64</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/api.py#L81-L83">81&ndash;83</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/api.py#L115-L117">115&ndash;117</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/api.py#L159-L161">159&ndash;161</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/api.py#L190-L192">190&ndash;192</a>, <a href="https://github.com/JH-DSAI/diseases/blob/main/app/routers/api.py#L230-L232">230&ndash;232</a></td></tr><tr><td><b>TOTAL</b></td><td><b>826</b></td><td><b>72</b></td><td><b>91%</b></td><td>&nbsp;</td></tr></tbody></table></details>
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
│   │   ├── css/
│   │   │   ├── app.css      # Tailwind CSS source (with @plugin directives)
│   │   │   └── custom.css   # Additional custom styles
│   │   ├── dist/
│   │   │   ├── main.css     # Built CSS (auto-generated, 88KB)
│   │   │   └── vendor.js    # Built JS bundle (auto-generated, ~150KB)
│   │   └── js/
│   │       ├── vendor.js    # Vendor bundle entry point (HTMX/Alpine/D3)
│   │       ├── app.js       # Custom application JavaScript
│   │       └── *.js         # Other custom scripts
│   └── templates/           # Jinja2 HTML templates
├── us_disease_tracker_data/ # Disease data (CSV files)
├── .github/workflows/       # CI/CD workflows
├── package.json             # Node.js dependencies for CSS build
├── vite.config.js           # Vite build configuration
├── tailwind.config.js       # Tailwind CSS configuration
├── pyproject.toml           # Project configuration & scripts
├── .env.example             # Environment variable template
├── QUICKSTART.md            # Quick start guide
└── README.md                # This file
```

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package installer
- Node.js 18+ and npm (for CSS build process)

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

### Frontend Build

The application uses a Vite build process to bundle CSS and JavaScript for optimal performance.

1. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

2. **Build assets** (one-time):
   ```bash
   npm run build
   ```
   This generates built assets in `app/static/dist/`:
   - `main.css` (88KB) - Tailwind CSS v4 + Typography plugin + DaisyUI components
   - `vendor.js` (~150KB) - HTMX, Alpine.js, and D3.js bundled together

3. **Development mode** (auto-rebuild on changes):
   ```bash
   npm run dev
   ```
   Run this in a separate terminal while developing. It watches for changes to:
   - `app/static/css/app.css` (CSS source)
   - `app/static/js/vendor.js` (vendor bundle entry)
   - `app/templates/**/*.html` (for Tailwind content scanning)
   - `tailwind.config.js`

**Note**: Built assets (`app/static/dist/`) are automatically generated by GitHub Actions on push. For local development, you must run `npm run build` or `npm run dev` at least once.

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

### Frontend Assets

The application uses **Vite** to build and bundle frontend assets for optimal performance.

**Built assets**:
- **CSS** (`app/static/dist/main.css`):
  - Tailwind CSS v4 with utility classes
  - Typography plugin for beautiful prose
  - DaisyUI component styles
- **JavaScript** (`app/static/dist/vendor.js`):
  - HTMX for dynamic HTML updates
  - Alpine.js for reactive components
  - D3.js for data visualizations

**Source files**:
- `app/static/css/app.css` - Main CSS source with `@plugin` directives
- `app/static/js/vendor.js` - Vendor bundle entry point
- `tailwind.config.js` - Tailwind configuration (content paths)
- `vite.config.js` - Build configuration

**To modify styles**:

1. Edit `app/static/css/app.css` or add utility classes in HTML templates
2. Run the dev server to auto-rebuild:
   ```bash
   npm run dev
   ```
3. Built assets will update automatically

**To modify vendor dependencies**:

1. Update `app/static/js/vendor.js` to add/remove libraries
2. Install new packages with `npm install <package>`
3. Run `npm run build` or `npm run dev` to rebuild

**Adding custom CSS**:
- Add utility classes directly in templates
- Or add custom CSS to `app/static/css/custom.css` (loaded separately)

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

### CI/CD

The project includes GitHub Actions workflows for continuous integration:

#### **Build Assets** (`.github/workflows/build-assets.yml`)
- Runs on push/PR when CSS/JS source files change
- Builds frontend assets (CSS + JS) with Vite
- Auto-commits built assets to repository
- Uploads built assets as artifact for download

#### **Tests** (`.github/workflows/test.yml`)
- Runs full test suite with pytest
- Generates coverage report
- Uploads coverage artifacts

#### **Ruff Linting** (`.github/workflows/ruff.yml`)
- Checks code style with Ruff linter
- Verifies code formatting

#### **Coverage Badge** (`.github/workflows/update-coverage-badge.yml`)
- Updates test coverage badge in README

All workflows run automatically on push to `main`/`master` and on pull requests.

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
