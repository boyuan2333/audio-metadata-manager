# AMM Retrieval Cockpit PRD

## Product Positioning

AMM is a local audio retrieval cockpit for producers. It should help the user turn a sample folder into a searchable, auditionable library without asking them to understand JSON files, databases, config files, or command-line workflows.

The Web UI is not a generic admin dashboard. It is the first interactive client for the retrieval loop:

1. Choose a sample folder.
2. Create or open the local AMM library.
3. Scan the folder from the UI.
4. Search and filter sounds.
5. Audition results immediately.
6. Open, copy, or locate the source file.
7. Correct tags or metadata when results are wrong.

## Target User

Primary user: a music producer, sound designer, or sample-heavy creator working on a local machine.

They usually think in terms like:

- "Find a dark 120 bpm loop."
- "Find kicks like this one."
- "Show me short vocal chops."
- "I want to hear results quickly."

They should not need to think in terms like:

- `library.json`
- database path
- config path
- CLI arguments
- schema versions

## Product Principles

- Hide implementation details. JSON and config files are internal storage, not user-facing setup concepts.
- The first-run experience must be guided. An empty app should not show empty dashboards or loading placeholders.
- Scanning must exist in the UI. A user should not have to run `python app.py index` before the Web UI becomes useful.
- Search and audition are the core. Reports, settings, visual polish, and desktop packaging are secondary.
- Every visible button should either work now or be removed from the UI.
- Advanced storage paths may be shown read-only for debugging, but should not be presented as required user input.

## First-Run Wizard

The first time AMM starts without a usable library, show a setup wizard instead of the normal dashboard.

Wizard steps:

1. Select Sample Folder
   - User chooses or enters a folder containing audio samples.
   - Validate that the folder exists.
   - Show a warning if no supported audio files are found.

2. Create Library
   - AMM creates a managed library at `<sample-folder>/.amm/library.json`.
   - The user does not choose this path.
   - If `.amm/library.json` already exists, offer to open it.

3. Scan
   - User starts scan from the wizard.
   - Show progress state: pending, scanning, complete, failed.
   - When complete, show number of indexed files and a button to open Library.

4. Search Smoke Test
   - Open the Library page with an initial query or empty result list.
   - Prompt user to try a search such as `kick`, `loop`, or `120 bpm`.

## Main Library Experience

The Library page should become the primary workspace.

Required capabilities:

- Search input with natural language and keyword support.
- Filters for format, brightness, loop state, BPM range, duration, and review status.
- Results list with stable pagination and sort.
- Play button for each result.
- Bottom mini player for current sound.
- Open file location or copy file path.
- Detail/review panel for correcting tags and notes.
- Visible empty states when no library, no scan, no results, or broken audio path.

## Scan Experience

Scanning must be available from the UI in two places:

- First-run wizard.
- Library page toolbar or setup/status area.

Scan requirements:

- Start scan for the configured sample directory.
- Write results to the managed library file.
- Support recursive scan by default.
- Show total discovered files, indexed files, failed files, and elapsed time.
- Do not block the whole UI without feedback.
- After scan completes, refresh Library results.

Non-goals for the first scan UI:

- Watch mode.
- Background service.
- Multi-folder libraries.
- Include/exclude pattern editor.
- Full task queue system.

## UX Issues To Fix

These are current or likely mismatches with producer expectations:

- Empty Settings requires users to understand library paths.
- Scan is still CLI-first.
- Dashboard can appear before a library exists.
- Report page is less important than finding and hearing sounds.
- Editor is separated from search results; corrections should be reachable from the result row or side panel.
- Language switching is partial; visible navigation and setup text must switch together.
- Audio path failures need clear inline explanations and a way to fix the sample folder.
- Buttons for rescan/reindex must not exist until backed by real APIs.
- The app should not use "database" as a primary user-facing term.

## Success Metrics

For v0.1-b10, success means:

- A new user can start the Web UI with no CLI indexing step.
- They can choose a sample folder, create a managed library, scan it, search it, and play a result.
- No user-facing step asks for a JSON path.
- The Library page communicates empty, scanning, no result, and playback error states clearly.
- Tests cover setup, scan API, managed library creation, search result contract, and key static UI expectations.

## Out Of Scope

- Desktop packaging.
- Cloud sync.
- Multi-user accounts.
- Full i18n across every historical page.
- ML subjective classifiers.
- Vector database or external search service.
