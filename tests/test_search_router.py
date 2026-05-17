from __future__ import annotations

import pytest

from audio_metadata.search_router import analyze_query


class TestKeywordRouting:
    """Pure keyword queries with no semantic or structured signals."""

    def test_kick_drum(self):
        result = analyze_query("kick drum")
        assert result["strategy"] == "keyword"
        assert result["keywords"] == ["kick", "drum"]
        assert result["structured_filters"] == {}
        assert result["semantic_text"] == ""

    def test_piano(self):
        result = analyze_query("piano")
        assert result["strategy"] == "keyword"
        assert result["keywords"] == ["piano"]

    def test_808(self):
        result = analyze_query("808")
        assert result["strategy"] == "keyword"
        assert result["keywords"] == ["808"]


class TestSemanticRouting:
    """Queries with descriptive / subjective words."""

    def test_chinese_warm_piano(self):
        result = analyze_query("温暖的钢琴音色")
        assert result["strategy"] == "semantic"
        assert "温暖" in result["semantic_text"]
        # structured_filters should be empty (no BPM, loop, etc.)
        assert result["structured_filters"] == {}

    def test_english_dark(self):
        result = analyze_query("dark pad sound")
        assert result["strategy"] == "semantic"
        assert "dark" in result["semantic_text"]

    def test_english_bright(self):
        result = analyze_query("bright synth")
        assert result["strategy"] == "semantic"
        assert "bright" in result["semantic_text"]


class TestHybridRouting:
    """Queries that combine structured filters with descriptive words."""

    def test_dark_loop_120bpm(self):
        result = analyze_query("暗的 loop 120bpm")
        assert result["strategy"] == "hybrid"
        # Should have structured filters for BPM and loop
        assert "bpm" in result["structured_filters"]
        assert result["structured_filters"]["bpm"]["min"] == 120
        assert result["structured_filters"]["bpm"]["max"] == 120
        assert "is_loop" in result["structured_filters"]
        assert result["structured_filters"]["is_loop"] is True
        # Should also detect the semantic word
        assert "暗" in result["semantic_text"]

    def test_warm_oneshot(self):
        result = analyze_query("warm one shot snare")
        assert result["strategy"] == "hybrid"
        assert "is_loop" in result["structured_filters"]
        assert result["structured_filters"]["is_loop"] is False
        assert "warm" in result["semantic_text"]

    def test_loop_only_is_hybrid(self):
        """A structured-only query (loop) should be hybrid, not keyword."""
        result = analyze_query("loop drum")
        assert result["strategy"] == "hybrid"
        assert result["structured_filters"]["is_loop"] is True


class TestFilterExtraction:
    """Test that structured filters are correctly extracted."""

    def test_bpm_extraction(self):
        result = analyze_query("kick 90bpm")
        assert result["structured_filters"]["bpm"]["min"] == 90
        assert result["structured_filters"]["bpm"]["max"] == 90

    def test_loop_extraction(self):
        result = analyze_query("loop pad")
        assert result["structured_filters"]["is_loop"] is True

    def test_oneshot_extraction(self):
        result = analyze_query("one-shot clap")
        assert result["structured_filters"]["is_loop"] is False

    def test_brightness_extraction(self):
        result = analyze_query("dark loop")
        assert result["structured_filters"]["brightness"] == "dark"
        assert "is_loop" in result["structured_filters"]

    def test_format_extraction(self):
        result = analyze_query("kick wav")
        assert result["structured_filters"]["format"] == "wav"


class TestEdgeCases:
    """Edge cases and mixed-language queries."""

    def test_empty_query(self):
        result = analyze_query("")
        assert result["strategy"] == "keyword"
        assert result["structured_filters"] == {}
        assert result["semantic_text"] == ""
        assert result["keywords"] == []

    def test_whitespace_only(self):
        result = analyze_query("   ")
        assert result["strategy"] == "keyword"
        assert result["keywords"] == []

    def test_mixed_chinese_english(self):
        result = analyze_query("温暖的 kick drum")
        assert result["strategy"] == "semantic"
        assert "温暖" in result["semantic_text"]
        # Keywords should still have the English tokens
        assert "kick" in result["keywords"] or "drum" in result["keywords"]

    def test_mixed_with_structured(self):
        result = analyze_query("明亮的 120bpm piano loop")
        assert result["strategy"] == "hybrid"
        assert "明亮" in result["semantic_text"]
        assert "bpm" in result["structured_filters"]
        assert result["structured_filters"]["is_loop"] is True
