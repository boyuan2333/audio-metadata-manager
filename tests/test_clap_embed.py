"""Tests for CLAP embedding computation (v0.1-b6)."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import audio_metadata.clap_embed as clap_embed


class TestCheckClapAvailable:
    """Test CLAP availability check."""

    def test_clap_available(self):
        """Test when CLAP is installed."""
        with patch.dict("sys.modules", {"laion_clap.hook": MagicMock()}):
            assert clap_embed.check_clap_available() is True

    def test_clap_not_available(self):
        """Test when CLAP is not installed."""
        with patch.dict("sys.modules", {"laion_clap.hook": None}, clear=False):
            # Simulate ImportError
            with patch("importlib.import_module", side_effect=ImportError):
                assert clap_embed.check_clap_available() is False


class TestCosineSimilarity:
    """Test cosine similarity computation."""

    def test_identical_vectors(self):
        """Identical vectors should have similarity 1.0."""
        vec = [0.1, 0.2, 0.3, 0.4, 0.5]
        similarity = clap_embed.cosine_similarity(vec, vec)
        assert abs(similarity - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        """Orthogonal vectors should have similarity 0."""
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [0.0, 1.0, 0.0]
        similarity = clap_embed.cosine_similarity(vec_a, vec_b)
        assert abs(similarity - 0.0) < 1e-6

    def test_opposite_vectors(self):
        """Opposite vectors should have similarity -1.0."""
        vec_a = [0.1, 0.2, 0.3]
        vec_b = [-0.1, -0.2, -0.3]
        similarity = clap_embed.cosine_similarity(vec_a, vec_b)
        assert abs(similarity - (-1.0)) < 1e-6

    def test_zero_vector(self):
        """Zero vector should result in 0 similarity."""
        vec_a = [0.0, 0.0, 0.0]
        vec_b = [0.1, 0.2, 0.3]
        similarity = clap_embed.cosine_similarity(vec_a, vec_b)
        assert similarity == 0.0


class TestSearchSimilar:
    """Test semantic search functionality."""

    @pytest.fixture
    def sample_embeddings(self, tmp_path):
        """Create sample embeddings file with distinct vectors."""
        # Create embeddings with different directions for meaningful similarity
        # vec1: mostly positive in first half, negative in second
        vec1 = [0.7] * 256 + [-0.7] * 256
        # vec2: opposite of vec1
        vec2 = [-0.7] * 256 + [0.7] * 256
        # vec3: mixed pattern
        vec3 = [0.5 if i % 2 == 0 else -0.5 for i in range(512)]
        
        embeddings_data = {
            "model": "laion-audioclip-full-2022",
            "embedding_dim": 512,
            "computed_at": "2026-04-14T00:00:00Z",
            "files": [
                {
                    "path": "/audio/pad_dark_120.wav",
                    "embedding": vec1,
                },
                {
                    "path": "/audio/bright_pluck_140.wav",
                    "embedding": vec2,
                },
                {
                    "path": "/audio/ambient_pad.wav",
                    "embedding": vec3,
                },
            ],
        }
        
        embeddings_file = tmp_path / "embeddings.json"
        with open(embeddings_file, "w") as f:
            json.dump(embeddings_data, f)
        
        return embeddings_file

    def test_search_top_k(self, sample_embeddings):
        """Test search returns top-K results."""
        # Query similar to first file (pad_dark)
        query_embedding = [0.7] * 256 + [-0.7] * 256
        
        results = clap_embed.search_similar(
            query_embedding,
            sample_embeddings,
            top_k=2,
        )
        
        assert len(results) == 2
        # First result should be most similar (pad_dark)
        assert results[0]["path"] == "/audio/pad_dark_120.wav"
        # Similarity should be ~1.0 for identical vectors
        assert results[0]["similarity"] > 0.99

    def test_search_threshold(self, sample_embeddings):
        """Test search with similarity threshold."""
        # Query identical to first file
        query_embedding = [0.7] * 256 + [-0.7] * 256
        
        # High threshold should filter out dissimilar results
        results = clap_embed.search_similar(
            query_embedding,
            sample_embeddings,
            top_k=10,
            threshold=0.9,
        )
        
        # Only the first file should match (others are very different)
        assert len(results) == 1
        assert results[0]["path"] == "/audio/pad_dark_120.wav"

    def test_search_no_results(self, sample_embeddings):
        """Test search with very high threshold."""
        # Use a threshold so high that nothing matches
        query_embedding = [0.1] * 512
        
        results = clap_embed.search_similar(
            query_embedding,
            sample_embeddings,
            top_k=10,
            threshold=0.999999,  # Nearly impossible to match
        )
        
        # Should find no results above this threshold
        assert len(results) == 0


class TestComputeEmbeddingsBatch:
    """Test batch embedding computation."""

    @pytest.fixture
    def mock_clap_model(self):
        """Create mock CLAP model."""
        mock_model = MagicMock()
        
        def create_mock_embedding(*args, **kwargs):
            """Create a proper mock embedding tensor."""
            import numpy as np
            embedding = np.array([[0.1] * 512], dtype=np.float32)
            mock_tensor = MagicMock()
            mock_tensor.cpu.return_value = MagicMock(numpy=MagicMock(return_value=embedding))
            return mock_tensor
        
        mock_model.get_audio_embedding_from_filelist.side_effect = create_mock_embedding
        
        return mock_model

    def test_compute_embeddings_batch_success(self, mock_clap_model, tmp_path):
        """Test successful batch embedding computation."""
        audio_files = [
            tmp_path / "audio1.wav",
            tmp_path / "audio2.wav",
        ]
        output_file = tmp_path / "output.json"
        
        # Create dummy audio files
        for f in audio_files:
            f.touch()
        
        with patch.object(clap_embed, "load_clap_model", return_value=mock_clap_model):
            result = clap_embed.compute_embeddings_batch(
                audio_files,
                output_file,
                verbose=False,
            )
        
        assert result["total_files"] == 2
        assert result["successful"] == 2
        assert result["failed"] == 0
        assert Path(output_file).exists()
        
        # Verify output structure
        with open(output_file) as f:
            data = json.load(f)
        
        assert data["model"] == clap_embed.CLAP_MODEL_NAME
        assert data["embedding_dim"] == clap_embed.CLAP_EMBEDDING_DIM
        assert "computed_at" in data
        assert len(data["files"]) == 2

    def test_compute_embeddings_with_failures(self, mock_clap_model, tmp_path):
        """Test batch computation with some failures."""
        audio_files = [
            tmp_path / "audio1.wav",
            tmp_path / "audio2.wav",
        ]
        output_file = tmp_path / "output.json"
        
        # Create dummy audio files
        for f in audio_files:
            f.touch()
        
        # Track which files have been processed
        call_count = [0]
        
        def side_effect(file_list, *args, **kwargs):
            call_count[0] += 1
            # Fail on second call (audio2)
            if call_count[0] == 2:
                raise Exception("File corrupted")
            import numpy as np
            embedding = np.array([[0.1] * 512], dtype=np.float32)
            mock_tensor = MagicMock()
            mock_tensor.cpu.return_value = MagicMock(numpy=MagicMock(return_value=embedding))
            return mock_tensor
        
        mock_clap_model.get_audio_embedding_from_filelist.side_effect = side_effect
        
        with patch.object(clap_embed, "load_clap_model", return_value=mock_clap_model):
            result = clap_embed.compute_embeddings_batch(
                audio_files,
                output_file,
                verbose=False,
            )
        
        assert result["total_files"] == 2
        assert result["successful"] == 1
        assert result["failed"] == 1
        assert len(result["failed_files"]) == 1

    def test_compute_embeddings_append_mode(self, mock_clap_model, tmp_path):
        """Test appending to existing embeddings."""
        audio_file = tmp_path / "audio3.wav"
        audio_file.touch()
        
        output_file = tmp_path / "output.json"
        
        # Create initial embeddings
        initial_data = {
            "model": "laion-audioclip-full-2022",
            "embedding_dim": 512,
            "computed_at": "2026-04-14T00:00:00Z",
            "files": [
                {
                    "path": str(tmp_path / "audio1.wav"),
                    "embedding": [0.2] * 512,
                }
            ],
        }
        
        with open(output_file, "w") as f:
            json.dump(initial_data, f)
        
        with patch.object(clap_embed, "load_clap_model", return_value=mock_clap_model):
            result = clap_embed.compute_embeddings_batch(
                [audio_file],
                output_file,
                append=True,
                verbose=False,
            )
        
        # Should have 2 embeddings (1 existing + 1 new)
        assert result["total_embeddings"] == 2
        
        # Verify file contains both
        with open(output_file) as f:
            data = json.load(f)
        
        assert len(data["files"]) == 2


class TestLoadClapModel:
    """Test CLAP model loading."""

    def test_load_model_cpu(self):
        """Test loading model on CPU."""
        mock_module = MagicMock()
        mock_model = MagicMock()
        mock_module.CLAP_Module.return_value = mock_model
        
        with patch.dict("sys.modules", {"laion_clap.hook": mock_module}):
            model = clap_embed.load_clap_model(device="cpu")
        
        mock_module.CLAP_Module.assert_called_once_with(
            enable_fusion=False,
            device="cpu"
        )
        mock_model.load_ckpt.assert_called_once()

    def test_load_model_not_installed(self):
        """Test loading when CLAP not installed."""
        with patch.dict("sys.modules", {"laion_clap.hook": None}):
            with pytest.raises(ImportError, match="CLAP not installed"):
                clap_embed.load_clap_model()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
