"""CLAP embedding computation CLI for v0.1-b6 semantic search."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import audio_metadata.clap_embed as clap_embed
from audio_metadata import scanner


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.py compute-embeddings",
        description="Compute CLAP embeddings for audio files (v0.1-b6, optional).",
        add_help=add_help,
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to audio directory or file",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output embeddings JSON file",
    )
    parser.add_argument(
        "--filter",
        default="*",
        help="File pattern filter (default: *)",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan directory recursively",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing embeddings file",
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default="cpu",
        help="Device for CLAP model (default: cpu)",
    )
    parser.add_argument(
        "--model",
        default=clap_embed.CLAP_MODEL_NAME,
        help=f"CLAP model name (default: {clap_embed.CLAP_MODEL_NAME})",
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
        parser.error(f"Input path not found: {input_path}")
    
    if input_path.is_file() and not input_path.suffix.lower() in (".wav", ".mp3", ".flac", ".aiff", ".aif", ".m4a", ".ogg"):
        parser.error(f"Input file does not appear to be audio: {input_path}")


def run(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # Check if CLAP is available
    if not clap_embed.check_clap_available():
        print("\nError: CLAP not installed.", file=sys.stderr)
        print("Install with: pip install -r requirements-optional.txt\n", file=sys.stderr)
        return 1
    
    # Collect audio files
    print(f"\nCollecting audio files from: {input_path}")
    
    if input_path.is_file():
        audio_files = [input_path]
    else:
        # Use scanner to find audio files
        audio_files = scanner.scan_audio_files(
            input_path,
            recursive=args.recursive,
        )
        
        if not audio_files:
            print("No audio files found.", file=sys.stderr)
            return 1
    
    print(f"Found {len(audio_files)} audio files\n")
    
    # Compute embeddings
    try:
        result = clap_embed.compute_embeddings_batch(
            audio_files,
            output_path,
            model_name=args.model,
            device=args.device,
            append=args.append,
            verbose=args.verbose,
        )
        
        print("\n=== CLAP Embedding Computation Complete ===")
        print(f"Output: {result['output_file']}")
        print(f"Total files processed: {result['total_files']}")
        print(f"Successful: {result['successful']}")
        if result['failed'] > 0:
            print(f"Failed: {result['failed']}")
        print(f"Total embeddings in file: {result['total_embeddings']}")
        
        if args.verbose and result['failed_files']:
            print("\nFailed files:")
            for failed in result['failed_files'][:10]:
                print(f"  - {failed['path']}: {failed['error']}")
            if len(result['failed_files']) > 10:
                print(f"  ... and {len(result['failed_files']) - 10} more")
        
        print()
        return 0
        
    except Exception as e:
        print(f"\nError: {e}\n", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    validate_args(args, parser)
    sys.exit(run(args))
