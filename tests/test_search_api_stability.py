"""Stability tests for GET /api/search query parsing and response shape."""

from __future__ import annotations


def test_search_returns_enveloped_response_with_default_pagination(test_client):
    resp = test_client.get("/api/search", params={"q": "drums"})

    assert resp.status_code == 200
    data = resp.json()
    assert set(data) == {"query", "total", "limit", "offset", "results"}
    assert data["query"] == "drums"
    assert data["limit"] == 25
    assert data["offset"] == 0
    assert data["total"] == len(data["results"])
    assert data["results"]

def test_search_ignores_empty_numeric_filters(test_client):
    resp = test_client.get(
        "/api/search",
        params={
            "q": "drums",
            "min_bpm": "",
            "max_bpm": "",
            "min_duration": "",
            "max_duration": "",
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["results"]


def test_search_rejects_invalid_bpm_with_human_message(test_client):
    resp = test_client.get("/api/search", params={"q": "drums", "min_bpm": "fast"})

    assert resp.status_code == 400
    assert "BPM 必须是数字" in resp.json()["detail"]


def test_search_rejects_invalid_duration_with_human_message(test_client):
    resp = test_client.get(
        "/api/search",
        params={"q": "drums", "max_duration": "short"},
    )

    assert resp.status_code == 400
    assert "时长" in resp.json()["detail"]
    assert "必须是数字" in resp.json()["detail"]


def test_search_accepts_tempo_aliases_and_applies_offset(test_client):
    resp = test_client.get(
        "/api/search",
        params={"q": "drums", "tempo_min": "100", "tempo_max": "130", "limit": 1, "offset": 1},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "drums"
    assert data["limit"] == 1
    assert data["offset"] == 1
    assert data["total"] == 2
    assert len(data["results"]) == 1
    assert data["results"][0]["metadata"]["bpm"] == 120
