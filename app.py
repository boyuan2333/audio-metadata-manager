from __future__ import annotations

import argparse

import main as index_command
import review_metadata as review_command
import search_metadata as search_command
import search_similar as similar_command
import nl_query as nl_query_command
import auto_tag_cli as auto_tag_command
import enrich_cli as enrich_command
import export_training_cli as export_training_command
import clap_embed_cli as clap_embed_command
import semantic_search_cli as semantic_search_command
import hybrid_search_cli as hybrid_search_command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.py",
        description=(
            "Local single-user audio sample manager core (v0.1-b6). "
            "Index audio into schema v1 JSON, review overrides, search by explicit fields, "
            "run lightweight similar retrieval, batch review fixes, review candidate discovery, "
            "review workflow presets, grouped review candidate discovery, finer review stats, "
            "natural language query, objective auto-tagging, CLAP embedding computation, "
            "semantic search, and hybrid search."
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

    nl_query_parser = subparsers.add_parser(
        "nl-query",
        help="Search with natural language query.",
        parents=[nl_query_command.build_parser(add_help=False)],
    )
    nl_query_parser.set_defaults(handler=nl_query_command.run, validator=nl_query_command.validate_args)

    auto_tag_parser = subparsers.add_parser(
        "auto-tag",
        help="Auto-tag audio files with objective feature-based labels.",
        parents=[auto_tag_command.build_parser(add_help=False)],
    )
    auto_tag_parser.set_defaults(handler=auto_tag_command.run, validator=auto_tag_command.validate_args)

    enrich_parser = subparsers.add_parser(
        "enrich",
        help="Enrich metadata with embedding coverage and semantic tags (v0.1-b7).",
        parents=[enrich_command.build_parser(add_help=False)],
    )
    enrich_parser.set_defaults(
        handler=enrich_command.run,
        validator=enrich_command.validate_args,
    )

    export_training_parser = subparsers.add_parser(
        "export-training",
        help="Export labeled training data for ML-based subjective classification (v0.1-b6).",
        parents=[export_training_command.build_parser(add_help=False)],
    )
    export_training_parser.set_defaults(
        handler=export_training_command.run,
        validator=export_training_command.validate_args,
    )

    compute_embeddings_parser = subparsers.add_parser(
        "compute-embeddings",
        help="Compute CLAP embeddings for audio files (v0.1-b6, optional).",
        parents=[clap_embed_command.build_parser(add_help=False)],
    )
    compute_embeddings_parser.set_defaults(
        handler=clap_embed_command.run,
        validator=clap_embed_command.validate_args,
    )

    semantic_search_parser = subparsers.add_parser(
        "semantic-search",
        help="Search audio using CLAP embeddings (v0.1-b6, optional).",
        parents=[semantic_search_command.build_parser(add_help=False)],
    )
    semantic_search_parser.set_defaults(
        handler=semantic_search_command.run,
        validator=semantic_search_command.validate_args,
    )

    hybrid_search_parser = subparsers.add_parser(
        "hybrid-search",
        help="Hybrid search combining rule-based filtering and CLAP semantic search (v0.1-b6, optional).",
        parents=[hybrid_search_command.build_parser(add_help=False)],
    )
    hybrid_search_parser.set_defaults(
        handler=hybrid_search_command.run,
        validator=hybrid_search_command.validate_args,
    )

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
