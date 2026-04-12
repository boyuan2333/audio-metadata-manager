"""
Auto-tagging module for objective audio feature detection.

This module implements deterministic feature-based tagging for audio files.
All tags are based on physically measurable audio characteristics.

v0.1-b5: Objective feature tags only (no ML-based subjective tags).

References:
- FitzGerald, D. (2010). Harmonic/Percussive Separation using Median Filtering
- Font, F. & Serra, J. (2016). Tempo Estimation with Confidence Measure. ISMIR
- Essentia Audio Analysis Library (Bogdanov et al., ISMIR 2013)
"""

from __future__ import annotations

import numpy as np
import librosa
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class AutoTagResult:
    """Result of auto-tagging an audio file."""
    
    tags: List[str] = field(default_factory=list)
    confidence: Dict[str, float] = field(default_factory=dict)
    classifier_version: str = "v0.1-b5-objective"
    classifier_type: str = "deterministic_rules"
    feature_params: Dict = field(default_factory=lambda: {
        "n_fft": 2048,
        "hop_length": 512,
        "sr": 22050,
    })
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "auto_tags": self.tags,
            "auto_tags_confidence": self.confidence,
            "classifier_version": self.classifier_version,
            "classifier_type": self.classifier_type,
            "feature_params": self.feature_params,
        }


# Feature detection thresholds (based on literature review)
# See: v0.1-b5 文献调研报告 (Feishu doc)
THRESHOLDS = {
    # HPSS separation (FitzGerald 2010)
    "is_percussive": 0.6,      # P/H ratio > 1.5 ≈ percussive/total > 0.6
    "is_sustained": 0.6,       # H/P ratio > 1.5 ≈ harmonic/total > 0.6
    
    # Spectral bandwidth (Essentia/AcousticBrainz standard)
    "wide_spectrum": 3000,     # Hz
    "narrow_spectrum": 1000,   # Hz
    
    # Spectral centroid (ISMIR standard for brightness)
    "is_bright": 2000,         # Hz
    "is_dark": 500,            # Hz
    
    # Tempo confidence (Font & Serra 2016)
    "high_tempo_confidence": 0.8,
    "low_tempo_confidence": 0.5,
    
    # Spectral flatness (Essentia standard)
    "is_noise_like": -30,      # dB
    "is_tone_like": -60,       # dB
}


def load_audio(file_path: str, sr: int = 22050) -> Tuple[np.ndarray, int]:
    """
    Load audio file and resample to target sample rate.
    
    Args:
        file_path: Path to audio file
        sr: Target sample rate (default: 22050 Hz)
    
    Returns:
        Tuple of (audio_samples, sample_rate)
    """
    y, sr = librosa.load(file_path, sr=sr, mono=True)
    return y, sr


def detect_hpss_features(y: np.ndarray, sr: int) -> Tuple[Optional[str], float]:
    """
    Detect percussive vs sustained content using HPSS separation.
    
    Based on: FitzGerald, D. (2010). Harmonic/Percussive Separation using Median Filtering
    
    Args:
        y: Audio samples
        sr: Sample rate
    
    Returns:
        Tuple of (tag or None, confidence)
    """
    # STFT
    D = librosa.stft(y, n_fft=2048, hop_length=512)
    
    # HPSS separation
    D_harmonic, D_percussive = librosa.decompose.hpss(D, kernel_size=31)
    
    # Calculate energy ratios
    percussive_energy = np.mean(np.abs(D_percussive))
    harmonic_energy = np.mean(np.abs(D_harmonic))
    total_energy = percussive_energy + harmonic_energy
    
    if total_energy == 0:
        return None, 0.0
    
    percussive_ratio = percussive_energy / total_energy
    harmonic_ratio = harmonic_energy / total_energy
    
    # Apply thresholds
    if percussive_ratio > THRESHOLDS["is_percussive"]:
        return "is_percussive", percussive_ratio
    elif harmonic_ratio > THRESHOLDS["is_sustained"]:
        return "is_sustained", harmonic_ratio
    
    return None, max(percussive_ratio, harmonic_ratio)


def detect_spectral_features(y: np.ndarray, sr: int) -> List[Tuple[str, float]]:
    """
    Detect spectral features (bandwidth, centroid, flatness).
    
    Based on: Essentia Audio Analysis Library (ISMIR 2013)
    
    Args:
        y: Audio samples
        sr: Sample rate
    
    Returns:
        List of (tag, confidence) tuples
    """
    tags = []
    
    # Spectral bandwidth
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    bandwidth_hz = spectral_bandwidth.mean()
    
    if bandwidth_hz > THRESHOLDS["wide_spectrum"]:
        confidence = min(1.0, (bandwidth_hz - THRESHOLDS["wide_spectrum"]) / 2000)
        tags.append(("wide_spectrum", confidence))
    elif bandwidth_hz < THRESHOLDS["narrow_spectrum"]:
        confidence = min(1.0, (THRESHOLDS["narrow_spectrum"] - bandwidth_hz) / 500)
        tags.append(("narrow_spectrum", confidence))
    
    # Spectral centroid (brightness)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    centroid_hz = spectral_centroid.mean()
    
    if centroid_hz > THRESHOLDS["is_bright"]:
        confidence = min(1.0, (centroid_hz - THRESHOLDS["is_bright"]) / 1000)
        tags.append(("is_bright", confidence))
    elif centroid_hz < THRESHOLDS["is_dark"]:
        confidence = min(1.0, (THRESHOLDS["is_dark"] - centroid_hz) / 250)
        tags.append(("is_dark", confidence))
    
    # Spectral flatness (noise-like vs tone-like)
    spectral_flatness = librosa.feature.spectral_flatness(y=y)
    flatness_db = librosa.power_to_db(spectral_flatness).mean()
    
    if flatness_db > THRESHOLDS["is_noise_like"]:
        confidence = min(1.0, (flatness_db - THRESHOLDS["is_noise_like"]) / 20)
        tags.append(("is_noise_like", confidence))
    elif flatness_db < THRESHOLDS["is_tone_like"]:
        confidence = min(1.0, (THRESHOLDS["is_tone_like"] - flatness_db) / 30)
        tags.append(("is_tone_like", confidence))
    
    return tags


def detect_tempo_confidence(y: np.ndarray, sr: int) -> List[Tuple[str, float]]:
    """
    Detect tempo confidence level.
    
    Based on: Font, F. & Serra, J. (2016). Tempo Estimation with Confidence Measure. ISMIR
    
    Args:
        y: Audio samples
        sr: Sample rate
    
    Returns:
        List of (tag, confidence) tuples
    """
    tempo, confidence = librosa.beat.beat_track(y=y, sr=sr)
    
    # Ensure confidence is a scalar (librosa 0.11+ returns array)
    try:
        if hasattr(confidence, '__len__') and len(confidence) > 0:
            confidence = float(confidence[0])
        elif hasattr(confidence, 'item'):
            confidence = float(confidence.item())
        else:
            confidence = float(confidence)
    except (ValueError, IndexError):
        # Fallback: if conversion fails, use 0.0 as default
        confidence = 0.0
    
    # Clamp confidence to [0, 1] range
    confidence = max(0.0, min(1.0, confidence))
    
    tags = []
    
    if confidence > THRESHOLDS["high_tempo_confidence"]:
        tags.append(("high_tempo_confidence", confidence))
    elif confidence < THRESHOLDS["low_tempo_confidence"]:
        tags.append(("low_tempo_confidence", 1.0 - confidence))
    
    return tags


def auto_tag_audio(y: np.ndarray, sr: int) -> AutoTagResult:
    """
    Run all feature detectors and generate auto-tags.
    
    Args:
        y: Audio samples
        sr: Sample rate
    
    Returns:
        AutoTagResult with all detected tags and confidences
    """
    result = AutoTagResult()
    
    # HPSS features
    hpss_tag, hpss_conf = detect_hpss_features(y, sr)
    if hpss_tag:
        result.tags.append(hpss_tag)
        result.confidence[hpss_tag] = round(hpss_conf, 3)
    
    # Spectral features
    spectral_tags = detect_spectral_features(y, sr)
    for tag, conf in spectral_tags:
        result.tags.append(tag)
        result.confidence[tag] = round(conf, 3)
    
    # Tempo confidence
    tempo_tags = detect_tempo_confidence(y, sr)
    for tag, conf in tempo_tags:
        result.tags.append(tag)
        result.confidence[tag] = round(conf, 3)
    
    return result


def auto_tag_file(file_path: str, sr: int = 22050) -> AutoTagResult:
    """
    Load audio file and generate auto-tags.
    
    Args:
        file_path: Path to audio file
        sr: Target sample rate
    
    Returns:
        AutoTagResult with all detected tags and confidences
    """
    y, sr = load_audio(file_path, sr=sr)
    return auto_tag_audio(y, sr)


if __name__ == "__main__":
    # Quick test
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        result = auto_tag_file(file_path)
        print(f"File: {file_path}")
        print(f"Tags: {result.tags}")
        print(f"Confidence: {result.confidence}")
    else:
        print("Usage: python -m audio_metadata.auto_tag <audio_file>")
