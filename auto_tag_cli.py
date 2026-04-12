"""
CLI command for auto-tagging audio files with objective features.

v0.1-b5: Auto-tag command for batch processing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from audio_metadata.auto_tag import auto_tag_file, AutoTagResult


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    """Build argument parser for auto-tag command."""
    parser = argparse.ArgumentParser(
        prog="auto-tag",
        description=(
            "Auto-tag audio files with objective feature-based labels. "
            "Tags include: is_percussive, is_sustained, wide_spectrum, "
            "narrow_spectrum, is_bright, is_dark, is_noise_like, is_tone_like, "
            "high_tempo_confidence, low_tempo_confidence."
        ),
        add_help=add_help,
    )
    
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to audio file or directory of audio files",
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output JSON file for results (default: print to stdout)",
    )
    
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview mode: show what would be tagged without writing",
    )
    
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing auto_tags in output JSON",
    )
    
    parser.add_argument(
        "--filter",
        type=str,
        default="*",
        help="File pattern to match (e.g., '*.wav', default: '*')",
    )
    
    parser.add_argument(
        "--sample-rate", "-s",
        type=int,
        default=22050,
        help="Target sample rate for analysis (default: 22050 Hz)",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output: show per-file results",
    )
    
    return parser


def find_audio_files(input_path: str, filter_pattern: str) -> List[Path]:
    """
    Find audio files in the given path.
    
    Args:
        input_path: File or directory path
        filter_pattern: Glob pattern (e.g., '*.wav')
    
    Returns:
        List of audio file paths
    """
    path = Path(input_path)
    
    if path.is_file():
        return [path]
    
    if not path.is_dir():
        return []
    
    # Common audio extensions
    audio_extensions = ['*.wav', '*.mp3', '*.flac', '*.aiff', '*.aif', '*.ogg', '*.m4a', '*.wma']
    
    files = []
    for ext in audio_extensions:
        files.extend(path.rglob(ext))
    
    # Apply filter pattern if specified
    if filter_pattern and filter_pattern != '*':
        files = [f for f in files if f.match(filter_pattern)]
    
    return sorted(files)


def run(args: argparse.Namespace) -> int:
    """
    Execute auto-tag command.
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    input_path = Path(args.input_path)
    
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        return 1
    
    # Find audio files
    audio_files = find_audio_files(str(input_path), args.filter)
    
    if not audio_files:
        print(f"No audio files found in: {input_path}", file=sys.stderr)
        return 1
    
    print(f"Found {len(audio_files)} audio file(s)")
    
    if args.dry_run:
        print(f"\n[DRY RUN] Would process {len(audio_files)} file(s)")
        for f in audio_files[:5]:  # Show first 5
            print(f"  - {f}")
        if len(audio_files) > 5:
            print(f"  ... and {len(audio_files) - 5} more")
        return 0
    
    # Process files
    results = []
    successful = 0
    failed = 0
    
    for i, file_path in enumerate(audio_files, 1):
        if args.verbose:
            print(f"\n[{i}/{len(audio_files)}] Processing: {file_path}")
        
        try:
            result: AutoTagResult = auto_tag_file(file_path, sr=args.sample_rate)
            
            result_dict = {
                "file": str(file_path),
                "tags": result.to_dict(),
            }
            results.append(result_dict)
            successful += 1
            
            if args.verbose:
                print(f"  Tags: {result.tags}")
                print(f"  Confidence: {result.confidence}")
        
        except Exception as e:
            failed += 1
            error_result = {
                "file": str(file_path),
                "error": str(e),
            }
            results.append(error_result)
            
            if args.verbose:
                print(f"  Error: {e}")
            else:
                print(f"Error processing {file_path}: {e}", file=sys.stderr)
    
    # Output results
    output_data = {
        "version": "v0.1-b5",
        "classifier": "v0.1-b5-objective",
        "total_files": len(audio_files),
        "successful": successful,
        "failed": failed,
        "results": results,
    }
    
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {output_path}")
    else:
        print(json.dumps(output_data, indent=2, ensure_ascii=False))
    
    # Summary
    print(f"\nSummary:")
    print(f"  Total: {len(audio_files)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    
    return 0 if failed == 0 else 1


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """
    Validate command-line arguments.
    
    Args:
        args: Parsed arguments
        parser: Argument parser for error messages
    """
    # Validate sample rate
    if args.sample_rate < 8000 or args.sample_rate > 192000:
        parser.error(f"Sample rate must be between 8000 and 192000 Hz, got {args.sample_rate}")
    
    # Validate input path exists (done in run())


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run(args))
