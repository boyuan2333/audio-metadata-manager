"""CLI tests for v0.1-b7 metadata enrichment command."""

from __future__ import annotations

import json


def _write_library(path) -> None:
    payload = {
        "schema_version": 1,
        "app_version": "test",
        "run": {},
        "files": [
            {
                "id": "rec-1",
                "status": "ok",
                "source": {
                    "path": "audio/warm_guitar.wav",
                    "file_name": "warm_guitar.wav",
                    "file_format": "wav",
                },
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_enrich_cli_dry_run_does_not_write_output(tmp_path, capsys):
    from enrich_cli import build_parser, run

    input_path = tmp_path / "library.json"
    output_path = tmp_path / "library.enriched.json"
    _write_library(input_path)

    parser = build_parser()
    args = parser.parse_args(
        [
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--dry-run",
        ]
    )

    exit_code = run(args)

    assert exit_code == 0
    assert not output_path.exists()
    captured = capsys.readouterr()
    assert "Enrichment summary:" in captured.out


def test_enrich_cli_refuses_to_overwrite_without_force(tmp_path, capsys):
    from enrich_cli import build_parser, run

    input_path = tmp_path / "library.json"
    output_path = tmp_path / "library.enriched.json"
    _write_library(input_path)
    output_path.write_text("{}", encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args(
        [
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    exit_code = run(args)

    assert exit_code == 1
    assert json.loads(output_path.read_text(encoding="utf-8")) == {}
    captured = capsys.readouterr()
    assert "Use --force to overwrite" in captured.err


def test_enrich_cli_force_overwrites_existing_output(tmp_path):
    from enrich_cli import build_parser, run

    input_path = tmp_path / "library.json"
    output_path = tmp_path / "library.enriched.json"
    _write_library(input_path)
    output_path.write_text('{"stale": true}', encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args(
        [
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--force",
        ]
    )

    exit_code = run(args)

    assert exit_code == 0
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["files"][0]["retrieval"]["embedding_status"] == "not_requested"


def test_enrich_cli_reports_invalid_json(tmp_path, capsys):
    from enrich_cli import build_parser, run

    input_path = tmp_path / "library.json"
    output_path = tmp_path / "library.enriched.json"
    input_path.write_text("{bad json", encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args(
        [
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    exit_code = run(args)

    assert exit_code == 1
    assert not output_path.exists()
    captured = capsys.readouterr()
    assert "Invalid JSON" in captured.err


def test_enrich_cli_writes_enriched_json(tmp_path):
    from enrich_cli import build_parser, run

    input_path = tmp_path / "library.json"
    output_path = tmp_path / "library.enriched.json"
    _write_library(input_path)

    parser = build_parser()
    args = parser.parse_args(
        [
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    exit_code = run(args)

    assert exit_code == 0
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["files"][0]["retrieval"]["embedding_status"] == "not_requested"


def test_app_parser_accepts_enrich_command(tmp_path):
    from app import build_parser

    input_path = tmp_path / "library.json"
    output_path = tmp_path / "library.enriched.json"

    parser = build_parser()
    args = parser.parse_args(
        [
            "enrich",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    assert args.command == "enrich"
    assert args.handler is not None
