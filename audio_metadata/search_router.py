from __future__ import annotations

import re
from typing import Any

from audio_metadata.nl_query import parse_nl_query

# Descriptive/subjective words that suggest semantic search is useful.
_SEMANTIC_WORDS: set[str] = {
    # Chinese
    "温暖", "暗", "明亮", "柔和", "厚重", "空灵", "忧伤", "欢快", "紧张",
    "温柔", "激烈", "深沉", "轻快", "沉重", "梦幻", "复古", "现代",
    "冷", "暖", "硬", "软",
    # English
    "dark",
    "bright",
    "warm",
    "cold",
    "soft",
    "hard",
    "gentle",
    "aggressive",
    "dreamy",
    "moody",
    "cheerful",
    "melancholic",
    "ethereal",
    "heavy",
    "light",
    "mellow",
    "punchy",
    "smooth",
    "rough",
    "crisp",
    "vintage",
    "retro",
    "modern",
    "futuristic",
    "ambient",
    "atmospheric",
    "lush",
    "airy",
    "deep",
}

# Structured keys that count as hard constraints for routing purposes.
# NOTE: brightness is a descriptive quality — it drives semantic routing,
#       not hybrid. It is still reported in structured_filters for downstream use.
_STRUCTURED_ROUTING_KEYS = {"min_bpm", "max_bpm", "is_loop"}

# Format-related keywords (detected from keywords string).
_FORMAT_KEYWORDS: set[str] = {
    "wav", "mp3", "flac", "ogg", "aiff", "m4a", "aac",
}

# Words that are purely structural / noise — stripped before keyword building.
_NOISE_WORDS: set[str] = {
    "的", "了", "和", "与", "及", "是", "在", "有", "一个", "一些",
    "a", "an", "the", "of", "for", "in", "on", "with", "to", "is",
}


def analyze_query(query: str) -> dict[str, Any]:
    """Analyze a natural-language search query and decide a search strategy.

    Returns a dict with keys:
        strategy:           "keyword" | "semantic" | "hybrid"
        structured_filters: dict of extracted constraints
        semantic_text:      descriptive/subjective portion (for CLAP embedding)
        keywords:           list of keyword terms for filename matching
    """
    if not query or not query.strip():
        return {
            "strategy": "keyword",
            "structured_filters": {},
            "semantic_text": "",
            "keywords": [],
        }

    # --- Step 0: preprocess for common tokenisation gaps ---
    # parse_nl_query expects "120 bpm" (space before bpm), not "120bpm".
    preprocessed = _preprocess_query(query)

    # --- Step 1: use existing parser for structured data ---
    parsed = parse_nl_query(preprocessed)

    # --- Step 2: build structured_filters from parsed result ---
    structured_filters: dict[str, Any] = {}
    if "min_bpm" in parsed or "max_bpm" in parsed:
        structured_filters["bpm"] = {
            "min": parsed.get("min_bpm"),
            "max": parsed.get("max_bpm"),
        }
    if "is_loop" in parsed:
        structured_filters["is_loop"] = parsed["is_loop"]
    if "brightness" in parsed:
        structured_filters["brightness"] = parsed["brightness"]

    # Detect format from keyword field
    keyword_str = parsed.get("keyword", "")
    detected_format = _detect_format(keyword_str)
    if detected_format:
        structured_filters["format"] = detected_format

    # Routing-relevant structured signal: BPM, loop, format (NOT brightness)
    has_routing_structured = any(
        key in parsed for key in _STRUCTURED_ROUTING_KEYS
    ) or detected_format is not None

    # --- Step 3: detect descriptive / semantic words ---
    semantic_text = _extract_semantic_text(query)
    has_semantic = bool(semantic_text)

    # --- Step 4: build keyword list ---
    keywords = _build_keywords(keyword_str, semantic_text)

    # --- Step 5: decide strategy ---
    if has_routing_structured and has_semantic:
        strategy = "hybrid"
    elif has_routing_structured:
        strategy = "hybrid"
    elif has_semantic:
        strategy = "semantic"
    else:
        strategy = "keyword"

    return {
        "strategy": strategy,
        "structured_filters": structured_filters,
        "semantic_text": semantic_text,
        "keywords": keywords,
    }


def _preprocess_query(query: str) -> str:
    """Fix common tokenisation gaps before passing to parse_nl_query."""
    result = query
    # "120bpm" → "120 bpm" (require space between digits and "bpm")
    result = re.sub(r"(\d+)\s*bpm\b", r"\1 bpm", result, flags=re.IGNORECASE)
    return result


def _detect_format(keyword_str: str) -> str | None:
    """Return a format string if a known audio format is found in keywords."""
    if not keyword_str:
        return None
    tokens = keyword_str.lower().split()
    for tok in tokens:
        if tok in _FORMAT_KEYWORDS:
            return tok
    return None


def _extract_semantic_text(query: str) -> str:
    """Extract descriptive / subjective words from the raw query."""
    lowered = query.strip()
    matched: list[str] = []

    for word in _SEMANTIC_WORDS:
        if word in lowered:
            matched.append(word)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for w in matched:
        if w not in seen:
            seen.add(w)
            unique.append(w)

    return " ".join(unique)


def _build_keywords(keyword_str: str, semantic_text: str) -> list[str]:
    """Build a list of keyword terms for filename matching."""
    raw_tokens: list[str] = []
    if keyword_str:
        raw_tokens.extend(keyword_str.lower().split())

    seen: set[str] = set()
    result: list[str] = []
    for tok in raw_tokens:
        tok = tok.strip()
        if tok and tok not in seen and tok not in _NOISE_WORDS:
            seen.add(tok)
            result.append(tok)
    return result
