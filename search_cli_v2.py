"""CLI entry point for unified search (keyword / semantic / hybrid)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from audio_metadata.unified_search import format_results, unified_search
from audio_metadata.search_router import analyze_query


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    """Build the argparse parser for the ``search-v2`` subcommand."""
    parser = argparse.ArgumentParser(
        prog="search-v2",
        description=(
            "Unified search: automatically selects keyword, semantic (CLAP), "
            "or hybrid strategy based on the query."
        ),
        add_help=add_help,
    )
    parser.add_argument(
        "query",
        help="The search query string.",
    )
    parser.add_argument(
        "--library",
        required=True,
        help="Path to the library JSON file.",
    )
    parser.add_argument(
        "--embeddings",
        default=None,
        help="Path to the CLAP embeddings JSON (optional).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of results to return (default: 10).",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help='Device for CLAP model: "cpu" or "cuda" (default: cpu).',
    )
    return parser


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser | None = None) -> None:
    """Validate that the library file exists."""
    lib = Path(args.library)
    if not lib.exists():
        msg = f"Library file not found: {args.library}"
        if parser is not None:
            parser.error(msg)
        else:
            raise FileNotFoundError(msg)


def run(args: argparse.Namespace) -> int:
    """Execute the unified search and print formatted results."""
    results = unified_search(
        query=args.query,
        library_path=args.library,
        embeddings_path=args.embeddings,
        top_k=args.top_k,
        device=args.device,
    )

    # Determine strategy for display purposes
    plan = analyze_query(args.query)
    strategy = plan.get("strategy", "keyword")

    output = format_results(results, args.query, strategy)
    print(output)
    return 0
