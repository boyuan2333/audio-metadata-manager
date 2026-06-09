"""Shared fixtures for AMM Web API tests."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ── Mock library data ────────────────────────────────────────────────────────

MOCK_LIBRARY: dict[str, Any] = {
    "files": [
        {
            "id": "sample-001",
            "source": {
                "path": "samples/kick_01.wav",
                "file_name": "kick_01.wav",
                "file_format": "wav",
            },
            "technical": {"duration_sec": 1.5, "sample_rate": 44100},
            "features": {"tempo_bpm": 120},
            "retrieval": {
                "tags": ["drums", "kick", "percussion"],
                "mood": "energetic",
                "texture": "punchy",
            },
            "derived": {"is_loop": False, "brightness": "bright"},
            "model_outputs": {"auto_tags": ["drums", "kick"]},
        },
        {
            "id": "sample-002",
            "source": {
                "path": "samples/pad_ambient.wav",
                "file_name": "pad_ambient.wav",
                "file_format": "wav",
            },
            "technical": {"duration_sec": 8.0, "sample_rate": 44100},
            "features": {"tempo_bpm": 90},
            "retrieval": {
                "tags": ["ambient", "pad", "synth"],
                "mood": "calm",
                "texture": "smooth",
            },
            "derived": {"is_loop": True, "brightness": "warm"},
            "model_outputs": {"auto_tags": ["ambient", "pad"]},
        },
        {
            "id": "sample-003",
            "source": {
                "path": "samples/bass_deep.flac",
                "file_name": "bass_deep.flac",
                "file_format": "flac",
            },
            "technical": {"duration_sec": 3.2, "sample_rate": 48000},
            "features": {"tempo_bpm": 140},
            "retrieval": {
                "tags": ["bass", "deep", "sub"],
                "mood": "dark",
                "texture": "heavy",
            },
            "derived": {"is_loop": False, "brightness": "dark"},
            "model_outputs": {"auto_tags": ["bass"]},
        },
        {
            "id": "sample-004",
            "source": {
                "path": "samples/vocal_chop.wav",
                "file_name": "vocal_chop.wav",
                "file_format": "wav",
            },
            "technical": {"duration_sec": 2.0, "sample_rate": 44100},
            "features": {"tempo_bpm": 100},
            "retrieval": {
                "tags": ["vocal", "chop", "texture"],
                "mood": "ethereal",
                "texture": "airy",
            },
            "derived": {"is_loop": False, "brightness": "bright"},
            "model_outputs": {},
        },
        {
            "id": "sample-005",
            "source": {
                "path": "samples/hihat_loop.wav",
                "file_name": "hihat_loop.wav",
                "file_format": "wav",
            },
            "technical": {"duration_sec": 4.0, "sample_rate": 44100},
            "features": {"tempo_bpm": 120},
            "retrieval": {
                "tags": ["drums", "hihat", "loop"],
                "mood": "groovy",
                "texture": "crisp",
            },
            "derived": {"is_loop": True, "brightness": "bright"},
            "model_outputs": {"auto_tags": ["drums", "hihat"]},
        },
    ]
}


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_library(tmp_path: Path) -> Path:
    """Write the mock library JSON to a temp file and return its path."""
    lib_file = tmp_path / "library.json"
    lib_file.write_text(json.dumps(MOCK_LIBRARY, indent=2), encoding="utf-8")
    return lib_file


@pytest.fixture()
def mock_samples_dir(tmp_path: Path) -> Path:
    """Create a temp samples directory with dummy .wav files matching library entries."""
    samples = tmp_path / "samples"
    samples.mkdir()

    # Create dummy files for every entry in the mock library
    for rec in MOCK_LIBRARY["files"]:
        src = rec["source"]
        file_path = samples.parent / src["path"]
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(b"")  # empty placeholder

    return samples


@pytest.fixture()
def test_client(mock_library: Path, mock_samples_dir: Path):
    """Yield a FastAPI TestClient with library/samples configured."""
    import web_server

    # Point the app at our test fixtures
    web_server._library_path = str(mock_library)
    web_server._sample_dir = str(mock_samples_dir.parent)  # parent because paths are samples/xxx

    from fastapi.testclient import TestClient

    client = TestClient(web_server.app)
    yield client
