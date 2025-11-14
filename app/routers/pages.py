"""HTML/HTMX page endpoints"""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth import verify_api_key
from app.database import db

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["pages"],
    dependencies=[Depends(verify_api_key)]
)

# Set up Jinja2 templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """
    Landing page with Hello World and navigation.

    Args:
        request: FastAPI request object

    Returns:
        Rendered HTML template
    """
    # Get available diseases for navigation
    diseases = db.get_diseases() if db._initialized else []

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "diseases": diseases,
            "page_title": "Disease Dashboard"
        }
    )


@router.get("/disease/{disease_name}", response_class=HTMLResponse)
async def disease_detail_page(request: Request, disease_name: str):
    """
    Disease-specific detail page.

    Args:
        request: FastAPI request object
        disease_name: Name of the disease

    Returns:
        Rendered HTML template
    """
    diseases = db.get_diseases() if db._initialized else []

    # Verify disease exists
    if db._initialized and disease_name not in diseases:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "diseases": diseases,
                "page_title": "Disease Not Found",
                "error": f"Disease '{disease_name}' not found"
            },
            status_code=404
        )

    return templates.TemplateResponse(
        "disease.html",
        {
            "request": request,
            "disease_name": disease_name,
            "diseases": diseases,
            "page_title": f"{disease_name.title()} Dashboard"
        }
    )
