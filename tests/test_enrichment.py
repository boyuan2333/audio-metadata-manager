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


class TestEmbeddingMissing:
    """Tests for embedding_status when no match found."""

    def test_enrich_marks_embedding_missing_when_no_match(self):
        """No matching embedding should result in missing status."""
        embeddings_data = {
            "model": "laion-audioclip-full-2022",
            "embedding_dim": 512,
            "files": [
                {"path": "audio/other.wav", "embedding": [0.1] * 512}
            ],
        }

        enriched, summary = enrich_payload(
            _payload_one_record(), embeddings_data=embeddings_data
        )

        record = enriched["files"][0]
        assert record["retrieval"]["embedding_status"] == "missing"
        assert summary["embeddings_missing"] == 1


class TestEmbeddingInvalid:
    """Tests for embedding_status when dimension is wrong."""

    def test_enrich_marks_embedding_invalid_when_dimension_is_wrong(self):
        """Wrong dimension embedding should result in invalid status."""
        embeddings_data = {
            "model": "laion-audioclip-full-2022",
            "embedding_dim": 512,
            "files": [
                {"path": "audio/warm_guitar.wav", "embedding": [0.1] * 3}
            ],
        }

        enriched, summary = enrich_payload(
            _payload_one_record(), embeddings_data=embeddings_data
        )

        record = enriched["files"][0]
        assert record["retrieval"]["embedding_status"] == "invalid"
        assert record["retrieval"]["embedding_model"] == "laion-audioclip-full-2022"
        assert summary["embeddings_invalid"] == 1

    def test_enrich_marks_embedding_invalid_when_not_a_list(self):
        """Non-list embedding should result in invalid status."""
        embeddings_data = {
            "model": "laion-audioclip-full-2022",
            "embedding_dim": 512,
            "files": [
                {"path": "audio/warm_guitar.wav", "embedding": "not_a_list"}
            ],
        }

        enriched, summary = enrich_payload(
            _payload_one_record(), embeddings_data=embeddings_data
        )

        record = enriched["files"][0]
        assert record["retrieval"]["embedding_status"] == "invalid"
        assert summary["embeddings_invalid"] == 1


class TestEmbeddingFilenameFallback:
    """Tests for filename-based embedding matching."""

    def test_enrich_matches_embedding_by_filename_fallback(self):
        """When path doesn't match but filename does, should be ready."""
        embeddings_data = {
            "model": "laion-audioclip-full-2022",
            "embedding_dim": 512,
            "files": [
                {"path": "/mnt/d/samples/warm_guitar.wav", "embedding": [0.1] * 512}
            ],
        }

        enriched, summary = enrich_payload(
            _payload_one_record(), embeddings_data=embeddings_data
        )

        record = enriched["files"][0]
        assert record["retrieval"]["embedding_status"] == "ready"
        assert summary["embeddings_ready"] == 1

    def test_enrich_prefers_exact_path_over_filename(self):
        """Exact path match should be preferred over filename match."""
        embeddings_data = {
            "model": "laion-audioclip-full-2022",
            "embedding_dim": 512,
            "files": [
                {"path": "audio/warm_guitar.wav", "embedding": [1.0] * 512},
                {"path": "/other/warm_guitar.wav", "embedding": [0.5] * 512},
            ],
        }

        enriched, summary = enrich_payload(
            _payload_one_record(), embeddings_data=embeddings_data
        )

        record = enriched["files"][0]
        assert record["retrieval"]["embedding_status"] == "ready"
        # Should use the exact path match
        assert record["retrieval"]["embedding_ref"] == "embeddings.json#audio/warm_guitar.wav"


class TestSemanticTagScoring:
    """Tests for semantic tag scoring against vocabulary."""

    def test_enrich_adds_semantic_tags_above_threshold(self):
        """Tags above threshold should be written to record."""
        embeddings_data = {
            "model": "laion-audioclip-full-2022",
            "embedding_dim": 512,
            "files": [
                {"path": "audio/warm_guitar.wav", "embedding": [1.0] + [0.0] * 511}
            ],
        }
        vocabulary_data = {
            "version": "test-vocab",
            "prompts": [
                {
                    "tag": "warm guitar",
                    "category": "instrument_texture",
                    "text": "warm guitar",
                    "threshold": 0.5,
                    "embedding": [1.0] + [0.0] * 511,
                }
            ],
        }

        enriched, summary = enrich_payload(
            _payload_one_record(),
            embeddings_data=embeddings_data,
            vocabulary_data=vocabulary_data,
            semantic_tags=True,
        )

        record = enriched["files"][0]
        assert record["retrieval"]["semantic_tags"] == ["warm guitar"]
        assert record["model_outputs"]["semantic_tags"] == ["warm guitar"]
        assert record["model_outputs"]["semantic_tags_confidence"]["warm guitar"] == 1.0
        assert record["model_outputs"]["classifier_version"] == "v0.1-b7-enrichment"
        assert record["model_outputs"]["classifier_type"] == "hybrid_metadata_enrichment"
        assert summary["semantic_tags_added"] == 1

    def test_enrich_skips_semantic_tags_below_threshold(self):
        """Tags below threshold should not be written."""
        embeddings_data = {
            "model": "laion-audioclip-full-2022",
            "embedding_dim": 512,
            "files": [
                {"path": "audio/warm_guitar.wav", "embedding": [1.0] + [0.0] * 511}
            ],
        }
        vocabulary_data = {
            "version": "test-vocab",
            "prompts": [
                {
                    "tag": "dark pad",
                    "category": "role_texture",
                    "text": "dark pad",
                    "threshold": 0.9,
                    "embedding": [0.0, 1.0] + [0.0] * 510,
                }
            ],
        }

        enriched, summary = enrich_payload(
            _payload_one_record(),
            embeddings_data=embeddings_data,
            vocabulary_data=vocabulary_data,
            semantic_tags=True,
        )

        record = enriched["files"][0]
        assert record["retrieval"]["semantic_tags"] == []
        assert record["model_outputs"]["semantic_tags"] == []
        assert summary["semantic_tags_added"] == 0

    def test_enrich_respects_top_n_limit(self):
        """Should limit semantic tags to top_n."""
        embeddings_data = {
            "model": "laion-audioclip-full-2022",
            "embedding_dim": 512,
            "files": [
                {"path": "audio/warm_guitar.wav", "embedding": [1.0] + [0.0] * 511}
            ],
        }
        # All tags will have score 1.0 (identical vectors)
        vocabulary_data = {
            "version": "test-vocab",
            "prompts": [
                {"tag": f"tag-{i}", "text": f"tag-{i}", "threshold": 0.1, "embedding": [1.0] + [0.0] * 511}
                for i in range(10)
            ],
        }

        enriched, summary = enrich_payload(
            _payload_one_record(),
            embeddings_data=embeddings_data,
            vocabulary_data=vocabulary_data,
            semantic_tags=True,
            top_n=3,
        )

        record = enriched["files"][0]
        assert len(record["retrieval"]["semantic_tags"]) == 3
        assert summary["semantic_tags_added"] == 3

    def test_enrich_no_semantic_tags_without_flag(self):
        """semantic_tags=False should skip scoring entirely."""
        embeddings_data = {
            "model": "laion-audioclip-full-2022",
            "embedding_dim": 512,
            "files": [
                {"path": "audio/warm_guitar.wav", "embedding": [1.0] + [0.0] * 511}
            ],
        }
        vocabulary_data = {
            "version": "test-vocab",
            "prompts": [
                {"tag": "guitar", "text": "guitar", "threshold": 0.1, "embedding": [1.0] + [0.0] * 511}
            ],
        }

        enriched, summary = enrich_payload(
            _payload_one_record(),
            embeddings_data=embeddings_data,
            vocabulary_data=vocabulary_data,
            semantic_tags=False,  # disabled
        )

        record = enriched["files"][0]
        assert record["retrieval"]["semantic_tags"] == []
        assert summary["semantic_tags_added"] == 0
