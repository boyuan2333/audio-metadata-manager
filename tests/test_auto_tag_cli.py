"""
Integration tests for auto-tag CLI command.

Tests cover:
- CLI argument parsing
- Dry-run mode
- Batch processing
- Output file generation
- Error handling
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

from app import build_parser
from auto_tag_cli import run, build_parser as auto_tag_build_parser, find_audio_files


class TestAutoTagCLI:
    """Integration tests for auto-tag CLI."""
    
    def test_parser_basic_args(self):
        """Test basic argument parsing."""
        parser = auto_tag_build_parser()
        args = parser.parse_args(["test.wav"])
        
        assert args.input_path == "test.wav"
        assert args.output is None
        assert args.dry_run is False
        assert args.force is False
        assert args.filter == "*"
        assert args.sample_rate == 22050
        assert args.verbose is False
    
    def test_parser_dry_run(self):
        """Test --dry-run flag."""
        parser = auto_tag_build_parser()
        args = parser.parse_args(["test.wav", "--dry-run"])
        
        assert args.dry_run is True
    
    def test_parser_output_file(self):
        """Test --output flag."""
        parser = auto_tag_build_parser()
        args = parser.parse_args(["test.wav", "-o", "output.json"])
        
        assert args.output == "output.json"
    
    def test_parser_verbose(self):
        """Test --verbose flag."""
        parser = auto_tag_build_parser()
        args = parser.parse_args(["test.wav", "-v"])
        
        assert args.verbose is True
    
    def test_parser_sample_rate(self):
        """Test --sample-rate flag."""
        parser = auto_tag_build_parser()
        args = parser.parse_args(["test.wav", "-s", "44100"])
        
        assert args.sample_rate == 44100
    
    def test_parser_invalid_sample_rate(self):
        """Test that invalid sample rate is rejected."""
        parser = auto_tag_build_parser()
        args = parser.parse_args(["test.wav", "-s", "1000"])
        
        # Validation happens in validate_args, not parse_args
        from auto_tag_cli import validate_args
        import pytest
        
        with pytest.raises(SystemExit):
            validate_args(args, parser)
    
    def test_find_audio_files_single_file(self, tmp_path):
        """Test finding a single audio file."""
        audio_file = tmp_path / "test.wav"
        audio_file.touch()
        
        files = find_audio_files(str(audio_file), "*")
        
        assert len(files) == 1
        assert files[0] == audio_file
    
    def test_find_audio_files_directory(self, tmp_path):
        """Test finding audio files in a directory."""
        # Create test files
        (tmp_path / "file1.wav").touch()
        (tmp_path / "file2.mp3").touch()
        (tmp_path / "file3.flac").touch()
        (tmp_path / "not_audio.txt").touch()
        
        files = find_audio_files(str(tmp_path), "*")
        
        assert len(files) == 3
        file_names = [f.name for f in files]
        assert "file1.wav" in file_names
        assert "file2.mp3" in file_names
        assert "file3.flac" in file_names
        assert "not_audio.txt" not in file_names
    
    def test_find_audio_files_filter_pattern(self, tmp_path):
        """Test filtering by pattern."""
        (tmp_path / "file1.wav").touch()
        (tmp_path / "file2.wav").touch()
        (tmp_path / "file3.mp3").touch()
        
        files = find_audio_files(str(tmp_path), "*.wav")
        
        assert len(files) == 2
        assert all(f.suffix == ".wav" for f in files)
    
    def test_find_audio_files_nonexistent_path(self):
        """Test with non-existent path."""
        files = find_audio_files("/nonexistent/path", "*")
        assert len(files) == 0


class TestAutoTagDryRun:
    """Tests for dry-run mode."""
    
    def test_dry_run_no_processing(self, tmp_path, capsys):
        """Test that dry-run mode doesn't process files."""
        audio_file = tmp_path / "test.wav"
        audio_file.touch()
        
        parser = auto_tag_build_parser()
        args = parser.parse_args([str(audio_file), "--dry-run"])
        
        # Mock auto_tag_file to ensure it's not called
        with patch('auto_tag_cli.auto_tag_file') as mock_tag:
            result = run(args)
            mock_tag.assert_not_called()
        
        assert result == 0
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert "Would process 1 file(s)" in captured.out


class TestAutoTagOutput:
    """Tests for output generation."""
    
    @patch('auto_tag_cli.auto_tag_file')
    def test_output_json_structure(self, mock_auto_tag, tmp_path, capsys):
        """Test that output JSON has correct structure."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "auto_tags": ["is_percussive"],
            "auto_tags_confidence": {"is_percussive": 0.9},
            "classifier_version": "v0.1-b5-objective",
            "classifier_type": "deterministic_rules",
            "feature_params": {"n_fft": 2048},
        }
        mock_auto_tag.return_value = mock_result
        
        # Create test file
        audio_file = tmp_path / "test.wav"
        audio_file.touch()
        
        parser = auto_tag_build_parser()
        args = parser.parse_args([str(audio_file)])  # Remove -v to avoid extra output
        
        result = run(args)
        
        assert result == 0
        captured = capsys.readouterr()
        
        # Find JSON in output (skip non-JSON lines)
        lines = captured.out.split('\n')
        json_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_start = i
                break
        
        assert json_start is not None, "No JSON found in output"
        
        # Find JSON end (closing brace before Summary)
        json_end = None
        for i in range(len(lines) - 1, json_start, -1):
            if lines[i].strip() == '}':
                json_end = i + 1
                break
        
        assert json_end is not None, "No JSON end found"
        json_str = '\n'.join(lines[json_start:json_end])
        output = json.loads(json_str)
        
        assert "version" in output
        assert "classifier" in output
        assert "total_files" in output
        assert "successful" in output
        assert "failed" in output
        assert "results" in output
        
        assert output["version"] == "v0.1-b5"
        assert output["classifier"] == "v0.1-b5-objective"
        assert output["total_files"] == 1
        assert output["successful"] == 1
    
    @patch('auto_tag_cli.auto_tag_file')
    def test_output_to_file(self, mock_auto_tag, tmp_path, capsys):
        """Test writing output to file."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "auto_tags": ["is_percussive"],
            "auto_tags_confidence": {"is_percussive": 0.9},
            "classifier_version": "v0.1-b5-objective",
            "classifier_type": "deterministic_rules",
            "feature_params": {"n_fft": 2048},
        }
        mock_auto_tag.return_value = mock_result
        
        # Create test file
        audio_file = tmp_path / "test.wav"
        audio_file.touch()
        
        output_file = tmp_path / "output.json"
        
        parser = auto_tag_build_parser()
        args = parser.parse_args([str(audio_file), "-o", str(output_file)])
        
        result = run(args)
        
        assert result == 0
        assert output_file.exists()
        
        # Read and verify output
        with open(output_file, 'r') as f:
            output = json.load(f)
        
        assert output["total_files"] == 1
        assert "results" in output
        
        captured = capsys.readouterr()
        assert f"Results saved to: {output_file}" in captured.out
    
    @patch('auto_tag_cli.auto_tag_file')
    def test_error_handling(self, mock_auto_tag, tmp_path, capsys):
        """Test error handling for failed files."""
        # Setup mock to raise exception
        mock_auto_tag.side_effect = Exception("Test error")
        
        # Create test file
        audio_file = tmp_path / "test.wav"
        audio_file.touch()
        
        parser = auto_tag_build_parser()
        args = parser.parse_args([str(audio_file), "-v"])
        
        result = run(args)
        
        # Should return non-zero on error
        assert result != 0
        
        captured = capsys.readouterr()
        assert "Error" in captured.out


class TestAppIntegration:
    """Test auto-tag integration with main app."""
    
    def test_app_has_auto_tag_command(self):
        """Test that app.py includes auto-tag command."""
        parser = build_parser()
        
        # Should raise SystemExit for --help (normal argparse behavior)
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["auto-tag", "--help"])
        
        # Exit code 0 means help was displayed successfully
        assert exc_info.value.code == 0
    
    def test_app_auto_tag_help(self, capsys):
        """Test auto-tag help message."""
        parser = build_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(["auto-tag", "--help"])
        
        captured = capsys.readouterr()
        # Check for key elements in help output
        assert "auto-tag" in captured.out
        assert "input_path" in captured.out
        assert "--output" in captured.out or "-o" in captured.out


class TestAutoTagBatchProcessing:
    """Tests for batch processing multiple files."""
    
    @patch('auto_tag_cli.auto_tag_file')
    def test_batch_multiple_files(self, mock_auto_tag, tmp_path, capsys):
        """Test processing multiple files."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "auto_tags": ["is_percussive"],
            "auto_tags_confidence": {"is_percussive": 0.9},
            "classifier_version": "v0.1-b5-objective",
            "classifier_type": "deterministic_rules",
            "feature_params": {"n_fft": 2048},
        }
        mock_auto_tag.return_value = mock_result
        
        # Create multiple test files
        for i in range(5):
            (tmp_path / f"file{i}.wav").touch()
        
        parser = auto_tag_build_parser()
        args = parser.parse_args([str(tmp_path), "-v"])
        
        result = run(args)
        
        assert result == 0
        assert mock_auto_tag.call_count == 5
        
        captured = capsys.readouterr()
        assert "Found 5 audio file(s)" in captured.out
        assert "Successful: 5" in captured.out
    
    @patch('auto_tag_cli.auto_tag_file')
    def test_batch_partial_failure(self, mock_auto_tag, tmp_path, capsys):
        """Test batch processing with some failures."""
        # Setup mock to fail on even indices
        call_count = [0]
        
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                raise Exception("Simulated failure")
            mock_result = MagicMock()
            mock_result.to_dict.return_value = {"auto_tags": []}
            return mock_result
        
        mock_auto_tag.side_effect = side_effect
        
        # Create multiple test files
        for i in range(4):
            (tmp_path / f"file{i}.wav").touch()
        
        parser = auto_tag_build_parser()
        args = parser.parse_args([str(tmp_path)])
        
        result = run(args)
        
        # Should return non-zero if any failed
        assert result != 0
        
        captured = capsys.readouterr()
        assert "Successful: 2" in captured.out
        assert "Failed: 2" in captured.out
