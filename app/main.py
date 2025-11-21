"""FastAPI main application entry point"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.database import db
from app.routers import api, pages

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
        db.load_csv_files()
        db.load_nndss_csv()
        logger.info("Database initialized successfully")

        # Log summary stats
        stats = db.get_summary_stats()
        source_breakdown = stats.get('source_breakdown', {})
        logger.info(f"Loaded {stats.get('total_records', 0)} total records from {stats.get('total_states', 0)} states")
        for source, counts in source_breakdown.items():
            logger.info(f"  - {source}: {counts.get('records', 0)} records, {counts.get('cases', 0)} cases")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    yield

    # Shutdown
    logger.info("Shutting down application")
    db.close()


class CookieAuthMiddleware(BaseHTTPMiddleware):
    """
    Cookie-based authentication middleware.

    When user visits with ?key= parameter:
    1. Validates the key
    2. Sets an HTTP-only cookie with the key
    3. Browser automatically sends cookie on all subsequent requests

    On subsequent requests:
    1. Checks for auth cookie
    2. Injects cookie value as Authorization header

    This allows sharing URLs like: https://app.fly.dev/?key=abc123...
    After first visit, browser handles authentication automatically.
    """
    COOKIE_NAME = "auth_key"
    COOKIE_MAX_AGE = 86400 * 7  # 7 days

    async def dispatch(self, request: Request, call_next):
        key_from_query = request.query_params.get("key")
        key_from_cookie = request.cookies.get(self.COOKIE_NAME)

        # Determine which key to use
        auth_key = key_from_query or key_from_cookie

        # If we have a key, inject it as Authorization header
        if auth_key and "authorization" not in request.headers:
            headers = dict(request.headers)
            headers["authorization"] = f"Bearer {auth_key}"

            # Update request scope with new headers
            request._headers = headers
            request.scope["headers"] = [
                (k.lower().encode(), v.encode())
                for k, v in headers.items()
            ]

        # Process the request
        response = await call_next(request)

        # If key came from query param and request was successful, set cookie
        # Only set cookie if the response is successful (not 401)
        if key_from_query and response.status_code < 400:
            response.set_cookie(
                key=self.COOKIE_NAME,
                value=key_from_query,
                max_age=self.COOKIE_MAX_AGE,
                httponly=True,  # Prevents JavaScript access
                secure=True,     # Only sent over HTTPS
                samesite="lax"   # CSRF protection
            )

        return response


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="US Disease Tracker Dashboard - Data visualizations for disease surveillance",
    lifespan=lifespan
)

# Add cookie-based auth middleware
app.add_middleware(CookieAuthMiddleware)

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include routers
app.include_router(api.router)
app.include_router(pages.router)


@app.get("/health")
async def root_health():
    """Root health check endpoint (unauthenticated)"""
    return {"status": "ok", "app": settings.app_name}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
