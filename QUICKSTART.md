# Quick Start Guide

## Installation

1. **Install dependencies with uv**:
   ```bash
   uv sync
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env if you want to configure API keys for authentication
   # Leave API_KEYS empty for development (no auth required)
   ```

## Running the Application

### Development mode (recommended)
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production mode
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Access the Application

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## API Endpoints

### Public Endpoints
- `GET /health` - Basic health check (no auth required)

### Protected Endpoints (no auth in dev mode)
- `GET /` - Landing page with "Hello World"
- `GET /api/health` - Detailed health check with database status
- `GET /api/diseases` - List all tracked diseases
- `GET /api/stats` - Summary statistics

### Example API Usage

```bash
# Health check
curl http://localhost:8000/health

# Get list of diseases
curl http://localhost:8000/api/diseases

# Get statistics
curl http://localhost:8000/api/stats
```

## Authentication (Optional)

To enable authentication in production:

1. Generate an API key:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. Add it to `.env`:
   ```
   API_KEYS="your-generated-key-here,another-key-if-needed"
   ```

3. Use the API key in requests:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/api/diseases
   ```

## Data

The application automatically loads disease surveillance data from:
- `us_disease_tracker_data/data/states/`

Currently tracking:
- **Measles**
- **Pertussis** (Whooping Cough)
- **Meningococcus**

Data is loaded into an in-memory DuckDB database on startup.

## Testing

Run the test script to verify everything works:
```bash
uv run python test_app.py
```

## Next Steps

The "Hello World" foundation is now in place. Ready to add:

1. **Data Visualizations**: D3.js charts showing temporal trends, geographic distribution, etc.
2. **Disease-Specific Pages**: Detailed analytics for each disease
3. **MCP Server**: Conversational interface for data queries
4. **Enhanced Features**: Filtering, export functionality, predictive models

See `README.md` for full documentation.
