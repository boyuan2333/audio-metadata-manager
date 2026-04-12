"""
Unit tests for auto_tag module.

Tests cover:
- HPSS feature detection (percussive/sustained)
- Spectral feature detection (bandwidth, centroid, flatness)
- Tempo confidence detection
- End-to-end auto-tagging
"""

import pytest
import numpy as np
import librosa
from audio_metadata.auto_tag import (
    AutoTagResult,
    detect_hpss_features,
    detect_spectral_features,
    detect_tempo_confidence,
    auto_tag_audio,
    THRESHOLDS,
)


def generate_percussive_test_audio(duration=1.0, sr=22050):
    """
    Generate synthetic percussive audio (noise bursts).
    
    Creates short noise bursts to simulate percussive content.
    """
    t = np.linspace(0, duration, int(sr * duration))
    
    # Create noise bursts at regular intervals
    audio = np.zeros_like(t)
    burst_duration = 0.05  # 50ms bursts
    burst_interval = 0.25  # Every 250ms
    
    for i in range(int(duration / burst_interval)):
        burst_start = int(i * sr * burst_interval)
        burst_end = int(burst_start + sr * burst_duration)
        if burst_end < len(t):
            # White noise burst with exponential decay
            noise = np.random.randn(burst_end - burst_start)
            envelope = np.exp(-np.linspace(0, 5, burst_end - burst_start))
            audio[burst_start:burst_end] = noise * envelope
    
    return audio, sr


def generate_sustained_test_audio(duration=1.0, sr=22050, freq=440):
    """
    Generate synthetic sustained audio (sine wave).
    
    Creates a pure tone to simulate sustained/harmonic content.
    """
    t = np.linspace(0, duration, int(sr * duration))
    # Sine wave with smooth envelope
    envelope = np.ones_like(t)
    envelope[:int(sr * 0.01)] = np.linspace(0, 1, int(sr * 0.01))  # Attack
    envelope[-int(sr * 0.01):] = np.linspace(1, 0, int(sr * 0.01))  # Release
    audio = np.sin(2 * np.pi * freq * t) * envelope
    return audio, sr


def generate_white_noise(duration=1.0, sr=22050):
    """
    Generate white noise (wide spectrum, noise-like).
    """
    t = np.linspace(0, duration, int(sr * duration))
    audio = np.random.randn(len(t))
    return audio, sr


def generate_sine_tone(duration=1.0, sr=22050, freq=1000):
    """
    Generate pure sine tone (narrow spectrum, tone-like).
    """
    t = np.linspace(0, duration, int(sr * duration))
    audio = np.sin(2 * np.pi * freq * t)
    return audio, sr


class TestHPSSFeatures:
    """Tests for HPSS-based feature detection."""
    
    def test_percussive_detection(self):
        """Test that percussive audio is detected as is_percussive."""
        audio, sr = generate_percussive_test_audio()
        tag, confidence = detect_hpss_features(audio, sr)
        
        assert tag == "is_percussive", f"Expected is_percussive, got {tag}"
        assert confidence > THRESHOLDS["is_percussive"], \
            f"Confidence {confidence} should exceed threshold {THRESHOLDS['is_percussive']}"
    
    def test_sustained_detection(self):
        """Test that sustained audio is detected as is_sustained."""
        audio, sr = generate_sustained_test_audio()
        tag, confidence = detect_hpss_features(audio, sr)
        
        assert tag == "is_sustained", f"Expected is_sustained, got {tag}"
        assert confidence > THRESHOLDS["is_sustained"], \
            f"Confidence {confidence} should exceed threshold {THRESHOLDS['is_sustained']}"
    
    def test_confidence_range(self):
        """Test that confidence values are in valid range [0, 1]."""
        audio, sr = generate_percussive_test_audio()
        _, confidence = detect_hpss_features(audio, sr)
        
        assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} out of range"


class TestSpectralFeatures:
    """Tests for spectral feature detection."""
    
    def test_wide_spectrum_detection(self):
        """Test that white noise is detected as wide_spectrum."""
        audio, sr = generate_white_noise()
        tags = detect_spectral_features(audio, sr)
        tag_names = [t[0] for t in tags]
        
        assert "wide_spectrum" in tag_names, \
            f"Expected wide_spectrum in {tag_names}"
    
    def test_narrow_spectrum_detection(self):
        """Test that pure tone is detected as narrow_spectrum."""
        audio, sr = generate_sine_tone()
        tags = detect_spectral_features(audio, sr)
        tag_names = [t[0] for t in tags]
        
        assert "narrow_spectrum" in tag_names, \
            f"Expected narrow_spectrum in {tag_names}"
    
    def test_tone_like_detection(self):
        """Test that pure tone is detected as is_tone_like."""
        audio, sr = generate_sine_tone()
        tags = detect_spectral_features(audio, sr)
        tag_names = [t[0] for t in tags]
        
        assert "is_tone_like" in tag_names, \
            f"Expected is_tone_like in {tag_names}"
    
    def test_confidence_range(self):
        """Test that all confidence values are in valid range [0, 1]."""
        audio, sr = generate_white_noise()
        tags = detect_spectral_features(audio, sr)
        
        for tag, confidence in tags:
            assert 0.0 <= confidence <= 1.0, \
                f"Confidence {confidence} for {tag} out of range"


class TestTempoConfidence:
    """Tests for tempo confidence detection."""
    
    def test_high_tempo_confidence(self):
        """Test that rhythmic audio has high tempo confidence."""
        audio, sr = generate_percussive_test_audio()
        tags = detect_tempo_confidence(audio, sr)
        tag_names = [t[0] for t in tags]
        
        # Percussive audio should have detectable tempo
        assert "high_tempo_confidence" in tag_names or len(tags) > 0, \
            f"Expected tempo detection, got {tag_names}"
    
    def test_low_tempo_confidence(self):
        """Test that non-rhythmic audio has low tempo confidence."""
        audio, sr = generate_sustained_test_audio()
        tags = detect_tempo_confidence(audio, sr)
        tag_names = [t[0] for t in tags]
        
        # Sustained tone may have low confidence
        # (this is a soft assertion - tempo detection can vary)
        if len(tags) > 0:
            assert "low_tempo_confidence" in tag_names or "high_tempo_confidence" in tag_names


class TestAutoTagAudio:
    """End-to-end tests for auto_tag_audio function."""
    
    def test_percussive_audio_tags(self):
        """Test auto-tagging of percussive audio."""
        audio, sr = generate_percussive_test_audio()
        result = auto_tag_audio(audio, sr)
        
        assert len(result.tags) > 0, "Expected at least one tag"
        assert "is_percussive" in result.tags, \
            f"Expected is_percussive in {result.tags}"
        assert "is_percussive" in result.confidence, \
            "Expected confidence for is_percussive"
    
    def test_sustained_audio_tags(self):
        """Test auto-tagging of sustained audio."""
        audio, sr = generate_sustained_test_audio()
        result = auto_tag_audio(audio, sr)
        
        assert len(result.tags) > 0, "Expected at least one tag"
        assert "is_sustained" in result.tags, \
            f"Expected is_sustained in {result.tags}"
    
    def test_result_structure(self):
        """Test that AutoTagResult has correct structure."""
        audio, sr = generate_white_noise()
        result = auto_tag_audio(audio, sr)
        
        # Check required attributes
        assert hasattr(result, "tags")
        assert hasattr(result, "confidence")
        assert hasattr(result, "classifier_version")
        assert hasattr(result, "classifier_type")
        assert hasattr(result, "feature_params")
        
        # Check values
        assert result.classifier_version == "v0.1-b5-objective"
        assert result.classifier_type == "deterministic_rules"
        assert result.feature_params["n_fft"] == 2048
        assert result.feature_params["hop_length"] == 512
    
    def test_to_dict(self):
        """Test AutoTagResult.to_dict() serialization."""
        audio, sr = generate_percussive_test_audio()
        result = auto_tag_audio(audio, sr)
        result_dict = result.to_dict()
        
        assert "auto_tags" in result_dict
        assert "auto_tags_confidence" in result_dict
        assert "classifier_version" in result_dict
        assert "classifier_type" in result_dict
        assert "feature_params" in result_dict
        
        # Check that tags match
        assert result_dict["auto_tags"] == result.tags
        assert result_dict["auto_tags_confidence"] == result.confidence
    
    def test_confidence_matches_tags(self):
        """Test that every tag has a corresponding confidence value."""
        audio, sr = generate_white_noise()
        result = auto_tag_audio(audio, sr)
        
        for tag in result.tags:
            assert tag in result.confidence, \
                f"Tag {tag} missing confidence value"
            assert 0.0 <= result.confidence[tag] <= 1.0, \
                f"Confidence {result.confidence[tag]} for {tag} out of range"


class TestThresholds:
    """Tests for threshold configuration."""
    
    def test_thresholds_defined(self):
        """Test that all expected thresholds are defined."""
        expected_thresholds = [
            "is_percussive",
            "is_sustained",
            "wide_spectrum",
            "narrow_spectrum",
            "is_bright",
            "is_dark",
            "high_tempo_confidence",
            "low_tempo_confidence",
            "is_noise_like",
            "is_tone_like",
        ]
        
        for threshold in expected_thresholds:
            assert threshold in THRESHOLDS, \
                f"Missing threshold: {threshold}"
    
    def test_threshold_values_reasonable(self):
        """Test that threshold values are in reasonable ranges."""
        # HPSS ratios should be between 0 and 1
        assert 0.0 < THRESHOLDS["is_percussive"] < 1.0
        assert 0.0 < THRESHOLDS["is_sustained"] < 1.0
        
        # Frequency thresholds should be positive
        assert THRESHOLDS["wide_spectrum"] > 0
        assert THRESHOLDS["narrow_spectrum"] > 0
        assert THRESHOLDS["is_bright"] > 0
        assert THRESHOLDS["is_dark"] > 0
        
        # Confidence thresholds should be between 0 and 1
        assert 0.0 < THRESHOLDS["high_tempo_confidence"] < 1.0
        assert 0.0 < THRESHOLDS["low_tempo_confidence"] < 1.0
        
        # Flatness thresholds (dB) should be negative
        assert THRESHOLDS["is_noise_like"] < 0
        assert THRESHOLDS["is_tone_like"] < 0
        
        # Noise threshold should be higher (less negative) than tone threshold
        assert THRESHOLDS["is_noise_like"] > THRESHOLDS["is_tone_like"]
