"""Comprehensive API tests for the AMM Web UI.

Tests cover:
  - Search API   (GET /api/search)
  - Audio API    (GET /api/audio/{path})
  - Report API   (GET /api/report)
  - Sample API   (GET /api/sample/{id}, PUT /api/sample/{id}/review)
  - Page routes  (/, /library, /editor, /settings)
"""

from __future__ import annotations

import json

import pytest


# ═════════════════════════════════════════════════════════════════════════════
# 1. Search API
# ═════════════════════════════════════════════════════════════════════════════


class TestSearchAPI:
    """Tests for GET /api/search."""

    def test_search_returns_results(self, test_client):
        """GET /api/search?q=drums — should return 200 with a non-empty list."""
        resp = test_client.get("/api/search", params={"q": "drums"})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Each result should have the expected keys
        for item in data:
            assert "file_name" in item
            assert "score" in item
            assert "metadata" in item

    def test_search_no_results(self, test_client):
        """GET /api/search?q=xyznonexistent123 — returns 200 with empty list."""
        resp = test_client.get("/api/search", params={"q": "xyznonexistent123"})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_search_missing_query_param(self, test_client):
        """GET /api/search (no q param) — returns 422 validation error."""
        resp = test_client.get("/api/search")
        assert resp.status_code == 422


# ═════════════════════════════════════════════════════════════════════════════
# 2. Audio API
# ═════════════════════════════════════════════════════════════════════════════


class TestAudioAPI:
    """Tests for GET /api/audio/{file_path}."""

    def test_stream_valid_audio(self, test_client, mock_samples_dir):
        """GET /api/audio/{valid_path} — returns 200 with audio content."""
        # Build the relative path from the sample dir parent
        # Files are at tmp/samples/kick_01.wav, sample_dir parent = tmp
        resp = test_client.get("/api/audio/samples/kick_01.wav")
        assert resp.status_code == 200
        assert "audio" in resp.headers.get("content-type", "")

    def test_path_traversal_blocked(self, test_client):
        """Path traversal attempts should be blocked (403 or 404)."""
        # URL-encode dots to prevent client-side path normalization
        resp = test_client.get("/api/audio/%2e%2e/%2e%2e/%2e%2e/etc/passwd")
        # The path may be normalised away by the HTTP client/routing layer,
        # resulting in 404 (no route match) — OR it reaches the endpoint
        # and is rejected with 403. Either way, the attack is blocked.
        assert resp.status_code in (403, 404)

    def test_nonexistent_audio_file(self, test_client):
        """GET /api/audio/nonexistent.wav — returns 404."""
        resp = test_client.get("/api/audio/nonexistent.wav")
        assert resp.status_code == 404


# ═════════════════════════════════════════════════════════════════════════════
# 3. Report API
# ═════════════════════════════════════════════════════════════════════════════


class TestReportAPI:
    """Tests for GET /api/report."""

    def test_report_returns_stats(self, test_client):
        """GET /api/report — returns 200 with a stats object."""
        resp = test_client.get("/api/report")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
        # Should contain the key report fields
        assert "total_files" in data
        assert "format_distribution" in data
        assert "duration_distribution" in data
        assert "type_distribution" in data
        assert "tag_coverage" in data
        assert "embedding_coverage" in data
        assert "category_heatmap" in data
        assert "warnings" in data

    def test_report_total_files(self, test_client):
        """Report should reflect the number of records in the mock library."""
        resp = test_client.get("/api/report")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_files"] == 5


# ═════════════════════════════════════════════════════════════════════════════
# 4. Sample API
# ═════════════════════════════════════════════════════════════════════════════


class TestSampleAPI:
    """Tests for GET /api/sample/{id} and PUT /api/sample/{id}/review."""

    def test_get_sample_valid_id(self, test_client):
        """GET /api/sample/sample-001 — returns 200 with full metadata."""
        resp = test_client.get("/api/sample/sample-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "sample-001"
        assert "source" in data
        assert "technical" in data
        assert "features" in data
        assert "retrieval" in data

    def test_get_sample_nonexistent(self, test_client):
        """GET /api/sample/nonexistent — returns 404."""
        resp = test_client.get("/api/sample/nonexistent")
        assert resp.status_code == 404

    def test_update_review(self, test_client, mock_library):
        """PUT /api/sample/sample-001/review — returns 200 and persists overrides."""
        payload = {
            "notes": "Great kick drum",
            "tags": ["favorite", "drums"],
            "overrides": {"retrieval.mood": "powerful"},
        }
        resp = test_client.put(
            "/api/sample/sample-001/review",
            json=payload,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["sample_id"] == "sample-001"
        assert data["review"]["notes"] == "Great kick drum"
        assert data["review"]["manual_tags"] == ["favorite", "drums"]

        # Verify the review was persisted to disk
        reviews_path = mock_library.with_suffix(".reviews.json")
        assert reviews_path.exists()
        saved = json.loads(reviews_path.read_text(encoding="utf-8"))
        assert "sample-001" in saved
        assert saved["sample-001"]["notes"] == "Great kick drum"

    def test_get_sample_with_review_overrides(self, test_client):
        """GET after PUT should include review_overrides in the response."""
        # First, create a review
        test_client.put(
            "/api/sample/sample-002/review",
            json={"notes": "Nice pad", "tags": ["chill"]},
        )
        # Then fetch the sample — should include review data
        resp = test_client.get("/api/sample/sample-002")
        assert resp.status_code == 200
        data = resp.json()
        assert "review_overrides" in data
        assert data["review_overrides"]["notes"] == "Nice pad"


# ═════════════════════════════════════════════════════════════════════════════
# 5. Page routes
# ═════════════════════════════════════════════════════════════════════════════


class TestPageRoutes:
    """Tests for HTML page routes (/, /library, /editor, /settings)."""

    @pytest.mark.parametrize("path", ["/", "/library", "/editor", "/settings"])
    def test_page_returns_200(self, test_client, path):
        """Each page route should return 200 with HTML content."""
        resp = test_client.get(path)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
