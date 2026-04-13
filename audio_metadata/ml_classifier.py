"""ML classifier training for subjective tag prediction (v0.1-b6).

This module trains classifiers to predict subjective tags (dark, bright, energetic, calm)
from objective audio features.

Supports:
- Random Forest (default)
- Logistic Regression
- Cross-validation and metrics
- Model persistence (pickle)
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any, Literal

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler


# Supported classifiers
ClassifierType = Literal["random_forest", "logistic_regression"]

# Feature columns (must match training_data.py)
FEATURE_COLUMNS = [
    "spectral_centroid_hz",
    "spectral_bandwidth_hz",
    "spectral_flatness",
    "loudness_lufs",
    "rms",
    "tempo_bpm",
    "tempo_confidence",
    "duration_sec",
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

# Target labels
SUBJECTIVE_LABELS = ["dark", "bright", "energetic", "calm"]


def train_classifier(
    input_csv: str | Path,
    output_model: str | Path | None = None,
    *,
    classifier_type: ClassifierType = "random_forest",
    test_size: float = 0.2,
    cv_folds: int = 5,
    random_state: int = 42,
    scale_features: bool = True,
    verbose: bool = True,
) -> dict[str, Any]:
    """Train a classifier on exported training data.
    
    Args:
        input_csv: Path to training data CSV (from export_training_data)
        output_model: Path to save trained model (pickle). If None, model not saved.
        classifier_type: "random_forest" or "logistic_regression"
        test_size: Fraction of data for testing (0.0-1.0)
        cv_folds: Number of cross-validation folds
        random_state: Random seed for reproducibility
        scale_features: Whether to standardize features
        verbose: Print training progress
        
    Returns:
        Dict with training metrics and model info
    """
    input_path = Path(input_csv)
    if not input_path.exists():
        raise FileNotFoundError(f"Training data CSV not found: {input_path}")
    
    # Load data
    df = pd.read_csv(input_path)
    
    # Filter to labeled samples only
    labeled_df = df.dropna(subset=["label"])
    
    if len(labeled_df) == 0:
        raise ValueError("No labeled samples found in training data. Use --include-unlabeled during export or add more labels.")
    
    if len(labeled_df) < 10:
        raise ValueError(f"Insufficient labeled samples ({len(labeled_df)}). Need at least 10 for training.")
    
    # Check label distribution
    label_counts = labeled_df["label"].value_counts()
    if len(label_counts) < 2:
        raise ValueError(f"Only one class found ({label_counts.index[0]}). Need at least 2 classes for classification.")
    
    # Prepare features and labels
    X = labeled_df[FEATURE_COLUMNS].values
    y = labeled_df["label"].values
    
    # Handle missing values in features
    if pd.isna(X).any():
        # Fill NaN with column median
        from sklearn.impute import SimpleImputer
        imputer = SimpleImputer(strategy="median")
        X = imputer.fit_transform(X)
    
    # Scale features
    scaler = StandardScaler() if scale_features else None
    if scaler is not None:
        X = scaler.fit_transform(X)
    
    # Split train/test
    # Use stratified split to preserve class distribution
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, stratify=y, random_state=random_state
        )
    except ValueError:
        # Fall back to non-stratified if a class has only 1 sample
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
    
    # Create classifier
    if classifier_type == "random_forest":
        clf = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=2,
            min_samples_leaf=1,
            random_state=random_state,
            n_jobs=-1,
        )
    elif classifier_type == "logistic_regression":
        clf = LogisticRegression(
            max_iter=1000,
            solver="lbfgs",
            random_state=random_state,
            n_jobs=-1,
        )
    else:
        raise ValueError(f"Unknown classifier type: {classifier_type}")
    
    # Train
    if verbose:
        print(f"Training {classifier_type} classifier...")
        print(f"  Training samples: {len(X_train)}")
        print(f"  Test samples: {len(X_test)}")
        print(f"  Classes: {list(set(y))}")
    
    clf.fit(X_train, y_train)
    
    # Predict
    y_pred = clf.predict(X_test)
    
    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    recall = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    
    # Cross-validation - adjust folds based on class distribution
    min_class_count = label_counts.min()
    actual_cv_folds = min(cv_folds, min_class_count)
    if actual_cv_folds < 2:
        actual_cv_folds = 2  # Minimum 2 folds
    
    cv_scores = cross_val_score(clf, X, y, cv=StratifiedKFold(n_splits=actual_cv_folds, shuffle=True, random_state=random_state))
    
    # Feature importances (for Random Forest)
    feature_importance = None
    if classifier_type == "random_forest" and hasattr(clf, "feature_importances_"):
        feature_importance = dict(zip(FEATURE_COLUMNS, clf.feature_importances_.tolist()))
    
    # Build result
    result = {
        "classifier_type": classifier_type,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "total_labeled_samples": len(labeled_df),
        "classes": list(set(y)),
        "label_distribution": label_counts.to_dict(),
        "test_metrics": {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_weighted": round(f1, 4),
        },
        "cross_validation": {
            "folds": cv_folds,
            "accuracy_mean": round(cv_scores.mean(), 4),
            "accuracy_std": round(cv_scores.std(), 4),
            "scores": [round(s, 4) for s in cv_scores.tolist()],
        },
        "feature_importance": feature_importance,
        "model_params": clf.get_params(),
        "scaler": scaler,
        "model": clf,
    }
    
    # Save model
    if output_model:
        output_path = Path(output_model)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            "classifier_type": classifier_type,
            "feature_columns": FEATURE_COLUMNS,
            "classes": SUBJECTIVE_LABELS,
            "scaler": scaler,
            "model": clf,
            "version": "v0.1-b6",
        }
        
        with open(output_path, "wb") as f:
            pickle.dump(model_data, f)
        
        if verbose:
            print(f"Model saved to: {output_path}")
    
    return result


def generate_training_report(metrics: dict[str, Any]) -> str:
    """Generate a human-readable training report."""
    lines = [
        "",
        "=== ML Classifier Training Report ===",
        "",
        f"Classifier: {metrics['classifier_type']}",
        f"Total labeled samples: {metrics['total_labeled_samples']}",
        f"  - Training: {metrics['training_samples']}",
        f"  - Test: {metrics['test_samples']}",
        "",
        "Classes:",
    ]
    
    for cls, count in metrics.get("label_distribution", {}).items():
        lines.append(f"  - {cls}: {count}")
    
    lines.extend([
        "",
        "Test Set Metrics:",
        f"  Accuracy:  {metrics['test_metrics']['accuracy']:.4f}",
        f"  Precision: {metrics['test_metrics']['precision']:.4f}",
        f"  Recall:    {metrics['test_metrics']['recall']:.4f}",
        f"  F1 Score:  {metrics['test_metrics']['f1_weighted']:.4f}",
        "",
        f"Cross-Validation ({metrics['cross_validation']['folds']} folds):",
        f"  Accuracy: {metrics['cross_validation']['accuracy_mean']:.4f} (+/- {metrics['cross_validation']['accuracy_std']:.4f})",
        f"  Scores: {metrics['cross_validation']['scores']}",
    ])
    
    if metrics.get("feature_importance"):
        lines.extend([
            "",
            "Top Feature Importances (Random Forest):",
        ])
        sorted_features = sorted(
            metrics["feature_importance"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for feat, imp in sorted_features[:10]:
            lines.append(f"  {feat}: {imp:.4f}")
    
    lines.append("")
    return "\n".join(lines)


def load_model(model_path: str | Path) -> dict[str, Any]:
    """Load a trained model from pickle file.
    
    Args:
        model_path: Path to model pickle file
        
    Returns:
        Dict with model, scaler, feature_columns, classes, version
    """
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    
    with open(path, "rb") as f:
        model_data = pickle.load(f)
    
    return model_data


def predict_tags(
    model_path: str | Path,
    input_csv: str | Path | None = None,
    input_features: dict[str, float] | None = None,
    *,
    confidence_threshold: float = 0.5,
) -> dict[str, Any]:
    """Predict subjective tags using a trained model.
    
    Args:
        model_path: Path to trained model pickle file
        input_csv: Path to CSV with features (for batch prediction)
        input_features: Dict of feature values (for single prediction)
        confidence_threshold: Minimum confidence to apply a tag
        
    Returns:
        Dict with predictions and confidences
    """
    model_data = load_model(model_path)
    clf = model_data["model"]
    scaler = model_data.get("scaler")
    feature_columns = model_data["feature_columns"]
    
    if input_csv:
        # Batch prediction
        df = pd.read_csv(input_csv)
        X = df[feature_columns].values
        
        # Handle missing values
        if pd.isna(X).any():
            from sklearn.impute import SimpleImputer
            imputer = SimpleImputer(strategy="median")
            X = imputer.fit_transform(X)
        
        # Scale
        if scaler is not None:
            X = scaler.transform(X)
        
        # Predict
        predictions = clf.predict(X)
        probabilities = clf.predict_proba(X)
        classes = clf.classes_
        
        results = []
        for i, (pred, probs) in enumerate(zip(predictions, probabilities)):
            confidences = dict(zip(classes, probs.tolist()))
            results.append({
                "row": i,
                "predicted_label": pred,
                "confidence": max(probs),
                "all_confidences": confidences,
            })
        
        return {
            "mode": "batch",
            "total_predictions": len(results),
            "predictions": results,
        }
    
    elif input_features:
        # Single prediction
        X = [[input_features.get(col, 0.0) for col in feature_columns]]
        
        # Handle missing values
        if any(pd.isna(X[0])):
            from sklearn.impute import SimpleImputer
            imputer = SimpleImputer(strategy="median")
            X = imputer.fit_transform(X)
        
        # Scale
        if scaler is not None:
            X = scaler.transform(X)
        
        # Predict
        pred = clf.predict(X)[0]
        probs = clf.predict_proba(X)[0]
        confidences = dict(zip(clf.classes_, probs.tolist()))
        
        return {
            "mode": "single",
            "predicted_label": pred,
            "confidence": max(probs),
            "all_confidences": confidences,
            "applies": {k: v for k, v in confidences.items() if v >= confidence_threshold},
        }
    
    else:
        raise ValueError("Either input_csv or input_features must be provided")
