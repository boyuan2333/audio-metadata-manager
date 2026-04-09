# Audio Metadata MVP v0.1-b4

`audio-metadata-mvp` is a local single-user audio sample manager core. It scans a folder of audio files, writes schema v1 JSON, supports minimal manual review overrides, searches that JSON with explicit metadata filters, **accepts natural language queries**, performs lightweight similarity retrieval from a reference audio file after candidate filtering, and adds a minimal batch-review workflow for real libraries.

v0.1-b4 intentionally stays small:

- Local only
- Single user
- JSON storage
- Explicit field search
- **Natural language query (v0.1-b4 new)**
- Lightweight similar retrieval
- Minimal `review.overrides` editing
- Batch review presets, grouped candidate discovery, and finer review stats

It does not include a database, vector store, UI, team workflows, cloud sync, segment analysis, retrieval overrides, or automatic `model_outputs` classification.

## v0.1-b4 Capabilities

- `index`: scan a local directory and export schema v1 JSON
- `review`: write minimal manual overrides into `review.overrides`
- `review-batch`: reuse explicit search filters or built-in presets, then preview or apply safe batch review updates
- `review-candidates`: list high-value records grouped by review rule, with recommended next actions
- `review-stats`: summarize current override coverage, note prefixes, inferred sources, and common reviewed filename keywords
- `search`: query the exported JSON with explicit field filters
- **`nl-query`: search with natural language queries (v0.1-b4 new)**
- `similar`: filter candidates, then rank them against a reference audio file using current numeric metadata
- Stable schema v1 with reserved space for future `segments`, `model_outputs`, and `retrieval` expansion

## Project Layout

```text
audio-metadata-mvp/
  app.py
  main.py
  review_metadata.py
  search_metadata.py
  search_similar.py
  audio_metadata/
    __init__.py
    extractor.py
    indexer.py
    models.py
    scanner.py
    schema.py
  audio/
  out/
  tests/
  README.md
  requirements.txt
```

Module boundaries in v0.1-b3:

- `audio_metadata.extractor`: per-file metadata and feature extraction
- `audio_metadata.scanner`: filesystem audio discovery
- `audio_metadata.indexer`: directory-to-JSON indexing flow
- `audio_metadata.schema`: schema v1 normalization, review override validation, and effective value shaping
- `review_metadata.py`: single-review editing, preset-based batch review, grouped candidate discovery, and finer review stats
- `app.py`: recommended unified CLI entry
- `main.py`, `review_metadata.py`, `search_metadata.py`, `search_similar.py`: direct entry points kept for local use where they already existed

## Installation

Recommended: use a Python 3.12 or 3.13 virtual environment if dependency installation on Python 3.14 is unstable.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Unified CLI

v0.1-b3 recommends `app.py` as the main entry point.

### Index

```bash
python app.py index --input ./audio --output ./out/library.json
python app.py index --input ./audio --output ./out/library.json --recursive
```

### Review

Write minimal manual overrides into `review.overrides` without modifying the original extracted fields:

```bash
python app.py review --input ./out/library.json --id <record_id> --is-loop false --brightness dark
python app.py review --input ./out/library.json --source-path ./audio/ref.wav --tempo-applicable false --tempo-bpm null --tempo-quality not_applicable --note "manual correction"
python app.py review --input ./out/library.json --id <record_id> --clear tempo_bpm notes
```

Supported override fields in v0.1-b3:

- `derived.is_loop`
- `derived.brightness`
- `derived.tempo_applicable`
- `features.tempo_bpm`
- `features.tempo_quality`
- `review.notes`

### Review Batch

`review-batch` now supports both manual `--set-*` updates and a small set of safe built-in presets. Presets keep the same dry-run/apply workflow, still accept explicit search filters for narrowing, and require `--output` when you apply them so reviewed copies stay separate from the main file.

Current presets:

- `restore-bpm-from-filename-for-loops`: restore `tempo_applicable`, `tempo_bpm`, and `tempo_quality=low` from filename BPM digits for loop material with disabled or missing tempo
- `mark-fill-as-non-loop`: set `derived.is_loop=false` for `fill` token matches
- `mark-dark-name-as-dark`: set `derived.brightness=dark` for `dark` token matches

Safety behavior in v0.1-b3:

- Default mode is dry-run
- Only `--apply` writes JSON
- Preset apply requires `--output <json>`
- Manual `review-batch` without a preset still requires at least one explicit filter

Minimal examples:

```bash
python app.py review-batch --input ./out/library.json --preset restore-bpm-from-filename-for-loops
python app.py review-batch --input ./out/library.json --preset restore-bpm-from-filename-for-loops --keyword KSHMR_100_vocal_loop --apply --output ./out/library-reviewed-b3.json
python app.py review-batch --input ./out/library.json --preset mark-fill-as-non-loop --keyword fill
python app.py review-batch --input ./out/library.json --preset mark-dark-name-as-dark --apply --output ./out/library-reviewed-b3.json
python app.py review-batch --input ./out/library.json --keyword fill --is-loop true --set-is-loop false --set-note "drum fill path: mark as non-loop"
```

Supported narrowing filters still reuse the current explicit search path, including:

- `--keyword`
- `--is-loop`
- `--brightness`
- `--tempo-applicable`
- `--tempo-quality`
- `--min-bpm`
- `--max-bpm`
- `--min-duration`
- `--max-duration`
- `--status`

### Review Candidates

`review-candidates` now behaves more like a review todo list. Output is grouped by rule, each rule group shows a candidate count plus example records, and each group includes a recommended next action so it maps directly into the new presets.

Current rules:

- Rule A: filename contains BPM-like digits, but `tempo_applicable=false` or `tempo_bpm=null`
- Rule B: filename contains a `fill` token, but `is_loop=true`
- Rule C: filename contains `dark`, but `brightness != dark`
- Rule D: optional low-tempo-quality loop or tempo-filterable material

Minimal examples:

```bash
python app.py review-candidates --input ./out/library-reviewed.json
python app.py review-candidates --input ./out/library-reviewed.json --rule A --limit 10
python app.py review-candidates --input ./out/library-reviewed.json --include-rule-d --limit 5
```

### Review Stats

`review-stats` still keeps the simple CLI text summary, but now adds a little more workflow signal.

Current output includes:

- reviewed record count
- per-override-field correction counts
- most common correction-type combinations
- most common full notes
- most common note prefixes such as `preset` or `batch b2`
- inferred correction sources such as `restore-bpm-from-filename-for-loops`
- rough reviewed filename keyword counts

Minimal examples:

```bash
python app.py review-stats --input ./out/library-reviewed.json
python app.py review-stats --input ./out/library-reviewed.json --top-notes 10 --top-note-prefixes 10 --top-sources 8 --top-combos 5 --top-keywords 8
```

### NL Query (v0.1-b4 new)

Search using natural language instead of explicit filters. The parser converts your query into structured intent and reuses the existing search execution:

```bash
python app.py nl-query --query "dark drum loops around 128 bpm" --input ./out/library.json
python app.py nl-query --query "bright percussion one shots" --input ./out/library.json
python app.py nl-query --query "slow loops under 90 bpm" --input ./out/library.json
python app.py nl-query --query "dark sounds with no tempo" --input ./out/library.json
```

**Supported query patterns:**
- Brightness: `dark`, `balanced`, `bright`, `very bright`
- Loop state: `loop(s)`, `one shot(s)`, `non-loop`, `fill(s)`
- Tempo: `no tempo`, `without tempo`, `no bpm`
- BPM: `X bpm`, `around X bpm`, `under X bpm`, `over X bpm`, `between X and Y bpm`
- Unrecognized words fall back to keyword search

**Output includes:**
- Matched record count
- Parsed intent (for inspection)
- Matched fields per record

### Search

```bash
python app.py search --input ./out/library.json --keyword drum --is-loop true
python app.py search --input ./out/library.json --tempo-applicable true --brightness bright --min-bpm 100 --max-bpm 140
python app.py search --input ./out/library.json --tempo-quality not_applicable --limit 5
```

### Similar

```bash
python app.py similar --input ./out/library.json --reference ./audio/ref.wav --is-loop true --top-k 5
python app.py similar --input ./audio --reference ./audio/ref.wav --recursive --is-loop true --top-k 5
```

The similarity stage uses only current numeric metadata fields:

- `technical.duration_sec`
- `features.tempo_bpm`
- `features.tempo_confidence`
- `features.spectral_centroid_hz`
- `features.rms`
- `features.loudness_lufs`

Discrete fields remain filters only.

## Recommended Workflow

A minimal v0.1-b3 workflow for a real sample library:

1. Run `review-candidates` to surface grouped rule buckets.
2. Pick the rule group you want to work on, then choose the matching `review-batch --preset`.
3. Run the preset in dry-run mode first and inspect the preview.
4. Re-run the preset with `--apply --output <reviewed-copy.json>` to write a reviewed copy.
5. Use `search` and `similar` against that reviewed copy to confirm retrieval improved.
6. Run `review-stats` to see which fields, note prefixes, and inferred sources dominate.

## Effective Value Precedence

For JSON-backed `search` and `similar`, effective values are resolved in this order:

1. Legal `review.overrides`
2. Original schema v1 fields
3. Alias fields only as compatibility output

This means `search` and JSON-backed `similar` will use override-adjusted values for:

- `derived.is_loop`
- `derived.brightness`
- `derived.tempo_applicable`
- `features.tempo_bpm`
- `features.tempo_quality`

## Schema v1 Notes

Top-level export shape:

```json
{
  "schema_version": "v1",
  "app_version": "v0.1-b3",
  "run": {},
  "files": [
    {
      "id": "2c9f...",
      "status": "ok",
      "source": {
        "path": "E:\\audio\\samples\\cue_01.wav",
        "file_name": "cue_01.wav",
        "file_format": "wav"
      },
      "technical": {
        "duration_sec": 12.345678,
        "sample_rate_hz": 48000,
        "channels": 2
      },
      "features": {
        "loudness_lufs": -15.203,
        "tempo_bpm": 120.0,
        "tempo_confidence": 0.742,
        "tempo_quality": "high",
        "spectral_centroid_hz": 1842.117,
        "rms": 0.082314
      },
      "derived": {
        "tempo_applicable": true,
        "is_loop": true,
        "duration_bucket": "short",
        "brightness": "bright"
      },
      "retrieval": {
        "tags": [],
        "mood": null,
        "texture": null,
        "density": null,
        "role": null,
        "domain": null
      },
      "review": {
        "overrides": {
          "derived": {
            "is_loop": false,
            "brightness": "dark",
            "tempo_applicable": false
          },
          "features": {
            "tempo_bpm": null,
            "tempo_quality": "not_applicable"
          }
        },
        "notes": [
          "manual correction"
        ]
      },
      "model_outputs": {
        "instrument_family": null,
        "texture": null,
        "timbre_type": null
      },
      "segments": [],
      "errors": []
    }
  ]
}
```

Compatibility notes:

- Alias fields such as `file_name`, `source_path`, `file_format`, `tempo_applicable`, `is_loop`, `duration_bucket`, and `brightness` are still written to each record so older scripts do not break.
- Old JSON files with top-level `files[]` flat records can still be loaded; any review write-back normalizes the whole file to schema v1.
- `similar --input <directory>` does not read `review.overrides`; overrides are only available on the JSON input path.

## Current Limits

- JSON is the only storage layer in v0.1-b3
- Review write-back still only supports the five override fields listed above plus `review.notes`
- There is no retrieval override support and no arbitrary nested patch system
- `tempo_bpm` is heuristic and may still be half-time or double-time relative to musical intent
- `tempo_applicable`, `tempo_quality`, `is_loop`, and `brightness` are useful retrieval helpers, not ground truth labels
- Similar retrieval is intentionally lightweight and uses current numeric metadata only
- There is no segment-level analysis yet
- `model_outputs` is reserved but not populated by a classifier yet

## Compatibility Entry Points

These remain available, but `app.py` is the recommended interface:

```bash
python main.py --input ./audio --output ./out/library.json
python review_metadata.py --input ./out/library.json --id <record_id> --is-loop false
python search_metadata.py --input ./out/library.json --keyword horn
python search_similar.py --input ./out/library.json --reference ./audio/ref.wav --top-k 5
```

