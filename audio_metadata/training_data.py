"""Training data export for ML-based subjective classification (v0.1-b6).

This module exports labeled training data from reviewed audio metadata.
It extracts objective features as input features and user-reviewed tags as labels.

Output format: CSV compatible with scikit-learn.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


# Subjective tags to predict (v0.1-b6 target labels)
SUBJECTIVE_LABELS = ["dark", "bright", "energetic", "calm"]

# Objective features to use as input
FEATURE_COLUMNS = [
    # Spectral features
    "spectral_centroid_hz",
    "spectral_bandwidth_hz",
    "spectral_flatness",
    # Energy features
    "loudness_lufs",
    "rms",
    # Tempo features
    "tempo_bpm",
    "tempo_confidence",
    # Duration features
    "duration_sec",
    # v0.1-b5 auto-tags (binary features)
    "is_percussive",
    "is_sustained",
    "wide_spectrum",
    "narrow_spectrum",
    "is_bright",
    "is_dark",
    "is_noise_like",
    "is_tone_like",
    "high_tempo_confidence",
    "low_tempo_confidence",
]


def export_training_data(
    input_json: str | Path,
    output_csv: str | Path,
    *,
    include_unlabeled: bool = False,
) -> dict[str, Any]:
    """Export training data from reviewed metadata JSON.
    
    Args:
        input_json: Path to reviewed metadata JSON file
        output_csv: Path to output CSV file
        include_unlabeled: If True, include records without subjective tags
        
    Returns:
        Dict with export statistics
    """
    input_path = Path(input_json)
    output_path = Path(output_csv)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input JSON not found: {input_path}")
    
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    records = data.get("files", [])
    if not isinstance(records, list):
        raise ValueError("Input JSON must contain a 'files' array")
    
    # Collect labeled samples
    labeled_samples = []
    unlabeled_count = 0
    
    for record in records:
        # Extract features
        features = _extract_features(record)
        
        # Extract labels from review.overrides or retrieval tags
        labels = _extract_labels(record)
        
        if labels:
            labeled_samples.append({**features, **labels})
        elif include_unlabeled:
            unlabeled_sample = {**features, "label": None, "source_path": record.get("source", {}).get("path", "")}
            labeled_samples.append(unlabeled_sample)
            unlabeled_count += 1
    
    # Write CSV
    fieldnames = FEATURE_COLUMNS + ["label", "source_path"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(labeled_samples)
    
    return {
        "total_records": len(records),
        "labeled_samples": len(labeled_samples) - unlabeled_count,
        "unlabeled_samples": unlabeled_count,
        "output_file": str(output_path),
    }


def _extract_features(record: dict[str, Any]) -> dict[str, Any]:
    """Extract objective features from a record."""
    features = {}
    
    # Technical features
    technical = record.get("technical", {})
    features["duration_sec"] = technical.get("duration_sec")
    
    # Audio features
    audio_features = record.get("features", {})
    features["spectral_centroid_hz"] = audio_features.get("spectral_centroid_hz")
    features["spectral_bandwidth_hz"] = audio_features.get("spectral_bandwidth_hz")
    features["spectral_flatness"] = audio_features.get("spectral_flatness")
    features["loudness_lufs"] = audio_features.get("loudness_lufs")
    features["rms"] = audio_features.get("rms")
    features["tempo_bpm"] = audio_features.get("tempo_bpm")
    features["tempo_confidence"] = audio_features.get("tempo_confidence")
    
    # v0.1-b5 auto-tags
    model_outputs = record.get("model_outputs", {})
    auto_tags = model_outputs.get("auto_tags", [])
    auto_tags_set = set(auto_tags) if isinstance(auto_tags, list) else set()
    
    features["is_percussive"] = 1 if "is_percussive" in auto_tags_set else 0
    features["is_sustained"] = 1 if "is_sustained" in auto_tags_set else 0
    features["wide_spectrum"] = 1 if "wide_spectrum" in auto_tags_set else 0
    features["narrow_spectrum"] = 1 if "narrow_spectrum" in auto_tags_set else 0
    features["is_bright"] = 1 if "is_bright" in auto_tags_set else 0
    features["is_dark"] = 1 if "is_dark" in auto_tags_set else 0
    features["is_noise_like"] = 1 if "is_noise_like" in auto_tags_set else 0
    features["is_tone_like"] = 1 if "is_tone_like" in auto_tags_set else 0
    features["high_tempo_confidence"] = 1 if "high_tempo_confidence" in auto_tags_set else 0
    features["low_tempo_confidence"] = 1 if "low_tempo_confidence" in auto_tags_set else 0
    
    # Add source path for reference
    features["source_path"] = record.get("source", {}).get("path", "")
    
    return features


def _extract_labels(record: dict[str, Any]) -> dict[str, Any]:
    """Extract subjective labels from review overrides or retrieval tags.
    
    Priority:
    1. review.overrides with subjective tags
    2. retrieval.tags
    3. derived.brightness (mapped to dark/bright)
    """
    labels = {}
    
    # Check review.overrides for subjective tags
    review = record.get("review", {})
    overrides = review.get("overrides", {})
    
    # Check model_outputs.subjective_tags (v0.1-b6+)
    model_outputs = record.get("model_outputs", {})
    subjective_tags = model_outputs.get("subjective_tags", [])
    if isinstance(subjective_tags, list) and subjective_tags:
        # Use first subjective tag as primary label
        labels["label"] = subjective_tags[0]
        return labels
    
    # Check retrieval.tags
    retrieval = record.get("retrieval", {})
    tags = retrieval.get("tags", [])
    if isinstance(tags, list):
        matching_tags = [t for t in tags if t in SUBJECTIVE_LABELS]
        if matching_tags:
            labels["label"] = matching_tags[0]
            return labels
    
    # Map derived.brightness to labels
    derived = record.get("derived", {})
    brightness = derived.get("brightness")
    if brightness:
        if brightness in ("dark",):
            labels["label"] = "dark"
            return labels
        elif brightness in ("bright", "very_bright"):
            labels["label"] = "bright"
            return labels
    
    return {}


def generate_training_report(input_json: str | Path) -> dict[str, Any]:
    """Generate a report on available training data.
    
    Args:
        input_json: Path to reviewed metadata JSON file
        
    Returns:
        Dict with label distribution statistics
    """
    input_path = Path(input_json)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input JSON not found: {input_path}")
    
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    records = data.get("files", [])
    label_counts: dict[str, int] = {}
    
    for record in records:
        labels = _extract_labels(record)
        if labels:
            label = labels.get("label", "")
            label_counts[label] = label_counts.get(label, 0) + 1
    
    total_labeled = sum(label_counts.values())
    total_records = len(records)
    
    return {
        "total_records": total_records,
        "total_labeled": total_labeled,
        "label_distribution": label_counts,
        "coverage_percentage": round(total_labeled / total_records * 100, 2) if total_records > 0 else 0,
    }
