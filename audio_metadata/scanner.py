from __future__ import annotations

from pathlib import Path

SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".aiff", ".aif", ".flac"}


def scan_audio_files(input_dir: Path, recursive: bool = False) -> list[Path]:
    if recursive:
        candidates = input_dir.rglob("*")
    else:
        candidates = input_dir.iterdir()

    return sorted(
        path.resolve()
        for path in candidates
        if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
    )
