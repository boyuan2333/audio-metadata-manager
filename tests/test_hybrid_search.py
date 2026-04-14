"""Tests for hybrid search (v0.1-b6)."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import audio_metadata.hybrid_search as hybrid_search


class TestMatchesIntent:
    """Test rule-based filtering logic."""

    def test_keyword_match_filename(self):
        """Test keyword matching in filename."""
        record = {
            "filename": "dark_pad_120.wav",
            "tags": [],
        }
        intent = {"keyword": "dark"}
        
        assert hybrid_search._matches_intent(record, intent) is True

    def test_keyword_match_tags(self):
        """Test keyword matching in tags."""
        record = {
            "filename": "pad_120.wav",
            "tags": ["dark", "ambient"],
        }
        intent = {"keyword": "dark"}
        
        assert hybrid_search._matches_intent(record, intent) is True

    def test_keyword_no_match(self):
        """Test keyword not matching."""
        record = {
            "filename": "bright_pluck.wav",
            "tags": ["bright", "energetic"],
        }
        intent = {"keyword": "dark"}
        
        assert hybrid_search._matches_intent(record, intent) is False

    def test_bpm_filter_match(self):
        """Test BPM range filtering."""
        record = {
            "tempo": {"bpm": 120},
        }
        intent = {"min_bpm": 110, "max_bpm": 130}
        
        assert hybrid_search._matches_intent(record, intent) is True

    def test_bpm_filter_too_low(self):
        """Test BPM below range."""
        record = {
            "tempo": {"bpm": 100},
        }
        intent = {"min_bpm": 110, "max_bpm": 130}
        
        assert hybrid_search._matches_intent(record, intent) is False

    def test_bpm_filter_too_high(self):
        """Test BPM above range."""
        record = {
            "tempo": {"bpm": 140},
        }
        intent = {"min_bpm": 110, "max_bpm": 130}
        
        assert hybrid_search._matches_intent(record, intent) is False

    def test_duration_filter_match(self):
        """Test duration range filtering."""
        record = {
            "duration": {"seconds": 30},
        }
        intent = {"min_duration": 20, "max_duration": 40}
        
        assert hybrid_search._matches_intent(record, intent) is True

    def test_duration_filter_too_short(self):
        """Test duration too short."""
        record = {
            "duration": {"seconds": 10},
        }
        intent = {"min_duration": 20, "max_duration": 40}
        
        assert hybrid_search._matches_intent(record, intent) is False

    def test_status_filter_match(self):
        """Test status filtering."""
        record = {
            "review": {"status": "approved"},
        }
        intent = {"status": "approved"}
        
        assert hybrid_search._matches_intent(record, intent) is True

    def test_status_filter_no_match(self):
        """Test status not matching."""
        record = {
            "review": {"status": "pending"},
        }
        intent = {"status": "approved"}
        
        assert hybrid_search._matches_intent(record, intent) is False

    def test_is_loop_filter_match(self):
        """Test is_loop filtering."""
        record = {
            "is_loop": True,
        }
        intent = {"is_loop": True}
        
        assert hybrid_search._matches_intent(record, intent) is True

    def test_is_loop_filter_no_match(self):
        """Test is_loop not matching."""
        record = {
            "is_loop": False,
        }
        intent = {"is_loop": True}
        
        assert hybrid_search._matches_intent(record, intent) is False

    def test_multiple_filters_all_match(self):
        """Test multiple filters all matching."""
        record = {
            "filename": "dark_pad.wav",
            "tags": ["ambient"],
            "tempo": {"bpm": 120},
            "duration": {"seconds": 30},
            "review": {"status": "approved"},
        }
        intent = {
            "keyword": "dark",
            "min_bpm": 110,
            "max_bpm": 130,
            "min_duration": 20,
            "max_duration": 40,
            "status": "approved",
        }
        
        assert hybrid_search._matches_intent(record, intent) is True

    def test_multiple_filters_one_fails(self):
        """Test multiple filters with one failing."""
        record = {
            "filename": "dark_pad.wav",
            "tags": ["ambient"],
            "tempo": {"bpm": 100},  # Too low
            "duration": {"seconds": 30},
        }
        intent = {
            "keyword": "dark",
            "min_bpm": 110,
            "max_bpm": 130,
        }
        
        assert hybrid_search._matches_intent(record, intent) is False

    def test_empty_intent_always_matches(self):
        """Test empty intent matches everything."""
        record = {
            "filename": "anything.wav",
            "tempo": {"bpm": 120},
        }
        intent = {}
        
        assert hybrid_search._matches_intent(record, intent) is True


class TestHybridSearch:
    """Test hybrid search integration."""

    @pytest.fixture
    def sample_library(self, tmp_path):
        """Create sample library JSON."""
        library_data = {
            "schema_version": "v1",
            "created_at": "2026-04-14T00:00:00Z",
            "files": [
                {
                    "path": "/audio/dark_pad_120.wav",
                    "filename": "dark_pad_120.wav",
                    "tags": ["dark", "pad"],
                    "tempo": {"bpm": 120},
                    "duration": {"seconds": 30},
                },
                {
                    "path": "/audio/bright_pluck_140.wav",
                    "filename": "bright_pluck_140.wav",
                    "tags": ["bright", "pluck"],
                    "tempo": {"bpm": 140},
                    "duration": {"seconds": 15},
                },
                {
                    "path": "/audio/ambient_drone_90.wav",
                    "filename": "ambient_drone_90.wav",
                    "tags": ["ambient", "drone"],
                    "tempo": {"bpm": 90},
                    "duration": {"seconds": 60},
                },
            ],
        }
        
        library_file = tmp_path / "library.json"
        with open(library_file, "w") as f:
            json.dump(library_data, f)
        
        return library_file

    @pytest.fixture
    def sample_embeddings(self, tmp_path):
        """Create sample embeddings JSON."""
        embeddings_data = {
            "model": "laion-audioclip-full-2022",
            "embedding_dim": 512,
            "computed_at": "2026-04-14T00:00:00Z",
            "files": [
                {
                    "path": "/audio/dark_pad_120.wav",
                    "embedding": [0.7] * 256 + [-0.7] * 256,
                },
                {
                    "path": "/audio/bright_pluck_140.wav",
                    "embedding": [-0.7] * 256 + [0.7] * 256,
                },
                {
                    "path": "/audio/ambient_drone_90.wav",
                    "embedding": [0.5 if i % 2 == 0 else -0.5 for i in range(512)],
                },
            ],
        }
        
        embeddings_file = tmp_path / "embeddings.json"
        with open(embeddings_file, "w") as f:
            json.dump(embeddings_data, f)
        
        return embeddings_file

    def test_hybrid_search_basic(self, sample_library, sample_embeddings):
        """Test basic hybrid search."""
        mock_model = MagicMock()
        
        def create_mock_embedding(*args, **kwargs):
            import numpy as np
            embedding = np.array([[0.7] * 256 + [-0.7] * 256], dtype=np.float32)
            mock_tensor = MagicMock()
            mock_tensor.cpu.return_value = MagicMock(numpy=MagicMock(return_value=embedding))
            return mock_tensor
        
        mock_model.get_audio_embedding_from_filelist.side_effect = create_mock_embedding
        mock_model.get_text_embedding.return_value = create_mock_embedding(["dark pad"])
        
        with patch.object(hybrid_search.clap_embed, "load_clap_model", return_value=mock_model):
            results = hybrid_search.hybrid_search(
                "dark pad around 120 bpm",
                sample_library,
                sample_embeddings,
                top_k=2,
            )
        
        # Should find at least one result
        assert len(results) >= 1
        # First result should have path and similarity
        assert "path" in results[0]
        assert "similarity" in results[0]
        assert "metadata" in results[0]

    def test_hybrid_search_filters_by_bpm(self, sample_library, sample_embeddings):
        """Test hybrid search respects BPM filter."""
        mock_model = MagicMock()
        
        def create_mock_embedding(*args, **kwargs):
            import numpy as np
            embedding = np.array([[0.1] * 512], dtype=np.float32)
            mock_tensor = MagicMock()
            mock_tensor.cpu.return_value = MagicMock(numpy=MagicMock(return_value=embedding))
            return mock_tensor
        
        mock_model.get_text_embedding.return_value = create_mock_embedding(["120 bpm"])
        
        with patch.object(hybrid_search.clap_embed, "load_clap_model", return_value=mock_model):
            results = hybrid_search.hybrid_search(
                "120 bpm",
                sample_library,
                sample_embeddings,
                top_k=10,
            )
        
        # Should only find the 120 BPM track
        for result in results:
            metadata = result["metadata"]
            bpm = metadata.get("tempo", {}).get("bpm")
            if bpm:
                assert 110 <= bpm <= 130  # Reasonable range around 120

    def test_hybrid_search_no_clap_raises(self, sample_library, sample_embeddings):
        """Test hybrid search raises ImportError when CLAP not available."""
        with patch.object(hybrid_search.clap_embed, "check_clap_available", return_value=False):
            with pytest.raises(ImportError, match="CLAP not installed"):
                hybrid_search.hybrid_search(
                    "test query",
                    sample_library,
                    sample_embeddings,
                )

    def test_hybrid_search_file_not_found(self, tmp_path):
        """Test hybrid search raises FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            hybrid_search.hybrid_search(
                "test query",
                tmp_path / "nonexistent.json",
                tmp_path / "embeddings.json",
            )


class TestFormatHybridResults:
    """Test result formatting."""

    def test_format_empty_results(self):
        """Test formatting empty results."""
        output = hybrid_search.format_hybrid_results([])
        assert "No results found" in output

    def test_format_basic_results(self):
        """Test formatting basic results."""
        results = [
            {
                "path": "/audio/test.wav",
                "similarity": 0.85,
                "metadata": {},
            }
        ]
        
        output = hybrid_search.format_hybrid_results(results)
        assert "test.wav" in output
        assert "1 result" in output or "result(s)" in output

    def test_format_verbose_results(self):
        """Test formatting verbose results with metadata."""
        results = [
            {
                "path": "/audio/test.wav",
                "similarity": 0.85,
                "metadata": {
                    "tempo": {"bpm": 120},
                    "duration": {"seconds": 30},
                },
            }
        ]
        
        output = hybrid_search.format_hybrid_results(results, verbose=True)
        assert "test.wav" in output
        assert "0.85" in output  # Similarity score
        assert "BPM" in output
        assert "Duration" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
