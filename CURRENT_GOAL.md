# CURRENT_GOAL.md

## Version
- Current repo version: `v0.1-b4` ✅ **RELEASED** (local main, pending remote push)
- Planned next milestone: `v0.1-b5` (Auto Tagging / Model Outputs)

## Goal (v0.1-b5) — Auto Tagging Layer
Build the first minimal automatic tagging layer that populates `model_outputs` fields based on audio features.

## Already True In The Repo (v0.1-b4 delivered)
- Audio directories can be indexed into schema v1 JSON.
- Manual review overrides can correct a small set of derived and tempo fields.
- `review-batch`, `review-candidates`, and `review-stats` support a lightweight manual cleanup workflow.
- `search` already supports explicit filters such as keyword, loop state, brightness, tempo applicability, tempo quality, BPM range, duration range, and status.
- `nl-query` accepts natural language queries and converts them to structured search intent.
- `similar` already performs lightweight numeric-metadata ranking after candidate filtering.
- Schema normalization preserves reserved `retrieval`, `model_outputs`, and `segments` fields, but no automatic semantic pipeline populates them.
- Tests cover schema normalization, override behavior, batch review tools, NL query parser, and basic search/similar smoke paths.

## What's Missing (v0.1-b5 target)
- No automatic classifier that fills `model_outputs.is_dark`, `model_outputs.is_bright`, etc.
- No feature-based auto-tagging for mood, energy, or instrumentation.
- No batch auto-tag command.

## Explicitly Out Of Scope (v0.1-b5)
- Vector DBs, embeddings, ANN search, rerankers, or full semantic retrieval.
- UI, web app, or desktop app work.
- Cloud sync, shared state, or multi-user features.
- Schema v2 changes.

## Acceptance Criteria (v0.1-b5)
- A simple feature-based classifier can populate `model_outputs.is_dark` / `is_bright` based on spectral features.
- The classifier is deterministic and explainable (no black-box ML).
- Tests cover representative audio samples.
- A new `auto-tag` command applies the classifier to indexed audio.
- No schema change is required.

## Example Auto-Tag Rules (to be implemented)
- `is_dark`: low spectral centroid, minor mode preference
- `is_bright`: high spectral centroid, major mode preference
- `is_energetic`: high RMS energy, fast tempo
- `is_calm`: low RMS energy, slow tempo

## Suggested Task Sequence (v0.1-b5)
1. Define feature thresholds for `is_dark` / `is_bright` (spectral centroid percentiles).
2. Write tests for the auto-tag classifier.
3. Implement `auto_tag_audio()` function in `audio_metadata/`.
4. Add `auto-tag` CLI command to `app.py`.
5. Verify with a small test dataset.
6. Update README and this file.
