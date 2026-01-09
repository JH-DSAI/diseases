"""FastAPI main application entry point"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.database import db
from app.middleware import BasicAuthMiddleware
from app.routers import api, html_api, pages, sql_api
from app.templates import templates

# Static directory path (used for hot reload and static file mounting)
static_dir = Path(__file__).parent / "static"
templates_dir = Path(__file__).parent / "templates"

# Hot reload setup (created early so lifespan can start/stop it)
hot_reload = None
if os.getenv("APP_ENV") == "development":
    import arel

    # Suppress noisy watchfiles debug logs
    logging.getLogger("watchfiles").setLevel(logging.WARNING)

    hot_reload = arel.HotReload(
        paths=[
            arel.Path(str(static_dir)),
            arel.Path(str(templates_dir)),
        ]
    )


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add Cache-Control headers to static assets for better performance."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        # Built assets (CSS/JS bundles) - cache for 1 year (immutable)
        if path.startswith("/static/dist/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        # Other static files - cache for 1 day
        elif path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=86400"
        return response


# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Start hot reload watcher (dev mode only)
    if hot_reload:
        await hot_reload.startup()
        logger.info("Hot reload enabled for development")

    # Initialize database and load data
    try:
        db.connect()
        db.load_all_sources()
        logger.info("Database initialized successfully")

        # Log summary stats
        stats = db.get_summary_stats()
        source_breakdown = stats.get("source_breakdown", {})
        logger.info(
            f"Loaded {stats.get('total_records', 0)} total records from {stats.get('total_states', 0)} states"
        )
        for source, counts in source_breakdown.items():
            logger.info(
                f"  - {source}: {counts.get('records', 0)} records, {counts.get('cases', 0)} cases"
            )

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    yield

    # Shutdown
    logger.info("Shutting down application")
    if hot_reload:
        await hot_reload.shutdown()
    db.close()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="US Disease Tracker Dashboard - Data visualizations for disease surveillance",
    lifespan=lifespan,
)

# Add caching middleware for static assets
app.add_middleware(CacheControlMiddleware)

# Add staging authentication middleware (if enabled)
if settings.staging_auth_enabled:
    app.add_middleware(BasicAuthMiddleware)
    logger.info("Staging authentication enabled")

# Mount static files
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include routers
app.include_router(api.router)
app.include_router(html_api.router)
app.include_router(sql_api.router)
app.include_router(pages.router)

# Register hot reload WebSocket route (dev mode only)
if hot_reload:
    app.add_websocket_route("/hot-reload", route=hot_reload, name="hot-reload")

# Make hot_reload available in all templates
templates.env.globals["hot_reload"] = hot_reload


@app.get("/health")
async def root_health():
    """Root health check endpoint (unauthenticated)"""
    return {"status": "ok", "app": settings.app_name}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)
