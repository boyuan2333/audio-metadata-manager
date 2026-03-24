from __future__ import annotations

import hashlib
import math
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from audio_metadata import APP_VERSION, SCHEMA_VERSION


BRIGHTNESS_CHOICES = ("dark", "balanced", "bright", "very_bright")
TEMPO_QUALITY_CHOICES = ("high", "medium", "low", "not_applicable")

FEATURE_FIELD_DEFAULTS: dict[str, Any] = {
    "loudness_lufs": None,
    "tempo_bpm": None,
    "tempo_confidence": None,
    "tempo_quality": None,
    "spectral_centroid_hz": None,
    "rms": None,
}
TECHNICAL_FIELD_DEFAULTS: dict[str, Any] = {
    "duration_sec": None,
    "sample_rate_hz": None,
    "channels": None,
}
DERIVED_FIELD_DEFAULTS: dict[str, Any] = {
    "tempo_applicable": None,
    "is_loop": None,
    "duration_bucket": None,
    "brightness": None,
}
RETRIEVAL_FIELD_DEFAULTS: dict[str, Any] = {
    "tags": [],
    "mood": None,
    "texture": None,
    "density": None,
    "role": None,
    "domain": None,
}
MODEL_OUTPUT_FIELD_DEFAULTS: dict[str, Any] = {
    "instrument_family": None,
    "texture": None,
    "timbre_type": None,
}


def to_plain_data(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    return value


def build_record_id(source_path: str | None, file_name: str | None, file_format: str | None) -> str:
    raw_text = "||".join(
        [
            source_path or "",
            file_name or "",
            file_format or "",
        ]
    )
    return hashlib.sha1(raw_text.encode("utf-8")).hexdigest()


def normalize_payload_schema_v1(
    payload: dict[str, Any],
    *,
    app_version: str | None = None,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Input JSON must be an object with a top-level 'files' array.")

    records = payload.get("files")
    if not isinstance(records, list):
        raise ValueError("Input JSON must contain a top-level 'files' array.")

    run_data = dict(payload.get("run") or {}) if isinstance(payload.get("run"), dict) else {}
    payload_app_version = payload.get("app_version") if isinstance(payload.get("app_version"), str) else APP_VERSION

    normalized_files: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Record at files[{index}] is not a JSON object.")
        normalized_files.append(normalize_record_schema_v1(record))

    return {
        "schema_version": SCHEMA_VERSION,
        "app_version": app_version or payload_app_version,
        "run": run_data,
        "files": normalized_files,
    }


def normalize_record_schema_v1(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)

    source_data = dict(record.get("source") or {}) if isinstance(record.get("source"), dict) else {}
    technical_data = dict(record.get("technical") or {}) if isinstance(record.get("technical"), dict) else {}
    features_data = dict(record.get("features") or {}) if isinstance(record.get("features"), dict) else {}
    derived_data = dict(record.get("derived") or {}) if isinstance(record.get("derived"), dict) else {}
    retrieval_data = dict(record.get("retrieval") or {}) if isinstance(record.get("retrieval"), dict) else {}
    raw_review_data = dict(record.get("review") or {}) if isinstance(record.get("review"), dict) else {}
    model_outputs_data = (
        dict(record.get("model_outputs") or {})
        if isinstance(record.get("model_outputs"), dict)
        else {}
    )
    segments_data = list(record.get("segments") or [])
    errors_data = list(record.get("errors") or [])

    file_name = _coalesce(source_data.get("file_name"), record.get("file_name"))
    source_path = _coalesce(source_data.get("path"), record.get("source_path"))
    file_format = _coalesce(source_data.get("file_format"), record.get("file_format"))
    status = record.get("status")

    technical = _build_section(TECHNICAL_FIELD_DEFAULTS, technical_data)
    features = _build_section(FEATURE_FIELD_DEFAULTS, features_data)
    derived = _build_section(
        DERIVED_FIELD_DEFAULTS,
        {
            **derived_data,
            "tempo_applicable": _coalesce(
                derived_data.get("tempo_applicable"),
                record.get("tempo_applicable"),
            ),
            "is_loop": _coalesce(
                derived_data.get("is_loop"),
                record.get("is_loop"),
            ),
            "duration_bucket": _coalesce(
                derived_data.get("duration_bucket"),
                record.get("duration_bucket"),
            ),
            "brightness": _coalesce(
                derived_data.get("brightness"),
                record.get("brightness"),
            ),
        },
    )
    retrieval = _build_section(
        RETRIEVAL_FIELD_DEFAULTS,
        {
            **retrieval_data,
            "tags": _coalesce(retrieval_data.get("tags"), record.get("tags"), []),
            "mood": _coalesce(retrieval_data.get("mood"), record.get("mood")),
            "texture": _coalesce(retrieval_data.get("texture"), record.get("texture")),
            "density": _coalesce(retrieval_data.get("density"), record.get("density")),
            "role": _coalesce(retrieval_data.get("role"), record.get("role")),
            "domain": _coalesce(retrieval_data.get("domain"), record.get("domain")),
        },
    )
    review = _sanitize_review_data(raw_review_data)
    _apply_review_overrides(features, derived, review)

    model_outputs = dict(model_outputs_data)
    for key, default_value in MODEL_OUTPUT_FIELD_DEFAULTS.items():
        model_outputs.setdefault(key, default_value)

    source = {
        "path": source_path,
        "file_name": file_name,
        "file_format": file_format,
    }
    record_id = record.get("id") or build_record_id(source_path, file_name, file_format)

    normalized.update(
        {
            "id": record_id,
            "status": status,
            "source": source,
            "technical": technical,
            "features": features,
            "derived": derived,
            "retrieval": retrieval,
            "review": review,
            "model_outputs": model_outputs,
            "segments": segments_data,
            "errors": errors_data,
            "file_name": file_name,
            "source_path": source_path,
            "file_format": file_format,
            "tempo_applicable": derived["tempo_applicable"],
            "is_loop": derived["is_loop"],
            "duration_bucket": derived["duration_bucket"],
            "brightness": derived["brightness"],
            "tags": retrieval["tags"],
            "mood": retrieval["mood"],
            "texture": retrieval["texture"],
            "density": retrieval["density"],
            "role": retrieval["role"],
            "domain": retrieval["domain"],
        }
    )
    return normalized


def build_output_payload(run_summary: Any, file_results: list[Any]) -> dict[str, Any]:
    run_data = to_plain_data(run_summary)
    raw_files = [to_plain_data(file_result) for file_result in file_results]
    return normalize_payload_schema_v1(
        {
            "schema_version": SCHEMA_VERSION,
            "app_version": APP_VERSION,
            "run": run_data,
            "files": raw_files,
        },
        app_version=APP_VERSION,
    )


def _apply_review_overrides(
    features: dict[str, Any],
    derived: dict[str, Any],
    review_data: dict[str, Any],
) -> None:
    overrides = dict(review_data.get("overrides") or {}) if isinstance(review_data.get("overrides"), dict) else {}
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

    if "is_loop" in derived_overrides:
        derived["is_loop"] = derived_overrides["is_loop"]
    if "brightness" in derived_overrides:
        derived["brightness"] = derived_overrides["brightness"]
    if "tempo_applicable" in derived_overrides:
        derived["tempo_applicable"] = derived_overrides["tempo_applicable"]
    if "tempo_bpm" in features_overrides:
        features["tempo_bpm"] = features_overrides["tempo_bpm"]
    if "tempo_quality" in features_overrides:
        features["tempo_quality"] = features_overrides["tempo_quality"]


def _sanitize_review_data(review_data: dict[str, Any]) -> dict[str, Any]:
    sanitized = {
        key: value
        for key, value in review_data.items()
        if key not in {"overrides", "notes"}
    }

    sanitized_overrides: dict[str, Any] = {}
    raw_overrides = dict(review_data.get("overrides") or {}) if isinstance(review_data.get("overrides"), dict) else {}

    raw_derived = dict(raw_overrides.get("derived") or {}) if isinstance(raw_overrides.get("derived"), dict) else {}
    derived_overrides: dict[str, Any] = {}
    if isinstance(raw_derived.get("is_loop"), bool):
        derived_overrides["is_loop"] = raw_derived["is_loop"]
    if isinstance(raw_derived.get("brightness"), str) and raw_derived["brightness"] in BRIGHTNESS_CHOICES:
        derived_overrides["brightness"] = raw_derived["brightness"]
    if isinstance(raw_derived.get("tempo_applicable"), bool):
        derived_overrides["tempo_applicable"] = raw_derived["tempo_applicable"]
    if derived_overrides:
        sanitized_overrides["derived"] = derived_overrides

    raw_features = (
        dict(raw_overrides.get("features") or {})
        if isinstance(raw_overrides.get("features"), dict)
        else {}
    )
    features_overrides: dict[str, Any] = {}
    if "tempo_bpm" in raw_features and _is_valid_tempo_bpm_override(raw_features.get("tempo_bpm")):
        raw_tempo_bpm = raw_features.get("tempo_bpm")
        features_overrides["tempo_bpm"] = None if raw_tempo_bpm is None else float(raw_tempo_bpm)
    if isinstance(raw_features.get("tempo_quality"), str) and raw_features["tempo_quality"] in TEMPO_QUALITY_CHOICES:
        features_overrides["tempo_quality"] = raw_features["tempo_quality"]
    if features_overrides:
        sanitized_overrides["features"] = features_overrides

    if sanitized_overrides:
        sanitized["overrides"] = sanitized_overrides

    raw_notes = review_data.get("notes")
    if isinstance(raw_notes, list):
        notes = [note for note in raw_notes if isinstance(note, str)]
        if notes:
            sanitized["notes"] = notes

    return sanitized


def _build_section(defaults: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    section = dict(values)
    for key, default_value in defaults.items():
        section.setdefault(key, default_value)
    return section


def _coalesce(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _is_valid_tempo_bpm_override(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(float(value))

