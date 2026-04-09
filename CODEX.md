# Codex Development Guide

## Project Overview

**audio-metadata-manager** — Local single-user audio sample manager core (v0.1-b3 → v0.1-b4)

**Current Goal:** Implement natural-language query layer that converts user text into structured search intent.

## Architecture

```
audio-metadata-manager/
├── app.py                    # Unified CLI entry point
├── main.py                   # Index command
├── review_metadata.py        # Review commands (single, batch, candidates, stats)
├── search_metadata.py        # Search with explicit field filters
├── search_similar.py         # Lightweight similarity retrieval
├── audio_metadata/           # Core package
│   ├── extractor.py          # Metadata & feature extraction
│   ├── scanner.py            # Filesystem discovery
│   ├── indexer.py            # Directory-to-JSON indexing
│   ├── schema.py             # Schema v1 normalization, review overrides
│   └── models.py             # Data models
├── tests/                    # Unit tests
└── examples/                 # Example fixtures
```

## CLI Commands

| Command | Purpose |
|---------|---------|
| `index` | Scan directory, export schema v1 JSON |
| `review` | Write manual overrides |
| `review-batch` | Batch review with presets |
| `review-candidates` | List records needing review |
| `review-stats` | Summarize review coverage |
| `search` | Query JSON with explicit filters |
| `similar` | Find similar items by numeric metadata |
| `nl-query` | **NEW (v0.1-b4)** — Natural language query |

## Schema v1 Fields

**Searchable fields for nl-query:**
- `keyword` — searches id, file_name, path, tags, etc.
- `is_loop` — boolean (true/false)
- `brightness` — dark/balanced/bright/very_bright
- `tempo_applicable` — boolean
- `tempo_quality` — high/medium/low/not_applicable
- `tempo_bpm` — numeric range (min/max)
- `duration_sec` — numeric range (min/max)
- `duration_bucket` — micro/short/medium/long
- `status` — ok/partial/failed

**Reserved (not used in v0.1-b4):**
- `retrieval.*` — tags, mood, texture, density, role, domain
- `model_outputs.*` — instrument_family, texture, timbre_type
- `segments` — segment-level analysis

## Development Rules

1. **TDD First** — Write tests before implementation
2. **Small Changes** — One behavior at a time
3. **Reuse Existing** — nl-query reuses search_metadata.py execution logic
4. **No Schema Changes** — v0.1-b4 does not modify schema v1
5. **Explainable** — Parser output must be inspectable in tests
6. **Safe Fallback** — Unknown wording doesn't crash, keeps as keyword

## NL Query Examples

```
Input: "dark drum loops around 128 bpm"
Intent: {brightness: "dark", keyword: "drum", is_loop: true, min_bpm: 120, max_bpm: 135}

Input: "bright percussion one shots"
Intent: {brightness: "bright", keyword: "percussion"}

Input: "show non-loop fills"
Intent: {keyword: "fill", is_loop: false}

Input: "slow loops under 90 bpm"
Intent: {is_loop: true, max_bpm: 90}

Input: "dark sounds with no tempo"
Intent: {brightness: "dark", tempo_applicable: false}
```

## Testing

```bash
# Run all tests
make test

# Run specific test module
python -m pytest tests/test_nl_query.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=term-missing
```

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/nl-query-v0.1-b4

# After each small change
git add <files>
git commit -m "feat: <description>"

# Before push, verify
make test
git log --oneline -5
```

## Codex Usage

```bash
# One-shot execution
codex exec --full-auto "<task description>"

# Interactive mode
codex

# Check status
codex login status
```

## Anti-Goals (Do NOT Add)

- UI, web app, or desktop app
- Cloud sync, multi-user features
- Vector DBs, embeddings, ANN search
- Automatic classifier pipelines
- Schema v2 changes
- Broad repo cleanup
