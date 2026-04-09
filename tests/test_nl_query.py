from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import search_metadata


def load_parse_nl_query() -> Callable[[str], dict[str, Any]]:
    try:
        module = importlib.import_module("nl_query")
    except ModuleNotFoundError as exc:  # pragma: no cover - expected during red phase
        raise AssertionError("Expected module 'nl_query' to exist.") from exc

    parser = getattr(module, "parse_nl_query", None)
    if parser is None:
        raise AssertionError("Expected nl_query.parse_nl_query(query) to exist.")
    return parser


def supported_intent_fields() -> set[str]:
    parser = search_metadata.build_parser(add_help=False)
    ignored_fields = {"help", "input", "limit"}
    return {
        action.dest
        for action in parser._actions
        if action.dest not in ignored_fields
    }


class NLQueryParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.allowed_fields = supported_intent_fields()

    def assert_supported_intent(self, intent: dict[str, Any]) -> None:
        self.assertIsInstance(intent, dict)
        self.assertTrue(
            set(intent).issubset(self.allowed_fields),
            msg=f"Intent contains unsupported fields: {sorted(set(intent) - self.allowed_fields)}",
        )

    def parse(self, query: str) -> dict[str, Any]:
        return load_parse_nl_query()(query)

    def test_example_queries_parse_into_structured_intent(self) -> None:
        cases = [
            (
                "dark drum loops around 128 bpm",
                {
                    "brightness": "dark",
                    "keyword": "drum",
                    "is_loop": True,
                    "min_bpm": 120.0,
                    "max_bpm": 135.0,
                },
            ),
            (
                "bright percussion one shots",
                {
                    "brightness": "bright",
                    "keyword": "percussion",
                    "is_loop": False,
                },
            ),
            (
                "show non-loop fills",
                {
                    "keyword": "fill",
                    "is_loop": False,
                },
            ),
            (
                "slow loops under 90 bpm",
                {
                    "is_loop": True,
                    "max_bpm": 90.0,
                },
            ),
            (
                "dark sounds with no tempo",
                {
                    "brightness": "dark",
                    "tempo_applicable": False,
                },
            ),
            (
                "find crash one shots",
                {
                    "keyword": "crash",
                    "is_loop": False,
                },
            ),
        ]

        for query, expected_intent in cases:
            with self.subTest(query=query):
                intent = self.parse(query)
                self.assert_supported_intent(intent)
                self.assertEqual(intent, expected_intent)

    def test_empty_query_returns_empty_intent(self) -> None:
        intent = self.parse("")

        self.assert_supported_intent(intent)
        self.assertEqual(intent, {})

    def test_unsupported_words_fall_back_to_keyword_only(self) -> None:
        intent = self.parse("mystic galaxy wobble")

        self.assert_supported_intent(intent)
        self.assertEqual(intent, {"keyword": "mystic galaxy wobble"})

    def test_conflicting_brightness_terms_do_not_set_brightness(self) -> None:
        intent = self.parse("bright dark loops")

        self.assert_supported_intent(intent)
        self.assertNotIn("brightness", intent)
        self.assertEqual(intent.get("is_loop"), True)

    def test_supported_field_whitelist_matches_search_metadata_filters(self) -> None:
        self.assertEqual(
            self.allowed_fields,
            {
                "keyword",
                "min_bpm",
                "max_bpm",
                "min_duration",
                "max_duration",
                "tempo_applicable",
                "tempo_quality",
                "is_loop",
                "duration_bucket",
                "brightness",
                "status",
            },
        )


if __name__ == "__main__":
    unittest.main()
