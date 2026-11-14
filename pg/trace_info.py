"""Read-only facts the dashboard needs to link to LangSmith. No secrets, no LangSmith calls.

LangSmith is the debugging view; Atlas stays the record of authority. The browser never gets the API key:
it only learns whether tracing is on, the project name, and an optional link to the project's trace list.
"""
from __future__ import annotations

import os

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/observability/langsmith")
def langsmith_info():
    on = os.environ.get("LANGSMITH_TRACING", "").lower() in ("1", "true", "yes") and bool(os.environ.get("LANGSMITH_API_KEY"))
    url = os.environ.get("LANGSMITH_PROJECT_URL", "")
    return {"enabled": on, "project": os.environ.get("LANGSMITH_PROJECT", "proofgate"),
            "project_url": url if url.startswith("https://") else None}
