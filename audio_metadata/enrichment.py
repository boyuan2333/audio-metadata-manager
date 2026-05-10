"""v0.1-b7 Metadata Enrichment Layer.

Combines indexed metadata, embedding coverage, and controlled semantic tags
into an enriched library payload. Does NOT load CLAP models — only reads
pre-computed embeddings from a JSON file.

Usage:
    from audio_metadata.enrichment import enrich_payload
    enriched, summary = enrich_payload(payload, embeddings_data=..., vocabulary_data=...)
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from audio_metadata.schema import normalize_payload_schema_v1

EMBEDDING_MODEL_DEFAULT = "laion-audioclip-full-2022"
EMBEDDING_DIM_DEFAULT = 512


def enrich_payload(
    payload: dict[str, Any],
    *,
    embeddings_data: dict[str, Any] | None = None,
    vocabulary_data: dict[str, Any] | None = None,
    semantic_tags: bool = False,
    threshold: float = 0.25,
    top_n: int = 5,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Enrich a library payload with embedding coverage and semantic tags.

    Args:
        payload: Normalized library JSON (schema v1).
        embeddings_data: Pre-computed CLAP embeddings JSON. None = skip embedding coverage.
        vocabulary_data: Semantic vocabulary with text embeddings. None = skip semantic tags.
        semantic_tags: Enable semantic tag scoring.
        threshold: Default cosine similarity threshold for semantic tags.
        top_n: Max semantic tags per record.

    Returns:
        (enriched_payload, summary_dict)
    """
    enriched = normalize_payload_schema_v1(deepcopy(payload))
    records = enriched["files"]
    summary: dict[str, Any] = {
        "records": len(records),
        "embeddings_ready": 0,
        "embeddings_missing": 0,
        "embeddings_invalid": 0,
        "embeddings_not_requested": 0,
        "semantic_tags_added": 0,
    }

    # No embeddings provided — mark all as not_requested
    if embeddings_data is None:
        for record in records:
            record["retrieval"]["embedding_status"] = "not_requested"
        summary["embeddings_not_requested"] = len(records)
        return enriched, summary

    # Build lookup indexes
    by_path, by_filename = _build_embedding_lookups(embeddings_data)
    model_name = embeddings_data.get("model") or EMBEDDING_MODEL_DEFAULT

    for record in records:
        path = _record_path(record)
        filename = _record_filename(record)
        item = by_path.get(path or "") or by_filename.get(filename or "")

        if item is None:
            record["retrieval"]["embedding_status"] = "missing"
            summary["embeddings_missing"] += 1
            continue

        if not _is_valid_embedding(item):
            record["retrieval"]["embedding_status"] = "invalid"
            record["retrieval"]["embedding_model"] = model_name
            summary["embeddings_invalid"] += 1
            continue

        record["retrieval"]["embedding_status"] = "ready"
        record["retrieval"]["embedding_model"] = model_name
        record["retrieval"]["embedding_ref"] = f"embeddings.json#{item['path']}"
        summary["embeddings_ready"] += 1

        # Semantic tag scoring (only for ready embeddings)
        if semantic_tags and vocabulary_data:
            tag_scores = _score_semantic_tags(
                item["embedding"],
                vocabulary_data,
                default_threshold=threshold,
                top_n=top_n,
            )
            if tag_scores:
                tags = list(tag_scores.keys())
                record["retrieval"]["semantic_tags"] = tags
                record["model_outputs"]["semantic_tags"] = tags
                record["model_outputs"]["semantic_tags_confidence"] = tag_scores
                record["model_outputs"]["classifier_version"] = "v0.1-b7-enrichment"
                record["model_outputs"]["classifier_type"] = "hybrid_metadata_enrichment"
                summary["semantic_tags_added"] += len(tags)

    return enriched, summary


def _build_embedding_lookups(
    embeddings_data: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Build path→item and filename→item lookup dicts."""
    by_path: dict[str, dict[str, Any]] = {}
    by_filename: dict[str, dict[str, Any]] = {}
    for item in embeddings_data.get("files", []):
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        if isinstance(path, str):
            by_path[path] = item
            by_filename.setdefault(Path(path).name, item)
    return by_path, by_filename


def _record_path(record: dict[str, Any]) -> str | None:
    source = record.get("source") if isinstance(record.get("source"), dict) else {}
    path = source.get("path")
    return path if isinstance(path, str) else None


def _record_filename(record: dict[str, Any]) -> str | None:
    source = record.get("source") if isinstance(record.get("source"), dict) else {}
    file_name = source.get("file_name")
    return file_name if isinstance(file_name, str) else None


def _is_valid_embedding(
    item: dict[str, Any], expected_dim: int = EMBEDDING_DIM_DEFAULT
) -> bool:
    """Check that the embedding is a list of correct dimension with numeric values."""
    embedding = item.get("embedding")
    if not isinstance(embedding, list):
        return False
    if len(embedding) != expected_dim:
        return False
    return all(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        for value in embedding
    )


def _is_embedding_vector(
    value: Any, expected_dim: int = EMBEDDING_DIM_DEFAULT
) -> bool:
    """Check that a value is a valid embedding vector (for vocabulary text embeddings)."""
    if not isinstance(value, list) or len(value) != expected_dim:
        return False
    return all(
        isinstance(item, (int, float)) and not isinstance(item, bool)
        for item in value
    )


def _score_semantic_tags(
    audio_embedding: list[float],
    vocabulary_data: dict[str, Any],
    *,
    default_threshold: float,
    top_n: int,
) -> dict[str, float]:
    """Score audio embedding against vocabulary text embeddings.

    Returns dict of {tag: score} for tags above threshold, sorted descending.
    """
    from audio_metadata.clap_embed import cosine_similarity

    scored: list[tuple[str, float]] = []
    for prompt in vocabulary_data.get("prompts", []):
        if not isinstance(prompt, dict):
            continue
        tag = prompt.get("tag")
        text_embedding = prompt.get("embedding")
        if not isinstance(tag, str) or not isinstance(text_embedding, list):
            continue
        if not _is_embedding_vector(text_embedding):
            continue
        score = cosine_similarity(audio_embedding, text_embedding)
        tag_threshold = prompt.get("threshold", default_threshold)
        if not isinstance(tag_threshold, (int, float)) or isinstance(tag_threshold, bool):
            tag_threshold = default_threshold
        if score >= float(tag_threshold):
            scored.append((tag, round(float(score), 3)))

    scored.sort(key=lambda item: item[1], reverse=True)
    return dict(scored[:top_n])
