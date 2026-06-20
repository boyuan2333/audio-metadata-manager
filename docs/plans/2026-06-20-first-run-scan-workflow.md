# First Run Scan Workflow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the v0.1-b10 first-run workflow so a user can choose a sample folder, create a managed AMM library, scan from the Web UI, then search and audition results without touching CLI commands or JSON paths.

**Architecture:** Add a small Core service boundary for managed libraries and scanning, then expose it through FastAPI routes used by the Web client. The UI should show setup when no usable library exists, and use the Library page as the primary workspace after setup.

**Tech Stack:** Python 3.12/3.13, FastAPI, vanilla HTML/CSS/JS, JSON-backed local library, pytest.

---

## Product Rules For This Plan

- Do not expose `library.json` as required user input.
- Treat `<sample-folder>/.amm/library.json` as the default managed library location.
- Keep scanning in the Web UI.
- Prefer Library/search workflow over dashboard/report polish.
- Remove or hide buttons that do not have working APIs.
- Preserve CLI commands, but make Web users independent from CLI setup.

---

### Task 1: Managed Library Core Service

**Files:**
- Create: `audio_metadata/library.py`
- Test: `tests/test_library_service.py`

**Step 1: Write failing tests**

```python
from pathlib import Path
import json

from audio_metadata.library import (
    managed_library_path,
    create_managed_library,
    load_library_summary,
)


def test_managed_library_path_lives_under_sample_folder(tmp_path):
    samples = tmp_path / "samples"
    samples.mkdir()

    assert managed_library_path(samples) == samples / ".amm" / "library.json"


def test_create_managed_library_creates_empty_library(tmp_path):
    samples = tmp_path / "samples"
    samples.mkdir()

    path = create_managed_library(samples)

    assert path == samples / ".amm" / "library.json"
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "files": [],
        "sample_dir": str(samples),
    }


def test_load_library_summary_counts_records(tmp_path):
    samples = tmp_path / "samples"
    samples.mkdir()
    path = create_managed_library(samples)
    path.write_text(
        json.dumps({"files": [{"id": "a"}, {"id": "b"}], "sample_dir": str(samples)}),
        encoding="utf-8",
    )

    summary = load_library_summary(path)

    assert summary["total_records"] == 2
    assert summary["library_path"] == str(path)
```

**Step 2: Run test to verify RED**

Run:

```bash
python -m pytest tests/test_library_service.py -q
```

Expected: fails because `audio_metadata.library` does not exist.

**Step 3: Implement minimal service**

Create `audio_metadata/library.py` with:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def managed_library_path(sample_dir: str | Path) -> Path:
    return Path(sample_dir) / ".amm" / "library.json"


def create_managed_library(sample_dir: str | Path) -> Path:
    sample_root = Path(sample_dir)
    path = managed_library_path(sample_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            json.dumps({"files": [], "sample_dir": str(sample_root)}, indent=2),
            encoding="utf-8",
        )
    return path


def load_library_summary(library_path: str | Path) -> dict[str, Any]:
    path = Path(library_path)
    if not path.exists():
        return {"library_path": str(path), "total_records": 0}
    data = json.loads(path.read_text(encoding="utf-8"))
    files = data.get("files") if isinstance(data, dict) else []
    return {
        "library_path": str(path),
        "total_records": len(files) if isinstance(files, list) else 0,
        "sample_dir": data.get("sample_dir") if isinstance(data, dict) else None,
    }
```

**Step 4: Run GREEN**

Run:

```bash
python -m pytest tests/test_library_service.py -q
```

Expected: pass.

---

### Task 2: Move Settings API To Core Service

**Files:**
- Modify: `web/api/settings_api.py`
- Test: `tests/test_settings_api.py`

**Step 1: Write failing tests**

Update tests so `/api/settings/create-library` expects the library service behavior:

```python
def test_create_library_uses_managed_library_service(test_client, tmp_path):
    sample_dir = tmp_path / "samples"
    sample_dir.mkdir()

    resp = test_client.post(
        "/api/settings/create-library",
        json={"sample_dir": str(sample_dir)},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["settings"]["managed_library_path"] == str(
        sample_dir / ".amm" / "library.json"
    )
```

**Step 2: Run RED**

Run:

```bash
python -m pytest tests/test_settings_api.py -q
```

Expected: fails until `settings_api.py` imports and uses `audio_metadata.library`.

**Step 3: Implement**

In `web/api/settings_api.py`:

- Remove duplicated managed path helpers.
- Import:

```python
from audio_metadata.library import create_managed_library, load_library_summary, managed_library_path
```

- `GET /api/settings` returns:

```python
{
    "sample_dir": sample_dir,
    "library_path": str(current_or_managed_path),
    "managed_library_path": str(current_or_managed_path),
    "db_path": str(current_or_managed_path),
    "total_records": summary["total_records"],
    "last_scan": None,
}
```

- `POST /api/settings/create-library` calls `create_managed_library(sample_dir)` and updates `web_server._library_path`.

**Step 4: Run GREEN**

Run:

```bash
python -m pytest tests/test_settings_api.py -q
```

Expected: pass, except known Python 3.14 Windows pytest cleanup warnings may appear after test completion.

---

### Task 3: Scan Core Service

**Files:**
- Modify: `audio_metadata/library.py`
- Test: `tests/test_library_scan_service.py`

**Step 1: Write failing tests**

Use a monkeypatched scanner/indexer seam so the test does not depend on actual audio decoding.

```python
import json

from audio_metadata.library import scan_sample_folder


def test_scan_sample_folder_writes_records(tmp_path, monkeypatch):
    samples = tmp_path / "samples"
    samples.mkdir()
    (samples / "kick.wav").write_bytes(b"fake")
    library = samples / ".amm" / "library.json"

    def fake_index(input_dir, output_path, recursive=True):
        output_path.write_text(
            json.dumps({"files": [{"id": "kick", "source": {"file_name": "kick.wav"}}]}),
            encoding="utf-8",
        )
        return {"indexed": 1, "failed": 0}

    monkeypatch.setattr("audio_metadata.library._run_indexer", fake_index)

    result = scan_sample_folder(samples, library)

    assert result["indexed"] == 1
    assert json.loads(library.read_text(encoding="utf-8"))["files"][0]["id"] == "kick"
```

**Step 2: Run RED**

Run:

```bash
python -m pytest tests/test_library_scan_service.py -q
```

Expected: fails because `scan_sample_folder` does not exist.

**Step 3: Implement**

Add to `audio_metadata/library.py`:

```python
def _run_indexer(input_dir: Path, output_path: Path, recursive: bool = True) -> dict[str, int]:
    import main as index_command

    args = index_command.build_parser().parse_args(
        ["--input", str(input_dir), "--output", str(output_path), "--recursive"]
    )
    code = index_command.run(args)
    if code not in (None, 0):
        raise RuntimeError(f"Index command failed with exit code {code}")
    data = json.loads(output_path.read_text(encoding="utf-8"))
    return {"indexed": len(data.get("files", [])), "failed": 0}


def scan_sample_folder(sample_dir: str | Path, library_path: str | Path | None = None) -> dict[str, Any]:
    sample_root = Path(sample_dir)
    if not sample_root.exists() or not sample_root.is_dir():
        raise FileNotFoundError(f"Sample directory not found: {sample_root}")
    path = Path(library_path) if library_path else create_managed_library(sample_root)
    result = _run_indexer(sample_root, path, recursive=True)
    return {
        "ok": True,
        "sample_dir": str(sample_root),
        "library_path": str(path),
        **result,
    }
```

**Step 4: Run GREEN**

Run:

```bash
python -m pytest tests/test_library_scan_service.py -q
```

Expected: pass.

---

### Task 4: Scan API

**Files:**
- Create: `web/api/scan_api.py`
- Modify: `web_server.py`
- Test: `tests/test_scan_api.py`

**Step 1: Write failing tests**

```python
def test_scan_api_requires_sample_dir(test_client, monkeypatch):
    import web_server

    web_server._sample_dir = ""

    resp = test_client.post("/api/scan")

    assert resp.status_code == 400


def test_scan_api_runs_scan_and_updates_library(test_client, tmp_path, monkeypatch):
    import web_server

    samples = tmp_path / "samples"
    samples.mkdir()
    library = samples / ".amm" / "library.json"
    web_server._sample_dir = str(samples)
    web_server._library_path = str(library)

    def fake_scan(sample_dir, library_path=None):
        library.parent.mkdir(parents=True, exist_ok=True)
        library.write_text('{"files": [{"id": "x"}]}', encoding="utf-8")
        return {"ok": True, "indexed": 1, "failed": 0, "library_path": str(library)}

    monkeypatch.setattr("web.api.scan_api.scan_sample_folder", fake_scan)

    resp = test_client.post("/api/scan")

    assert resp.status_code == 200
    assert resp.json()["indexed"] == 1
```

**Step 2: Run RED**

Run:

```bash
python -m pytest tests/test_scan_api.py -q
```

Expected: fails because `/api/scan` does not exist.

**Step 3: Implement**

Create `web/api/scan_api.py`:

```python
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from audio_metadata.library import scan_sample_folder

router = APIRouter(tags=["scan"])


@router.post("/scan")
async def scan_library():
    import web_server

    sample_dir = web_server.get_sample_dir()
    if not sample_dir:
        raise HTTPException(400, detail="Sample directory is not configured")
    result = scan_sample_folder(sample_dir, web_server.get_library_path() or None)
    web_server._library_path = result["library_path"]
    return result
```

Register in `web_server.py`:

```python
from web.api.scan_api import router as scan_router
app.include_router(scan_router, prefix="/api")
```

**Step 4: Run GREEN**

Run:

```bash
python -m pytest tests/test_scan_api.py -q
```

Expected: pass.

---

### Task 5: First-Run Setup Route

**Files:**
- Modify: `web_server.py`
- Create: `web/templates/setup.html`
- Modify: `web/static/app.js`
- Test: `tests/test_setup_routes.py`, `tests/test_web_static.py`

**Step 1: Write failing route tests**

```python
def test_root_redirects_to_setup_when_library_missing(test_client):
    import web_server

    web_server._library_path = ""

    resp = test_client.get("/", follow_redirects=False)

    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/setup"


def test_setup_page_returns_html(test_client):
    resp = test_client.get("/setup")

    assert resp.status_code == 200
    assert "setup-sample-dir" in resp.text
    assert "btn-setup-scan" in resp.text
```

**Step 2: Run RED**

Run:

```bash
python -m pytest tests/test_setup_routes.py -q
```

Expected: fails because `/setup` route and redirect do not exist.

**Step 3: Implement route**

In `web_server.py`:

- Import `RedirectResponse`.
- Add helper:

```python
def has_usable_library() -> bool:
    return bool(_library_path) and Path(_library_path).exists()
```

- Change `/` route:

```python
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not has_usable_library():
        return RedirectResponse("/setup")
    return render_page(request, "dashboard.html")
```

- Add:

```python
@app.get("/setup", response_class=HTMLResponse)
async def setup(request: Request):
    return render_page(request, "setup.html")
```

**Step 4: Create setup template**

Create `web/templates/setup.html` with:

- Sample folder input `id="setup-sample-dir"`.
- Create library button `id="btn-setup-create"`.
- Scan button `id="btn-setup-scan"`.
- Status area `id="setup-status"`.
- Link to Library hidden until scan succeeds.

**Step 5: Add JS**

In `web/static/app.js`:

- Add `setupInit()`.
- It should:
  - PUT `/api/settings` with sample dir.
  - POST `/api/settings/create-library`.
  - POST `/api/scan`.
  - Show status transitions.
  - Enable Open Library when complete.
- Expose `window.setupInit = setupInit`.

**Step 6: Run GREEN**

Run:

```bash
python -m pytest tests/test_setup_routes.py tests/test_web_static.py -q
```

Expected: pass.

---

### Task 6: Library Page Scan Control

**Files:**
- Modify: `web/templates/library.html`
- Modify: `web/static/app.js`
- Test: `tests/test_web_static.py`

**Step 1: Write failing static test**

```python
def test_library_page_exposes_scan_action():
    html = LIBRARY_TEMPLATE.read_text(encoding="utf-8")
    js = APP_JS.read_text(encoding="utf-8")

    assert 'id="btn-library-scan"' in html
    assert "fetch('/api/scan'" in js
    assert "libraryScan" in js
```

**Step 2: Run RED**

Run:

```bash
python -m pytest tests/test_web_static.py -q
```

Expected: fails because scan action is not present.

**Step 3: Implement**

- Add a toolbar button above results:

```html
<button id="btn-library-scan" type="button" class="btn-ghost flex items-center gap-xs">
    <span class="material-symbols-outlined text-sm">sync</span>
    <span data-i18n="library.scan">Scan</span>
</button>
<span id="library-scan-status" class="text-xs text-text-secondary"></span>
```

- Add `_libraryScan()` in `app.js`:

```javascript
function _libraryScan() {
    var status = document.getElementById('library-scan-status');
    if (status) status.textContent = 'Scanning...';
    fetch('/api/scan', { method: 'POST' })
        .then(function (resp) {
            if (!resp.ok) throw new Error('Scan failed');
            return resp.json();
        })
        .then(function (data) {
            if (status) status.textContent = 'Indexed ' + (data.indexed || 0) + ' files';
            _librarySearch();
        })
        .catch(function () {
            if (status) status.textContent = 'Scan failed';
        });
}
```

- Wire `btn-library-scan` in `libraryInit`.

**Step 4: Run GREEN**

Run:

```bash
python -m pytest tests/test_web_static.py -q
```

Expected: pass.

---

### Task 7: Remove Misleading Dead UI

**Files:**
- Modify: `web/templates/settings.html`
- Modify: `web/templates/dashboard.html`
- Modify: `web/templates/library.html`
- Test: `tests/test_web_static.py`

**Step 1: Write failing static tests**

```python
def test_no_dead_scan_or_reindex_buttons_without_real_handlers():
    settings = SETTINGS_TEMPLATE.read_text(encoding="utf-8")

    assert "btn-reindex" not in settings
    assert "btn-rescan" not in settings


def test_user_facing_copy_does_not_expose_library_json_as_setup_requirement():
    settings = SETTINGS_TEMPLATE.read_text(encoding="utf-8")

    assert "library-path-input" not in settings
    assert "Library Path" not in settings
```

**Step 2: Run RED**

Run:

```bash
python -m pytest tests/test_web_static.py -q
```

Expected: fails if dead or misleading controls still exist.

**Step 3: Implement**

- Remove buttons with no backend.
- Rename user-facing storage terms:
  - Prefer "Library" / "Storage".
  - Avoid "Database" in primary setup copy.
  - Keep "Advanced Storage" only for read-only debug paths.

**Step 4: Run GREEN**

Run:

```bash
python -m pytest tests/test_web_static.py -q
```

Expected: pass.

---

### Task 8: Search Result Repair Entry Point

**Files:**
- Modify: `web/templates/library.html`
- Modify: `web/static/app.js`
- Test: `tests/test_web_static.py`

**Step 1: Write failing static test**

```python
def test_library_results_have_review_entry_point():
    js = APP_JS.read_text(encoding="utf-8")

    assert "Review" in js or "Edit tags" in js
    assert "_editorSelectFile" in js
```

**Step 2: Run RED**

Run:

```bash
python -m pytest tests/test_web_static.py -q
```

Expected: fails if results have no correction path.

**Step 3: Implement minimally**

- Add an "Edit" button on each result card.
- On click, navigate to `/editor?id=<sample_id>` or call a shared detail panel if already available.
- Do not build a full side panel yet unless existing editor logic can be reused safely.

**Step 4: Run GREEN**

Run:

```bash
python -m pytest tests/test_web_static.py -q
```

Expected: pass.

---

## Verification Commands

Run focused checks after each task:

```bash
python -m pytest tests/test_library_service.py -q
python -m pytest tests/test_settings_api.py -q
python -m pytest tests/test_scan_api.py -q
python -m pytest tests/test_setup_routes.py -q
python -m pytest tests/test_web_static.py -q
```

Run broader checks before calling the milestone complete:

```bash
python -m pytest tests/test_search_api_stability.py tests/test_web_api.py tests/test_web_static.py -q
```

Known environment note: Python 3.14 on Windows has shown pytest cleanup issues around `pytest-current`. Prefer Python 3.12 or 3.13 for final verification, matching the README recommendation.

---

## Milestone Acceptance

v0.1-b10 is acceptable when:

- Starting with no library opens `/setup`.
- User can enter a sample folder.
- User can create `<sample-folder>/.amm/library.json`.
- User can scan from the UI.
- Library results refresh after scan.
- User can search and play at least one indexed audio file.
- No setup page asks for a JSON path.
- Settings does not show dead rescan/reindex controls.
- Main visible setup/navigation text supports English and Simplified Chinese.
