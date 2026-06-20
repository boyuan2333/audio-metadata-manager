# CURRENT_GOAL.md

## Version

- Current repo version: `v0.1-b10` planned
- Previous milestone: `v0.1-b9` Web UI MVP exploration
- Current milestone: `v0.1-b10` First-Run Scan Workflow

---

## Goal

Build a Web-first setup and scan workflow so a non-technical audio producer can start AMM, choose a sample folder, create a managed local library, scan from the UI, then search and audition results without touching CLI commands or JSON paths.

Product source of truth:

- PRD: `docs/product/amm-retrieval-cockpit-prd.md`
- Implementation plan: `docs/plans/2026-06-20-first-run-scan-workflow.md`
- Architecture roadmap: `docs/development/amm-architecture-roadmap.md`

---

## Product Rule

Do not make the user manage `library.json`, database paths, or config files. AMM may show advanced storage paths for debugging, but setup should be expressed as:

1. Choose sample folder.
2. Create library.
3. Scan.
4. Search and audition.

---

## v0.1-b10 Required Deliverables

1. Core managed library service
   - `audio_metadata.library`
   - Default managed library path: `<sample-folder>/.amm/library.json`
   - Summary helpers for record count and storage status

2. First-run setup wizard
   - `/setup` route
   - Redirect from `/` when no usable library exists
   - Sample folder input
   - Create Library action
   - Scan action
   - Open Library action after scan

3. UI scan workflow
   - `POST /api/scan`
   - Scan button in setup
   - Scan button/status in Library
   - Results refresh after scan

4. Library search cockpit improvements
   - Search remains the primary workspace
   - Result rows support play
   - Result rows expose a correction/edit entry point
   - Empty states explain missing library, missing scan, no results, and broken audio paths

5. Remove misleading UI
   - No visible Library Path input
   - No dead rescan/reindex buttons
   - No setup flow that requires CLI indexing first
   - No primary "Database" wording for normal users

6. Language baseline
   - English and Simplified Chinese for global navigation, setup, settings, and main Library actions
   - Full historical page translation is not required for this milestone

---

## Non-Goals

- Desktop packaging
- Cloud sync
- Multi-folder library management
- Watch mode
- Full task queue
- Full report/dashboard polish
- Vector database
- Full app-wide i18n completeness

---

## Acceptance Criteria

1. Starting without a library opens the setup workflow.
2. User can enter a sample folder and create a managed library.
3. Managed library is created at `<sample-folder>/.amm/library.json`.
4. User can run scan from the Web UI.
5. After scan, Library page shows searchable results.
6. User can play at least one result.
7. User can reach a correction/edit path from a search result.
8. No user-facing setup control asks for a JSON path.
9. Focused tests for setup, settings, scan, static UI, and search contracts pass.

---

## Recommended Verification

Use Python 3.12 or 3.13 where possible.

```bash
python -m pytest tests/test_library_service.py -q
python -m pytest tests/test_settings_api.py -q
python -m pytest tests/test_scan_api.py -q
python -m pytest tests/test_setup_routes.py -q
python -m pytest tests/test_web_static.py -q
python -m pytest tests/test_search_api_stability.py -q
```

Known local issue: Python 3.14 on Windows has shown pytest cleanup failures around `pytest-current`. Treat that as an environment issue only after test bodies have clearly passed.
