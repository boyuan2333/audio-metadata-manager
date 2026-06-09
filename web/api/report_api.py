"""Report API — GET /api/report."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["report"])


@router.get("/report")
async def get_report():
    """Return library aggregate statistics."""
    from web_server import get_library_path
    from audio_metadata import report as report_mod

    lib = get_library_path()
    if not lib:
        raise HTTPException(500, detail="No library path configured. Start with --library or set AMM_LIBRARY.")

    try:
        data = report_mod.generate_report(lib)
        return data
    except FileNotFoundError:
        raise HTTPException(404, detail=f"Library file not found: {lib}")
    except Exception as e:
        raise HTTPException(500, detail=str(e))
