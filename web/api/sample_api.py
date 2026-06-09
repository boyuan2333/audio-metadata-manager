"""Sample Detail + Edit API — GET /api/sample/{id}, PUT /api/sample/{id}/review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["sample"])


def _reviews_path(library_path: str) -> Path:
    """Return the review-override JSON path for a library file."""
    p = Path(library_path)
    return p.with_suffix(".reviews.json")


def _load_library(library_path: str) -> dict[str, Any]:
    """Load the library JSON and return {id: record} mapping."""
    p = Path(library_path)
    if not p.exists():
        raise FileNotFoundError(f"Library file not found: {library_path}")
    data = json.loads(p.read_text(encoding="utf-8"))
    files = data.get("files") if isinstance(data, dict) else None
    if not isinstance(files, list):
        raise ValueError("Library JSON has no 'files' array")
    return {rec["id"]: rec for rec in files if isinstance(rec, dict) and "id" in rec}


def _load_reviews(library_path: str) -> dict[str, Any]:
    """Load the reviews JSON (creates empty if missing)."""
    rp = _reviews_path(library_path)
    if not rp.exists():
        return {}
    return json.loads(rp.read_text(encoding="utf-8"))


def _save_reviews(library_path: str, reviews: dict[str, Any]) -> None:
    """Persist the reviews JSON."""
    rp = _reviews_path(library_path)
    rp.write_text(json.dumps(reviews, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Request / response models ────────────────────────────────────────

class ReviewPayload(BaseModel):
    """Body for PUT /api/sample/{id}/review."""
    notes: str | None = None
    tags: list[str] | None = None
    overrides: dict[str, Any] | None = None


# ── Routes ────────────────────────────────────────────────────────────

@router.get("/sample/{sample_id}")
async def get_sample(sample_id: str):
    """Return full metadata for a single sample, merged with review overrides."""
    from web_server import get_library_path

    lib = get_library_path()
    if not lib:
        raise HTTPException(500, detail="No library path configured.")

    try:
        records = _load_library(lib)
    except FileNotFoundError as exc:
        raise HTTPException(404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(500, detail=str(exc))

    record = records.get(sample_id)
    if record is None:
        raise HTTPException(404, detail=f"Sample not found: {sample_id}")

    # Merge review overrides if present
    reviews = _load_reviews(lib)
    review_data = reviews.get(sample_id)
    if review_data:
        record = {**record, "review_overrides": review_data}

    return record


@router.put("/sample/{sample_id}/review")
async def update_review(sample_id: str, body: ReviewPayload):
    """Update review overrides (notes, manual tags, field overrides) for a sample."""
    from web_server import get_library_path

    lib = get_library_path()
    if not lib:
        raise HTTPException(500, detail="No library path configured.")

    # Verify sample exists in library
    try:
        records = _load_library(lib)
    except FileNotFoundError as exc:
        raise HTTPException(404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(500, detail=str(exc))

    if sample_id not in records:
        raise HTTPException(404, detail=f"Sample not found: {sample_id}")

    # Build and persist review
    reviews = _load_reviews(lib)
    entry: dict[str, Any] = reviews.get(sample_id, {})

    if body.notes is not None:
        entry["notes"] = body.notes
    if body.tags is not None:
        entry["manual_tags"] = body.tags
    if body.overrides is not None:
        entry["overrides"] = {**entry.get("overrides", {}), **body.overrides}

    reviews[sample_id] = entry
    _save_reviews(lib, reviews)

    return {"ok": True, "sample_id": sample_id, "review": entry}
