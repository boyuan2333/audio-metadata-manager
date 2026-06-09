"""Search API — GET /api/search?q={query}&limit={n}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from audio_metadata.unified_search import execute_search

router = APIRouter(tags=["search"])


@router.get("/search")
async def search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=200),
):
    """Search the library with unified search."""
    from web_server import get_library_path

    lib = get_library_path()
    if not lib:
        raise HTTPException(500, "Library path not configured")

    try:
        result = execute_search(lib, q, limit=limit)
        return result
    except FileNotFoundError:
        raise HTTPException(404, f"Library file not found: {lib}")
    except Exception as e:
        raise HTTPException(500, f"Search failed: {e}")
