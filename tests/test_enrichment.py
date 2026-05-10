"""
Unit tests for v0.1-b7 metadata enrichment layer.

Tests cover:
- enrich_payload() pure logic
- embedding coverage status
- semantic tag scoring
"""

import pytest
from audio_metadata.enrichment import enrich_payload


def _payload_one_record():
    return {
        "schema_version": 1,
        "app_version": "test",
        "run": {},
        "files": [
            {
                "id": "rec-1",
                "status": "ok",
                "source": {
                    "path": "audio/warm_guitar.wav",
                    "file_name": "warm_guitar.wav",
                    "file_format": "wav",
                },
            }
        ],
    }


class TestEmbeddingNotRequested:
    """Tests for embedding_status when no embeddings provided."""

    def test_enrich_marks_embedding_not_requested_without_embeddings(self):
        """Without embeddings_data, all records should be not_requested."""
        enriched, summary = enrich_payload(_payload_one_record())

        record = enriched["files"][0]
        assert record["retrieval"]["embedding_status"] == "not_requested"
        assert record["retrieval"]["embedding_ref"] is None
        assert summary["records"] == 1
        assert summary["embeddings_not_requested"] == 1


class TestEmbeddingReady:
    """Tests for embedding_status when path matches."""

    def test_enrich_marks_embedding_ready_when_path_matches(self):
        """Exact path match should result in ready status."""
        embeddings_data = {
            "model": "laion-audioclip-full-2022",
            "embedding_dim": 512,
            "files": [
                {
                    "path": "audio/warm_guitar.wav",
                    "embedding": [0.1] * 512,
                }
            ],
        }

        enriched, summary = enrich_payload(
            _payload_one_record(),
            embeddings_data=embeddings_data,
        )

        record = enriched["files"][0]
        assert record["retrieval"]["embedding_status"] == "ready"
        assert record["retrieval"]["embedding_model"] == "laion-audioclip-full-2022"
        assert record["retrieval"]["embedding_ref"] == "embeddings.json#audio/warm_guitar.wav"
        assert summary["embeddings_ready"] == 1
