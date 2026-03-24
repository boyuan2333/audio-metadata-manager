from __future__ import annotations

import argparse
from pathlib import Path

from audio_metadata.indexer import index_audio_directory, write_output_payload


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan a local directory and export schema v1 audio metadata JSON.",
        add_help=add_help,
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Directory containing audio files.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to the output JSON file.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively scan subdirectories.",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    input_dir = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not input_dir.exists() or not input_dir.is_dir():
        raise ValueError(f"Input directory does not exist or is not a directory: {input_dir}")

    payload = index_audio_directory(input_dir, output_path, recursive=args.recursive)
    write_output_payload(output_path, payload)
    print(f"Wrote metadata for {len(payload['files'])} file(s) to {output_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
