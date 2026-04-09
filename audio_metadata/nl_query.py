from __future__ import annotations

import re
from typing import Any


_NON_WORD_RE = re.compile(r"[^a-z0-9]+")
_WS_RE = re.compile(r"\s+")

_BRIGHTNESS_PATTERNS: tuple[tuple[str, str], ...] = (
    ("very bright", "very_bright"),
    ("balanced", "balanced"),
    ("bright", "bright"),
    ("dark", "dark"),
)

_LOOP_PATTERNS: tuple[tuple[tuple[str, ...], bool], ...] = (
    (("non loop", "nonloop", "one shots", "one shot", "one-shots", "one-shot", "oneshots", "oneshot"), False),
    (("loops", "loop"), True),
)

_KEYWORD_NORMALIZATIONS = {
    "fills": "fill",
}

_KEYWORD_EXCLUDE = {
    "and",
    "around",
    "bpm",
    "find",
    "no",
    "over",
    "show",
    "slow",
    "sounds",
    "tempo",
    "under",
    "with",
    "without",
}

_TEMPO_APPLICABLE_PATTERNS = (
    "no tempo",
    "without tempo",
    "no bpm",
)


def parse_nl_query(query: str) -> dict[str, Any]:
    normalized = _normalize_query(query)
    if not normalized:
        return {}

    working = normalized
    intent: dict[str, Any] = {}

    working, brightness = _extract_brightness(working)
    if brightness is not None:
        intent["brightness"] = brightness

    working, is_loop = _extract_is_loop(working)
    if is_loop is not None:
        intent["is_loop"] = is_loop

    working, tempo_applicable = _extract_tempo_applicable(working)
    if tempo_applicable is not None:
        intent["tempo_applicable"] = tempo_applicable

    working, bpm_range = _extract_bpm_range(working)
    if bpm_range is not None:
        min_bpm, max_bpm = bpm_range
        if min_bpm is not None:
            intent["min_bpm"] = min_bpm
        if max_bpm is not None:
            intent["max_bpm"] = max_bpm

    keyword = _extract_keyword(working)
    if keyword:
        intent["keyword"] = keyword

    return intent


def _normalize_query(query: str) -> str:
    lowered = query.strip().casefold().replace("-", " ")
    collapsed = _NON_WORD_RE.sub(" ", lowered)
    return _WS_RE.sub(" ", collapsed).strip()


def _extract_brightness(text: str) -> tuple[str, str | None]:
    matches: list[str] = []
    working = text
    for phrase, value in _BRIGHTNESS_PATTERNS:
        if re.search(rf"\b{re.escape(phrase)}\b", working):
            matches.append(value)
            working = re.sub(rf"\b{re.escape(phrase)}\b", " ", working)

    unique_matches = set(matches)
    if len(unique_matches) == 1:
        return _clean_text(working), matches[0]
    return _clean_text(working), None


def _extract_is_loop(text: str) -> tuple[str, bool | None]:
    matches: list[bool] = []
    working = text
    for phrases, value in _LOOP_PATTERNS:
        for phrase in phrases:
            if re.search(rf"\b{re.escape(phrase)}\b", working):
                matches.append(value)
                working = re.sub(rf"\b{re.escape(phrase)}\b", " ", working)

    unique_matches = set(matches)
    if len(unique_matches) == 1:
        return _clean_text(working), matches[0]
    return _clean_text(working), None


def _extract_tempo_applicable(text: str) -> tuple[str, bool | None]:
    working = text
    matched = False
    for phrase in _TEMPO_APPLICABLE_PATTERNS:
        if re.search(rf"\b{re.escape(phrase)}\b", working):
            matched = True
            working = re.sub(rf"\b{re.escape(phrase)}\b", " ", working)

    if matched:
        return _clean_text(working), False
    return _clean_text(working), None


def _extract_bpm_range(text: str) -> tuple[str, tuple[float | None, float | None] | None]:
    working = text

    between_match = re.search(r"\bbetween\s+(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)\s+bpm\b", working)
    if between_match:
        first = float(between_match.group(1))
        second = float(between_match.group(2))
        min_bpm = min(first, second)
        max_bpm = max(first, second)
        working = working[:between_match.start()] + " " + working[between_match.end():]
        return _clean_text(working), (min_bpm, max_bpm)

    around_match = re.search(r"\baround\s+(\d+(?:\.\d+)?)\s+bpm\b", working)
    if around_match:
        bpm = float(around_match.group(1))
        working = working[:around_match.start()] + " " + working[around_match.end():]
        return _clean_text(working), (max(0.0, bpm - 8.0), bpm + 7.0)

    under_match = re.search(r"\bunder\s+(\d+(?:\.\d+)?)\s+bpm\b", working)
    if under_match:
        bpm = float(under_match.group(1))
        working = working[:under_match.start()] + " " + working[under_match.end():]
        return _clean_text(working), (None, bpm)

    over_match = re.search(r"\bover\s+(\d+(?:\.\d+)?)\s+bpm\b", working)
    if over_match:
        bpm = float(over_match.group(1))
        working = working[:over_match.start()] + " " + working[over_match.end():]
        return _clean_text(working), (bpm, None)

    exact_match = re.search(r"\b(\d+(?:\.\d+)?)\s+bpm\b", working)
    if exact_match:
        bpm = float(exact_match.group(1))
        working = working[:exact_match.start()] + " " + working[exact_match.end():]
        return _clean_text(working), (bpm, bpm)

    return _clean_text(working), None


def _extract_keyword(text: str) -> str | None:
    tokens = []
    for token in text.split():
        if token in _KEYWORD_EXCLUDE:
            continue
        tokens.append(_KEYWORD_NORMALIZATIONS.get(token, token))

    if not tokens:
        return None
    return " ".join(tokens)


def _clean_text(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()
