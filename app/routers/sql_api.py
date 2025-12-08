"""SQL API endpoint for Mosaic coordinator queries.

This endpoint accepts SQL queries from the frontend Mosaic coordinator
and returns JSON results. It validates queries to ensure security.
"""

import logging
import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from app.database import db
from app.dependencies import get_db, run_db_query

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["sql"],
)

# Allowed table names for queries
ALLOWED_TABLES = frozenset([
    "disease_data",
    "disease_mapping",
])

# SQL keywords that indicate mutation (not allowed)
FORBIDDEN_KEYWORDS = frozenset([
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "CREATE",
    "ALTER",
    "TRUNCATE",
    "GRANT",
    "REVOKE",
    "EXECUTE",
    "EXEC",
])


class QueryRequest(BaseModel):
    """Request body for SQL query endpoint."""

    sql: str
    type: str = "json"  # "json" or "arrow"

    @field_validator("sql")
    @classmethod
    def validate_sql(cls, v: str) -> str:
        """Validate SQL query for safety."""
        if not v or not v.strip():
            raise ValueError("SQL query cannot be empty")

        # Normalize whitespace for checking
        normalized = " ".join(v.upper().split())

        # Must start with SELECT
        if not normalized.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")

        # Check for forbidden keywords
        for keyword in FORBIDDEN_KEYWORDS:
            # Match keyword as whole word
            if re.search(rf"\b{keyword}\b", normalized):
                raise ValueError(f"Forbidden SQL keyword: {keyword}")

        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate response type."""
        if v not in ("json", "arrow"):
            raise ValueError("type must be 'json' or 'arrow'")
        return v


class QueryResponse(BaseModel):
    """Response body for SQL query endpoint."""

    data: list[dict[str, Any]]
    columns: list[str]
    row_count: int


def validate_tables_in_query(sql: str) -> None:
    """
    Validate that query only references allowed tables.

    Args:
        sql: The SQL query string

    Raises:
        HTTPException: If query references disallowed tables
    """
    # Simple regex to find table names after FROM and JOIN
    # This is a basic check - production should use proper SQL parsing
    normalized = sql.upper()

    # Find table references (basic pattern)
    from_pattern = r"\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)"
    join_pattern = r"\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)"

    tables_found = set()
    for match in re.finditer(from_pattern, normalized):
        tables_found.add(match.group(1).lower())
    for match in re.finditer(join_pattern, normalized):
        tables_found.add(match.group(1).lower())

    # Check all found tables are allowed
    disallowed = tables_found - ALLOWED_TABLES
    if disallowed:
        raise HTTPException(
            status_code=400,
            detail=f"Query references disallowed tables: {', '.join(disallowed)}"
        )


@router.post("/query", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    _db=Depends(get_db)
) -> QueryResponse:
    """
    Execute a SQL query and return results.

    This endpoint is used by the Mosaic coordinator for cross-filtering
    interactions. Only SELECT queries on allowed tables are permitted.

    Args:
        request: The query request containing SQL and response type

    Returns:
        QueryResponse with data rows, column names, and row count

    Raises:
        HTTPException: 400 for invalid queries, 500 for execution errors
    """
    # Additional table validation
    validate_tables_in_query(request.sql)

    logger.debug(f"Executing query: {request.sql[:100]}...")

    try:
        result = await run_db_query(db.execute_sql, request.sql)

        return QueryResponse(
            data=result["data"],
            columns=result["columns"],
            row_count=result["row_count"]
        )

    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Query execution failed: {str(e)}"
        )
