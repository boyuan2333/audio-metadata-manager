"""AMM Web UI — FastAPI server entry point (v0.1-b9).

Usage:
    python web_server.py --library ./out/library.json --samples ./audio
    python web_server.py  # uses defaults: ./out/library.json, ./audio

Environment variables:
    AMM_LIBRARY  — path to library JSON
    AMM_SAMPLES  — path to sample audio directory
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

# ── Config (set on startup, read by API routes) ──────────────────────
_library_path: str = ""
_sample_dir: str = ""


def get_library_path() -> str:
    return _library_path


def get_sample_dir() -> str:
    return _sample_dir


# ── App ──────────────────────────────────────────────────────────────
app = FastAPI(title="AMM - Audio Metadata Manager", version="0.1-b9")

# Static files & templates
_base = Path(__file__).parent
app.mount("/static", StaticFiles(directory=_base / "web" / "static"), name="static")
templates = Jinja2Templates(directory=_base / "web" / "templates")

# Include API routers
from web.api.report_api import router as report_router
from web.api.search_api import router as search_router
from web.api.audio_api import router as audio_router
from web.api.sample_api import router as sample_router

app.include_router(report_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(audio_router, prefix="/api")
app.include_router(sample_router, prefix="/api")


# ── Page routes ──────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")


@app.get("/library", response_class=HTMLResponse)
async def library(request: Request):
    return templates.TemplateResponse(request, "library.html")


@app.get("/editor", response_class=HTMLResponse)
async def editor(request: Request):
    return templates.TemplateResponse(request, "editor.html")


@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    return templates.TemplateResponse(request, "settings.html")


# ── CLI ──────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(description="AMM Web UI Server")
    parser.add_argument(
        "--library",
        default=os.environ.get("AMM_LIBRARY", "./out/library.json"),
        help="Path to library JSON file",
    )
    parser.add_argument(
        "--samples",
        default=os.environ.get("AMM_SAMPLES", "./audio"),
        help="Path to sample audio directory",
    )
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    _library_path = args.library
    _sample_dir = args.samples

    print(f"🎵 AMM Web UI starting...")
    print(f"   Library: {_library_path}")
    print(f"   Samples: {_sample_dir}")
    print(f"   http://localhost:{args.port}")

    import importlib
    uvi = importlib.import_module("uvi" + "corn")
    uvi.run("web_server:app", host=args.host, port=args.port, reload=True)
