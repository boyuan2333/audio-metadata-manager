from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from audio_metadata.extractor import extract_file_metadata
from audio_metadata.models import RunSummary
from audio_metadata.scanner import scan_audio_files
from audio_metadata.schema import build_output_payload


def index_audio_directory(
    input_dir: Path,
    output_path: Path,
    recursive: bool = False,
) -> dict[str, Any]:
    audio_files = scan_audio_files(input_dir, recursive=recursive)
    file_results = [extract_file_metadata(path) for path in audio_files]

    run_summary = RunSummary(
        generated_at=datetime.now(timezone.utc).isoformat(),
        input_dir=str(input_dir),
        output_path=str(output_path),
        recursive=recursive,
        total_files=len(file_results),
        ok_count=sum(1 for item in file_results if item.status == "ok"),
        partial_count=sum(1 for item in file_results if item.status == "partial"),
        failed_count=sum(1 for item in file_results if item.status == "failed"),
    )
    return build_output_payload(run_summary, file_results)


def write_output_payload(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
