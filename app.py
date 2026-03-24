from __future__ import annotations

import argparse

import main as index_command
import review_metadata as review_command
import search_metadata as search_command
import search_similar as similar_command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.py",
        description=(
            "Local single-user audio sample manager core (v0.1-b3). "
            "Index audio into schema v1 JSON, review overrides, search by explicit fields, "
            "run lightweight similar retrieval, batch review fixes, review candidate discovery, "
            "review workflow presets, grouped review candidate discovery, and finer review stats."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser(
        "index",
        help="Scan a directory and write schema v1 JSON.",
        parents=[index_command.build_parser(add_help=False)],
    )
    index_parser.set_defaults(handler=index_command.run, validator=None)

    review_parser = subparsers.add_parser(
        "review",
        help="Write minimal review overrides into an indexed JSON file.",
        parents=[review_command.build_parser(add_help=False)],
    )
    review_parser.set_defaults(handler=review_command.run, validator=review_command.validate_args)

    review_batch_parser = subparsers.add_parser(
        "review-batch",
        help="Preview or apply minimal review overrides to matched records.",
        parents=[review_command.build_batch_parser(add_help=False)],
    )
    review_batch_parser.set_defaults(
        handler=review_command.run_batch,
        validator=review_command.validate_batch_args,
    )

    review_candidates_parser = subparsers.add_parser(
        "review-candidates",
        help="List high-value records that likely need manual review.",
        parents=[review_command.build_candidates_parser(add_help=False)],
    )
    review_candidates_parser.set_defaults(
        handler=review_command.run_candidates,
        validator=review_command.validate_candidates_args,
    )

    review_stats_parser = subparsers.add_parser(
        "review-stats",
        help="Summarize current review override and notes coverage.",
        parents=[review_command.build_stats_parser(add_help=False)],
    )
    review_stats_parser.set_defaults(
        handler=review_command.run_stats,
        validator=review_command.validate_stats_args,
    )

    search_parser = subparsers.add_parser(
        "search",
        help="Search an indexed JSON file with explicit field filters.",
        parents=[search_command.build_parser(add_help=False)],
    )
    search_parser.set_defaults(handler=search_command.run, validator=search_command.validate_args)

    similar_parser = subparsers.add_parser(
        "similar",
        help="Find similar items after explicit candidate filtering.",
        parents=[similar_command.build_parser(add_help=False)],
    )
    similar_parser.set_defaults(handler=similar_command.run, validator=similar_command.validate_args)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    validator = getattr(args, "validator", None)
    if validator is not None:
        validator(args, parser)

    try:
        return args.handler(args)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())

