#!/usr/bin/env python3
"""Demo script for v0.1-b6 ML classifier training pipeline."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd: str):
    """Run a command and print output."""
    print(f"\n{'='*60}")
    print(f"$ {cmd}")
    print('='*60)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode

def main():
    base_dir = Path(__file__).parent
    venv_python = base_dir / ".venv" / "bin" / "python"
    app_py = base_dir / "app.py"
    
    # Step 1: Check example data
    print("\n### v0.1-b6 ML Classifier Training Demo ###")
    
    # Step 2: Export training data (report mode)
    run_cmd(f"{venv_python} {app_py} export-training --input {base_dir}/examples/search-demo.json --report")
    
    # Step 3: Create synthetic training data for demo
    print("\n### Creating synthetic training data for demo... ###")
    
    import csv
    import audio_metadata.ml_classifier as ml
    
    demo_csv = base_dir / "out" / "demo-training.csv"
    demo_csv.parent.mkdir(exist_ok=True)
    
    with open(demo_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ml.FEATURE_COLUMNS + ["label", "source_path"])
        writer.writeheader()
        
        # Generate synthetic samples
        samples = []
        
        # Dark samples (low spectral centroid)
        for i in range(8):
            samples.append({
                "spectral_centroid_hz": 300.0 + i * 30,
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
        
        # Bright samples (high spectral centroid)
        for i in range(8):
            samples.append({
                "spectral_centroid_hz": 2500.0 + i * 50,
                "spectral_bandwidth_hz": 3500.0,
                "spectral_flatness": -30.0,
                "loudness_lufs": -12.0,
                "rms": 0.12,
                "tempo_bpm": 130.0,
                "tempo_confidence": 0.85,
                "duration_sec": 3.0,
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
        
        writer.writerows(samples)
    
    print(f"Created: {demo_csv} ({len(samples)} samples)")
    
    # Step 4: Train classifier
    model_path = base_dir / "out" / "demo-model.pkl"
    run_cmd(f"{venv_python} {app_py} train-classifier --input {demo_csv} --output {model_path} -v")
    
    # Step 5: Test prediction
    print("\n### Testing prediction with trained model... ###")
    import pickle
    import json
    
    with open(model_path, "rb") as f:
        model_data = pickle.load(f)
    
    clf = model_data["model"]
    scaler = model_data.get("scaler")
    
    # Test sample (bright-like features)
    test_features = {col: 0.5 for col in ml.FEATURE_COLUMNS}
    test_features["spectral_centroid_hz"] = 2800.0
    test_features["is_bright"] = 1
    
    X = [[test_features[col] for col in model_data["feature_columns"]]]
    if scaler:
        X = scaler.transform(X)
    
    pred = clf.predict(X)[0]
    probs = clf.predict_proba(X)[0]
    
    print(f"\nTest prediction:")
    print(f"  Input: high spectral centroid (2800 Hz), is_bright=1")
    print(f"  Predicted: {pred}")
    print(f"  Confidence: {max(probs):.2%}")
    print(f"  All probabilities: {dict(zip(clf.classes_, [f'{p:.2%}' for p in probs]))}")
    
    print("\n### Demo Complete! ###")
    print(f"\nModel saved to: {model_path}")
    print(f"Training data: {demo_csv}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
