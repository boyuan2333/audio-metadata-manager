"""CLAP semantic search CLI for v0.1-b6."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import audio_metadata.clap_embed as clap_embed


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.py semantic-search",
        description="Search audio using CLAP embeddings (v0.1-b6, optional).",
        add_help=add_help,
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Natural language search query",
    )
    parser.add_argument(
        "--embeddings",
        required=True,
        help="Path to embeddings JSON file",
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
        help="Verbose output (show similarity scores)",
    )
    return parser


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    embeddings_path = Path(args.embeddings)
    if not embeddings_path.exists():
        parser.error(f"Embeddings file not found: {embeddings_path}")
    
    if args.top_k < 1:
        parser.error("--top-k must be at least 1")
    
    if args.threshold < 0.0 or args.threshold > 1.0:
        parser.error("--threshold must be between 0.0 and 1.0")


def run(args: argparse.Namespace) -> int:
    embeddings_path = Path(args.embeddings)
    
    # Check if CLAP is available
    if not clap_embed.check_clap_available():
        print("\nError: CLAP not installed.", file=sys.stderr)
        print("Install with: pip install -r requirements-optional.txt\n", file=sys.stderr)
        return 1
    
    # Load model
    try:
        print(f"\nLoading CLAP model...")
        model = clap_embed.load_clap_model(device=args.device)
    except Exception as e:
        print(f"\nError loading CLAP model: {e}\n", file=sys.stderr)
        return 1
    
    # Compute text embedding
    print(f"Query: \"{args.query}\"")
    
    try:
        query_embedding = clap_embed.compute_text_embedding(model, args.query, device=args.device)
    except Exception as e:
        print(f"\nError computing text embedding: {e}\n", file=sys.stderr)
        return 1
    
    # Search
    try:
        results = clap_embed.search_similar(
            query_embedding,
            embeddings_path,
            top_k=args.top_k,
            threshold=args.threshold,
        )
    except Exception as e:
        print(f"\nError searching embeddings: {e}\n", file=sys.stderr)
        return 1
    
    # Output
    if not results:
        print("\nNo results found.")
        if args.threshold > 0:
            print("Hint: Try lowering the --threshold value.")
        print()
        return 0
    
    print(f"\nTop {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        similarity = result["similarity"]
        path = result["path"]
        
        if args.verbose:
            print(f"  {i}. [{similarity:.4f}] {path}")
        else:
            print(f"  {i}. {path}")
    
    print()
    return 0


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    validate_args(args, parser)
    sys.exit(run(args))
