"""Hybrid search combining rule-based filtering and CLAP semantic search (v0.1-b6).

This module integrates natural language query parsing with CLAP embeddings
for more accurate audio retrieval.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import audio_metadata.clap_embed as clap_embed
from audio_metadata.nl_query import parse_nl_query


def hybrid_search(
    query: str,
    library_json: str | Path,
    embeddings_json: str | Path,
    *,
    top_k: int = 10,
    threshold: float = 0.0,
    device: str = "cpu",
) -> list[dict[str, Any]]:
    """Perform hybrid search combining rule-based and semantic search.
    
    Flow:
    1. Parse natural language query to extract explicit filters (BPM, duration, keywords)
    2. Apply rule-based filtering to get candidate set
    3. Use CLAP to re-rank candidates by semantic similarity
    4. Return top-K results
    
    Args:
        query: Natural language search query
        library_json: Path to library metadata JSON
        embeddings_json: Path to CLAP embeddings JSON
        top_k: Number of results to return
        threshold: Minimum CLAP similarity threshold
        device: "cpu" or "cuda" for CLAP model
        
    Returns:
        List of results with path, similarity score, and metadata
        
    Raises:
        FileNotFoundError: If library or embeddings file not found
        ImportError: If CLAP not available
    """
    # Check CLAP availability
    if not clap_embed.check_clap_available():
        raise ImportError("CLAP not installed. Install with: pip install -r requirements-optional.txt")
    
    # Load library
    library_path = Path(library_json)
    if not library_path.exists():
        raise FileNotFoundError(f"Library file not found: {library_path}")
    
    with open(library_path, "r", encoding="utf-8") as f:
        library = json.load(f)
    
    # Load embeddings
    embeddings_path = Path(embeddings_json)
    if not embeddings_path.exists():
        raise FileNotFoundError(f"Embeddings file not found: {embeddings_path}")
    
    with open(embeddings_path, "r", encoding="utf-8") as f:
        embeddings_data = json.load(f)
    
    # Build embeddings lookup
    embeddings_lookup = {item["path"]: item["embedding"] for item in embeddings_data.get("files", [])}
    
    # Parse query to extract explicit filters
    intent = parse_nl_query(query)
    
    # Step 1: Rule-based filtering
    candidates = []
    for record in library.get("files", []):
        if _matches_intent(record, intent):
            candidates.append(record)
    
    if not candidates:
        return []
    
    # Step 2: CLAP semantic re-ranking
    # Load model and compute text embedding
    model = clap_embed.load_clap_model(device=device)
    query_embedding = clap_embed.compute_text_embedding(model, query, device=device)
    
    # Compute similarity for each candidate
    results = []
    for candidate in candidates:
        path = candidate.get("path", "")
        if path not in embeddings_lookup:
            # Skip files without embeddings
            continue
        
        similarity = clap_embed.cosine_similarity(query_embedding, embeddings_lookup[path])
        
        if similarity >= threshold:
            results.append({
                "path": path,
                "similarity": similarity,
                "metadata": candidate,
            })
    
    # Sort by similarity (descending)
    results.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Return top-K
    return results[:top_k]


def _matches_intent(record: dict[str, Any], intent: dict[str, Any]) -> bool:
    """Check if a record matches the parsed query intent.
    
    Args:
        record: Audio metadata record
        intent: Parsed NL query intent
        
    Returns:
        True if record matches all explicit filters
    """
    # Keyword filter
    if intent.get("keyword"):
        keyword = intent["keyword"].lower()
        # Check filename and tags
        filename = record.get("filename", "").lower()
        tags = " ".join(record.get("tags", [])).lower()
        if keyword not in filename and keyword not in tags:
            return False
    
    # BPM filter
    tempo = record.get("tempo", {})
    if tempo:
        bpm = tempo.get("bpm")
        if bpm:
            if intent.get("min_bpm") and bpm < intent["min_bpm"]:
                return False
            if intent.get("max_bpm") and bpm > intent["max_bpm"]:
                return False
    
    # Duration filter
    duration = record.get("duration", {})
    if duration:
        dur_sec = duration.get("seconds")
        if dur_sec:
            if intent.get("min_duration") and dur_sec < intent["min_duration"]:
                return False
            if intent.get("max_duration") and dur_sec > intent["max_duration"]:
                return False
    
    # Status filter
    if intent.get("status"):
        review_status = record.get("review", {}).get("status")
        if review_status != intent["status"]:
            return False
    
    # Is loop filter
    if intent.get("is_loop") is not None:
        is_loop = record.get("is_loop")
        if is_loop != intent["is_loop"]:
            return False
    
    return True


def format_hybrid_results(results: list[dict[str, Any]], verbose: bool = False) -> str:
    """Format hybrid search results for display.
    
    Args:
        results: List of search results
        verbose: If True, show similarity scores and full metadata
        
    Returns:
        Formatted string for terminal output
    """
    if not results:
        return "No results found."
    
    lines = [f"\nFound {len(results)} result(s):\n"]
    
    for i, result in enumerate(results, 1):
        path = result["path"]
        similarity = result["similarity"]
        metadata = result.get("metadata", {})
        
        if verbose:
            lines.append(f"  {i}. [{similarity:.4f}] {path}")
            # Show key metadata
            if "tempo" in metadata and metadata["tempo"]:
                bpm = metadata["tempo"].get("bpm")
                if bpm:
                    lines.append(f"      BPM: {bpm}")
            if "duration" in metadata and metadata["duration"]:
                dur = metadata["duration"].get("seconds")
                if dur:
                    lines.append(f"      Duration: {dur:.1f}s")
        else:
            lines.append(f"  {i}. {path}")
    
    return "\n".join(lines)
