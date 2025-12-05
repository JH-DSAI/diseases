"""FastAPI main application entry point"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import db
from app.middleware import BasicAuthMiddleware
from app.routers import api, html_api, pages

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
    db.close()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="US Disease Tracker Dashboard - Data visualizations for disease surveillance",
    lifespan=lifespan,
)

# Add staging authentication middleware (if enabled)
if settings.staging_auth_enabled:
    app.add_middleware(BasicAuthMiddleware)
    logger.info("Staging authentication enabled")

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include routers
app.include_router(api.router)
app.include_router(html_api.router)
app.include_router(pages.router)


@app.get("/health")
async def root_health():
    """Root health check endpoint (unauthenticated)"""
    return {"status": "ok", "app": settings.app_name}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)
