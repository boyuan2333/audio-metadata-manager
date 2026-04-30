# Audio Metadata Manager

Local, single-user CLI tools for indexing, reviewing, searching, tagging, and preparing audio sample metadata.

This project is intentionally small. It uses local files, JSON, and deterministic feature extraction instead of a database, cloud sync, UI, or vector store.

Current version: **v0.1-b6**

## What It Does

Audio Metadata Manager helps you turn a folder of samples into a searchable metadata library.

Core workflow:

1. Scan audio files into a schema v1 JSON library.
2. Review and correct metadata with explicit override fields.
3. Search the library with filters or natural language.
4. Rank similar sounds from a reference audio file.
5. Generate deterministic objective auto-tags.
6. Export reviewed data for future subjective ML classification.

## Features

- Local folder indexing into JSON
- Technical metadata extraction: duration, sample rate, channels, format
- Audio feature extraction: loudness, RMS, tempo, spectral features
- Manual review overrides without destroying original extracted values
- Safe batch-review presets with dry-run/apply behavior
- Review candidate discovery and review coverage stats
- Explicit metadata search
- Natural language query parsing
- Lightweight similarity ranking after candidate filtering
- Deterministic objective auto-tagging
- Training CSV export for future subjective labels such as `dark`, `bright`, `energetic`, and `calm`

## What It Is Not

This is not a full sample-library app yet.

Missing by design in the current version:

- No database
- No GUI
- No cloud sync
- No multi-user workflow
- No vector store
- No segment-level analysis
- No arbitrary nested JSON patch system
- No trained subjective classifier yet

## Installation

Python 3.12 or 3.13 is recommended. Python 3.14 may have dependency issues depending on your environment.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS/Linux/WSL:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Dependencies are listed in `requirements.txt`:

- `librosa`
- `mutagen`
- `numpy`
- `pyloudnorm`
- `scipy`
- `soundfile`

## Quick Start

Create a metadata library from an audio folder:

```bash
python app.py index --input ./audio --output ./out/library.json --recursive
```

Search that library:

```bash
python app.py search --input ./out/library.json --keyword drum --is-loop true
python app.py search --input ./out/library.json --brightness bright --min-bpm 100 --max-bpm 140
```

Use natural language search:

```bash
python app.py nl-query --query "dark drum loops around 128 bpm" --input ./out/library.json
python app.py nl-query --query "bright percussion one shots" --input ./out/library.json
```

Find similar sounds:

```bash
python app.py similar --input ./out/library.json --reference ./audio/ref.wav --is-loop true --top-k 5
```

Generate objective auto-tags:

```bash
python app.py auto-tag ./audio/samples --dry-run -v
python app.py auto-tag ./audio/samples -o tags.json -v
```

Export reviewed data for ML training:

```bash
python app.py export-training --input ./out/library-reviewed.json --report
python app.py export-training --input ./out/library-reviewed.json --output ./out/training.csv
```

## Commands

### `index`

Scan a directory and write schema v1 JSON.

```bash
python app.py index --input ./audio --output ./out/library.json
python app.py index --input ./audio --output ./out/library.json --recursive
```

### `search`

Search an indexed JSON file with explicit filters.

```bash
python app.py search --input ./out/library.json --keyword kick
python app.py search --input ./out/library.json --is-loop true --tempo-applicable true
python app.py search --input ./out/library.json --tempo-quality not_applicable --limit 5
```

Common filters include:

- `--keyword`
- `--is-loop`
- `--brightness`
- `--tempo-applicable`
- `--tempo-quality`
- `--min-bpm` / `--max-bpm`
- `--min-duration` / `--max-duration`
- `--status`

### `nl-query`

Parse a natural language query into structured search filters.

```bash
python app.py nl-query --query "slow loops under 90 bpm" --input ./out/library.json
python app.py nl-query --query "dark sounds with no tempo" --input ./out/library.json
```

Supported query ideas:

- Brightness: `dark`, `balanced`, `bright`, `very bright`
- Loop state: `loop`, `one shot`, `non-loop`, `fill`
- Tempo: `no tempo`, `without tempo`, `no bpm`
- BPM ranges: `around 128 bpm`, `under 90 bpm`, `over 140 bpm`, `between 100 and 120 bpm`
- Unknown words fall back to keyword search

### `similar`

Filter candidates first, then rank them against a reference audio file.

```bash
python app.py similar --input ./out/library.json --reference ./audio/ref.wav --top-k 5
python app.py similar --input ./out/library.json --reference ./audio/ref.wav --is-loop true --top-k 10
```

Similarity currently uses numeric metadata only:

- `technical.duration_sec`
- `features.tempo_bpm`
- `features.tempo_confidence`
- `features.spectral_centroid_hz`
- `features.rms`
- `features.loudness_lufs`

Discrete fields are filters, not similarity dimensions.

### `review`

Write manual corrections into `review.overrides`.

```bash
python app.py review --input ./out/library.json --id <record_id> --is-loop false --brightness dark
python app.py review --input ./out/library.json --source-path ./audio/ref.wav --tempo-applicable false --tempo-bpm null --tempo-quality not_applicable --note "manual correction"
python app.py review --input ./out/library.json --id <record_id> --clear tempo_bpm notes
```

Supported override fields:

- `derived.is_loop`
- `derived.brightness`
- `derived.tempo_applicable`
- `features.tempo_bpm`
- `features.tempo_quality`
- `review.notes`

### `review-batch`

Preview or apply review overrides to matched records.

Default behavior is dry-run. Writing requires `--apply` and an explicit `--output` file.

```bash
python app.py review-batch --input ./out/library.json --preset restore-bpm-from-filename-for-loops
python app.py review-batch --input ./out/library.json --preset mark-fill-as-non-loop --keyword fill
python app.py review-batch --input ./out/library.json --keyword fill --is-loop true --set-is-loop false --set-note "drum fill path: mark as non-loop"
python app.py review-batch --input ./out/library.json --preset mark-dark-name-as-dark --apply --output ./out/library-reviewed.json
```

Built-in presets:

- `restore-bpm-from-filename-for-loops`
- `mark-fill-as-non-loop`
- `mark-dark-name-as-dark`

### `review-candidates`

Find records that probably need manual review.

```bash
python app.py review-candidates --input ./out/library.json
python app.py review-candidates --input ./out/library.json --rule A --limit 10
python app.py review-candidates --input ./out/library.json --include-rule-d --limit 5
```

Current candidate rules:

- Rule A: filename contains BPM-like digits, but tempo is missing or disabled
- Rule B: filename contains a `fill` token, but `is_loop=true`
- Rule C: filename contains `dark`, but brightness is not `dark`
- Rule D: optional low-tempo-quality loop or tempo-filterable material

### `review-stats`

Summarize review coverage and correction patterns.

```bash
python app.py review-stats --input ./out/library-reviewed.json
python app.py review-stats --input ./out/library-reviewed.json --top-notes 10 --top-note-prefixes 10 --top-sources 8 --top-combos 5 --top-keywords 8
```

### `auto-tag`

Generate deterministic, objective tags from measurable audio features.

```bash
python app.py auto-tag ./audio/samples --dry-run -v
python app.py auto-tag ./audio/samples -o tags.json -v
python app.py auto-tag ./audio/samples --filter "*.wav" -o tags.json
python app.py auto-tag ./audio/samples -s 44100 -o tags.json
```

Objective tags include:

| Tag | Basis |
| --- | --- |
| `is_percussive` | HPSS percussive/harmonic ratio |
| `is_sustained` | HPSS harmonic/percussive ratio |
| `wide_spectrum` | Spectral bandwidth |
| `narrow_spectrum` | Spectral bandwidth |
| `is_bright` | Spectral centroid |
| `is_dark` | Spectral centroid |
| `is_noise_like` | Spectral flatness |
| `is_tone_like` | Spectral flatness |
| `high_tempo_confidence` | Tempo confidence |
| `low_tempo_confidence` | Tempo confidence |

### `export-training`

Export reviewed records into CSV for future subjective ML classification.

```bash
python app.py export-training --input ./out/library-reviewed.json --report
python app.py export-training --input ./out/library-reviewed.json --output ./out/training.csv
python app.py export-training --input ./out/library-reviewed.json --output ./out/training.csv --include-unlabeled
```

Training labels are extracted in this order:

1. `model_outputs.subjective_tags`
2. matching tags in `retrieval.tags`
3. `derived.brightness` mapped to `dark` or `bright`

Target subjective labels:

- `dark`
- `bright`
- `energetic`
- `calm`

## JSON Schema Overview

The index command writes schema v1 JSON with this general shape:

```json
{
  "schema_version": "v1",
  "app_version": "v0.1-b6",
  "run": {},
  "files": [
    {
      "id": "...",
      "status": "ok",
      "source": {},
      "technical": {},
      "features": {},
      "derived": {},
      "retrieval": {},
      "review": {
        "overrides": {},
        "notes": []
      },
      "model_outputs": {},
      "segments": [],
      "errors": []
    }
  ]
}
```

For JSON-backed `search` and `similar`, effective values are resolved in this order:

1. Valid `review.overrides`
2. Original schema v1 fields
3. Compatibility alias fields

This means manual review corrections affect retrieval without deleting the original extracted metadata.

## Project Layout

```text
audio-metadata-manager/
  app.py                  # Unified CLI entry
  main.py                 # Index command
  review_metadata.py      # Review, batch review, candidates, stats
  search_metadata.py      # Explicit search
  search_similar.py       # Similarity search
  nl_query.py             # Natural language query
  auto_tag_cli.py         # Objective auto-tag CLI
  export_training_cli.py  # Training data export CLI
  audio_metadata/         # Core package
  audio/                  # Local sample input folder, optional
  out/                    # Local output folder, optional
  tests/
  requirements.txt
  README.md
```

## Compatibility Entry Points

`app.py` is the recommended interface, but older direct entry points still exist:

```bash
python main.py --input ./audio --output ./out/library.json
python review_metadata.py --input ./out/library.json --id <record_id> --is-loop false
python search_metadata.py --input ./out/library.json --keyword horn
python search_similar.py --input ./out/library.json --reference ./audio/ref.wav --top-k 5
```

## Current Limits

- JSON is the only storage layer.
- Review write-back supports only the listed override fields.
- Similarity search is intentionally lightweight.
- Tempo detection is heuristic and may produce half-time or double-time results.
- Objective auto-tags are deterministic rules, not musical taste judgments.
- Subjective ML classification is not implemented yet; v0.1-b6 only prepares/export training data.
- Segment-level analysis is still reserved for future work.

## WSL2 Path Note

From WSL2, Windows files are available under `/mnt`.

```bash
# Windows path:
# C:\Users\bo\Music\Samples

# WSL2 path:
python app.py auto-tag /mnt/c/Users/bo/Music/Samples -o tags.json -v
```

Accessing `/mnt` paths can be slower than using files inside the native WSL2 filesystem. For large libraries, copy samples into WSL first.
