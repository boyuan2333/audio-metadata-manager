"""Tests for audio_metadata.report – library report generation."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from audio_metadata.report import generate_report, format_report


# ── helpers ─────────────────────────────────────────────────────────

def _make_record(
    file_name: str = "kick.wav",
    file_format: str = "wav",
    path: str = "samples/kick.wav",
    duration: float | None = 0.5,
    is_loop: bool | None = False,
    tags: list[str] | None = None,
    semantic_tags: list[str] | None = None,
    auto_tags: list[str] | None = None,
    embedding_status: str | None = None,
    review: dict | None = None,
) -> dict:
    """Build a single normalised record matching schema v1."""
    return {
        "id": f"id-{file_name}",
        "status": "ok",
        "source": {
            "path": path,
            "file_name": file_name,
            "file_format": file_format,
        },
        "technical": {
            "duration_sec": duration,
            "sample_rate_hz": 44100,
            "channels": 1,
        },
        "features": {},
        "derived": {
            "is_loop": is_loop,
            "tempo_applicable": None,
            "duration_bucket": None,
            "brightness": None,
        },
        "retrieval": {
            "tags": tags or [],
            "semantic_tags": semantic_tags or [],
            "mood": None,
            "texture": None,
            "density": None,
            "role": None,
            "domain": None,
            "embedding_ref": None,
            "embedding_model": None,
            "embedding_status": embedding_status,
        },
        "model_outputs": {
            "auto_tags": auto_tags or [],
            "auto_tags_confidence": {},
            "semantic_tags": [],
        },
        "review": review or {},
        "segments": [],
        "errors": [],
    }


def _write_library(tmp_path: Path, records: list[dict], key: str = "files") -> Path:
    """Write a library JSON file and return its path."""
    payload = {
        "schema_version": "v1",
        "app_version": "test",
        "run": {},
        key: records,
    }
    lib = tmp_path / "library.json"
    lib.write_text(json.dumps(payload), encoding="utf-8")
    return lib


def _write_embeddings(tmp_path: Path, paths: list[str]) -> Path:
    """Write an embeddings JSON file and return its path."""
    payload = {
        "model": "test-model",
        "embedding_dim": 512,
        "files": [{"path": p, "embedding": [0.0] * 512} for p in paths],
    }
    emb = tmp_path / "embeddings.json"
    emb.write_text(json.dumps(payload), encoding="utf-8")
    return emb


# ── synthetic library fixture ───────────────────────────────────────

def _synthetic_records() -> list[dict]:
    """8 records covering various formats, durations, loops, tags."""
    return [
        _make_record("kick.wav", "wav", "s/kick.wav", 0.3, False,
                      tags=["drum", "kick"], auto_tags=["percussion"]),
        _make_record("snare.wav", "wav", "s/snare.wav", 0.4, False,
                      tags=["drum", "snare"], auto_tags=["percussion"]),
        _make_record("pad_loop.aiff", "aiff", "s/pad_loop.aiff", 8.0, True,
                      tags=["synth", "pad"], semantic_tags=["ambient"]),
        _make_record("bass.wav", "wav", "s/bass.wav", 2.5, False,
                      tags=["bass"], semantic_tags=["sub-bass"]),
        _make_record("vocal_chop.flac", "flac", "s/vocal_chop.flac", 1.2, False,
                      tags=["vocal"]),
        _make_record("atmo.wav", "wav", "s/atmo.wav", 45.0, True,
                      tags=["ambient", "atmosphere"], semantic_tags=["dark"]),
        _make_record("hihat.wav", "wav", "s/hihat.wav", 0.15, False,
                      tags=["drum", "hihat"], auto_tags=["percussion", "cymbal"]),
        _make_record("untagged.wav", "wav", "s/untagged.wav", None, None),
    ]


# ── tests ───────────────────────────────────────────────────────────

class TestMinimalSyntheticLibrary:
    """Smoke test with the 8-record synthetic library."""

    def test_total_files(self, tmp_path):
        lib = _write_library(tmp_path, _synthetic_records())
        report = generate_report(str(lib))
        assert report["total_files"] == 8

    def test_all_expected_keys_present(self, tmp_path):
        lib = _write_library(tmp_path, _synthetic_records())
        report = generate_report(str(lib))
        expected_keys = {
            "total_files", "format_distribution", "duration_distribution",
            "type_distribution", "tag_coverage", "embedding_coverage",
            "category_heatmap", "warnings",
        }
        assert expected_keys == set(report.keys())


class TestFormatDistribution:
    def test_counts_formats(self, tmp_path):
        lib = _write_library(tmp_path, _synthetic_records())
        report = generate_report(str(lib))
        fd = report["format_distribution"]
        assert fd["wav"] == 6
        assert fd["aiff"] == 1
        assert fd["flac"] == 1


class TestDurationBuckets:
    def test_bucket_distribution(self, tmp_path):
        lib = _write_library(tmp_path, _synthetic_records())
        report = generate_report(str(lib))
        dd = report["duration_distribution"]
        # kick 0.3, snare 0.4, hihat 0.15 → <1s = 3
        assert dd["<1s"] == 3
        # vocal_chop 1.2 → 1-5s = 1  (bass 2.5 also 1-5s → 2)
        assert dd["1-5s"] == 2
        # pad_loop 8.0 → 5-30s = 1
        assert dd["5-30s"] == 1
        # atmo 45.0 → >30s = 1
        assert dd[">30s"] == 1
        # untagged has None duration → counted in unknown bucket internally,
        # but duration_distribution only has 4 buckets so unknown is excluded
        # total bucketed = 3+2+1+1 = 7, missing = 1 (untagged)


class TestTypeDistribution:
    def test_loop_vs_oneshot(self, tmp_path):
        lib = _write_library(tmp_path, _synthetic_records())
        report = generate_report(str(lib))
        td = report["type_distribution"]
        # pad_loop (True), atmo (True) → 2 loops
        assert td["loop"] == 2
        # everything else → 6 one-shots
        assert td["one_shot"] == 6


class TestTagCoverage:
    def test_auto_tag_coverage(self, tmp_path):
        lib = _write_library(tmp_path, _synthetic_records())
        report = generate_report(str(lib))
        tc = report["tag_coverage"]
        # kick, snare, hihat have auto_tags → 3
        assert tc["auto_tag"] == 3
        assert tc["auto_tag_pct"] == pytest.approx(37.5)

    def test_semantic_coverage(self, tmp_path):
        lib = _write_library(tmp_path, _synthetic_records())
        report = generate_report(str(lib))
        tc = report["tag_coverage"]
        # pad_loop, bass, atmo have semantic_tags → 3
        assert tc["semantic"] == 3
        assert tc["semantic_pct"] == pytest.approx(37.5)

    def test_review_coverage(self, tmp_path):
        records = _synthetic_records()
        # Add review to two records
        records[0]["review"] = {"notes": ["good quality"]}
        records[1]["review"] = {"overrides": {"derived": {"is_loop": True}}}
        lib = _write_library(tmp_path, records)
        report = generate_report(str(lib))
        tc = report["tag_coverage"]
        assert tc["review"] == 2
        assert tc["review_pct"] == pytest.approx(25.0)


class TestEmbeddingCoverage:
    def test_without_embeddings_file(self, tmp_path):
        records = [
            _make_record("a.wav", embedding_status="ready"),
            _make_record("b.wav", embedding_status="missing"),
            _make_record("c.wav", embedding_status=None),
        ]
        lib = _write_library(tmp_path, records)
        report = generate_report(str(lib))
        ec = report["embedding_coverage"]
        assert ec["ready"] == 1
        assert ec["missing"] == 1

    def test_with_embeddings_file(self, tmp_path):
        records = [
            _make_record("a.wav", path="s/a.wav"),
            _make_record("b.wav", path="s/b.wav"),
            _make_record("c.wav", path="s/c.wav"),
        ]
        lib = _write_library(tmp_path, records)
        emb = _write_embeddings(tmp_path, ["s/a.wav", "s/b.wav"])
        report = generate_report(str(lib), embeddings_path=str(emb))
        ec = report["embedding_coverage"]
        # a.wav and b.wav matched → 2 ready; c.wav → 1 missing
        # But also counts from retrieval.embedding_status (none set)
        # The embeddings-file logic adds ready/missing for all records
        assert ec["ready"] == 2
        assert ec["missing"] == 1


class TestEmptyLibrary:
    def test_empty_files_array(self, tmp_path):
        lib = _write_library(tmp_path, [])
        report = generate_report(str(lib))
        assert report["total_files"] == 0
        assert report["format_distribution"] == {}
        assert report["duration_distribution"] == {"<1s": 0, "1-5s": 0, "5-30s": 0, ">30s": 0}
        assert report["type_distribution"] == {"loop": 0, "one_shot": 0}
        assert report["tag_coverage"]["auto_tag"] == 0
        assert report["tag_coverage"]["auto_tag_pct"] == 0.0
        assert report["embedding_coverage"] == {"ready": 0, "missing": 0}
        assert report["category_heatmap"] == {}
        assert report["warnings"] == []


class TestCategoryHeatmap:
    def test_top_tags(self, tmp_path):
        lib = _write_library(tmp_path, _synthetic_records())
        report = generate_report(str(lib))
        ch = report["category_heatmap"]
        # "drum" appears in kick, snare, hihat → 3
        assert ch["drum"] == 3
        # "kick", "snare", "hihat" each 1
        assert "kick" in ch
        assert "snare" in ch

    def test_limits_to_10(self, tmp_path):
        # Create 12 unique tags
        records = [
            _make_record(f"f{i}.wav", tags=[f"tag{i}"])
            for i in range(12)
        ]
        lib = _write_library(tmp_path, records)
        report = generate_report(str(lib))
        assert len(report["category_heatmap"]) == 10


class TestWarnings:
    def test_missing_duration_warning(self, tmp_path):
        lib = _write_library(tmp_path, _synthetic_records())
        report = generate_report(str(lib))
        # untagged.wav has None duration
        assert any("missing duration" in w for w in report["warnings"])

    def test_no_tags_warning(self, tmp_path):
        lib = _write_library(tmp_path, _synthetic_records())
        report = generate_report(str(lib))
        # untagged.wav has no tags at all
        assert any("no tags" in w for w in report["warnings"])


class TestFormatReport:
    def test_contains_sections(self, tmp_path):
        lib = _write_library(tmp_path, _synthetic_records())
        stats = generate_report(str(lib))
        text = format_report(stats)
        assert "LIBRARY REPORT" in text
        assert "Format Distribution" in text
        assert "Duration Distribution" in text
        assert "Type Distribution" in text
        assert "Tag Coverage" in text
        assert "Embedding Coverage" in text
        assert "Category Heatmap" in text

    def test_contains_data(self, tmp_path):
        lib = _write_library(tmp_path, _synthetic_records())
        stats = generate_report(str(lib))
        text = format_report(stats)
        assert "Total files: 8" in text
        assert "wav" in text
        assert "drum" in text

    def test_warnings_section_when_present(self, tmp_path):
        lib = _write_library(tmp_path, _synthetic_records())
        stats = generate_report(str(lib))
        text = format_report(stats)
        assert "Warnings" in text
        assert "⚠" in text

    def test_no_warnings_section_when_empty(self, tmp_path):
        records = [
            _make_record("a.wav", duration=1.0, tags=["drum"]),
        ]
        lib = _write_library(tmp_path, records)
        stats = generate_report(str(lib))
        text = format_report(stats)
        # No warnings block when there are no warnings
        assert "Warnings" not in text


class TestRecordsKeyFallback:
    """Library JSON may use 'records' key instead of 'files'."""

    def test_records_key_works(self, tmp_path):
        lib = _write_library(tmp_path, _synthetic_records(), key="records")
        report = generate_report(str(lib))
        assert report["total_files"] == 8
