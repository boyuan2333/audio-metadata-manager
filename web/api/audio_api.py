"""Audio streaming API — GET /api/audio/{file_path}."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

router = APIRouter(tags=["audio"])


@router.get("/audio/{file_path:path}")
async def stream_audio(file_path: str, request: Request):
    """Stream an audio file for browser playback.

    Security: file must be within the configured sample directory.
    """
    from web_server import get_sample_dir

    sample_dir = get_sample_dir()
    if not sample_dir:
        raise HTTPException(500, "Sample directory not configured")

    # Resolve and validate path
    base = Path(sample_dir).resolve()
    target = (base / file_path).resolve()

    # Security: prevent path traversal
    if not str(target).startswith(str(base)):
        raise HTTPException(403, "Access denied: path outside sample directory")

    if not target.is_file():
        raise HTTPException(404, f"Audio file not found: {file_path}")

    # Determine media type
    suffix = target.suffix.lower()
    media_types = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".flac": "audio/flac",
        ".aiff": "audio/aiff",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(
        path=str(target),
        media_type=media_type,
        filename=target.name,
    )
