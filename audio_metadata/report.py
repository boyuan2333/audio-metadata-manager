"""Library report generation module.

Computes aggregate statistics over a library JSON file (schema v1):
  - total files
  - format / duration / type distributions
  - tag coverage (auto-tag, semantic, review)
  - embedding coverage (ready / missing)
  - category heatmap (top 10 retrieval.tags)
  - actionable warnings
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

# ── duration buckets ────────────────────────────────────────────────
_DURATION_BUCKETS: list[tuple[str, float | None, float | None]] = [
    ("<1s", None, 1.0),
    ("1-5s", 1.0, 5.0),
    ("5-30s", 5.0, 30.0),
    (">30s", 30.0, None),
]


def _bucket_for(duration: float | None) -> str | None:
    """Return the bucket label for a duration value, or None if unknown."""
    if duration is None:
        return None
    for label, lo, hi in _DURATION_BUCKETS:
        lo_ok = lo is None or duration >= lo
        hi_ok = hi is None or duration < hi
        if lo_ok and hi_ok:
            return label
    return None


# ── public API ──────────────────────────────────────────────────────

def generate_report(
    library_path: str,
    embeddings_path: str | None = None,
) -> dict[str, Any]:
    """Compute library statistics from a schema-v1 JSON file.

    Parameters
    ----------
    library_path:
        Path to the library JSON file (``{"files": [...]}``).
    embeddings_path:
        Optional path to an embeddings JSON file. When provided the
        report includes *embedding_coverage* (ready / missing counts).

    Returns
    -------
    dict with keys: ``total_files``, ``format_distribution``,
    ``duration_distribution``, ``type_distribution``, ``tag_coverage``,
    ``embedding_coverage``, ``category_heatmap``, ``warnings``.
    """
    library_path_obj = Path(library_path)
    with library_path_obj.open("r", encoding="utf-8-sig") as fh:
        payload: dict[str, Any] = json.load(fh)

    records: list[dict[str, Any]] = payload.get("files") or payload.get("records") or []

    # ── embeddings index (optional) ─────────────────────────────────
    embedding_paths: set[str] | None = None
    if embeddings_path is not None:
        emb_path = Path(embeddings_path)
        with emb_path.open("r", encoding="utf-8-sig") as fh:
            emb_payload: dict[str, Any] = json.load(fh)
        emb_files: list[dict[str, Any]] = emb_payload.get("files") or []
        embedding_paths = {
            entry.get("path", "") for entry in emb_files if entry.get("path")
        }

    total = len(records)

    # ── accumulators ────────────────────────────────────────────────
    fmt_counter: Counter[str] = Counter()
    dur_buckets: Counter[str] = Counter()
    loop_count = 0
    one_shot_count = 0
    auto_tagged = 0
    semantic_tagged = 0
    review_tagged = 0
    embedding_ready = 0
    embedding_missing = 0
    tag_counter: Counter[str] = Counter()
    warnings: list[str] = []

    for rec in records:
        source = rec.get("source") or {}
        technical = rec.get("technical") or {}
        derived = rec.get("derived") or {}
        retrieval = rec.get("retrieval") or {}
        model_outputs = rec.get("model_outputs") or {}
        review = rec.get("review") or {}

        # format
        fmt = (source.get("file_format") or "").lower()
        if fmt:
            fmt_counter[fmt] += 1

        # duration
        dur = technical.get("duration_sec")
        bucket = _bucket_for(dur)
        if bucket:
            dur_buckets[bucket] += 1
        else:
            dur_buckets["unknown"] += 1

        # type (loop vs one-shot)
        is_loop = derived.get("is_loop")
        if is_loop is True:
            loop_count += 1
        else:
            one_shot_count += 1

        # tag coverage
        auto_tags = model_outputs.get("auto_tags") or retrieval.get("auto_tags") or []
        if auto_tags:
            auto_tagged += 1

        sem_tags = retrieval.get("semantic_tags") or []
        if sem_tags:
            semantic_tagged += 1

        review_overrides = review.get("overrides") if isinstance(review, dict) else None
        review_notes = review.get("notes") if isinstance(review, dict) else None
        has_review = bool(review_overrides) or bool(review_notes)
        if has_review:
            review_tagged += 1

        # embedding coverage (from retrieval.embedding_status)
        emb_status = retrieval.get("embedding_status")
        if emb_status == "ready":
            embedding_ready += 1
        elif emb_status in ("missing", None, ""):
            # count as missing only if we have some embedding context
            pass  # handled below

        # category heatmap from retrieval.tags
        tags = retrieval.get("tags") or []
        for t in tags:
            if isinstance(t, str):
                tag_counter[t] += 1

        # ── warnings ───────────────────────────────────────────────
        fname = source.get("file_name") or rec.get("file_name") or rec.get("id", "unknown")
        if dur is None:
            warnings.append(f"{fname}: missing duration")
        if not tags and not sem_tags and not auto_tags:
            warnings.append(f"{fname}: no tags (auto/semantic/manual)")

    # embedding coverage from the embeddings file if provided
    if embedding_paths is not None:
        for rec in records:
            source = rec.get("source") or {}
            rec_path = source.get("path") or ""
            if rec_path in embedding_paths:
                embedding_ready += 1
            else:
                embedding_missing += 1
    else:
        # Count based on retrieval.embedding_status
        for rec in records:
            retrieval = rec.get("retrieval") or {}
            emb_status = retrieval.get("embedding_status")
            if emb_status == "ready":
                pass  # already counted above
            elif emb_status == "missing":
                embedding_missing += 1

    # top 10 categories
    category_heatmap = dict(tag_counter.most_common(10))

    # ── assemble report ─────────────────────────────────────────────
    report: dict[str, Any] = {
        "total_files": total,
        "format_distribution": dict(fmt_counter),
        "duration_distribution": {
            "<1s": dur_buckets.get("<1s", 0),
            "1-5s": dur_buckets.get("1-5s", 0),
            "5-30s": dur_buckets.get("5-30s", 0),
            ">30s": dur_buckets.get(">30s", 0),
        },
        "type_distribution": {
            "loop": loop_count,
            "one_shot": one_shot_count,
        },
        "tag_coverage": {
            "auto_tag": auto_tagged,
            "auto_tag_pct": round(auto_tagged / total * 100, 1) if total else 0.0,
            "semantic": semantic_tagged,
            "semantic_pct": round(semantic_tagged / total * 100, 1) if total else 0.0,
            "review": review_tagged,
            "review_pct": round(review_tagged / total * 100, 1) if total else 0.0,
        },
        "embedding_coverage": {
            "ready": embedding_ready,
            "missing": embedding_missing,
        },
        "category_heatmap": category_heatmap,
        "warnings": warnings,
    }
    return report


# ── formatting ──────────────────────────────────────────────────────

def format_report(stats: dict[str, Any]) -> str:
    """Format a report dict (from :func:`generate_report`) into a readable string."""
    lines: list[str] = []

    lines.append("=" * 60)
    lines.append("  LIBRARY REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Total files
    lines.append(f"  Total files: {stats['total_files']}")
    lines.append("")

    # Format distribution
    lines.append("  Format Distribution")
    lines.append("  " + "-" * 40)
    for fmt, count in sorted(stats.get("format_distribution", {}).items()):
        lines.append(f"    {fmt:<12} {count:>6}")
    lines.append("")

    # Duration distribution
    lines.append("  Duration Distribution")
    lines.append("  " + "-" * 40)
    for bucket in ("<1s", "1-5s", "5-30s", ">30s"):
        count = stats.get("duration_distribution", {}).get(bucket, 0)
        lines.append(f"    {bucket:<12} {count:>6}")
    lines.append("")

    # Type distribution
    lines.append("  Type Distribution")
    lines.append("  " + "-" * 40)
    td = stats.get("type_distribution", {})
    lines.append(f"    {'loop':<12} {td.get('loop', 0):>6}")
    lines.append(f"    {'one-shot':<12} {td.get('one_shot', 0):>6}")
    lines.append("")

    # Tag coverage
    lines.append("  Tag Coverage")
    lines.append("  " + "-" * 40)
    tc = stats.get("tag_coverage", {})
    lines.append(
        f"    auto-tag:    {tc.get('auto_tag', 0):>4}  ({tc.get('auto_tag_pct', 0):.1f}%)"
    )
    lines.append(
        f"    semantic:    {tc.get('semantic', 0):>4}  ({tc.get('semantic_pct', 0):.1f}%)"
    )
    lines.append(
        f"    review:      {tc.get('review', 0):>4}  ({tc.get('review_pct', 0):.1f}%)"
    )
    lines.append("")

    # Embedding coverage
    lines.append("  Embedding Coverage")
    lines.append("  " + "-" * 40)
    ec = stats.get("embedding_coverage", {})
    lines.append(f"    ready:       {ec.get('ready', 0):>4}")
    lines.append(f"    missing:     {ec.get('missing', 0):>4}")
    lines.append("")

    # Category heatmap
    lines.append("  Category Heatmap (top 10)")
    lines.append("  " + "-" * 40)
    for tag, count in stats.get("category_heatmap", {}).items():
        lines.append(f"    {tag:<20} {count:>6}")
    lines.append("")

    # Warnings
    warnings = stats.get("warnings", [])
    if warnings:
        lines.append(f"  Warnings ({len(warnings)})")
        lines.append("  " + "-" * 40)
        for w in warnings:
            lines.append(f"    ⚠ {w}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)
