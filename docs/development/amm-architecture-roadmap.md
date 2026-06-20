# AMM Architecture Roadmap

This note captures the next architecture direction for Audio Metadata Manager as it grows from local CLI scripts and a thin Web UI into a more stable application stack.

Current product source of truth:

- PRD: `docs/product/amm-retrieval-cockpit-prd.md`
- Implementation plan: `docs/plans/2026-06-20-first-run-scan-workflow.md`
- Current milestone: `CURRENT_GOAL.md`

## Current Shape

AMM is currently centered on command modules that read a `library.json`, normalize records, perform an operation, and write or display results. The Web UI exists, but it is still a thin shell around file-backed behavior rather than a full application boundary.

Several project-wide issues are now visible:

- Repeated read and normalize logic for `library.json` appears across commands and web routes.
- Search state, pagination, sort, and filter handling are still unstable as an API contract.
- Frontend input cleaning is doing work that should be owned by a shared backend service layer.
- The boundary between the Web UI and CLI is unclear, so behavior can diverge.
- Audio paths currently depend on local absolute paths, which makes portability and desktop packaging harder.
- There is no library config file yet, so a library has no durable place for root paths, scan settings, UI preferences, or derived cache locations.

## Product North Star

AMM should be treated as a local audio retrieval cockpit, not a generic metadata admin app. The primary user promise is: help a producer find the right sound fast while staying in a local, private, single-user workflow.

The core loop is:

1. Search by filename, tags, technical filters, or natural language.
2. Audition results immediately.
3. Decide whether a result is useful.
4. Locate/use the source audio file in the user's production workflow.
5. Correct tags or review metadata so the next search gets better.

Web is a validation client for this loop. It is not the product center and it should not pull ownership away from the Core library. The Web UI is useful because CLI search cannot provide fast audition and browsing, but new UI work must prove the retrieval loop before it expands the application surface.

## Agent Consistency Guardrails

When different agents work on AMM, use these guardrails to keep decisions aligned:

- Do not add new top-level Web pages until the main library/search page can complete the search -> audition -> decide -> locate/use -> correct loop against a real sample folder.
- Maintain a single shared search contract for CLI, Web API, and future desktop clients. Today that means the Web API returns an envelope with `query`, `total`, `limit`, `offset`, and `results`, and each result uses `file_name`, `path`, `score`, and `metadata`.
- Keep Web code as a Client. It may render, collect input, paginate, play audio, and show errors, but library loading, path resolution, search planning, filtering, mutation, and saving belong in Core services.
- Prefer fixing the retrieval loop over polishing dashboards, reports, settings, visual themes, or desktop packaging.
- Treat Tauri or Electron as packaging routes after the local search workflow is useful, not as a substitute for search quality.
- When behavior can be shared by CLI and Web, add it to `audio_metadata.library` or another Core service first, then call it from both surfaces.

## Destination Layers

The future shape should be three layers: Core library, CLI, and Client.

### Core library

The Core library should become the source of truth for loading, validating, normalizing, searching, mutating, and saving AMM libraries. The immediate next step is an `audio_metadata.library` service layer that hides raw `library.json` access behind stable functions and data contracts.

The first service responsibilities should include:

- Load and save library data through one path.
- Normalize records exactly once at the boundary.
- Provide stable search inputs and outputs for keyword search, structured filters, natural language parsing, sort, pagination, and result counts.
- Centralize frontend input cleaning so CLI, Web UI, and future desktop clients use the same rules.
- Resolve audio paths from configured library roots instead of assuming local absolute paths everywhere.
- Own scan workflow state such as source folders, recursive mode, include and exclude patterns, and last scan time.

### CLI

The CLI should become a thin command surface over the Core library. Commands such as index, search, nl-query, similar, review, review-batch, review-candidates, review-stats, auto-tag, and export-training should call `audio_metadata.library` services instead of each re-reading and reshaping the library file.

The CLI should remain useful for automation, tests, batch work, and power-user flows. It should also be the easiest place to prove new Core library behavior before the Client exposes it.

### Client

The Client should be any interactive user surface: current Web UI, future desktop app, or another local UI. Its job should be presentation and interaction, not library ownership. It should call a stable API backed by the Core library.

The sample browser UX target is:

- Left filters for folders, tags, type, loop state, tempo range, brightness, review status, and text search.
- Center list for searchable samples with stable pagination, sorting, selection, and scan state feedback.
- Right details for metadata, review overrides, derived values, source path, and edit history.
- Bottom player for transport, waveform or preview state, current sample, volume, and preview errors.

## Desktop Route

For a near-term desktop app, prefer Tauri or Electron wrapping a local FastAPI server. This keeps the Python audio and metadata logic in process with the existing backend while allowing a richer desktop shell for file dialogs, playback, and packaging.

PySide6/Qt remains a reasonable alternative if native widgets, deeper desktop integration, or a pure-Python distribution becomes more important than reusing the web client.

A desktop scan workflow should include:

1. Select or create an AMM library.
2. Choose one or more audio roots.
3. Configure recursive scan, include/exclude patterns, and output/cache locations.
4. Write those settings into `amm_config.json`.
5. Run scan through the Core library service layer.
6. Refresh the sample browser without requiring the user to manually pass `library.json` paths.

## Library Configuration

Introduce `amm_config.json` beside the library data. It should make a library self-describing without hard-coding one user's machine paths.

Initial fields should cover:

- Library schema version.
- Library file path or relative data directory.
- Audio root directories, preferably relative to the config when possible.
- Cache and generated artifact directories.
- Scan options such as recursive mode and include/exclude globs.
- Client preferences that are safe to share across sessions.

Path handling should support local absolute paths for today's single-user workflow, but the Core library should resolve paths through config so later portability work has one place to change.

## Near-Term Sequence

1. Build the first-run setup flow: choose sample folder, create managed library, scan, then open Library.
2. Add `audio_metadata.library` as the service boundary for managed library creation, summary, scan, load, normalize, save, and search.
3. Add Web scan support through a stable `POST /api/scan` endpoint and Library-page scan control.
4. Stabilize the current Web search contract so the Library page consumes `results[]` consistently and can audition returned paths.
5. Remove or hide UI that asks users to manage `library.json`, database paths, dead rescan/reindex actions, or CLI-first setup.
6. Move CLI commands to the Core service boundary one command group at a time.
7. Add portable library configuration only after setup and scan are usable from the UI. Configuration must remain internal unless there is a clear user-facing workflow.
8. Evolve the Client sample browser around left filters, center list, right details, and bottom player, without adding unrelated pages first.
9. Build the desktop shell with Tauri or Electron plus FastAPI only after the local setup -> scan -> search -> audition workflow is useful.
