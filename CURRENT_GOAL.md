# CURRENT_GOAL.md

## Version
- Current repo version: `v0.1-b9` 🚧 IN PROGRESS
- Previous version: `v0.1-b8` (Unified Search + Library Report) ✅ COMPLETE
- Current milestone: `v0.1-b9` (Web UI MVP)

---

## Goal (v0.1-b9) — Web UI MVP

**Core idea:** Add a local web interface (FastAPI + browser) so audio producers can search, preview, and manage samples without using the CLI.

**Why this matters:**
- CLI is not friendly for non-technical users (audio producers/musicians)
- No way to preview/listen to search results quickly
- Need to validate if audio producers will actually use AMM before investing in desktop app

**Product roadmap:**
- Phase 1 (v0.1-b9): FastAPI + Web UI — validate core workflow
- Phase 2: Polish experience (waveform, batch ops, favorites)
- Phase 3: Tauri desktop packaging for distribution

---

## v0.1-b9 Deliverables

### T1: FastAPI Server Entry
- [ ] `web_server.py` — Main FastAPI app, route registration, static files
- [ ] `requirements.txt` — Add fastapi, uvicorn

### T2: Search API
- [ ] `web/api_search.py` — GET /api/search?q={query}&limit={n}
- [ ] Call unified_search, return JSON results

### T3: Audio Streaming API
- [ ] `web/api_audio.py` — GET /api/audio/{file_path}
- [ ] Stream audio file for browser playback
- [ ] Security: restrict to configured sample directory

### T4: Report API
- [ ] `web/api_report.py` — GET /api/report
- [ ] Call report module, return JSON stats

### T5: Sample Detail + Edit API
- [ ] `web/api_sample.py` — GET /api/sample/{id}, PUT /api/sample/{id}/review
- [ ] Read/write review overrides

### T6: Search Page (Frontend)
- [ ] `web/static/index.html` — Search box, filters, results table, audio player

### T7: Report Page (Frontend)
- [ ] `web/static/report.html` — Library stats visualization

### T8: Frontend Logic
- [ ] `web/static/app.js` — API calls, DOM updates, audio playback

### T9: Styles
- [ ] `web/static/style.css` — Clean, minimal UI

### T10: API Tests
- [ ] `tests/test_web_api.py` — Test all API endpoints

### T11: Documentation
- [ ] `README.md` — Add Web UI section
- [ ] `CURRENT_GOAL.md` — Update to v0.1-b9

---

## Architecture

```
Browser (HTML/JS)
    │
    ▼
FastAPI (web_server.py)
    │
    ├── /api/search     → unified_search.py
    ├── /api/audio      → file streaming
    ├── /api/report     → report.py
    └── /api/sample     → schema.py + review
    │
    ▼
JSON library + audio files
```

---

## API Design

### Search
```
GET /api/search?q=dark+loop+120bpm&limit=20
→ { "query": "...", "strategy": "...", "total": 23, "results": [...] }
```

### Audio
```
GET /api/audio/path/to/file.wav
→ audio/mpeg (stream)
```

### Report
```
GET /api/report
→ { "total_files": 1562, "format_distribution": {...}, ... }
```

### Sample Detail
```
GET /api/sample/{id}
→ { full metadata }

PUT /api/sample/{id}/review
→ { "overrides": {...}, "notes": "..." }
```

---

## Success Criteria

1. `python web_server.py` starts the server
2. Browser opens http://localhost:8000
3. Search "kick drum" returns results with play buttons
4. Click ▶ plays audio
5. Report page shows library stats
6. Edit sample tags and save
7. `pytest tests/test_web_api.py -v` passes
8. `pytest tests/ -v` — no regression

---

## Design Constraints

- No database — continue using JSON
- No user auth — local tool
- No waveform — Phase 2
- No batch operations — Phase 2
- No Tauri — Phase 3
- Frontend: vanilla JS only (no React/Vue)
- All existing CLI commands remain unchanged
