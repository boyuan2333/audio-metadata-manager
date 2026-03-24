from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from audio_metadata.extractor import extract_file_metadata
from audio_metadata.schema import normalize_record_schema_v1
from audio_metadata.scanner import scan_audio_files
from search_metadata import (
    add_filter_arguments,
    collect_matched_fields,
    get_nested_value,
    load_records,
    match_record,
    validate_args as validate_search_args,
)


SIMILARITY_FIELD_PATHS = (
    ("technical", "duration_sec"),
    ("features", "tempo_bpm"),
    ("features", "tempo_confidence"),
    ("features", "spectral_centroid_hz"),
    ("features", "rms"),
    ("features", "loudness_lufs"),
)
MISSING_VALUE_PENALTY = 1.0


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Search similar audio items by combining explicit metadata filters "
            "with lightweight similarity ranking."
        ),
        add_help=add_help,
    )
    add_filter_arguments(
        parser,
        input_help="Path to a metadata JSON file or an audio directory.",
        include_limit=False,
    )
    parser.add_argument(
        "--reference",
        required=True,
        help="Path to the reference audio file.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively scan subdirectories when --input points to a directory.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Maximum number of similar results to display. Default: 5.",
    )
    return parser


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.top_k <= 0:
        parser.error("--top-k must be greater than 0.")
    validate_search_args(args, parser)


def load_candidate_records(input_path: Path, recursive: bool) -> list[dict[str, Any]]:
    if input_path.is_dir():
        audio_files = scan_audio_files(input_path, recursive=recursive)
        return [normalize_record_schema_v1(_file_result_to_record(extract_file_metadata(path))) for path in audio_files]

    return load_records(input_path)


def _file_result_to_record(file_result: Any) -> dict[str, Any]:
    if hasattr(file_result, "__dict__"):
        return json.loads(json.dumps(file_result, default=lambda value: value.__dict__, ensure_ascii=False))
    raise TypeError(f"Unsupported record type: {type(file_result)!r}")


def get_numeric_value(record: dict[str, Any], path: tuple[str, ...]) -> float | None:
    value = get_nested_value(record, *path)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def build_reference_record(reference_path: Path) -> dict[str, Any]:
    return normalize_record_schema_v1(_file_result_to_record(extract_file_metadata(reference_path)))


def exclude_reference_self(
    records: list[dict[str, Any]],
    reference_path: Path,
) -> list[dict[str, Any]]:
    reference_resolved = reference_path.resolve()
    filtered_records: list[dict[str, Any]] = []
    for record in records:
        source_path = record.get("source_path")
        if not isinstance(source_path, str):
            filtered_records.append(record)
            continue
        try:
            candidate_path = Path(source_path).resolve()
        except OSError:
            filtered_records.append(record)
            continue
        if candidate_path == reference_resolved:
            continue
        filtered_records.append(record)
    return filtered_records


def build_similarity_stats(records: list[dict[str, Any]]) -> dict[tuple[str, ...], tuple[float, float]]:
    stats: dict[tuple[str, ...], tuple[float, float]] = {}
    for path in SIMILARITY_FIELD_PATHS:
        values = [value for record in records if (value := get_numeric_value(record, path)) is not None]
        if not values:
            stats[path] = (0.0, 1.0)
            continue
        scale = pstdev(values) if len(values) > 1 else 0.0
        stats[path] = (mean(values), scale or 1.0)
    return stats


def compute_similarity_score(
    reference_record: dict[str, Any],
    candidate_record: dict[str, Any],
    stats: dict[tuple[str, ...], tuple[float, float]],
) -> float | None:
    distances: list[float] = []

    for path in SIMILARITY_FIELD_PATHS:
        reference_value = get_numeric_value(reference_record, path)
        candidate_value = get_numeric_value(candidate_record, path)

        if reference_value is None and candidate_value is None:
            continue

        if reference_value is None or candidate_value is None:
            distances.append(MISSING_VALUE_PENALTY)
            continue

        center, scale = stats[path]
        normalized_reference = (reference_value - center) / scale
        normalized_candidate = (candidate_value - center) / scale
        distances.append(abs(normalized_reference - normalized_candidate))

    if not distances:
        return None

    distance = sum(distances) / len(distances)
    return 1.0 / (1.0 + distance)


def format_matched_filters_summary(record: dict[str, Any], args: argparse.Namespace) -> str:
    matched_fields = collect_matched_fields(record, args)
    if not matched_fields:
        return "none"

    keyword_fields = [
        str(item.get("field", "<unknown>"))
        for item in matched_fields
        if item.get("field") not in {
            "status",
            "tempo_bpm",
            "duration_sec",
            "tempo_applicable",
            "tempo_quality",
            "is_loop",
            "duration_bucket",
            "brightness",
        }
    ]

    summary_parts: list[str] = []
    if args.keyword and keyword_fields:
        keyword_targets = ",".join(sorted(set(keyword_fields)))
        summary_parts.append(f'keyword={json.dumps(args.keyword, ensure_ascii=False)} in {keyword_targets}')

    if args.status is not None:
        summary_parts.append(f"status={json.dumps(record.get('status'), ensure_ascii=False)}")

    if args.min_bpm is not None or args.max_bpm is not None:
        bpm_value = get_nested_value(record, "features", "tempo_bpm")
        summary_parts.append(f"tempo_bpm={json.dumps(bpm_value, ensure_ascii=False)}")

    if args.min_duration is not None or args.max_duration is not None:
        duration_value = get_nested_value(record, "technical", "duration_sec")
        summary_parts.append(f"duration_sec={json.dumps(duration_value, ensure_ascii=False)}")

    if args.tempo_applicable is not None:
        summary_parts.append(f"tempo_applicable={json.dumps(record.get('tempo_applicable'), ensure_ascii=False)}")

    if args.tempo_quality is not None:
        tempo_quality = get_nested_value(record, "features", "tempo_quality")
        summary_parts.append(f"tempo_quality={json.dumps(tempo_quality, ensure_ascii=False)}")

    if args.is_loop is not None:
        summary_parts.append(f"is_loop={json.dumps(record.get('is_loop'), ensure_ascii=False)}")

    if args.duration_bucket is not None:
        summary_parts.append(f"duration_bucket={json.dumps(record.get('duration_bucket'), ensure_ascii=False)}")

    if args.brightness is not None:
        summary_parts.append(f"brightness={json.dumps(record.get('brightness'), ensure_ascii=False)}")

    return "; ".join(summary_parts) if summary_parts else "none"


def format_result(
    record: dict[str, Any],
    similarity_score: float,
    matched_filters_summary: str,
) -> str:
    file_name = record.get("file_name", "<unknown>")
    source_path = record.get("source_path", "<unknown>")
    return (
        f"file_name: {file_name}\n"
        f"source_path: {source_path}\n"
        f"similarity_score: {similarity_score:.6f}\n"
        f"matched_filters_summary: {matched_filters_summary}"
    )


def run(args: argparse.Namespace) -> int:
    input_path = Path(args.input).expanduser().resolve()
    reference_path = Path(args.reference).expanduser().resolve()

    if not reference_path.exists() or not reference_path.is_file():
        raise ValueError(f"Reference audio file does not exist or is not a file: {reference_path}")

    try:
        records = load_candidate_records(input_path, recursive=args.recursive)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    reference_record = build_reference_record(reference_path)
    total_candidates = len(records)
    records_without_self = exclude_reference_self(records, reference_path)
    filtered_candidates = [record for record in records_without_self if match_record(record, args)]
    stats = build_similarity_stats(filtered_candidates)

    ranked_results: list[tuple[float, dict[str, Any]]] = []
    for record in filtered_candidates:
        similarity_score = compute_similarity_score(reference_record, record, stats)
        if similarity_score is None:
            continue
        ranked_results.append((similarity_score, record))

    ranked_results.sort(
        key=lambda item: (
            -item[0],
            str(item[1].get("file_name", "")).casefold(),
            str(item[1].get("source_path", "")).casefold(),
        )
    )
    displayed_results = ranked_results[: args.top_k]

    print(f"reference_file: {reference_path}")
    print(f"total_candidates: {total_candidates}")
    print(f"filtered_candidates: {len(filtered_candidates)}")
    print(f"ranked_candidates: {len(ranked_results)}")

    if not displayed_results:
        return 0

    for index, (similarity_score, record) in enumerate(displayed_results, start=1):
        matched_filters_summary = format_matched_filters_summary(record, args)
        print()
        print(f"[{index}]")
        print(format_result(record, similarity_score, matched_filters_summary))

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(args, parser)
    try:
        return run(args)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
