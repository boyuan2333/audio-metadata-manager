from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from audio_metadata.schema import (
    BRIGHTNESS_CHOICES,
    TEMPO_QUALITY_CHOICES,
    normalize_payload_schema_v1,
    normalize_record_schema_v1,
)


KEYWORD_FIELD_PATHS = (
    ("id",),
    ("source", "file_name"),
    ("source", "path"),
    ("source", "file_format"),
    ("status",),
    ("derived", "duration_bucket"),
    ("derived", "brightness"),
    ("derived", "tempo_applicable"),
    ("derived", "is_loop"),
    ("features", "tempo_quality"),
    ("retrieval", "tags"),
    ("retrieval", "mood"),
    ("retrieval", "texture"),
    ("retrieval", "density"),
    ("retrieval", "role"),
    ("retrieval", "domain"),
    ("model_outputs", "instrument_family"),
    ("model_outputs", "texture"),
    ("model_outputs", "timbre_type"),
)

DURATION_BUCKET_CHOICES = ("micro", "short", "medium", "long")


def parse_bool_arg(value: str) -> bool:
    normalized = value.strip().casefold()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def parse_choice_arg(value: str, allowed: tuple[str, ...]) -> str:
    normalized = value.strip().casefold()
    if normalized not in allowed:
        allowed_text = ", ".join(allowed)
        raise argparse.ArgumentTypeError(f"expected one of: {allowed_text}")
    return normalized


def add_filter_arguments(
    parser: argparse.ArgumentParser,
    *,
    input_help: str,
    include_limit: bool,
) -> argparse.ArgumentParser:
    parser.add_argument(
        "--input",
        required=True,
        help=input_help,
    )
    parser.add_argument(
        "--keyword",
        help="Case-insensitive keyword matched against whitelisted text fields.",
    )
    parser.add_argument(
        "--min-bpm",
        type=float,
        help="Minimum features.tempo_bpm value.",
    )
    parser.add_argument(
        "--max-bpm",
        type=float,
        help="Maximum features.tempo_bpm value.",
    )
    parser.add_argument(
        "--min-duration",
        type=float,
        help="Minimum technical.duration_sec value.",
    )
    parser.add_argument(
        "--max-duration",
        type=float,
        help="Maximum technical.duration_sec value.",
    )
    parser.add_argument(
        "--tempo-applicable",
        type=parse_bool_arg,
        metavar="<true|false>",
        help="Filter by derived.tempo_applicable.",
    )
    parser.add_argument(
        "--tempo-quality",
        type=lambda value: parse_choice_arg(value, TEMPO_QUALITY_CHOICES),
        metavar="<high|medium|low|not_applicable>",
        help="Filter by features.tempo_quality.",
    )
    parser.add_argument(
        "--is-loop",
        type=parse_bool_arg,
        metavar="<true|false>",
        help="Filter by derived.is_loop.",
    )
    parser.add_argument(
        "--duration-bucket",
        type=lambda value: parse_choice_arg(value, DURATION_BUCKET_CHOICES),
        metavar="<micro|short|medium|long>",
        help="Filter by derived.duration_bucket.",
    )
    parser.add_argument(
        "--brightness",
        type=lambda value: parse_choice_arg(value, BRIGHTNESS_CHOICES),
        metavar="<dark|balanced|bright|very_bright>",
        help="Filter by derived.brightness.",
    )
    parser.add_argument(
        "--status",
        choices=("ok", "partial", "failed"),
        help="Filter by record status.",
    )
    if include_limit:
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Maximum number of matching records to display. Default: 20.",
        )
    return parser


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search exported audio metadata JSON with explicit field filters.",
        add_help=add_help,
    )
    return add_filter_arguments(
        parser,
        input_help="Path to an exported metadata JSON file.",
        include_limit=True,
    )


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    limit = getattr(args, "limit", None)
    if limit is not None and limit <= 0:
        parser.error("--limit must be greater than 0.")

    validate_range(args.min_bpm, args.max_bpm, "--min-bpm", "--max-bpm", parser)
    validate_range(
        args.min_duration,
        args.max_duration,
        "--min-duration",
        "--max-duration",
        parser,
    )


def validate_range(
    min_value: float | None,
    max_value: float | None,
    min_name: str,
    max_name: str,
    parser: argparse.ArgumentParser,
) -> None:
    if min_value is not None and max_value is not None and min_value > max_value:
        parser.error(f"{min_name} cannot be greater than {max_name}.")


def load_payload(input_path: Path) -> dict[str, Any]:
    if not input_path.exists() or not input_path.is_file():
        raise ValueError(f"Input JSON file does not exist or is not a file: {input_path}")

    try:
        payload = json.loads(input_path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise ValueError(f"Could not read input JSON file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Input file is not valid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno})"
        ) from exc

    return normalize_payload_schema_v1(payload)


def load_records(input_path: Path) -> list[dict[str, Any]]:
    return load_payload(input_path)["files"]


def get_nested_value(record: dict[str, Any], *path: str) -> Any:
    current: Any = record
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def match_record(record: dict[str, Any], args: argparse.Namespace) -> bool:
    if args.status is not None and record.get("status") != args.status:
        return False

    if args.keyword and not record_matches_keyword(record, args.keyword):
        return False

    tempo_bpm = get_nested_value(record, "features", "tempo_bpm")
    if not matches_numeric_range(tempo_bpm, args.min_bpm, args.max_bpm):
        return False

    duration_sec = get_nested_value(record, "technical", "duration_sec")
    if not matches_numeric_range(duration_sec, args.min_duration, args.max_duration):
        return False

    if not matches_exact_value(record.get("tempo_applicable"), args.tempo_applicable):
        return False

    if not matches_exact_value(get_nested_value(record, "features", "tempo_quality"), args.tempo_quality):
        return False

    if not matches_exact_value(record.get("is_loop"), args.is_loop):
        return False

    if not matches_exact_value(record.get("duration_bucket"), args.duration_bucket):
        return False

    if not matches_exact_value(record.get("brightness"), args.brightness):
        return False

    return True


def matches_numeric_range(value: Any, min_value: float | None, max_value: float | None) -> bool:
    if min_value is None and max_value is None:
        return True

    if not isinstance(value, (int, float)):
        return False

    numeric_value = float(value)
    if min_value is not None and numeric_value < min_value:
        return False
    if max_value is not None and numeric_value > max_value:
        return False
    return True


def matches_exact_value(value: Any, expected: Any) -> bool:
    if expected is None:
        return True
    return value == expected


def record_matches_keyword(record: dict[str, Any], keyword: str) -> bool:
    needle = keyword.casefold()
    return any(search_field(record, field_path, needle) for field_path in KEYWORD_FIELD_PATHS)


def search_field(record: dict[str, Any], field_path: tuple[str, ...], needle: str) -> bool:
    value = get_nested_value(record, *field_path)
    if isinstance(value, str):
        return needle in value.casefold()
    if isinstance(value, bool):
        return needle in str(value).casefold()
    if isinstance(value, list):
        return any(isinstance(item, str) and needle in item.casefold() for item in value)
    return False


def collect_matched_fields(record: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    matched_fields: list[dict[str, Any]] = []

    if args.keyword:
        needle = args.keyword.casefold()
        for field_path in KEYWORD_FIELD_PATHS:
            matched_fields.extend(collect_keyword_matches(record, field_path, needle))

    if args.status is not None:
        matched_fields.append({"field": "status", "value": record.get("status")})

    if args.min_bpm is not None or args.max_bpm is not None:
        matched_fields.append(
            {"field": "tempo_bpm", "value": get_nested_value(record, "features", "tempo_bpm")}
        )

    if args.min_duration is not None or args.max_duration is not None:
        matched_fields.append(
            {
                "field": "duration_sec",
                "value": get_nested_value(record, "technical", "duration_sec"),
            }
        )

    if args.tempo_applicable is not None:
        matched_fields.append({"field": "tempo_applicable", "value": record.get("tempo_applicable")})

    if args.tempo_quality is not None:
        matched_fields.append(
            {"field": "tempo_quality", "value": get_nested_value(record, "features", "tempo_quality")}
        )

    if args.is_loop is not None:
        matched_fields.append({"field": "is_loop", "value": record.get("is_loop")})

    if args.duration_bucket is not None:
        matched_fields.append({"field": "duration_bucket", "value": record.get("duration_bucket")})

    if args.brightness is not None:
        matched_fields.append({"field": "brightness", "value": record.get("brightness")})

    return dedupe_matched_fields(matched_fields)


def collect_keyword_matches(record: dict[str, Any], field_path: tuple[str, ...], needle: str) -> list[dict[str, Any]]:
    value = get_nested_value(record, *field_path)
    field_name = ".".join(field_path)
    if isinstance(value, str) and needle in value.casefold():
        return [{"field": field_name, "value": value}]
    if isinstance(value, bool) and needle in str(value).casefold():
        return [{"field": field_name, "value": value}]
    if isinstance(value, list):
        matches = [item for item in value if isinstance(item, str) and needle in item.casefold()]
        if matches:
            return [{"field": field_name, "value": matches}]
    return []


def dedupe_matched_fields(matched_fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in matched_fields:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped


def format_result(record: dict[str, Any], matched_fields: list[dict[str, Any]]) -> str:
    file_name = record.get("file_name", "<unknown>")
    source_path = record.get("source_path", "<unknown>")
    matched_json = json.dumps(matched_fields, indent=2, ensure_ascii=False)
    return (
        f"file_name: {file_name}\n"
        f"source_path: {source_path}\n"
        f"matched_fields:\n{matched_json}"
    )


def run(args: argparse.Namespace) -> int:
    input_path = Path(args.input).expanduser().resolve()

    try:
        records = load_records(input_path)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    matched_records = [record for record in records if match_record(record, args)]
    displayed_records = matched_records[: args.limit]

    if matched_records:
        print(f"Matched {len(matched_records)} record(s). Showing {len(displayed_records)}.")
    else:
        print("Matched 0 record(s).")
        return 0

    for index, record in enumerate(displayed_records, start=1):
        matched_fields = collect_matched_fields(record, args)
        print()
        print(f"[{index}]")
        print(format_result(record, matched_fields))

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(args, parser)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())



