from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from audio_metadata import APP_VERSION
from audio_metadata.schema import (
    BRIGHTNESS_CHOICES,
    TEMPO_QUALITY_CHOICES,
    normalize_payload_schema_v1,
)
from search_metadata import (
    add_filter_arguments,
    get_nested_value,
    load_payload,
    match_record,
    parse_bool_arg,
    parse_choice_arg,
    validate_args as validate_search_args,
)


_UNSET = object()
CLEARABLE_FIELDS = (
    "is_loop",
    "brightness",
    "tempo_applicable",
    "tempo_bpm",
    "tempo_quality",
    "notes",
)
OVERRIDE_FIELD_LABELS = {
    "is_loop": "derived.is_loop",
    "brightness": "derived.brightness",
    "tempo_applicable": "derived.tempo_applicable",
    "tempo_bpm": "features.tempo_bpm",
    "tempo_quality": "features.tempo_quality",
    "notes": "review.notes",
}
OVERRIDE_FIELD_ORDER = (
    "derived.is_loop",
    "derived.brightness",
    "derived.tempo_applicable",
    "features.tempo_bpm",
    "features.tempo_quality",
)
CANDIDATE_RULE_DESCRIPTIONS = {
    "A": "filename has BPM but tempo is disabled or missing",
    "B": "filename contains fill token but is_loop is still true",
    "C": "filename contains dark but brightness is not dark",
    "D": "tempo_quality is low on loop or tempo-filterable material",
}
FILENAME_BPM_PATTERN = re.compile(r"(?<!\d)(\d{2,3})(?!\d)")
FILENAME_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")
FILENAME_STOPWORDS = {"kshmr", "wav", "mp3", "aif", "aiff", "flac"}
RULE_CHOICES = ("A", "B", "C", "D")
BATCH_PRESET_CHOICES = (
    "restore-bpm-from-filename-for-loops",
    "mark-fill-as-non-loop",
    "mark-dark-name-as-dark",
)
BATCH_PRESET_DESCRIPTIONS = {
    "restore-bpm-from-filename-for-loops": "Restore tempo flags and BPM from filename digits for loop material.",
    "mark-fill-as-non-loop": "Mark fill-named material as non-loop.",
    "mark-dark-name-as-dark": "Set brightness to dark when the filename says dark.",
}
RULE_RECOMMENDED_PRESETS = {
    "A": "restore-bpm-from-filename-for-loops",
    "B": "mark-fill-as-non-loop",
    "C": "mark-dark-name-as-dark",
    "D": "manual-review-low-tempo-quality",
}
PRESET_NOTE_PREFIX = "preset: "
DEFAULT_BATCH_PREVIEW_LIMIT = 5
DEFAULT_CANDIDATE_LIMIT = 20
DEFAULT_STATS_TOP_NOTES = 10
DEFAULT_STATS_TOP_NOTE_PREFIXES = 10
DEFAULT_STATS_TOP_SOURCES = 8
DEFAULT_STATS_TOP_COMBOS = 5
DEFAULT_STATS_TOP_KEYWORDS = 8


def parse_optional_float_arg(value: str) -> float | None:
    normalized = value.strip().casefold()
    if normalized == "null":
        return None

    try:
        numeric_value = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected a float or null") from exc

    if not math.isfinite(numeric_value):
        raise argparse.ArgumentTypeError("expected a finite float or null")

    return numeric_value


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write minimal review overrides into a schema v1 metadata JSON file.",
        add_help=add_help,
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the input metadata JSON file.",
    )
    parser.add_argument(
        "--output",
        help="Path to the output JSON file. Defaults to --input.",
    )

    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--id", help="Target record id.")
    target_group.add_argument("--source-path", help="Target record source path.")

    _add_review_change_arguments(parser)
    return parser


def build_batch_parser(add_help: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preview or batch-apply minimal review overrides to records matched by explicit search filters."
        ),
        add_help=add_help,
    )
    add_filter_arguments(
        parser,
        input_help="Path to the input metadata JSON file.",
        include_limit=False,
    )
    parser.add_argument(
        "--preset",
        choices=BATCH_PRESET_CHOICES,
        help="Use a built-in safe batch-review template instead of manual --set-* overrides.",
    )
    parser.add_argument(
        "--output",
        help="Path to the output JSON file. Defaults to --input when --apply is used.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to JSON. Default behavior is dry-run preview only.",
    )
    parser.add_argument(
        "--preview-limit",
        type=int,
        default=DEFAULT_BATCH_PREVIEW_LIMIT,
        help=f"Number of matched records to preview. Default: {DEFAULT_BATCH_PREVIEW_LIMIT}.",
    )
    _add_review_change_arguments(parser, option_prefix="--set-", dest_prefix="set_")
    return parser


def build_candidates_parser(add_help: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List high-value records that likely deserve manual review.",
        add_help=add_help,
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the input metadata JSON file.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_CANDIDATE_LIMIT,
        help=f"Maximum number of examples to display per rule. Default: {DEFAULT_CANDIDATE_LIMIT}.",
    )
    parser.add_argument(
        "--rule",
        choices=RULE_CHOICES,
        help="Only show candidates for one rule group.",
    )
    parser.add_argument(
        "--include-rule-d",
        action="store_true",
        help="Also include low-tempo-quality loop or tempo-filterable candidates.",
    )
    return parser


def build_stats_parser(add_help: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize current review override and notes coverage.",
        add_help=add_help,
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the input metadata JSON file.",
    )
    parser.add_argument(
        "--top-notes",
        type=int,
        default=DEFAULT_STATS_TOP_NOTES,
        help=f"Number of full note strings to display. Default: {DEFAULT_STATS_TOP_NOTES}.",
    )
    parser.add_argument(
        "--top-note-prefixes",
        type=int,
        default=DEFAULT_STATS_TOP_NOTE_PREFIXES,
        help=f"Number of note prefixes to display. Default: {DEFAULT_STATS_TOP_NOTE_PREFIXES}.",
    )
    parser.add_argument(
        "--top-sources",
        type=int,
        default=DEFAULT_STATS_TOP_SOURCES,
        help=f"Number of inferred correction sources to display. Default: {DEFAULT_STATS_TOP_SOURCES}.",
    )
    parser.add_argument(
        "--top-combos",
        type=int,
        default=DEFAULT_STATS_TOP_COMBOS,
        help=f"Number of correction-type combinations to display. Default: {DEFAULT_STATS_TOP_COMBOS}.",
    )
    parser.add_argument(
        "--top-keywords",
        type=int,
        default=DEFAULT_STATS_TOP_KEYWORDS,
        help=f"Number of reviewed filename keywords to display. Default: {DEFAULT_STATS_TOP_KEYWORDS}.",
    )
    return parser


def _add_review_change_arguments(
    parser: argparse.ArgumentParser,
    *,
    option_prefix: str = "--",
    dest_prefix: str = "",
) -> None:
    parser.add_argument(
        f"{option_prefix}is-loop",
        dest=f"{dest_prefix}is_loop",
        type=parse_bool_arg,
        metavar="<true|false>",
        default=_UNSET,
        help="Set review.overrides.derived.is_loop.",
    )
    parser.add_argument(
        f"{option_prefix}brightness",
        dest=f"{dest_prefix}brightness",
        type=lambda value: parse_choice_arg(value, BRIGHTNESS_CHOICES),
        metavar="<dark|balanced|bright|very_bright>",
        default=_UNSET,
        help="Set review.overrides.derived.brightness.",
    )
    parser.add_argument(
        f"{option_prefix}tempo-applicable",
        dest=f"{dest_prefix}tempo_applicable",
        type=parse_bool_arg,
        metavar="<true|false>",
        default=_UNSET,
        help="Set review.overrides.derived.tempo_applicable.",
    )
    parser.add_argument(
        f"{option_prefix}tempo-bpm",
        dest=f"{dest_prefix}tempo_bpm",
        type=parse_optional_float_arg,
        metavar="<float|null>",
        default=_UNSET,
        help="Set review.overrides.features.tempo_bpm.",
    )
    parser.add_argument(
        f"{option_prefix}tempo-quality",
        dest=f"{dest_prefix}tempo_quality",
        type=lambda value: parse_choice_arg(value, TEMPO_QUALITY_CHOICES),
        metavar="<high|medium|low|not_applicable>",
        default=_UNSET,
        help="Set review.overrides.features.tempo_quality.",
    )
    parser.add_argument(
        f"{option_prefix}note",
        dest=f"{dest_prefix}note",
        action="extend",
        nargs="+",
        help="Replace review.notes with one or more note strings.",
    )
    parser.add_argument(
        "--clear",
        action="extend",
        nargs="+",
        choices=CLEARABLE_FIELDS,
        help="Clear one or more override fields or notes.",
    )


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    _validate_review_change_args(args, parser)


def validate_batch_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    validate_search_args(args, parser)

    if args.preview_limit <= 0:
        parser.error("--preview-limit must be greater than 0.")

    if args.preset is not None:
        manual_change_request = _build_change_request_from_args(args, prefix="set_", require_change=False)
        if manual_change_request["set"] or manual_change_request["clear"]:
            parser.error("--preset cannot be combined with manual --set-* or --clear review changes.")
        if args.apply and args.output is None:
            parser.error("--output is required with --preset --apply so batch presets write to a reviewed copy.")
        return

    _validate_review_change_args(args, parser, prefix="set_")
    if not _has_any_batch_filter(args):
        parser.error("At least one filter is required for review-batch to avoid whole-library updates.")


def validate_candidates_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.limit <= 0:
        parser.error("--limit must be greater than 0.")


def validate_stats_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.top_notes <= 0:
        parser.error("--top-notes must be greater than 0.")
    if args.top_note_prefixes <= 0:
        parser.error("--top-note-prefixes must be greater than 0.")
    if args.top_sources <= 0:
        parser.error("--top-sources must be greater than 0.")
    if args.top_combos <= 0:
        parser.error("--top-combos must be greater than 0.")
    if args.top_keywords <= 0:
        parser.error("--top-keywords must be greater than 0.")


def run(args: argparse.Namespace) -> int:
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output or args.input).expanduser().resolve()

    try:
        payload = load_payload(input_path)
        target_record = _find_target_record(payload["files"], args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    target_record["review"] = _build_updated_review(target_record, args)
    normalized_payload = normalize_payload_schema_v1(payload, app_version=APP_VERSION)
    _write_payload(output_path, normalized_payload)

    print(
        f"Updated review for {target_record.get('file_name', '<unknown>')} "
        f"({target_record.get('id', '<unknown>')}) -> {output_path}"
    )
    return 0


def run_batch(args: argparse.Namespace) -> int:
    input_path = Path(args.input).expanduser().resolve()

    try:
        payload = load_payload(input_path)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    plans = _collect_batch_plans(payload["files"], args)
    matched_records = [plan["record"] for plan in plans]
    pending_plans = [plan for plan in plans if plan["changed"]]

    if args.preset is not None:
        print(f"Preset: {args.preset}")
        print(f"Preset description: {BATCH_PRESET_DESCRIPTIONS[args.preset]}")

    print(f"Matched {len(matched_records)} record(s).")
    print(f"Records that would change: {len(pending_plans)}.")
    print("Requested changes:")
    source_plans = pending_plans or plans
    for line in _describe_change_requests(plan["change_request"] for plan in source_plans):
        print(f"- {line}")

    preview_records = [plan["record"] for plan in pending_plans] or matched_records
    preview_count = min(len(preview_records), args.preview_limit)
    if preview_count:
        print(f"Previewing {preview_count} record(s):")
        for index, record in enumerate(preview_records[:preview_count], start=1):
            print(
                f"[{index}] {record.get('file_name', '<unknown>')} | "
                f"{record.get('source_path', '<unknown>')}"
            )
    else:
        print("Previewing 0 record(s).")

    if not args.apply:
        print("Dry-run only. Re-run with --apply to write changes.")
        return 0

    if not pending_plans:
        print("No changes were written because all matched records already had the requested review state.")
        return 0

    output_path = Path(args.output or args.input).expanduser().resolve()
    for plan in pending_plans:
        plan["record"]["review"] = plan["updated_review"]

    normalized_payload = normalize_payload_schema_v1(payload, app_version=APP_VERSION)
    _write_payload(output_path, normalized_payload)

    print(f"Wrote {len(pending_plans)} updated record(s) to {output_path}")
    return 0


def run_candidates(args: argparse.Namespace) -> int:
    input_path = Path(args.input).expanduser().resolve()

    try:
        records = load_payload(input_path)["files"]
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    include_rule_d = args.include_rule_d or args.rule == "D"
    candidates = _collect_review_candidates(records, include_rule_d=include_rule_d)
    if args.rule is not None:
        candidates = [item for item in candidates if args.rule in item["rules"]]
        selected_rules = (args.rule,)
    else:
        selected_rules = tuple(rule for rule in RULE_CHOICES if any(rule in item["rules"] for item in candidates))

    grouped_candidates = _group_review_candidates(candidates, selected_rules)

    print(f"Found {len(candidates)} review candidate(s).")
    print("Rule groups:")
    for rule_name in selected_rules:
        rule_items = grouped_candidates.get(rule_name, [])
        if not rule_items:
            continue
        print(f"- Rule {rule_name}: {len(rule_items)} ({CANDIDATE_RULE_DESCRIPTIONS[rule_name]})")
        print(f"  Recommended action: {RULE_RECOMMENDED_PRESETS[rule_name]}")

    print(f"Showing up to {args.limit} example(s) per rule.")
    for rule_name in selected_rules:
        rule_items = grouped_candidates.get(rule_name, [])
        if not rule_items:
            continue
        print()
        print(f"Rule {rule_name} examples ({min(len(rule_items), args.limit)}/{len(rule_items)}):")
        for index, item in enumerate(rule_items[: args.limit], start=1):
            print()
            print(f"[{index}]")
            print(_format_candidate(item))

    return 0


def run_stats(args: argparse.Namespace) -> int:
    input_path = Path(args.input).expanduser().resolve()

    try:
        records = load_payload(input_path)["files"]
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    reviewed_records = [record for record in records if _record_has_review_content(record)]
    override_counts = Counter()
    note_counts = Counter()
    note_prefix_counts = Counter()
    source_counts = Counter()
    combo_counts = Counter()
    keyword_counts = Counter()

    for record in reviewed_records:
        review = _get_review_dict(record)
        override_fields = _collect_override_field_labels(review)
        for field_label in override_fields:
            override_counts[field_label] += 1

        notes = _get_review_notes(review)
        for note in notes:
            note_counts[note] += 1
            note_prefix_counts[_extract_note_prefix(note)] += 1
            inferred_source = _infer_correction_source(note)
            if inferred_source is not None:
                source_counts[inferred_source] += 1

        if override_fields:
            combo_counts[" + ".join(override_fields)] += 1
        elif notes:
            combo_counts["review.notes only"] += 1

        keyword_counts.update(_extract_review_keywords(record.get("file_name")))

    print(f"Total records: {len(records)}")
    print(f"Reviewed records: {len(reviewed_records)}")
    print("Override field counts:")
    for field_label in OVERRIDE_FIELD_ORDER:
        print(f"- {field_label}: {override_counts[field_label]}")

    print("Most common correction types:")
    if combo_counts:
        for label, count in combo_counts.most_common(args.top_combos):
            print(f"- {label}: {count}")
    else:
        print("- none")

    print("Most common notes:")
    if note_counts:
        for note, count in note_counts.most_common(args.top_notes):
            print(f"- {note}: {count}")
    else:
        print("- none")

    print("Most common note prefixes:")
    if note_prefix_counts:
        for prefix, count in note_prefix_counts.most_common(args.top_note_prefixes):
            print(f"- {prefix}: {count}")
    else:
        print("- none")

    print("Inferred correction sources:")
    if source_counts:
        for label, count in source_counts.most_common(args.top_sources):
            print(f"- {label}: {count}")
    else:
        print("- none")

    print("Reviewed filename keywords:")
    if keyword_counts:
        for keyword, count in keyword_counts.most_common(args.top_keywords):
            print(f"- {keyword}: {count}")
    else:
        print("- none")

    return 0


def _validate_review_change_args(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    *,
    prefix: str = "",
) -> None:
    change_request = _build_change_request_from_args(args, prefix=prefix, require_change=False)
    set_fields = set(change_request["set"])
    clear_fields = set(change_request["clear"])

    if not set_fields and not clear_fields:
        parser.error("At least one review override or notes change must be provided.")

    conflicting_fields = sorted(set_fields & clear_fields)
    if conflicting_fields:
        joined = ", ".join(conflicting_fields)
        parser.error(f"Cannot set and clear the same field in one command: {joined}")


def _collect_set_field_names(args: argparse.Namespace, *, prefix: str = "") -> set[str]:
    set_fields: set[str] = set()
    if _get_review_arg(args, "is_loop", prefix) is not _UNSET:
        set_fields.add("is_loop")
    if _get_review_arg(args, "brightness", prefix) is not _UNSET:
        set_fields.add("brightness")
    if _get_review_arg(args, "tempo_applicable", prefix) is not _UNSET:
        set_fields.add("tempo_applicable")
    if _get_review_arg(args, "tempo_bpm", prefix) is not _UNSET:
        set_fields.add("tempo_bpm")
    if _get_review_arg(args, "tempo_quality", prefix) is not _UNSET:
        set_fields.add("tempo_quality")
    if _get_review_arg(args, "note", prefix) is not None:
        set_fields.add("notes")
    return set_fields


def _get_review_arg(args: argparse.Namespace, field_name: str, prefix: str) -> Any:
    return getattr(args, f"{prefix}{field_name}")


def _find_target_record(records: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    if args.id is not None:
        matches = [record for record in records if record.get("id") == args.id]
        selector = f"id={args.id}"
    else:
        raw_source_path = str(args.source_path)
        resolved_source_path = _normalize_path_text(raw_source_path)
        matches = []
        for record in records:
            candidate_source_path = record.get("source_path")
            if not isinstance(candidate_source_path, str):
                continue
            if candidate_source_path == raw_source_path:
                matches.append(record)
                continue
            if _normalize_path_text(candidate_source_path) == resolved_source_path:
                matches.append(record)
        selector = f"source_path={raw_source_path}"

    if not matches:
        raise ValueError(f"No record matched {selector}.")
    if len(matches) > 1:
        raise ValueError(f"More than one record matched {selector}.")
    return matches[0]


def _build_updated_review(
    record: dict[str, Any],
    args: argparse.Namespace,
    *,
    prefix: str = "",
) -> dict[str, Any]:
    return _build_updated_review_from_change_request(
        record,
        _build_change_request_from_args(args, prefix=prefix, require_change=True),
    )


def _build_change_request_from_args(
    args: argparse.Namespace,
    *,
    prefix: str = "",
    require_change: bool,
) -> dict[str, Any]:
    set_values: dict[str, Any] = {}
    for field_name in ("is_loop", "brightness", "tempo_applicable", "tempo_bpm", "tempo_quality"):
        value = _get_review_arg(args, field_name, prefix)
        if value is _UNSET:
            continue
        set_values[field_name] = value

    note_value = _get_review_arg(args, "note", prefix)
    if note_value is not None:
        set_values["notes"] = list(note_value)

    clear_fields = set(args.clear or [])
    if require_change and not set_values and not clear_fields:
        raise ValueError("At least one review override or notes change must be provided.")

    return {
        "set": set_values,
        "clear": clear_fields,
        "note_mode": "replace",
    }


def _build_updated_review_from_change_request(
    record: dict[str, Any],
    change_request: dict[str, Any],
) -> dict[str, Any]:
    review = _get_review_dict(record)
    overrides = dict(review.get("overrides") or {}) if isinstance(review.get("overrides"), dict) else {}
    derived_overrides = (
        dict(overrides.get("derived") or {})
        if isinstance(overrides.get("derived"), dict)
        else {}
    )
    features_overrides = (
        dict(overrides.get("features") or {})
        if isinstance(overrides.get("features"), dict)
        else {}
    )

    clear_fields = set(change_request.get("clear") or set())
    for field_name in clear_fields:
        if field_name == "notes":
            review.pop("notes", None)
        elif field_name in {"is_loop", "brightness", "tempo_applicable"}:
            derived_overrides.pop(field_name, None)
        elif field_name in {"tempo_bpm", "tempo_quality"}:
            features_overrides.pop(field_name, None)

    set_values = dict(change_request.get("set") or {})
    if "is_loop" in set_values:
        derived_overrides["is_loop"] = set_values["is_loop"]
    if "brightness" in set_values:
        derived_overrides["brightness"] = set_values["brightness"]
    if "tempo_applicable" in set_values:
        derived_overrides["tempo_applicable"] = set_values["tempo_applicable"]
    if "tempo_bpm" in set_values:
        features_overrides["tempo_bpm"] = set_values["tempo_bpm"]
    if "tempo_quality" in set_values:
        features_overrides["tempo_quality"] = set_values["tempo_quality"]

    note_values = set_values.get("notes")
    if note_values is not None:
        if change_request.get("note_mode") == "append":
            existing_notes = _get_review_notes(review)
            combined_notes = list(existing_notes)
            for note in note_values:
                if note not in combined_notes:
                    combined_notes.append(note)
            if combined_notes:
                review["notes"] = combined_notes
        else:
            review["notes"] = list(note_values)

    if derived_overrides:
        overrides["derived"] = derived_overrides
    else:
        overrides.pop("derived", None)

    if features_overrides:
        overrides["features"] = features_overrides
    else:
        overrides.pop("features", None)

    if overrides:
        review["overrides"] = overrides
    else:
        review.pop("overrides", None)

    return review


def _build_preset_change_request(record: dict[str, Any], preset_name: str) -> dict[str, Any] | None:
    file_name = str(record.get("file_name") or "")
    filename_tokens = set(_extract_filename_tokens(file_name))
    filename_bpm = _extract_filename_bpm(file_name)
    tempo_bpm = get_nested_value(record, "features", "tempo_bpm")

    if preset_name == "restore-bpm-from-filename-for-loops":
        if record.get("is_loop") is not True:
            return None
        if filename_bpm is None:
            return None
        if not (record.get("tempo_applicable") is False or tempo_bpm is None):
            return None
        return {
            "set": {
                "tempo_applicable": True,
                "tempo_bpm": float(filename_bpm),
                "tempo_quality": "low",
                "notes": [f"{PRESET_NOTE_PREFIX}{preset_name}"],
            },
            "clear": set(),
            "note_mode": "append",
        }

    if preset_name == "mark-fill-as-non-loop":
        if "fill" not in filename_tokens or record.get("is_loop") is not True:
            return None
        return {
            "set": {
                "is_loop": False,
                "notes": [f"{PRESET_NOTE_PREFIX}{preset_name}"],
            },
            "clear": set(),
            "note_mode": "append",
        }

    if preset_name == "mark-dark-name-as-dark":
        if "dark" not in filename_tokens or record.get("brightness") == "dark":
            return None
        return {
            "set": {
                "brightness": "dark",
                "notes": [f"{PRESET_NOTE_PREFIX}{preset_name}"],
            },
            "clear": set(),
            "note_mode": "append",
        }

    raise ValueError(f"Unsupported batch preset: {preset_name}")


def _collect_batch_plans(records: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    plans: list[dict[str, Any]] = []
    manual_change_request = None
    if args.preset is None:
        manual_change_request = _build_change_request_from_args(args, prefix="set_", require_change=True)

    for record in records:
        if not match_record(record, args):
            continue

        change_request = (
            _build_preset_change_request(record, args.preset)
            if args.preset is not None
            else manual_change_request
        )
        if change_request is None:
            continue

        updated_review = _build_updated_review_from_change_request(record, change_request)
        plans.append(
            {
                "record": record,
                "change_request": change_request,
                "updated_review": updated_review,
                "changed": updated_review != _get_review_dict(record),
            }
        )

    return plans


def _has_any_batch_filter(args: argparse.Namespace) -> bool:
    filter_names = (
        "keyword",
        "min_bpm",
        "max_bpm",
        "min_duration",
        "max_duration",
        "tempo_applicable",
        "tempo_quality",
        "is_loop",
        "duration_bucket",
        "brightness",
        "status",
    )
    return any(getattr(args, name) is not None for name in filter_names)


def _describe_requested_changes(args: argparse.Namespace, *, prefix: str = "") -> list[str]:
    return _describe_change_request(_build_change_request_from_args(args, prefix=prefix, require_change=False))


def _describe_change_request(change_request: dict[str, Any]) -> list[str]:
    return _describe_change_requests([change_request])


def _describe_change_requests(change_requests) -> list[str]:
    set_values_by_field: dict[str, list[Any]] = {}
    clear_fields: set[str] = set()
    note_mode = None

    for change_request in change_requests:
        clear_fields.update(change_request.get("clear") or set())
        current_note_mode = change_request.get("note_mode")
        if current_note_mode is not None:
            note_mode = current_note_mode
        for field_name, value in dict(change_request.get("set") or {}).items():
            set_values_by_field.setdefault(field_name, []).append(value)

    lines: list[str] = []
    for field_name in ("is_loop", "brightness", "tempo_applicable", "tempo_bpm", "tempo_quality"):
        values = set_values_by_field.get(field_name)
        if not values:
            continue
        serialized_values = {json.dumps(value, ensure_ascii=False) for value in values}
        if len(serialized_values) == 1:
            value_text = next(iter(serialized_values))
        elif field_name == "tempo_bpm":
            value_text = "<filename_bpm per record>"
        else:
            value_text = "<varies per record>"
        lines.append(f"set {OVERRIDE_FIELD_LABELS[field_name]} = {value_text}")

    note_values = set_values_by_field.get("notes")
    if note_values:
        serialized_notes = {json.dumps(value, ensure_ascii=False) for value in note_values}
        if len(serialized_notes) == 1:
            note_text = next(iter(serialized_notes))
        else:
            note_text = "<varies per record>"
        if note_mode == "append":
            lines.append(f"append review.notes += {note_text}")
        else:
            lines.append(f"set review.notes = {note_text}")

    for field_name in sorted(clear_fields):
        lines.append(f"clear {OVERRIDE_FIELD_LABELS[field_name]}")

    return lines


def _collect_review_candidates(
    records: list[dict[str, Any]],
    *,
    include_rule_d: bool,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for record in records:
        rules = _detect_candidate_rules(record, include_rule_d=include_rule_d)
        if not rules:
            continue
        candidates.append(
            {
                "record": record,
                "rules": rules,
                "summary": _build_candidate_summary(record),
            }
        )

    candidates.sort(
        key=lambda item: (
            -len(item["rules"]),
            str(item["record"].get("file_name", "")).casefold(),
            str(item["record"].get("source_path", "")).casefold(),
        )
    )
    return candidates


def _group_review_candidates(
    candidates: list[dict[str, Any]],
    selected_rules: tuple[str, ...],
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {rule_name: [] for rule_name in selected_rules}
    for item in candidates:
        for rule_name in item["rules"]:
            if rule_name in grouped:
                grouped[rule_name].append(item)
    return grouped


def _detect_candidate_rules(record: dict[str, Any], *, include_rule_d: bool) -> list[str]:
    file_name = str(record.get("file_name") or "")
    filename_tokens = set(_extract_filename_tokens(file_name))
    filename_bpm = _extract_filename_bpm(file_name)
    tempo_bpm = get_nested_value(record, "features", "tempo_bpm")
    tempo_quality = get_nested_value(record, "features", "tempo_quality")

    rules: list[str] = []
    if filename_bpm is not None and (record.get("tempo_applicable") is False or tempo_bpm is None):
        rules.append("A")
    if "fill" in filename_tokens and record.get("is_loop") is True:
        rules.append("B")
    if "dark" in filename_tokens and record.get("brightness") != "dark":
        rules.append("C")
    if include_rule_d and tempo_quality == "low":
        if record.get("is_loop") is True or (record.get("tempo_applicable") is True and tempo_bpm is not None):
            rules.append("D")

    return rules


def _build_candidate_summary(record: dict[str, Any]) -> str:
    file_name = str(record.get("file_name") or "")
    parts = [
        f"filename_bpm={json.dumps(_extract_filename_bpm(file_name), ensure_ascii=False)}",
        f"tempo_applicable={json.dumps(record.get('tempo_applicable'), ensure_ascii=False)}",
        f"tempo_bpm={json.dumps(get_nested_value(record, 'features', 'tempo_bpm'), ensure_ascii=False)}",
        f"tempo_quality={json.dumps(get_nested_value(record, 'features', 'tempo_quality'), ensure_ascii=False)}",
        f"is_loop={json.dumps(record.get('is_loop'), ensure_ascii=False)}",
        f"brightness={json.dumps(record.get('brightness'), ensure_ascii=False)}",
    ]
    return ", ".join(parts)


def _format_candidate(item: dict[str, Any]) -> str:
    record = item["record"]
    rule_parts = [f"Rule {rule} ({CANDIDATE_RULE_DESCRIPTIONS[rule]})" for rule in item["rules"]]
    return (
        f"file_name: {record.get('file_name', '<unknown>')}\n"
        f"source_path: {record.get('source_path', '<unknown>')}\n"
        f"rules: {', '.join(rule_parts)}\n"
        f"current_fields: {item['summary']}"
    )


def _extract_filename_bpm(file_name: str) -> int | None:
    for match in FILENAME_BPM_PATTERN.finditer(file_name):
        bpm = int(match.group(1))
        if 40 <= bpm <= 220:
            return bpm
    return None


def _extract_filename_tokens(file_name: str) -> list[str]:
    return [token.casefold() for token in FILENAME_TOKEN_PATTERN.findall(file_name)]


def _record_has_review_content(record: dict[str, Any]) -> bool:
    return bool(_get_review_dict(record))


def _get_review_dict(record: dict[str, Any]) -> dict[str, Any]:
    review = record.get("review")
    return dict(review) if isinstance(review, dict) else {}


def _get_review_notes(review: dict[str, Any]) -> list[str]:
    raw_notes = review.get("notes")
    if not isinstance(raw_notes, list):
        return []
    return [note for note in raw_notes if isinstance(note, str)]


def _collect_override_field_labels(review: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    overrides = dict(review.get("overrides") or {}) if isinstance(review.get("overrides"), dict) else {}
    derived = dict(overrides.get("derived") or {}) if isinstance(overrides.get("derived"), dict) else {}
    features = dict(overrides.get("features") or {}) if isinstance(overrides.get("features"), dict) else {}

    if "is_loop" in derived:
        labels.append("derived.is_loop")
    if "brightness" in derived:
        labels.append("derived.brightness")
    if "tempo_applicable" in derived:
        labels.append("derived.tempo_applicable")
    if "tempo_bpm" in features:
        labels.append("features.tempo_bpm")
    if "tempo_quality" in features:
        labels.append("features.tempo_quality")

    return labels


def _extract_review_keywords(file_name: Any) -> list[str]:
    if not isinstance(file_name, str):
        return []

    keywords: list[str] = []
    for token in _extract_filename_tokens(file_name):
        if token in FILENAME_STOPWORDS:
            continue
        if token.isdigit():
            continue
        keywords.append(token)
    return keywords


def _extract_note_prefix(note: str) -> str:
    stripped = note.strip()
    if ":" not in stripped:
        return stripped
    prefix, _ = stripped.split(":", 1)
    return prefix.strip()


def _infer_correction_source(note: str) -> str | None:
    stripped = note.strip()
    if stripped.casefold().startswith(PRESET_NOTE_PREFIX.casefold()):
        return stripped[len(PRESET_NOTE_PREFIX) :].strip() or None

    normalized = stripped.casefold()
    if "restore bpm" in normalized and "filename" in normalized:
        return "restore-bpm-from-filename-for-loops"
    if "fill" in normalized and "non-loop" in normalized:
        return "mark-fill-as-non-loop"
    if "dark" in normalized:
        return "mark-dark-name-as-dark"
    return None


def _normalize_path_text(path_text: str) -> str:
    try:
        return str(Path(path_text).expanduser().resolve())
    except OSError:
        return str(Path(path_text).expanduser())


def _write_payload(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


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



