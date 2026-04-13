"""Tests for ML classifier training (v0.1-b6)."""

import csv
import json
import pickle
import tempfile
from pathlib import Path

import pytest

import audio_metadata.ml_classifier as ml_classifier


@pytest.fixture
def sample_training_data():
    """Create sample training data CSV."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        fieldnames = ml_classifier.FEATURE_COLUMNS + ["label", "source_path"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # Create samples for 3 classes (4 samples each = 12 total, enough for train/test split)
        samples = []
        
        # Dark samples (low spectral centroid, low energy)
        for i in range(4):
            samples.append({
                "spectral_centroid_hz": 300.0 + i * 20,
                "spectral_bandwidth_hz": 500.0,
                "spectral_flatness": -50.0,
                "loudness_lufs": -20.0,
                "rms": 0.05,
                "tempo_bpm": 80.0,
                "tempo_confidence": 0.6,
                "duration_sec": 5.0,
                "is_percussive": 0,
                "is_sustained": 1,
                "wide_spectrum": 0,
                "narrow_spectrum": 1,
                "is_bright": 0,
                "is_dark": 1,
                "is_noise_like": 0,
                "is_tone_like": 1,
                "high_tempo_confidence": 0,
                "low_tempo_confidence": 1,
                "label": "dark",
                "source_path": f"/audio/dark{i+1}.wav",
            })
        
        # Bright samples (high spectral centroid, high energy)
        for i in range(4):
            samples.append({
                "spectral_centroid_hz": 2800.0 + i * 50,
                "spectral_bandwidth_hz": 3800.0,
                "spectral_flatness": -25.0,
                "loudness_lufs": -12.0,
                "rms": 0.14,
                "tempo_bpm": 135.0,
                "tempo_confidence": 0.85,
                "duration_sec": 2.5,
                "is_percussive": 1,
                "is_sustained": 0,
                "wide_spectrum": 1,
                "narrow_spectrum": 0,
                "is_bright": 1,
                "is_dark": 0,
                "is_noise_like": 0,
                "is_tone_like": 0,
                "high_tempo_confidence": 1,
                "low_tempo_confidence": 0,
                "label": "bright",
                "source_path": f"/audio/bright{i+1}.wav",
            })
        
        # Energetic samples (high tempo, high energy)
        for i in range(4):
            samples.append({
                "spectral_centroid_hz": 1800.0 + i * 50,
                "spectral_bandwidth_hz": 3200.0,
                "spectral_flatness": -35.0,
                "loudness_lufs": -9.0,
                "rms": 0.18,
                "tempo_bpm": 155.0 + i * 5,
                "tempo_confidence": 0.9,
                "duration_sec": 3.5,
                "is_percussive": 1,
                "is_sustained": 0,
                "wide_spectrum": 1,
                "narrow_spectrum": 0,
                "is_bright": 1,
                "is_dark": 0,
                "is_noise_like": 0,
                "is_tone_like": 0,
                "high_tempo_confidence": 1,
                "low_tempo_confidence": 0,
                "label": "energetic",
                "source_path": f"/audio/energetic{i+1}.wav",
            })
        
        writer.writerows(samples)
        temp_path = Path(f.name)
    
    yield temp_path
    temp_path.unlink()


@pytest.fixture
def sample_model_output(tmp_path):
    """Create a trained model file."""
    # First create training data
    csv_path = tmp_path / "train.csv"
    with open(csv_path, "w", newline="") as f:
        fieldnames = ml_classifier.FEATURE_COLUMNS + ["label", "source_path"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # Minimal samples for quick training (12 samples: 6 per class)
        for i in range(12):
            row = {col: 0.5 + (i * 0.01) for col in ml_classifier.FEATURE_COLUMNS}
            row["label"] = "dark" if i < 6 else "bright"
            row["source_path"] = f"/audio/sample{i}.wav"
            writer.writerow(row)
    
    # Train and save model
    model_path = tmp_path / "model.pkl"
    ml_classifier.train_classifier(
        csv_path,
        model_path,
        classifier_type="random_forest",
        test_size=0.33,
        cv_folds=2,
        verbose=False,
    )
    
    return model_path


class TestTrainClassifier:
    """Tests for train_classifier function."""
    
    def test_train_random_forest(self, sample_training_data):
        """Test Random Forest classifier training."""
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            model_path = Path(f.name)
        
        try:
            metrics = ml_classifier.train_classifier(
                sample_training_data,
                model_path,
                classifier_type="random_forest",
                test_size=0.33,
                cv_folds=2,
                verbose=False,
            )
            
            assert metrics["classifier_type"] == "random_forest"
            assert metrics["total_labeled_samples"] == 12
            assert metrics["training_samples"] > 0
            assert metrics["test_samples"] > 0
            assert "accuracy" in metrics["test_metrics"]
            assert "cross_validation" in metrics
            assert metrics["feature_importance"] is not None
            assert model_path.exists()
        finally:
            model_path.unlink()
    
    def test_train_logistic_regression(self, sample_training_data):
        """Test Logistic Regression classifier training."""
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            model_path = Path(f.name)
        
        try:
            metrics = ml_classifier.train_classifier(
                sample_training_data,
                model_path,
                classifier_type="logistic_regression",
                test_size=0.33,
                cv_folds=2,
                verbose=False,
            )
            
            assert metrics["classifier_type"] == "logistic_regression"
            assert metrics["feature_importance"] is None  # LR doesn't have feature_importances_
            assert model_path.exists()
        finally:
            model_path.unlink()
    
    def test_no_scaling(self, sample_training_data):
        """Test training without feature scaling."""
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            model_path = Path(f.name)
        
        try:
            metrics = ml_classifier.train_classifier(
                sample_training_data,
                model_path,
                scale_features=False,
                verbose=False,
            )
            
            assert metrics["scaler"] is None
        finally:
            model_path.unlink()
    
    def test_file_not_found(self):
        """Test error when input file not found."""
        with pytest.raises(FileNotFoundError):
            ml_classifier.train_classifier("/nonexistent/path.csv", "model.pkl")
    
    def test_no_labeled_samples(self, tmp_path):
        """Test error when no labeled samples available."""
        csv_path = tmp_path / "unlabeled.csv"
        with open(csv_path, "w", newline="") as f:
            fieldnames = ml_classifier.FEATURE_COLUMNS + ["label", "source_path"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({col: 0.5 for col in ml_classifier.FEATURE_COLUMNS} | {"label": None, "source_path": "/audio/test.wav"})
        
        with pytest.raises(ValueError, match="No labeled samples"):
            ml_classifier.train_classifier(csv_path, "model.pkl")
    
    def test_insufficient_samples(self, tmp_path):
        """Test error when too few samples."""
        csv_path = tmp_path / "few.csv"
        with open(csv_path, "w", newline="") as f:
            fieldnames = ml_classifier.FEATURE_COLUMNS + ["label", "source_path"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            # Only 9 samples (need at least 10)
            for i in range(9):
                row = {col: 0.5 for col in ml_classifier.FEATURE_COLUMNS}
                row["label"] = "dark" if i < 5 else "bright"
                row["source_path"] = f"/audio/sample{i}.wav"
                writer.writerow(row)
        
        with pytest.raises(ValueError, match="Insufficient labeled samples"):
            ml_classifier.train_classifier(csv_path, "model.pkl")
    
    def test_single_class(self, tmp_path):
        """Test error when only one class present."""
        csv_path = tmp_path / "single_class.csv"
        with open(csv_path, "w", newline="") as f:
            fieldnames = ml_classifier.FEATURE_COLUMNS + ["label", "source_path"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            # All samples are "dark"
            for i in range(10):
                row = {col: 0.5 for col in ml_classifier.FEATURE_COLUMNS}
                row["label"] = "dark"
                row["source_path"] = f"/audio/sample{i}.wav"
                writer.writerow(row)
        
        with pytest.raises(ValueError, match="Only one class found"):
            ml_classifier.train_classifier(csv_path, "model.pkl")
    
    def test_invalid_classifier_type(self, sample_training_data):
        """Test error for invalid classifier type."""
        with pytest.raises(ValueError, match="Unknown classifier type"):
            ml_classifier.train_classifier(
                sample_training_data,
                "model.pkl",
                classifier_type="invalid_classifier",  # type: ignore
            )


class TestLoadModel:
    """Tests for load_model function."""
    
    def test_load_model(self, sample_model_output):
        """Test loading a trained model."""
        model_data = ml_classifier.load_model(sample_model_output)
        
        assert "classifier_type" in model_data
        assert "feature_columns" in model_data
        assert "classes" in model_data
        assert "scaler" in model_data
        assert "model" in model_data
        assert "version" in model_data
        assert model_data["version"] == "v0.1-b6"
    
    def test_load_model_not_found(self):
        """Test error when model file not found."""
        with pytest.raises(FileNotFoundError):
            ml_classifier.load_model("/nonexistent/model.pkl")


class TestPredictTags:
    """Tests for predict_tags function."""
    
    def test_predict_single(self, sample_model_output):
        """Test single prediction."""
        features = {col: 0.5 for col in ml_classifier.FEATURE_COLUMNS}
        result = ml_classifier.predict_tags(
            sample_model_output,
            input_features=features,
        )
        
        assert result["mode"] == "single"
        assert "predicted_label" in result
        assert "confidence" in result
        assert "all_confidences" in result
        assert isinstance(result["confidence"], float)
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_predict_with_threshold(self, sample_model_output):
        """Test prediction with confidence threshold."""
        features = {col: 0.5 for col in ml_classifier.FEATURE_COLUMNS}
        result = ml_classifier.predict_tags(
            sample_model_output,
            input_features=features,
            confidence_threshold=0.9,
        )
        
        # With high threshold, may not apply any tags
        assert "applies" in result
        assert isinstance(result["applies"], dict)
    
    def test_predict_batch(self, sample_model_output, tmp_path):
        """Test batch prediction."""
        csv_path = tmp_path / "predict.csv"
        with open(csv_path, "w", newline="") as f:
            fieldnames = ml_classifier.FEATURE_COLUMNS + ["label", "source_path"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for i in range(3):
                row = {col: 0.5 for col in ml_classifier.FEATURE_COLUMNS}
                row["label"] = None
                row["source_path"] = f"/audio/test{i}.wav"
                writer.writerow(row)
        
        result = ml_classifier.predict_tags(
            sample_model_output,
            input_csv=csv_path,
        )
        
        assert result["mode"] == "batch"
        assert result["total_predictions"] == 3
        assert len(result["predictions"]) == 3
    
    def test_predict_no_input(self, sample_model_output):
        """Test error when no input provided."""
        with pytest.raises(ValueError, match="Either input_csv or input_features"):
            ml_classifier.predict_tags(sample_model_output)


class TestGenerateTrainingReport:
    """Tests for generate_training_report function."""
    
    def test_generate_report(self, sample_training_data):
        """Test report generation."""
        metrics = ml_classifier.train_classifier(
            sample_training_data,
            None,  # Don't save model
            verbose=False,
        )
        
        report = ml_classifier.generate_training_report(metrics)
        
        assert isinstance(report, str)
        assert "ML Classifier Training Report" in report
        assert "Classifier:" in report
        assert "Total labeled samples:" in report
        assert "Test Set Metrics:" in report
        assert "Accuracy:" in report
        assert "Cross-Validation" in report
    
    def test_report_with_feature_importance(self, sample_training_data):
        """Test report includes feature importances for Random Forest."""
        metrics = ml_classifier.train_classifier(
            sample_training_data,
            None,
            classifier_type="random_forest",
            verbose=False,
        )
        
        report = ml_classifier.generate_training_report(metrics)
        
        assert "Feature Importances" in report
        assert "spectral_centroid_hz" in report or "Top Feature" in report
