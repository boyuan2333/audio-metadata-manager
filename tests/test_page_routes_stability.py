"""Regression tests for stable AMM HTML page routes."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import web_server


TEMPLATES_DIR = Path(web_server.__file__).resolve().parent / "web" / "templates"


def test_favicon_route_does_not_404(test_client):
    resp = test_client.get("/favicon.ico")

    assert resp.status_code != 404
    assert resp.status_code in (200, 204)
    if resp.status_code == 200:
        assert resp.content == b""


def test_dashboard_template_failure_returns_friendly_error(monkeypatch):
    original_template_response = web_server.templates.TemplateResponse

    def fail_dashboard_template(request, template_name, *args, **kwargs):
        if template_name == "dashboard.html":
            raise RuntimeError("simulated dashboard render failure")
        return original_template_response(request, template_name, *args, **kwargs)

    monkeypatch.setattr(web_server.templates, "TemplateResponse", fail_dashboard_template)

    client = TestClient(web_server.app, raise_server_exceptions=False)
    resp = client.get("/")

    assert resp.status_code == 500
    assert resp.text != "Internal Server Error"
    assert "Internal Server Error" not in resp.text
    assert "AMM" in resp.text


def test_error_template_exists():
    assert (TEMPLATES_DIR / "error.html").is_file()
