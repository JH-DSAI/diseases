"""Shared FastAPI dependencies for database access."""

import asyncio
from collections.abc import Callable
from typing import Any

from fastapi import HTTPException

from app.database import db


async def get_db():
    """
    Dependency that ensures database is initialized.

    Raises:
        HTTPException: 503 if database is not initialized

    Returns:
        The database instance
    """
    if not db.is_initialized():
        raise HTTPException(status_code=503, detail="Database not initialized")
    return db


async def run_db_query(func: Callable, *args, **kwargs) -> Any:
    """
    Run a synchronous database query in a thread pool.

    This wraps blocking database calls to work with FastAPI's async handlers.

    Args:
        func: The database method to call
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the database query
    """
    return await asyncio.to_thread(func, *args, **kwargs)


async def get_disease_name_or_404(disease_slug: str) -> str:
    """
    Look up disease name by slug, raising 404 if not found.

    Args:
        disease_slug: URL-safe slug for the disease

    Returns:
        The disease name

    Raises:
        HTTPException: 404 if disease not found
    """
    disease_name = await run_db_query(db.get_disease_name_by_slug, disease_slug)
    if disease_name is None:
        raise HTTPException(status_code=404, detail=f"Disease '{disease_slug}' not found")
    return disease_name
