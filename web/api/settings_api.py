"""Settings API for the local Web UI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["settings"])


class SettingsPayload(BaseModel):
    library_path: str | None = None
    sample_dir: str | None = None


def _count_records(library_path: str) -> int:
    if not library_path:
        return 0
    path = Path(library_path)
    if not path.exists():
        return 0
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    files = data.get("files") if isinstance(data, dict) else None
    return len(files) if isinstance(files, list) else 0


def _default_library_path(sample_dir: str | None = None) -> Path:
    if sample_dir:
        return Path(sample_dir) / ".amm" / "library.json"
    return Path.cwd() / "out" / "library.json"


def _ensure_managed_library(sample_dir: str | None = None, *, prefer_sample_dir: bool = False) -> Path:
    import web_server

    current = web_server.get_library_path()
    if current and not prefer_sample_dir and Path(current) != Path("./out/library.json"):
        path = Path(current)
    else:
        path = _default_library_path(sample_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        payload: dict[str, Any] = {"files": []}
        if sample_dir:
            payload["sample_dir"] = sample_dir
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    web_server._library_path = str(path)
    return path


def _settings_dict() -> dict[str, Any]:
    from web_server import get_library_path, get_sample_dir

    library_path = get_library_path()
    sample_dir = get_sample_dir()
    if not library_path:
        library_path = str(_default_library_path(sample_dir))
    return {
        "library_path": library_path,
        "managed_library_path": library_path,
        "sample_dir": sample_dir,
        "db_path": library_path,
        "total_records": _count_records(library_path),
        "last_scan": None,
    }


@router.get("/settings")
async def get_settings():
    return _settings_dict()


@router.put("/settings")
async def update_settings(body: SettingsPayload):
    import web_server

    if body.sample_dir is not None:
        sample_dir = body.sample_dir.strip()
        if not sample_dir:
            raise HTTPException(400, detail="sample_dir cannot be empty")
        web_server._sample_dir = sample_dir

    return {"ok": True, "settings": _settings_dict()}


@router.post("/settings/create-library")
async def create_library(body: SettingsPayload):
    import web_server

    sample_dir = body.sample_dir.strip() if body.sample_dir else web_server.get_sample_dir()
    if not sample_dir:
        raise HTTPException(400, detail="sample_dir cannot be empty")
    web_server._sample_dir = sample_dir
    _ensure_managed_library(sample_dir, prefer_sample_dir=True)
    return {"ok": True, "settings": _settings_dict()}
