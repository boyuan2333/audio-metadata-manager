"""Tests for training data export (v0.1-b6)."""

import json
import tempfile
from pathlib import Path

import pytest

import audio_metadata.training_data as training_data


@pytest.fixture
def sample_reviewed_json():
    """Create a sample reviewed JSON file with mixed labeled/unlabeled data."""
    data = {
        "schema_version": "v1",
        "app_version": "v0.1-b6",
        "run": {},
        "files": [
            # Labeled via subjective_tags
            {
                "id": "sample1",
                "source": {"path": "/audio/dark_pad.wav", "file_name": "dark_pad.wav", "file_format": "wav"},
                "technical": {"duration_sec": 10.5},
                "features": {
                    "spectral_centroid_hz": 800.0,
                    "spectral_bandwidth_hz": 1200.0,
                    "spectral_flatness": -45.0,
                    "loudness_lufs": -18.0,
                    "rms": 0.05,
                    "tempo_bpm": None,
                    "tempo_confidence": None,
                },
                "derived": {"brightness": "dark", "is_loop": True},
                "retrieval": {"tags": []},
                "model_outputs": {
                    "auto_tags": ["is_dark", "narrow_spectrum", "is_tone_like"],
                    "auto_tags_confidence": {"is_dark": 0.85},
                    "subjective_tags": ["dark", "calm"],
                },
                "review": {"overrides": {}, "notes": []},
            },
            # Labeled via retrieval.tags
            {
                "id": "sample2",
                "source": {"path": "/audio/bright_arp.wav", "file_name": "bright_arp.wav", "file_format": "wav"},
                "technical": {"duration_sec": 5.2},
                "features": {
                    "spectral_centroid_hz": 3500.0,
                    "spectral_bandwidth_hz": 4000.0,
                    "spectral_flatness": -25.0,
                    "loudness_lufs": -12.0,
                    "rms": 0.12,
                    "tempo_bpm": 128.0,
                    "tempo_confidence": 0.9,
                },
                "derived": {"brightness": "bright", "is_loop": True},
                "retrieval": {"tags": ["bright", "energetic"]},
                "model_outputs": {
                    "auto_tags": ["is_bright", "wide_spectrum", "is_percussive"],
                    "subjective_tags": [],
                },
                "review": {"overrides": {}, "notes": []},
            },
            # Labeled via derived.brightness mapping
            {
                "id": "sample3",
                "source": {"path": "/audio/very_bright_lead.wav", "file_name": "very_bright_lead.wav", "file_format": "wav"},
                "technical": {"duration_sec": 8.0},
                "features": {
                    "spectral_centroid_hz": 4200.0,
                    "spectral_bandwidth_hz": 5000.0,
                    "spectral_flatness": -20.0,
                    "loudness_lufs": -10.0,
                    "rms": 0.15,
                    "tempo_bpm": 140.0,
                    "tempo_confidence": 0.85,
                },
                "derived": {"brightness": "very_bright", "is_loop": False},
                "retrieval": {"tags": []},
                "model_outputs": {
                    "auto_tags": ["is_bright", "wide_spectrum"],
                    "subjective_tags": [],
                },
                "review": {"overrides": {}, "notes": []},
            },
            # Unlabeled
            {
                "id": "sample4",
                "source": {"path": "/audio/unknown.wav", "file_name": "unknown.wav", "file_format": "wav"},
                "technical": {"duration_sec": 6.0},
                "features": {
                    "spectral_centroid_hz": 2000.0,
                    "spectral_bandwidth_hz": 2500.0,
                    "spectral_flatness": -35.0,
                    "loudness_lufs": -15.0,
                    "rms": 0.08,
                    "tempo_bpm": 100.0,
                    "tempo_confidence": 0.7,
                },
                "derived": {"brightness": "balanced", "is_loop": True},
                "retrieval": {"tags": []},
                "model_outputs": {
                    "auto_tags": [],
                    "subjective_tags": [],
                },
                "review": {"overrides": {}, "notes": []},
            },
        ],
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        return Path(f.name)


def test_export_training_data_basic(sample_reviewed_json):
    """Test basic training data export."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        output_path = Path(f.name)
    
    try:
        result = training_data.export_training_data(sample_reviewed_json, output_path)
        
        assert result["total_records"] == 4
        assert result["labeled_samples"] == 3
        assert result["unlabeled_samples"] == 0
        assert output_path.exists()
        
        # Verify CSV content
        with open(output_path, "r") as f:
            lines = f.readlines()
            assert len(lines) == 4  # Header + 3 labeled samples
            assert "spectral_centroid_hz" in lines[0]
            assert "label" in lines[0]
    finally:
        output_path.unlink()


def test_export_with_unlabeled(sample_reviewed_json):
    """Test export including unlabeled samples."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        output_path = Path(f.name)
    
    try:
        result = training_data.export_training_data(
            sample_reviewed_json,
            output_path,
            include_unlabeled=True,
        )
        
        assert result["labeled_samples"] == 3
        assert result["unlabeled_samples"] == 1
        
        with open(output_path, "r") as f:
            lines = f.readlines()
            assert len(lines) == 5  # Header + 3 labeled + 1 unlabeled
    finally:
        output_path.unlink()


def test_generate_training_report(sample_reviewed_json):
    """Test training data report generation."""
    report = training_data.generate_training_report(sample_reviewed_json)
    
    assert report["total_records"] == 4
    assert report["total_labeled"] == 3
    assert report["coverage_percentage"] == 75.0
    assert "dark" in report["label_distribution"]
    assert "bright" in report["label_distribution"]


def test_label_extraction_priority(sample_reviewed_json):
    """Test that label extraction follows correct priority."""
    with open(sample_reviewed_json, "r") as f:
        data = json.load(f)
    
    # Sample 1: subjective_tags should take priority
    labels1 = training_data._extract_labels(data["files"][0])
    assert labels1.get("label") == "dark"
    
    # Sample 2: retrieval.tags used when no subjective_tags
    labels2 = training_data._extract_labels(data["files"][1])
    assert labels2.get("label") == "bright"
    
    # Sample 3: derived.brightness mapping
    labels3 = training_data._extract_labels(data["files"][2])
    assert labels3.get("label") == "bright"
    
    # Sample 4: no labels
    labels4 = training_data._extract_labels(data["files"][3])
    assert labels4 == {}


def test_feature_extraction(sample_reviewed_json):
    """Test feature extraction from records."""
    with open(sample_reviewed_json, "r") as f:
        data = json.load(f)
    
    features = training_data._extract_labels(data["files"][0])
    assert "label" in features
    
    # Verify auto-tags are converted to binary features
    record = data["files"][0]
    auto_tags = set(record["model_outputs"]["auto_tags"])
    assert "is_dark" in auto_tags


def test_empty_json():
    """Test handling of empty JSON."""
    data = {"schema_version": "v1", "app_version": "v0.1-b6", "run": {}, "files": []}
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        input_path = Path(f.name)
    
    try:
        report = training_data.generate_training_report(input_path)
        assert report["total_records"] == 0
        assert report["total_labeled"] == 0
        assert report["coverage_percentage"] == 0
    finally:
        input_path.unlink()


def test_file_not_found():
    """Test error handling for missing files."""
    with pytest.raises(FileNotFoundError):
        training_data.export_training_data("/nonexistent.json", "/tmp/out.csv")
    
    with pytest.raises(FileNotFoundError):
        training_data.generate_training_report("/nonexistent.json")
