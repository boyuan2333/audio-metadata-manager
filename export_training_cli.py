"""Training data export CLI for v0.1-b6 ML-based subjective classification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import audio_metadata.training_data as training_data


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.py export-training",
        description="Export labeled training data from reviewed metadata for ML classification.",
        add_help=add_help,
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to reviewed metadata JSON file",
    )
    parser.add_argument(
        "--output",
        required=False,
        default=None,
        help="Path to output CSV file (not required with --report)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate training data report without exporting",
    )
    parser.add_argument(
        "--include-unlabeled",
        action="store_true",
        help="Include unlabeled samples in output (label=None)",
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
        parser.error(f"Input file not found: {input_path}")
    
    if not args.report and not args.output:
        parser.error("--output is required unless --report is used")


def run(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    
    if args.report:
        # Generate report only
        report = training_data.generate_training_report(input_path)
        
        print("\n=== Training Data Report ===")
        print(f"Total records: {report['total_records']}")
        print(f"Labeled samples: {report['total_labeled']}")
        print(f"Coverage: {report['coverage_percentage']}%")
        
        if report['label_distribution']:
            print("\nLabel distribution:")
            for label, count in sorted(report['label_distribution'].items()):
                print(f"  {label}: {count}")
        else:
            print("\nNo labeled samples found.")
            print("\nHint: Use 'review' or 'review-batch' to add subjective tags to records.")
            print("Labels are extracted from:")
            print("  - model_outputs.subjective_tags (v0.1-b6+)")
            print("  - retrieval.tags (if contains dark/bright/energetic/calm)")
            print("  - derived.brightness (mapped: dark→dark, bright/very_bright→bright)")
        
        print()
        return 0
    
    # Export training data
    output_path = Path(args.output)
    if args.verbose:
        print(f"Reading: {input_path}")
    
    result = training_data.export_training_data(
        input_path,
        output_path,
        include_unlabeled=args.include_unlabeled,
    )
    
    print("\n=== Training Data Export Complete ===")
    print(f"Output: {result['output_file']}")
    print(f"Labeled samples: {result['labeled_samples']}")
    if result['unlabeled_samples'] > 0:
        print(f"Unlabeled samples: {result['unlabeled_samples']}")
    print(f"Total records processed: {result['total_records']}")
    
    if args.verbose and result['labeled_samples'] > 0:
        print("\nFeature columns:")
        for col in training_data.FEATURE_COLUMNS:
            print(f"  - {col}")
        print(f"\nLabel column: label (values: {', '.join(training_data.SUBJECTIVE_LABELS)})")
    
    print()
    return 0


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    validate_args(args, parser)
    sys.exit(run(args))
