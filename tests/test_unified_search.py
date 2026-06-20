"""Tests for audio_metadata.unified_search."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from audio_metadata.unified_search import (
    _keyword_score,
    _passes_structured,
    _to_result,
    format_results,
    unified_search,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _make_record(
    *,
    file_name: str = "test.wav",
    path: str = "/audio/test.wav",
    tags: list[str] | None = None,
    mood: str | None = None,
    texture: str | None = None,
    bpm: float | None = None,
    duration: float | None = None,
    is_loop: bool | None = None,
    brightness: str | None = None,
) -> dict:
    """Build a single normalised record matching the schema v1."""
    return {
        "source": {"file_name": file_name, "path": path, "file_format": "wav"},
        "features": {"tempo_bpm": bpm},
        "technical": {"duration_sec": duration},
        "retrieval": {"tags": tags or [], "mood": mood, "texture": texture},
        "derived": {"is_loop": is_loop, "brightness": brightness},
    }


def _write_library(tmp_path: Path, records: list[dict]) -> Path:
    lib = tmp_path / "library.json"
    lib.write_text(json.dumps({"files": records}), encoding="utf-8")
    return lib


# ── Tests: keyword search by file name ───────────────────────────────────────

class TestKeywordSearchByName:
    def test_finds_file_by_name(self, tmp_path: Path):
        records = [
            _make_record(file_name="dark_pad_loop_120bpm.wav", tags=["pad", "loop", "dark"]),
            _make_record(file_name="bright_kick.wav", tags=["kick"]),
        ]
        lib = _write_library(tmp_path, records)

        results = unified_search("pad loop", lib, top_k=10)
        names = [r["file_name"] for r in results]
        assert "dark_pad_loop_120bpm.wav" in names

    def test_case_insensitive(self, tmp_path: Path):
        records = [_make_record(file_name="KICK_DRUM.WAV")]
        lib = _write_library(tmp_path, records)

        results = unified_search("kick", lib)
        assert len(results) == 1
        assert results[0]["file_name"] == "KICK_DRUM.WAV"

    def test_partial_match(self, tmp_path: Path):
        records = [_make_record(file_name="synth_bass_heavy.wav")]
        lib = _write_library(tmp_path, records)

        results = unified_search("bass", lib)
        assert len(results) == 1


# ── Tests: keyword search by tags ────────────────────────────────────────────

class TestKeywordSearchByTags:
    def test_finds_by_tag(self, tmp_path: Path):
        records = [
            _make_record(file_name="a.wav", tags=["pad", "ambient"]),
            _make_record(file_name="b.wav", tags=["kick", "punchy"]),
        ]
        lib = _write_library(tmp_path, records)

        results = unified_search("ambient", lib)
        assert len(results) == 1
        assert results[0]["file_name"] == "a.wav"

    def test_finds_by_mood(self, tmp_path: Path):
        records = [
            _make_record(file_name="sad.wav", mood="melancholic"),
            _make_record(file_name="happy.wav", mood="cheerful"),
        ]
        lib = _write_library(tmp_path, records)

        results = unified_search("melancholic", lib)
        assert len(results) == 1
        assert results[0]["file_name"] == "sad.wav"

    def test_finds_by_texture(self, tmp_path: Path):
        records = [
            _make_record(file_name="smooth.wav", texture="smooth"),
            _make_record(file_name="rough.wav", texture="rough"),
        ]
        lib = _write_library(tmp_path, records)

        results = unified_search("smooth", lib)
        assert len(results) == 1
        assert results[0]["file_name"] == "smooth.wav"


# ── Tests: format_results ────────────────────────────────────────────────────

class TestFormatResults:
    def test_contains_query_and_strategy(self):
        results = [
            {
                "path": "/audio/dark.wav",
                "file_name": "dark_pad.wav",
                "score": 0.95,
                "metadata": {"duration": 4.0, "bpm": 120, "tags": ["pad", "dark"]},
            }
        ]
        text = format_results(results, "dark pad", "keyword")
        assert '搜索: "dark pad"' in text
        assert "策略: keyword" in text
        assert "匹配: 1 个文件" in text

    def test_contains_file_info(self):
        results = [
            {
                "path": "/audio/test.wav",
                "file_name": "dark_pad_loop_120bpm.wav",
                "score": 0.92,
                "metadata": {"duration": 4.0, "bpm": 120, "tags": ["pad", "loop", "dark"]},
            }
        ]
        text = format_results(results, "test", "hybrid")
        assert "dark_pad_loop_120bpm.wav" in text
        assert "4.0s" in text
        assert "120" in text
        assert "pad" in text

    def test_empty_results(self):
        text = format_results([], "nothing", "keyword")
        assert "匹配: 0 个文件" in text
        assert "无结果" in text

    def test_dashes_for_missing_metadata(self):
        results = [
            {
                "path": "/audio/test.wav",
                "file_name": "test.wav",
                "score": 0.5,
                "metadata": {"duration": None, "bpm": None, "tags": []},
            }
        ]
        text = format_results(results, "test", "keyword")
        # Should contain dashes for missing values
        assert "-" in text


# ── Tests: fallback when no embeddings ───────────────────────────────────────

class TestFallbackNoEmbeddings:
    def test_semantic_falls_back_to_keyword(self, tmp_path: Path):
        """If strategy is semantic but embeddings_path is None, fall back."""
        records = [
            _make_record(file_name="kick_dark.wav", tags=["kick"]),
            _make_record(file_name="pad.wav", tags=["pad"]),
        ]
        lib = _write_library(tmp_path, records)

        # "dark kick" routes to semantic (contains semantic word "dark")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = unified_search("dark kick", lib, embeddings_path=None)
        # Should still return results via keyword fallback
        assert len(results) >= 1
        assert any("keyword" in str(w.message).lower() for w in caught)

    def test_hybrid_falls_back_to_keyword(self, tmp_path: Path):
        """If strategy is hybrid but embeddings_path is None, fall back."""
        records = [
            _make_record(file_name="loop.wav", tags=["loop"], is_loop=True, bpm=120),
        ]
        lib = _write_library(tmp_path, records)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            # "loop 120bpm" triggers hybrid via structured filters
            results = unified_search("loop 120bpm", lib, embeddings_path=None)
        assert len(results) >= 1
        assert any("keyword" in str(w.message).lower() or "embeddings" in str(w.message).lower() for w in caught)


# ── Tests: empty library ─────────────────────────────────────────────────────

class TestEmptyLibrary:
    def test_empty_library_returns_empty(self, tmp_path: Path):
        lib = _write_library(tmp_path, [])
        results = unified_search("kick", lib)
        assert results == []

    def test_library_with_no_files_key(self, tmp_path: Path):
        """Library JSON missing 'files' key should return empty."""
        lib = tmp_path / "empty.json"
        lib.write_text("{}", encoding="utf-8")
        results = unified_search("kick", lib)
        assert results == []


# ── Tests: internal helpers ──────────────────────────────────────────────────

class TestInternalHelpers:
    def test_keyword_score_no_keywords(self):
        rec = _make_record(file_name="test.wav")
        assert _keyword_score(rec, []) == 1.0

    def test_keyword_score_all_match(self):
        rec = _make_record(file_name="dark_pad.wav", tags=["pad", "dark"])
        score = _keyword_score(rec, ["dark", "pad"])
        assert score == 1.0

    def test_keyword_score_partial_match(self):
        rec = _make_record(file_name="pad.wav", tags=["pad"])
        score = _keyword_score(rec, ["pad", "kick"])
        assert score == 0.5

    def test_keyword_score_no_match(self):
        rec = _make_record(file_name="kick.wav", tags=["kick"])
        score = _keyword_score(rec, ["pad"])
        assert score == 0.0

    def test_passes_structured_no_filters(self):
        rec = _make_record(bpm=120)
        assert _passes_structured(rec, {}) is True

    def test_passes_structured_bpm_match(self):
        rec = _make_record(bpm=120)
        assert _passes_structured(rec, {"bpm": {"min": 100, "max": 140}}) is True

    def test_passes_structured_bpm_fail(self):
        rec = _make_record(bpm=80)
        assert _passes_structured(rec, {"bpm": {"min": 100, "max": 140}}) is False

    def test_passes_structured_loop(self):
        rec = _make_record(is_loop=True)
        assert _passes_structured(rec, {"is_loop": True}) is True
        assert _passes_structured(rec, {"is_loop": False}) is False

    def test_to_result_format(self):
        rec = _make_record(
            file_name="test.wav",
            path="/audio/test.wav",
            tags=["pad"],
            bpm=120,
            duration=4.0,
        )
        result = _to_result({"score": 0.85, "record": rec})
        assert result["path"] == "/audio/test.wav"
        assert result["file_name"] == "test.wav"
        assert result["score"] == 0.85
        assert result["metadata"]["format"] == "wav"
        assert result["metadata"]["bpm"] == 120
        assert result["metadata"]["duration"] == 4.0
        assert "pad" in result["metadata"]["tags"]


# ── Tests: structured filter integration ─────────────────────────────────────

class TestStructuredFilterIntegration:
    def test_bpm_filter_in_keyword_search(self, tmp_path: Path):
        """Structured filters (BPM) should be respected in keyword search."""
        records = [
            _make_record(file_name="fast.wav", bpm=140, is_loop=True),
            _make_record(file_name="slow.wav", bpm=80, is_loop=True),
        ]
        lib = _write_library(tmp_path, records)
        # "loop 140bpm" → hybrid strategy, falls back to keyword with structured filters
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            results = unified_search("loop 140bpm", lib)
        names = [r["file_name"] for r in results]
        # At minimum, fast.wav should be in results
        assert "fast.wav" in names

    def test_file_not_found_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            unified_search("test", tmp_path / "nonexistent.json")
