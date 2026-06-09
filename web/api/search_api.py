"""Search API — GET /api/search?q={query}&limit={n}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from audio_metadata.unified_search import execute_search

router = APIRouter(tags=["search"])


_SEARCH_FETCH_LIMIT = 10000


def parse_optional_float(value: str | None, label: str) -> float | None:
    """Parse optional numeric query params while treating empty strings as unset."""
    if value is None or value.strip() == "":
        return None
    try:
        return float(value.strip())
    except ValueError:
        raise HTTPException(400, f"{label} 必须是数字")


def _matches_range(value: object, minimum: float | None, maximum: float | None) -> bool:
    if minimum is None and maximum is None:
        return True
    if not isinstance(value, (int, float)):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


@router.get("/search")
async def search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    min_bpm: str | None = Query(None),
    max_bpm: str | None = Query(None),
    min_duration: str | None = Query(None),
    max_duration: str | None = Query(None),
    tempo_min: str | None = Query(None),
    tempo_max: str | None = Query(None),
):
    """Search the library with unified search."""
    from web_server import get_library_path

    bpm_min = parse_optional_float(min_bpm if min_bpm is not None else tempo_min, "BPM")
    bpm_max = parse_optional_float(max_bpm if max_bpm is not None else tempo_max, "BPM")
    duration_min = parse_optional_float(min_duration, "时长")
    duration_max = parse_optional_float(max_duration, "时长")

    lib = get_library_path()
    if not lib:
        raise HTTPException(500, "Library path not configured")

    try:
        results = execute_search(lib, q, limit=_SEARCH_FETCH_LIMIT)
        filtered = [
            item
            for item in results
            if _matches_range(item.get("metadata", {}).get("bpm"), bpm_min, bpm_max)
            and _matches_range(
                item.get("metadata", {}).get("duration"), duration_min, duration_max
            )
        ]
        return {
            "query": q,
            "total": len(filtered),
            "limit": limit,
            "offset": offset,
            "results": filtered[offset : offset + limit],
        }
    except FileNotFoundError:
        raise HTTPException(404, f"Library file not found: {lib}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Search failed: {e}")
