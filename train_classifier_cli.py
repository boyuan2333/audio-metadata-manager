"""ML classifier training CLI for v0.1-b6 subjective tag prediction."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import audio_metadata.ml_classifier as ml_classifier


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.py train-classifier",
        description="Train ML classifier for subjective tag prediction (v0.1-b6).",
        add_help=add_help,
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to training data CSV (from export-training command)",
    )
    parser.add_argument(
        "--output",
        required=False,
        default=None,
        help="Path to save trained model (pickle format). Required unless --report-only.",
    )
    parser.add_argument(
        "--classifier",
        choices=["random_forest", "logistic_regression"],
        default="random_forest",
        help="Classifier type (default: random_forest)",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of data for testing (default: 0.2)",
    )
    parser.add_argument(
        "--cv-folds",
        type=int,
        default=5,
        help="Number of cross-validation folds (default: 5)",
    )
    parser.add_argument(
        "--no-scale",
        action="store_true",
        help="Disable feature scaling (default: scaling enabled)",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Show training data stats without training",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    return parser


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    input_path = Path(args.input)
    if not input_path.exists():
        parser.error(f"Training data CSV not found: {input_path}")
    
    if not args.report_only and not args.output:
        parser.error("--output is required unless --report-only is used")
    
    if args.test_size <= 0 or args.test_size >= 1:
        parser.error("--test-size must be between 0 and 1")
    
    if args.cv_folds < 2:
        parser.error("--cv-folds must be at least 2")


def run(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    
    if args.report_only:
        # Show data stats only
        import pandas as pd
        df = pd.read_csv(input_path)
        
        labeled_df = df.dropna(subset=["label"])
        unlabeled_df = df[df["label"].isna()]
        
        print("\n=== Training Data Summary ===")
        print(f"Total rows: {len(df)}")
        print(f"Labeled samples: {len(labeled_df)}")
        print(f"Unlabeled samples: {len(unlabeled_df)}")
        
        if len(labeled_df) > 0:
            print("\nLabel distribution:")
            label_counts = labeled_df["label"].value_counts()
            for label, count in label_counts.items():
                print(f"  {label}: {count} ({count/len(labeled_df)*100:.1f}%)")
            
            print("\nFeature columns:")
            for col in ml_classifier.FEATURE_COLUMNS:
                if col in df.columns:
                    non_null = df[col].notna().sum()
                    print(f"  {col}: {non_null}/{len(df)} non-null")
        else:
            print("\nNo labeled samples found. Cannot train classifier.")
            print("Hint: Use 'export-training --include-unlabeled' or add more labels via review.")
        
        print()
        return 0
    
    # Train classifier
    output_path = Path(args.output) if args.output else None
    
    try:
        metrics = ml_classifier.train_classifier(
            input_path,
            output_path,
            classifier_type=args.classifier,
            test_size=args.test_size,
            cv_folds=args.cv_folds,
            scale_features=not args.no_scale,
            verbose=args.verbose,
        )
        
        report = ml_classifier.generate_training_report(metrics)
        print(report)
        
        if args.verbose and metrics.get("feature_importance"):
            print("\nAll Feature Importances:")
            sorted_features = sorted(
                metrics["feature_importance"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            for feat, imp in sorted_features:
                print(f"  {feat}: {imp:.4f}")
        
        print()
        return 0
        
    except ValueError as e:
        print(f"\nError: {e}\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    validate_args(args, parser)
    sys.exit(run(args))
