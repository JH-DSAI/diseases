"""HTML/HTMX page endpoints"""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.auth import verify_api_key
from app.database import db
from app.dependencies import run_db_query
from app.templates import templates

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["pages"],
    dependencies=[Depends(verify_api_key)]
)


@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """
    Landing page with navigation.
    Disease cards are loaded via HTMX from /api/html/diseases.

    Args:
        request: FastAPI request object

    Returns:
        Rendered HTML template
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "page_title": "Disease Dashboard"
        }
    )


@router.get("/disease/{disease_slug}", response_class=HTMLResponse)
async def disease_detail_page(request: Request, disease_slug: str):
    """
    Disease-specific detail page.
    Stats and charts are loaded via HTMX from /api/html/disease/{slug}/*.

    Args:
        request: FastAPI request object
        disease_slug: URL-safe slug for the disease

    Returns:
        Rendered HTML template
    """
    # Look up disease name from slug for page title
    disease_name = await run_db_query(db.get_disease_name_by_slug, disease_slug) if db.is_initialized() else None

    if db.is_initialized() and disease_name is None:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "page_title": "Disease Not Found",
                "error": f"Disease with slug '{disease_slug}' not found"
            },
            status_code=404
        )

    return templates.TemplateResponse(
        "disease.html",
        {
            "request": request,
            "disease_name": disease_name,
            "disease_slug": disease_slug,
            "page_title": f"{disease_name.title()} Dashboard" if disease_name else "Disease Dashboard"
        }
    )
