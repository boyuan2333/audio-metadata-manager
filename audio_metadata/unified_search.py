"""Unified search execution engine.

Combines keyword, semantic (CLAP), and hybrid search strategies into a
single entry point. The search router selects the best strategy; this
module executes it and returns a consistent result format.
"""

from __future__ import annotations

import json
import logging
import sys
import warnings
from pathlib import Path
from typing import Any

import audio_metadata.clap_embed as clap_embed
from audio_metadata.search_router import analyze_query

logger = logging.getLogger(__name__)

# ── Fields that participate in keyword matching (case-insensitive substring) ──
_KEYWORD_FIELDS: list[tuple[str, ...]] = [
    ("source", "file_name"),
    ("retrieval", "tags"),
    ("retrieval", "mood"),
    ("retrieval", "texture"),
]


# ──────────────────────────────────────────────────────────────────────────────
# Core API
# ──────────────────────────────────────────────────────────────────────────────

def unified_search(
    query: str,
    library_path: str | Path,
    embeddings_path: str | Path | None = None,
    *,
    top_k: int = 10,
    device: str = "cpu",
) -> list[dict[str, Any]]:
    """Run a search against the audio library.

    Parameters
    ----------
    query:
        Natural-language search query.
    library_path:
        Path to the exported library JSON (``{"files": [...]}``).
    embeddings_path:
        Path to the CLAP embeddings JSON.  May be ``None``; in that
        case strategies requiring CLAP fall back to keyword search.
    top_k:
        Maximum number of results to return.
    device:
        ``"cpu"`` or ``"cuda"`` for the CLAP model.

    Returns
    -------
    list[dict]
        Each dict contains ``path``, ``file_name``, ``score``,
        and ``metadata`` (duration, bpm, tags, etc.).
    """
    library_path = Path(library_path)
    if not library_path.exists():
        raise FileNotFoundError(f"Library file not found: {library_path}")

    with open(library_path, encoding="utf-8") as fh:
        payload = json.load(fh)
    records: list[dict[str, Any]] = payload.get("files", [])

    if not records:
        return []

    # 1. Decide strategy
    plan = analyze_query(query)
    strategy: str = plan["strategy"]

    # 2. Fallback if CLAP is needed but unavailable
    if strategy in ("semantic", "hybrid") and embeddings_path is None:
        warnings.warn(
            f"Strategy '{strategy}' requires CLAP embeddings but no "
            "embeddings_path was provided. Falling back to keyword search.",
            stacklevel=2,
        )
        strategy = "keyword"

    # 3. Execute
    if strategy == "keyword":
        raw = _keyword_search(records, plan, top_k)
    elif strategy == "semantic":
        raw = _semantic_search(records, plan, embeddings_path, top_k, device)
    elif strategy == "hybrid":
        raw = _hybrid_search(records, plan, embeddings_path, top_k, device)
    else:
        raw = _keyword_search(records, plan, top_k)

    # 4. Normalize output
    return [_to_result(r) for r in raw]


# ──────────────────────────────────────────────────────────────────────────────
# Keyword search
# ──────────────────────────────────────────────────────────────────────────────

def _keyword_search(
    records: list[dict[str, Any]],
    plan: dict[str, Any],
    top_k: int,
) -> list[dict[str, Any]]:
    """Filter records by keyword substring match and score them."""
    keywords: list[str] = plan.get("keywords", [])
    structured: dict[str, Any] = plan.get("structured_filters", {})

    scored: list[tuple[float, dict[str, Any]]] = []
    for rec in records:
        if not _passes_structured(rec, structured):
            continue
        score = _keyword_score(rec, keywords)
        if score > 0:
            scored.append((score, rec))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"score": s, "record": r} for s, r in scored[:top_k]]


def _keyword_score(record: dict[str, Any], keywords: list[str]) -> float:
    """Return a 0-1 score based on how many keywords match."""
    if not keywords:
        # No keywords → everything matches (score 1) when no filter is useful
        return 1.0

    hits = 0
    for kw in keywords:
        needle = kw.lower()
        for field_path in _KEYWORD_FIELDS:
            value = _get_nested(record, *field_path)
            if _field_contains(value, needle):
                hits += 1
                break  # count each keyword at most once
    return hits / len(keywords) if keywords else 1.0


def _passes_structured(record: dict[str, Any], structured: dict[str, Any]) -> bool:
    """Check structured filters (BPM, loop, etc.) against a record."""
    if not structured:
        return True

    # BPM range
    bpm_filter = structured.get("bpm")
    if bpm_filter:
        bpm_val = _get_nested(record, "features", "tempo_bpm")
        if not isinstance(bpm_val, (int, float)):
            return False
        if bpm_filter.get("min") is not None and bpm_val < bpm_filter["min"]:
            return False
        if bpm_filter.get("max") is not None and bpm_val > bpm_filter["max"]:
            return False

    # Loop filter (skip if record has no value — treat as unknown, allow through)
    if "is_loop" in structured:
        rec_loop = _get_nested(record, "derived", "is_loop")
        if rec_loop is not None and rec_loop != structured["is_loop"]:
            return False

    # Brightness (skip if record has no value — treat as unknown, allow through)
    if "brightness" in structured:
        rec_bright = _get_nested(record, "derived", "brightness")
        if rec_bright is not None and rec_bright != structured["brightness"]:
            return False

    # Format
    fmt = structured.get("format")
    if fmt:
        rec_fmt = _get_nested(record, "source", "file_format")
        if not isinstance(rec_fmt, str) or rec_fmt.lower() != fmt:
            return False

    return True


# ──────────────────────────────────────────────────────────────────────────────
# Semantic search (CLAP)
# ──────────────────────────────────────────────────────────────────────────────

def _semantic_search(
    records: list[dict[str, Any]],
    plan: dict[str, Any],
    embeddings_path: str | Path,
    top_k: int,
    device: str,
) -> list[dict[str, Any]]:
    """CLAP embedding similarity search across the full library."""
    semantic_text = plan.get("semantic_text", "") or " ".join(plan.get("keywords", []))

    if not embeddings_path or not Path(embeddings_path).exists():
        warnings.warn("Embeddings file missing – falling back to keyword search.", stacklevel=2)
        return _keyword_search(records, plan, top_k)

    if not clap_embed.check_clap_available():
        warnings.warn("CLAP not installed – falling back to keyword search.", stacklevel=2)
        return _keyword_search(records, plan, top_k)

    model = clap_embed.load_clap_model(device=device)
    query_emb = clap_embed.compute_text_embedding(model, semantic_text, device=device)

    with open(embeddings_path, encoding="utf-8") as fh:
        emb_data = json.load(fh)
    emb_lookup: dict[str, list[float]] = {
        item["path"]: item["embedding"] for item in emb_data.get("files", [])
    }

    # Build record-by-path lookup
    by_path: dict[str, dict[str, Any]] = {}
    for rec in records:
        p = _get_nested(rec, "source", "path") or ""
        if p:
            by_path[p] = rec

    scored: list[tuple[float, dict[str, Any]]] = []
    for path, rec in by_path.items():
        emb = emb_lookup.get(path)
        if emb is None:
            continue
        sim = clap_embed.cosine_similarity(query_emb, emb)
        scored.append((sim, rec))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"score": s, "record": r} for s, r in scored[:top_k]]


# ──────────────────────────────────────────────────────────────────────────────
# Hybrid search  (keyword filter → CLAP re-rank)
# ──────────────────────────────────────────────────────────────────────────────

def _hybrid_search(
    records: list[dict[str, Any]],
    plan: dict[str, Any],
    embeddings_path: str | Path,
    top_k: int,
    device: str,
) -> list[dict[str, Any]]:
    """Rule-based filter to get candidates, then CLAP re-rank."""
    # Step 1: keyword / structured filter (no top_k limit — keep all candidates)
    candidates = _keyword_search(records, plan, top_k=len(records))
    if not candidates:
        return []

    # If no embeddings, return keyword results
    if not embeddings_path or not Path(embeddings_path).exists():
        warnings.warn(
            "Embeddings file missing for hybrid search – returning keyword-only results.",
            stacklevel=2,
        )
        return candidates[:top_k]

    if not clap_embed.check_clap_available():
        warnings.warn("CLAP not installed – returning keyword-only results.", stacklevel=2)
        return candidates[:top_k]

    # Step 2: CLAP re-rank
    semantic_text = plan.get("semantic_text", "") or " ".join(plan.get("keywords", []))
    model = clap_embed.load_clap_model(device=device)
    query_emb = clap_embed.compute_text_embedding(model, semantic_text, device=device)

    with open(embeddings_path, encoding="utf-8") as fh:
        emb_data = json.load(fh)
    emb_lookup: dict[str, list[float]] = {
        item["path"]: item["embedding"] for item in emb_data.get("files", [])
    }

    reranked: list[tuple[float, dict[str, Any]]] = []
    for cand in candidates:
        rec = cand["record"]
        path = _get_nested(rec, "source", "path") or ""
        emb = emb_lookup.get(path)
        if emb is None:
            # Keep keyword score as fallback
            reranked.append((cand["score"] * 0.5, rec))
            continue
        sim = clap_embed.cosine_similarity(query_emb, emb)
        # Blend keyword score (40 %) with semantic score (60 %)
        blended = 0.4 * cand["score"] + 0.6 * sim
        reranked.append((blended, rec))

    reranked.sort(key=lambda x: x[0], reverse=True)
    return [{"score": s, "record": r} for s, r in reranked[:top_k]]


# ──────────────────────────────────────────────────────────────────────────────
# Result formatting
# ──────────────────────────────────────────────────────────────────────────────

def format_results(results: list[dict[str, Any]], query: str, strategy: str) -> str:
    """Return a nicely formatted table of search results.

    Parameters
    ----------
    results:
        Output of :func:`unified_search`.
    query:
        The original search query string.
    strategy:
        The strategy that was used (``"keyword"``, ``"semantic"``,
        or ``"hybrid"``).

    Returns
    -------
    str
        Multi-line formatted string ready for terminal output.
    """
    lines: list[str] = []
    lines.append(f'🔍 搜索: "{query}"')
    lines.append(f"📋 策略: {strategy}")
    lines.append(f"🎯 匹配: {len(results)} 个文件")
    lines.append("")

    if not results:
        lines.append("（无结果）")
        return "\n".join(lines)

    # Column widths
    num_w = max(3, len(str(len(results))))
    score_w = 6
    name_w = max(8, max(len(r.get("file_name", "")) for r in results))
    name_w = min(name_w, 40)  # cap for readability
    dur_w = 8
    bpm_w = 5
    tag_w = 20

    # Header
    header = (
        f" {'#':>{num_w}} | {'分数':^{score_w}} | {'文件名':<{name_w}}"
        f" | {'时长':^{dur_w}} | {'BPM':^{bpm_w}} | {'标签':<{tag_w}}"
    )
    sep = (
        f" {'-' * num_w}-+-{'-' * score_w}-+-{'-' * name_w}"
        f"-+-{'-' * dur_w}-+-{'-' * bpm_w}-+-{'-' * tag_w}"
    )
    lines.append(header)
    lines.append(sep)

    for i, r in enumerate(results, 1):
        name = r.get("file_name", "")
        if len(name) > name_w:
            name = name[: name_w - 1] + "…"
        score = r.get("score", 0.0)
        meta = r.get("metadata", {})
        duration = meta.get("duration")
        bpm = meta.get("bpm")
        tags = meta.get("tags", [])

        dur_str = f"{duration:.1f}s" if duration is not None else "-"
        bpm_str = str(int(bpm)) if bpm is not None else "-"
        tag_str = ", ".join(tags) if tags else "-"
        if len(tag_str) > tag_w:
            tag_str = tag_str[: tag_w - 1] + "…"

        row = (
            f" {i:>{num_w}} | {score:^{score_w}.2f} | {name:<{name_w}}"
            f" | {dur_str:>{dur_w}} | {bpm_str:>{bpm_w}} | {tag_str:<{tag_w}}"
        )
        lines.append(row)

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

def _to_result(scored: dict[str, Any]) -> dict[str, Any]:
    """Convert internal ``{score, record}`` to the public result format."""
    rec: dict[str, Any] = scored["record"]
    score: float = scored["score"]

    file_name = _get_nested(rec, "source", "file_name") or rec.get("file_name", "")
    path = _get_nested(rec, "source", "path") or rec.get("source_path", "")

    duration = _get_nested(rec, "technical", "duration_sec")
    bpm = _get_nested(rec, "features", "tempo_bpm")
    tags = _get_nested(rec, "retrieval", "tags") or []
    mood = _get_nested(rec, "retrieval", "mood")
    texture = _get_nested(rec, "retrieval", "texture")
    is_loop = _get_nested(rec, "derived", "is_loop")
    brightness = _get_nested(rec, "derived", "brightness")

    metadata: dict[str, Any] = {
        "duration": duration,
        "bpm": bpm,
        "tags": list(tags) if isinstance(tags, list) else [],
        "mood": mood,
        "texture": texture,
        "is_loop": is_loop,
        "brightness": brightness,
    }

    return {
        "path": path,
        "file_name": file_name,
        "score": round(score, 4),
        "metadata": metadata,
    }


def _get_nested(record: dict[str, Any], *keys: str) -> Any:
    """Safe nested dict access."""
    current: Any = record
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _field_contains(value: Any, needle: str) -> bool:
    """Check whether *needle* appears in *value* (case-insensitive)."""
    if isinstance(value, str):
        return needle in value.lower()
    if isinstance(value, list):
        return any(isinstance(item, str) and needle in item.lower() for item in value)
    if isinstance(value, bool):
        return needle in str(value).lower()
    return False
