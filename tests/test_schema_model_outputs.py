"""
Unit tests for schema v1 model_outputs field (v0.1-b5 auto-tag interface).

Tests cover:
- model_outputs schema defaults
- auto_tags field integration
- classifier_version tracking
- Future ML interface compatibility
"""

import pytest
from audio_metadata.schema import (
    MODEL_OUTPUT_FIELD_DEFAULTS,
    normalize_record_schema_v1,
    build_output_payload,
)


class TestModelOutputsSchema:
    """Tests for model_outputs field definitions."""
    
    def test_model_outputs_defaults_defined(self):
        """Test that all model_outputs defaults are defined."""
        assert "instrument_family" in MODEL_OUTPUT_FIELD_DEFAULTS
        assert "texture" in MODEL_OUTPUT_FIELD_DEFAULTS
        assert "timbre_type" in MODEL_OUTPUT_FIELD_DEFAULTS
        
        # v0.1-b5 auto-tag fields
        assert "auto_tags" in MODEL_OUTPUT_FIELD_DEFAULTS
        assert "auto_tags_confidence" in MODEL_OUTPUT_FIELD_DEFAULTS
        assert "classifier_version" in MODEL_OUTPUT_FIELD_DEFAULTS
        assert "classifier_type" in MODEL_OUTPUT_FIELD_DEFAULTS
        
        # v0.1-b5 ML interface fields
        assert "subjective_tags" in MODEL_OUTPUT_FIELD_DEFAULTS
        assert "subjective_tags_confidence" in MODEL_OUTPUT_FIELD_DEFAULTS
        assert "ml_model_version" in MODEL_OUTPUT_FIELD_DEFAULTS
    
    def test_auto_tags_default_is_list(self):
        """Test that auto_tags default is an empty list."""
        assert MODEL_OUTPUT_FIELD_DEFAULTS["auto_tags"] == []
        assert isinstance(MODEL_OUTPUT_FIELD_DEFAULTS["auto_tags"], list)
    
    def test_auto_tags_confidence_default_is_dict(self):
        """Test that auto_tags_confidence default is an empty dict."""
        assert MODEL_OUTPUT_FIELD_DEFAULTS["auto_tags_confidence"] == {}
        assert isinstance(MODEL_OUTPUT_FIELD_DEFAULTS["auto_tags_confidence"], dict)
    
    def test_classifier_version_default_is_none(self):
        """Test that classifier_version default is None."""
        assert MODEL_OUTPUT_FIELD_DEFAULTS["classifier_version"] is None
    
    def test_classifier_type_default_is_none(self):
        """Test that classifier_type default is None."""
        assert MODEL_OUTPUT_FIELD_DEFAULTS["classifier_type"] is None
    
    def test_subjective_tags_default_is_list(self):
        """Test that subjective_tags default is an empty list."""
        assert MODEL_OUTPUT_FIELD_DEFAULTS["subjective_tags"] == []
        assert isinstance(MODEL_OUTPUT_FIELD_DEFAULTS["subjective_tags"], list)
    
    def test_ml_model_version_default_is_none(self):
        """Test that ml_model_version default is None."""
        assert MODEL_OUTPUT_FIELD_DEFAULTS["ml_model_version"] is None


class TestModelOutputsNormalization:
    """Tests for model_outputs in record normalization."""
    
    def test_normalize_record_includes_model_outputs(self):
        """Test that normalized records include model_outputs."""
        record = {
            "source": {
                "file_name": "test.wav",
                "path": "/test/test.wav",
                "file_format": "wav",
            },
        }
        
        normalized = normalize_record_schema_v1(record)
        
        assert "model_outputs" in normalized
        model_outputs = normalized["model_outputs"]
        
        # Check auto-tag fields
        assert "auto_tags" in model_outputs
        assert "auto_tags_confidence" in model_outputs
        assert "classifier_version" in model_outputs
        assert "classifier_type" in model_outputs
        
        # Check ML interface fields
        assert "subjective_tags" in model_outputs
        assert "subjective_tags_confidence" in model_outputs
        assert "ml_model_version" in model_outputs
        
        # Check default values
        assert model_outputs["auto_tags"] == []
        assert model_outputs["auto_tags_confidence"] == {}
        assert model_outputs["classifier_version"] is None
    
    def test_normalize_record_preserves_existing_model_outputs(self):
        """Test that existing model_outputs values are preserved."""
        record = {
            "source": {
                "file_name": "test.wav",
                "path": "/test/test.wav",
                "file_format": "wav",
            },
            "model_outputs": {
                "instrument_family": "strings",
                "auto_tags": ["is_percussive"],
                "auto_tags_confidence": {"is_percussive": 0.9},
                "classifier_version": "v0.1-b5-objective",
                "classifier_type": "deterministic_rules",
            },
        }
        
        normalized = normalize_record_schema_v1(record)
        model_outputs = normalized["model_outputs"]
        
        assert model_outputs["instrument_family"] == "strings"
        assert model_outputs["auto_tags"] == ["is_percussive"]
        assert model_outputs["auto_tags_confidence"]["is_percussive"] == 0.9
        assert model_outputs["classifier_version"] == "v0.1-b5-objective"
        assert model_outputs["classifier_type"] == "deterministic_rules"
    
    def test_normalize_record_merges_partial_model_outputs(self):
        """Test that partial model_outputs are merged with defaults."""
        record = {
            "source": {
                "file_name": "test.wav",
                "path": "/test/test.wav",
                "file_format": "wav",
            },
            "model_outputs": {
                "auto_tags": ["wide_spectrum"],
            },
        }
        
        normalized = normalize_record_schema_v1(record)
        model_outputs = normalized["model_outputs"]
        
        # Provided value
        assert model_outputs["auto_tags"] == ["wide_spectrum"]
        
        # Default values should be filled in
        assert model_outputs["auto_tags_confidence"] == {}
        assert model_outputs["classifier_version"] is None
        assert model_outputs["instrument_family"] is None


class TestAutoTagIntegration:
    """Tests for auto-tag result integration with schema."""
    
    def test_auto_tag_result_to_schema(self):
        """Test converting AutoTagResult to schema format."""
        from audio_metadata.auto_tag import AutoTagResult
        
        result = AutoTagResult(
            tags=["is_percussive", "wide_spectrum"],
            confidence={
                "is_percussive": 0.89,
                "wide_spectrum": 0.72,
            },
            classifier_version="v0.1-b5-objective",
            classifier_type="deterministic_rules",
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["auto_tags"] == ["is_percussive", "wide_spectrum"]
        assert result_dict["auto_tags_confidence"]["is_percussive"] == 0.89
        assert result_dict["auto_tags_confidence"]["wide_spectrum"] == 0.72
        assert result_dict["classifier_version"] == "v0.1-b5-objective"
        assert result_dict["classifier_type"] == "deterministic_rules"
    
    def test_build_output_payload_with_auto_tags(self):
        """Test building output payload with auto-tag results."""
        from audio_metadata.auto_tag import AutoTagResult
        
        # Simulate auto-tag result
        auto_tag_result = AutoTagResult(
            tags=["is_percussive"],
            confidence={"is_percussive": 0.9},
            classifier_version="v0.1-b5-objective",
            classifier_type="deterministic_rules",
        )
        
        file_result = {
            "source": {
                "file_name": "kick.wav",
                "path": "/samples/kick.wav",
                "file_format": "wav",
            },
            "model_outputs": auto_tag_result.to_dict(),
        }
        
        payload = build_output_payload(
            run_summary={"total_files": 1, "successful": 1},
            file_results=[file_result],
        )
        
        assert "files" in payload
        assert len(payload["files"]) == 1
        
        model_outputs = payload["files"][0]["model_outputs"]
        assert model_outputs["auto_tags"] == ["is_percussive"]
        assert model_outputs["auto_tags_confidence"]["is_percussive"] == 0.9
        assert model_outputs["classifier_version"] == "v0.1-b5-objective"


class TestMLInterfaceCompatibility:
    """Tests for future ML interface compatibility."""
    
    def test_subjective_tags_field_exists(self):
        """Test that subjective_tags field exists for future ML."""
        record = {
            "source": {
                "file_name": "test.wav",
                "path": "/test/test.wav",
                "file_format": "wav",
            },
        }
        
        normalized = normalize_record_schema_v1(record)
        model_outputs = normalized["model_outputs"]
        
        assert "subjective_tags" in model_outputs
        assert model_outputs["subjective_tags"] == []
    
    def test_ml_model_version_field_exists(self):
        """Test that ml_model_version field exists for future ML."""
        record = {
            "source": {
                "file_name": "test.wav",
                "path": "/test/test.wav",
                "file_format": "wav",
            },
        }
        
        normalized = normalize_record_schema_v1(record)
        model_outputs = normalized["model_outputs"]
        
        assert "ml_model_version" in model_outputs
        assert model_outputs["ml_model_version"] is None
    
    def test_future_ml_result_compatibility(self):
        """Test that schema can accommodate future ML results."""
        # Simulate future ML-based tagging (v0.1-b6+)
        ml_result = {
            "auto_tags": ["is_percussive"],  # Objective (v0.1-b5)
            "auto_tags_confidence": {"is_percussive": 0.89},
            "classifier_version": "v0.1-b5-objective",
            "classifier_type": "deterministic_rules",
            "subjective_tags": ["dark"],  # Subjective (v0.1-b6+)
            "subjective_tags_confidence": {"dark": 0.75},
            "ml_model_version": "v0.1-b6-ml",
        }
        
        record = {
            "source": {
                "file_name": "test.wav",
                "path": "/test/test.wav",
                "file_format": "wav",
            },
            "model_outputs": ml_result,
        }
        
        normalized = normalize_record_schema_v1(record)
        model_outputs = normalized["model_outputs"]
        
        # Both objective and subjective tags preserved
        assert model_outputs["auto_tags"] == ["is_percussive"]
        assert model_outputs["subjective_tags"] == ["dark"]
        assert model_outputs["classifier_version"] == "v0.1-b5-objective"
        assert model_outputs["ml_model_version"] == "v0.1-b6-ml"
    
    def test_separation_of_concerns(self):
        """Test that objective and subjective tags are clearly separated."""
        # v0.1-b5 should only populate auto_tags
        v01b5_result = {
            "auto_tags": ["is_percussive", "wide_spectrum"],
            "auto_tags_confidence": {
                "is_percussive": 0.89,
                "wide_spectrum": 0.72,
            },
            "classifier_version": "v0.1-b5-objective",
            "classifier_type": "deterministic_rules",
            # Subjective tags should remain empty
            "subjective_tags": [],
            "subjective_tags_confidence": {},
            "ml_model_version": None,
        }
        
        record = {
            "source": {
                "file_name": "test.wav",
                "path": "/test/test.wav",
                "file_format": "wav",
            },
            "model_outputs": v01b5_result,
        }
        
        normalized = normalize_record_schema_v1(record)
        model_outputs = normalized["model_outputs"]
        
        # Objective tags populated
        assert len(model_outputs["auto_tags"]) > 0
        assert len(model_outputs["auto_tags_confidence"]) > 0
        
        # Subjective tags empty (v0.1-b5 doesn't use them)
        assert model_outputs["subjective_tags"] == []
        assert model_outputs["subjective_tags_confidence"] == {}
        assert model_outputs["ml_model_version"] is None
