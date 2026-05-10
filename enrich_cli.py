"""CLI command for v0.1-b7 metadata enrichment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from audio_metadata.enrichment import enrich_payload


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    """Build argument parser for enrich command."""
    parser = argparse.ArgumentParser(
        prog="enrich",
        description="Enrich audio metadata with embedding coverage and semantic tags.",
        add_help=add_help,
    )
    parser.add_argument("--input", required=True, help="Input library JSON file.")
    parser.add_argument("--output", required=True, help="Output enriched library JSON file.")
    parser.add_argument("--embeddings", help="Optional CLAP embeddings JSON file.")
    parser.add_argument("--vocabulary", help="Optional semantic vocabulary JSON file.")
    parser.add_argument(
        "--semantic-tags",
        action="store_true",
        help="Enable semantic tag scoring.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.25,
        help="Default semantic tag threshold.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Max semantic tags per record.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print summary without writing output.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite output if it exists.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print verbose summary.",
    )
    return parser


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """Validate enrich command arguments."""
    if args.top_n <= 0:
        parser.error("--top-n must be greater than 0.")
    if args.threshold < -1.0 or args.threshold > 1.0:
        parser.error("--threshold must be between -1.0 and 1.0.")


def run(args: argparse.Namespace) -> int:
    """Execute enrich command."""
    try:
        input_path = Path(args.input)
        output_path = Path(args.output)

        payload = _read_json(input_path)
        embeddings_data = _read_json(Path(args.embeddings)) if args.embeddings else None
        vocabulary_data = _read_json(Path(args.vocabulary)) if args.vocabulary else None

        enriched, summary = enrich_payload(
            payload,
            embeddings_data=embeddings_data,
            vocabulary_data=vocabulary_data,
            semantic_tags=args.semantic_tags,
            threshold=args.threshold,
            top_n=args.top_n,
        )

        _print_summary(summary, output_path)

        if args.dry_run:
            return 0

        if output_path.exists() and not args.force:
            print(
                f"Error: output file already exists: {output_path}. Use --force to overwrite.",
                file=sys.stderr,
            )
            return 1

        _write_json_atomic(output_path, enriched)
        return 0
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise ValueError(f"Could not read JSON file {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in {path}: {exc.msg} (line {exc.lineno}, column {exc.colno})"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(f"Input JSON must be an object: {path}")
    return data


def _write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    tmp_path.replace(path)


def _print_summary(summary: dict[str, Any], output_path: Path) -> None:
    print("Enrichment summary:")
    print(f"  records: {summary.get('records', 0)}")
    print(f"  embeddings ready: {summary.get('embeddings_ready', 0)}")
    print(f"  embeddings missing: {summary.get('embeddings_missing', 0)}")
    print(f"  embeddings invalid: {summary.get('embeddings_invalid', 0)}")
    print(f"  embeddings not requested: {summary.get('embeddings_not_requested', 0)}")
    print(f"  semantic tags added: {summary.get('semantic_tags_added', 0)}")
    print(f"  output: {output_path}")


if __name__ == "__main__":
    parser = build_parser()
    parsed_args = parser.parse_args()
    validate_args(parsed_args, parser)
    raise SystemExit(run(parsed_args))
