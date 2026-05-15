"""CLI entry point for library report generation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from audio_metadata.report import format_report, generate_report


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    """Return the argument parser for the ``report`` subcommand."""
    parser = argparse.ArgumentParser(
        prog="app.py report",
        description="Generate an aggregate library report (stats, coverage, warnings).",
        add_help=add_help,
    )
    parser.add_argument(
        "--library",
        required=True,
        help="Path to library JSON file.",
    )
    parser.add_argument(
        "--embeddings",
        default=None,
        help="Path to embeddings JSON file (optional).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Save report to file instead of printing to stdout.",
    )
    return parser


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser | None = None) -> None:
    """Validate that the library file exists."""
    lib_path = Path(args.library)
    if not lib_path.is_file():
        msg = f"Library file not found: {args.library}"
        if parser is not None:
            parser.error(msg)
        raise FileNotFoundError(msg)


def run(args: argparse.Namespace) -> int:
    """Generate and output the library report."""
    stats = generate_report(
        library_path=args.library,
        embeddings_path=args.embeddings,
    )
    text = format_report(stats)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(text, encoding="utf-8")
        print(f"Report saved to {out_path}")
    else:
        print(text)

    return 0
