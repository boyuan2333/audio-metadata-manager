"""CLAP embedding computation for semantic search (v0.1-b6).

This module computes audio embeddings using the pre-trained CLAP model.
CLAP (Contrastive Language-Audio Pretraining) maps audio and text to the same
embedding space, enabling semantic search without training data.

Reference: https://github.com/LAION-AI/CLAP
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tqdm import tqdm


# CLAP model info
CLAP_MODEL_NAME = "laion-audioclip-full-2022"
CLAP_EMBEDDING_DIM = 512


def check_clap_available() -> bool:
    """Check if CLAP is installed."""
    try:
        from laion_clap.hook import CLAP_Module  # noqa: F401
        return True
    except ImportError:
        return False


def load_clap_model(model_name: str = CLAP_MODEL_NAME, device: str = "cpu"):
    """Load pre-trained CLAP model.
    
    Args:
        model_name: Ignored for laion_clap (uses default checkpoint)
        device: "cpu" or "cuda"
        
    Returns:
        CLAP model instance
        
    Raises:
        ImportError: If CLAP not installed
    """
    try:
        from laion_clap.hook import CLAP_Module
        
        model = CLAP_Module(enable_fusion=False, device=device)
        model.load_ckpt()  # Uses default checkpoint (downloads if needed)
        
        return model
    except ImportError as e:
        raise ImportError(
            "CLAP not installed. Install with: pip install -r requirements-optional.txt"
        ) from e


def compute_audio_embedding(model, audio_path: str | Path, device: str = "cpu") -> list[float]:
    """Compute embedding for a single audio file.
    
    Args:
        model: CLAP model instance (laion_clap.CLAP_Module)
        audio_path: Path to audio file
        device: "cpu" or "cuda"
        
    Returns:
        512-dimensional embedding as list of floats
    """
    import torch
    
    # CLAP expects file path list
    audio_paths = [str(audio_path)]
    
    # Compute embedding (laion_clap API)
    with torch.no_grad():
        embedding = model.get_audio_embedding_from_filelist(audio_paths)
    
    # Convert to list of floats (embedding is already on CPU)
    if hasattr(embedding, 'cpu'):
        embedding = embedding.cpu()
    if hasattr(embedding, 'numpy'):
        embedding = embedding.numpy()
    
    return embedding[0].tolist()


def compute_text_embedding(model, text: str, device: str = "cpu") -> list[float]:
    """Compute embedding for a text query.
    
    Args:
        model: CLAP model instance (laion_clap.CLAP_Module)
        text: Text query
        device: "cpu" or "cuda"
        
    Returns:
        512-dimensional embedding as list of floats
    """
    import torch
    
    # Compute embedding (laion_clap API)
    with torch.no_grad():
        embedding = model.get_text_embedding([text])
    
    # Convert to list of floats
    if hasattr(embedding, 'cpu'):
        embedding = embedding.cpu()
    if hasattr(embedding, 'numpy'):
        embedding = embedding.numpy()
    
    return embedding[0].tolist()


def compute_embeddings_batch(
    audio_files: list[str | Path],
    output_json: str | Path,
    *,
    model_name: str = CLAP_MODEL_NAME,
    device: str = "cpu",
    append: bool = False,
    verbose: bool = True,
) -> dict[str, Any]:
    """Compute CLAP embeddings for multiple audio files.
    
    Args:
        audio_files: List of audio file paths
        output_json: Path to output JSON file
        model_name: CLAP model name
        device: "cpu" or "cuda"
        append: If True, append to existing embeddings
        verbose: Print progress
        
    Returns:
        Dict with computation statistics
    """
    # Load model
    if verbose:
        print(f"Loading CLAP model ({model_name})...")
    model = load_clap_model(model_name, device)
    
    # Load existing embeddings if appending
    existing_data = None
    if append and Path(output_json).exists():
        with open(output_json, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
        if verbose:
            print(f"Loaded {len(existing_data.get('files', []))} existing embeddings")
    
    # Compute embeddings
    embeddings = []
    failed = []
    
    iterator = tqdm(audio_files, desc="Computing embeddings") if verbose else audio_files
    
    for audio_path in iterator:
        try:
            embedding = compute_audio_embedding(model, audio_path, device)
            embeddings.append({
                "path": str(audio_path),
                "embedding": embedding,
            })
        except Exception as e:
            failed.append({
                "path": str(audio_path),
                "error": str(e),
            })
            if verbose:
                print(f"\nFailed: {audio_path} — {e}")
    
    # Build output
    output_data = {
        "model": model_name,
        "embedding_dim": CLAP_EMBEDDING_DIM,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "files": embeddings,
    }
    
    # Merge with existing if appending
    if existing_data:
        # Avoid duplicates by path
        existing_paths = {f["path"] for f in existing_data.get("files", [])}
        new_embeddings = [e for e in embeddings if e["path"] not in existing_paths]
        
        output_data = {
            **existing_data,
            "files": existing_data.get("files", []) + new_embeddings,
            "computed_at": datetime.now(timezone.utc).isoformat(),  # Update timestamp
        }
    
    # Write output
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    
    return {
        "total_files": len(audio_files),
        "successful": len(embeddings),
        "failed": len(failed),
        "output_file": str(output_path),
        "total_embeddings": len(output_data["files"]),
        "failed_files": failed,
    }


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors.
    
    Args:
        a: First vector
        b: Second vector
        
    Returns:
        Cosine similarity (0-1, higher = more similar)
    """
    import numpy as np
    
    a_vec = np.array(a)
    b_vec = np.array(b)
    
    dot_product = np.dot(a_vec, b_vec)
    norm_a = np.linalg.norm(a_vec)
    norm_b = np.linalg.norm(b_vec)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(dot_product / (norm_a * norm_b))


def search_similar(
    query_embedding: list[float],
    embeddings_json: str | Path,
    *,
    top_k: int = 10,
    threshold: float = 0.0,
) -> list[dict[str, Any]]:
    """Search for similar audio embeddings.
    
    Args:
        query_embedding: Query vector (512-dim)
        embeddings_json: Path to embeddings JSON
        top_k: Number of results to return
        threshold: Minimum similarity score
        
    Returns:
        List of results with path, similarity score, and embedding
    """
    # Load embeddings
    with open(embeddings_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    files = data.get("files", [])
    
    # Compute similarities
    results = []
    for file_data in files:
        similarity = cosine_similarity(query_embedding, file_data["embedding"])
        if similarity >= threshold:
            results.append({
                "path": file_data["path"],
                "similarity": similarity,
                "embedding": file_data["embedding"],
            })
    
    # Sort by similarity (descending)
    results.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Return top-K
    return results[:top_k]
