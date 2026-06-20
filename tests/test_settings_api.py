from __future__ import annotations

import json


def test_settings_returns_configured_paths_and_record_count(
    test_client, mock_library, mock_samples_dir
):
    resp = test_client.get("/api/settings")

    assert resp.status_code == 200
    data = resp.json()
    assert data["library_path"] == str(mock_library)
    assert data["managed_library_path"] == str(mock_library)
    assert data["sample_dir"] == str(mock_samples_dir.parent)
    assert data["db_path"] == str(mock_library)
    assert data["total_records"] == 5


def test_settings_updates_sample_dir_without_exposing_library_path(test_client, tmp_path):
    new_samples = tmp_path / "new-samples"
    new_samples.mkdir()

    resp = test_client.put(
        "/api/settings",
        json={"sample_dir": str(new_samples), "library_path": str(tmp_path / "ignored.json")},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["settings"]["sample_dir"] == str(new_samples)
    assert data["settings"]["library_path"] != str(tmp_path / "ignored.json")


def test_create_library_creates_managed_json_for_sample_dir(test_client, tmp_path):
    sample_dir = tmp_path / "samples"
    sample_dir.mkdir()

    resp = test_client.post("/api/settings/create-library", json={"sample_dir": str(sample_dir)})

    assert resp.status_code == 200
    data = resp.json()
    managed_path = data["settings"]["managed_library_path"]
    assert data["ok"] is True
    assert data["settings"]["sample_dir"] == str(sample_dir)
    assert managed_path == str(sample_dir / ".amm" / "library.json")
    payload = json.loads(open(managed_path, encoding="utf-8").read())
    assert payload["files"] == []
    assert payload["sample_dir"] == str(sample_dir)
