"""Hybrid search CLI for v0.1-b6 — combines rule-based filtering with CLAP semantic search."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import audio_metadata.hybrid_search as hybrid_search_module


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.py hybrid-search",
        description="Hybrid search combining rule-based filtering and CLAP semantic search (v0.1-b6).",
        add_help=add_help,
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Natural language search query (e.g., 'dark pad around 120 bpm')",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to library metadata JSON file",
    )
    parser.add_argument(
        "--embeddings",
        required=True,
        help="Path to CLAP embeddings JSON file",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of results to return (default: 10)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Minimum similarity threshold (0.0-1.0, default: 0.0)",
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default="cpu",
        help="Device for CLAP model (default: cpu)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output (show similarity scores and metadata)",
    )
    return parser


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    input_path = Path(args.input)
    if not input_path.exists():
        parser.error(f"Library file not found: {input_path}")
    
    embeddings_path = Path(args.embeddings)
    if not embeddings_path.exists():
        parser.error(f"Embeddings file not found: {embeddings_path}")
    
    if args.top_k < 1:
        parser.error("--top-k must be at least 1")
    
    if args.threshold < 0.0 or args.threshold > 1.0:
        parser.error("--threshold must be between 0.0 and 1.0")


def run(args: argparse.Namespace) -> int:
    # Check if CLAP is available
    if not hybrid_search_module.clap_embed.check_clap_available():
        print("\nError: CLAP not installed.", file=sys.stderr)
        print("Install with: pip install -r requirements-optional.txt\n", file=sys.stderr)
        return 1
    
    try:
        results = hybrid_search_module.hybrid_search(
            args.query,
            args.input,
            args.embeddings,
            top_k=args.top_k,
            threshold=args.threshold,
            device=args.device,
        )
    except ImportError as e:
        print(f"\nError: {e}\n", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\nError: {e}\n", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    # Output
    output = hybrid_search_module.format_hybrid_results(results, verbose=args.verbose)
    print(output)
    print()
    
    return 0


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    validate_args(args, parser)
    sys.exit(run(args))
