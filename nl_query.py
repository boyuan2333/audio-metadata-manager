from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from audio_metadata.nl_query import parse_nl_query
from audio_metadata.schema import normalize_payload_schema_v1

import search_metadata


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search with natural language query.",
        add_help=add_help,
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Natural language query string.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to an exported metadata JSON file.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of matching records to display. Default: 20.",
    )
    return parser


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    limit = getattr(args, "limit", None)
    if limit is not None and limit <= 0:
        parser.error("--limit must be greater than 0.")


def intent_to_args(intent: dict[str, Any], base_args: argparse.Namespace) -> argparse.Namespace:
    """Convert NL query intent to search-compatible args namespace."""
    search_args = argparse.Namespace()
    search_args.input = base_args.input
    search_args.limit = base_args.limit
    search_args.keyword = intent.get("keyword")
    search_args.min_bpm = intent.get("min_bpm")
    search_args.max_bpm = intent.get("max_bpm")
    search_args.min_duration = intent.get("min_duration")
    search_args.max_duration = intent.get("max_duration")
    search_args.tempo_applicable = intent.get("tempo_applicable")
    search_args.tempo_quality = intent.get("tempo_quality")
    search_args.is_loop = intent.get("is_loop")
    search_args.duration_bucket = intent.get("duration_bucket")
    search_args.brightness = intent.get("brightness")
    search_args.status = intent.get("status")
    return search_args


def run(args: argparse.Namespace) -> int:
    query = args.query
    input_path = Path(args.input).expanduser().resolve()

    intent = parse_nl_query(query)

    if not input_path.exists() or not input_path.is_file():
        print(f"Error: Input JSON file does not exist or is not a file: {input_path}", file=sys.stderr)
        return 1

    try:
        payload = json.loads(input_path.read_text(encoding="utf-8-sig"))
        payload = normalize_payload_schema_v1(payload)
    except OSError as exc:
        print(f"Error: Could not read input JSON file: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Error: Input file is not valid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno})", file=sys.stderr)
        return 1

    search_args = intent_to_args(intent, args)

    records = payload["files"]
    matched_records = [record for record in records if search_metadata.match_record(record, search_args)]
    displayed_records = matched_records[: args.limit]

    if matched_records:
        print(f"Matched {len(matched_records)} record(s). Showing {len(displayed_records)}.")
        print(f"Query: {query!r}")
        print(f"Intent: {json.dumps(intent, ensure_ascii=False)}")
    else:
        print("Matched 0 record(s).")
        print(f"Query: {query!r}")
        print(f"Intent: {json.dumps(intent, ensure_ascii=False)}")
        return 0

    for index, record in enumerate(displayed_records, start=1):
        matched_fields = search_metadata.collect_matched_fields(record, search_args)
        print()
        print(f"[{index}]")
        print(search_metadata.format_result(record, matched_fields))

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(args, parser)
    return run(args)


__all__ = ["parse_nl_query", "build_parser", "validate_args", "run", "main"]
