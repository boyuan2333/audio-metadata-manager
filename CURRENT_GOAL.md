# CURRENT_GOAL.md

## Version
- Current repo version: `v0.1-b6` 🚧 **IN PROGRESS**
- Previous version: `v0.1-b5` (Objective Auto-Tagging Layer) ✅
- Current milestone: `v0.1-b6` (ML-Based Subjective Tags)

## Goal (v0.1-b6) — ML-Based Subjective Tags 🚧 IN PROGRESS

Build a ML-based subjective classification layer that:
1. 🚧 Collects user-labeled training data from reviewed metadata
2. ⏳ Trains simple classifiers (Random Forest / Logistic Regression)
3. ⏳ Predicts subjective tags: `dark`, `bright`, `energetic`, `calm`
4. ⏳ Combines with objective auto-tags for hybrid scoring

## v0.1-b6 Deliverables

### Phase 1: Training Data Collection Pipeline ✅
- [x] `audio_metadata/training_data.py` — training data export module
  - `export_training_data()` — export labeled samples to CSV
  - `generate_training_report()` — analyze label distribution
  - Label extraction priority: subjective_tags > retrieval.tags > derived.brightness
- [x] `export_training_cli.py` — CLI command for training data export
  - `--report` mode for label distribution analysis
  - `--include-unlabeled` for semi-supervised learning
  - `--verbose` for detailed feature column info
- [x] `tests/test_training_data.py` — 7 unit tests (100% pass)
- [x] `app.py export-training` — integrated CLI command

### Phase 2: ML Classifier Training ⏳
- [ ] `audio_metadata/ml_classifier.py` — ML training module
  - Random Forest classifier (default)
  - Logistic Regression (alternative)
  - Cross-validation and metrics
- [ ] `tests/test_ml_classifier.py` — classifier tests

### Phase 3: Prediction Integration ⏳
- [ ] `audio_metadata/predict_tags.py` — prediction module
  - Load trained model
  - Predict subjective tags for new audio
  - Confidence scoring
- [ ] `predict_tags_cli.py` — CLI command for batch prediction
- [ ] `app.py predict-tags` — integrated CLI command

### Phase 4: Hybrid Scoring ⏳
- [ ] Combine objective + subjective tags
- [ ] Confidence-weighted tag application
- [ ] User feedback loop

## v0.1-b5 Deliverables ✅ COMPLETE

Build a minimal auto-tagging layer that:
1. ✅ Populates `model_outputs.auto_tags` with **objective, physically-measurable features**
2. ✅ Provides a clean interface for future ML-based subjective classifiers (v0.1-b6+)
3. ✅ All tags are deterministic and explainable (no ML black box)

## v0.1-b5 Deliverables

### Phase 1: Feature Detection Core ✅
- [x] `audio_metadata/auto_tag.py` — deterministic feature detection
  - `is_percussive` / `is_sustained` (HPSS separation, FitzGerald 2010)
  - `wide_spectrum` / `narrow_spectrum` (spectral bandwidth)
  - `is_bright` / `is_dark` (spectral centroid)
  - `is_noise_like` / `is_tone_like` (spectral flatness)
  - `high_tempo_confidence` / `low_tempo_confidence` (Font & Serra 2016)
- [x] `tests/test_auto_tag.py` — 16 unit tests (100% pass)

### Phase 2: CLI Integration ✅
- [x] `auto_tag_cli.py` — CLI command for batch processing
  - `--dry-run` preview mode
  - `--output` JSON file output
  - `--filter` file pattern matching
  - `--verbose` per-file output
  - `--sample-rate` configurable analysis sample rate
- [x] `app.py` integration — `auto-tag` subcommand
- [x] `tests/test_auto_tag_cli.py` — 18 integration tests (100% pass)

### Phase 3: ML Interface Stub ✅
- [x] `audio_metadata/schema.py` — `model_outputs` schema extension
  - `auto_tags` — stores auto-generated tags
  - `auto_tags_confidence` — confidence scores per tag
  - `classifier_version` — tracks classifier version
  - `classifier_type` — `deterministic_rules` (v0.1-b5) or `ml_model` (future)
  - `subjective_tags` — reserved for ML-based tags (v0.1-b6+)
  - `subjective_tags_confidence` — reserved for ML confidence
  - `ml_model_version` — reserved for ML model version
- [x] `tests/test_schema_model_outputs.py` — 16 schema tests (100% pass)

### Phase 4: Verification & Documentation ✅
- [x] Full test suite: 68 passed, 9 subtests passed
- [x] `README.md` updated with auto-tag documentation
- [x] `CURRENT_GOAL.md` updated (this file)
- [x] Git commits pushed to main

## Acceptance Criteria (v0.1-b5) — ALL MET ✅

### Objective Feature Tags (deterministic)
- [x] `is_percussive`: Percussive/Harmonic ratio > 0.6 (≈ P/H > 1.5)
- [x] `is_sustained`: Harmonic/Percussive ratio > 0.6 (≈ H/P > 1.5)
- [x] `wide_spectrum`: Frequency span > 3000Hz
- [x] `narrow_spectrum`: Frequency span < 1000Hz
- [x] `is_bright`: Spectral centroid > 2000Hz
- [x] `is_dark`: Spectral centroid < 500Hz
- [x] `is_noise_like`: Spectral flatness > -30dB
- [x] `is_tone_like`: Spectral flatness < -60dB
- [x] `high_tempo_confidence`: Tempo confidence > 0.8
- [x] `low_tempo_confidence`: Tempo confidence < 0.5

### ML Interface (stub for v0.1-b6+)
- [x] `model_outputs.auto_tags` — stores auto-generated tags
- [x] `model_outputs.auto_tags_confidence` — confidence scores per tag
- [x] `model_outputs.classifier_version` — classifier version tracking
- [x] `model_outputs.classifier_type` — distinguishes rules vs ML
- [x] Clean separation: objective tags (v0.1-b5) vs subjective tags (future)

### CLI & Tests
- [x] `auto-tag` command applies feature detection to audio files/directories
- [x] Tests cover representative synthetic audio samples
- [x] No schema change required (uses existing v1 structure)
- [x] Full test suite: 68 tests + 9 subtests passed

### Documentation
- [x] README.md updated with auto-tag usage examples
- [x] Feature tags table with physical basis and thresholds
- [x] Output JSON structure documented
- [x] Windows host audio access from WSL2 documented
- [x] CURRENT_GOAL.md updated

## Literature Support

v0.1-b5 design is backed by academic and industry standards:

| Feature | Reference | Standard |
|---------|-----------|----------|
| HPSS Separation | FitzGerald (2010) | Librosa default |
| Spectral Bandwidth | Essentia / AcousticBrainz | ISMIR 2013 |
| Spectral Centroid | ISMIR standard | Librosa default |
| Spectral Flatness | Essentia standard | -30dB / -60dB |
| Tempo Confidence | Font & Serra (2016) | ISMIR |

Full literature review: See Feishu docs "v0.1-b5 文献调研报告"

## Example Auto-Tag Output

```json
{
  "version": "v0.1-b5",
  "classifier": "v0.1-b5-objective",
  "total_files": 1,
  "successful": 1,
  "failed": 0,
  "results": [
    {
      "file": "/path/to/kick.wav",
      "tags": {
        "auto_tags": ["is_percussive", "wide_spectrum"],
        "auto_tags_confidence": {
          "is_percussive": 0.89,
          "wide_spectrum": 0.72
        },
        "classifier_version": "v0.1-b5-objective",
        "classifier_type": "deterministic_rules",
        "feature_params": {
          "n_fft": 2048,
          "hop_length": 512,
          "sr": 22050
        }
      }
    }
  ]
}
```

## Usage Examples

```bash
# Preview mode
python app.py auto-tag ./audio/samples --dry-run -v

# Batch tag to JSON
python app.py auto-tag ./audio/samples -o tags.json -v

# Filter by file type
python app.py auto-tag ./audio/samples --filter "*.wav" -o tags.json

# Access Windows host audio from WSL2
python app.py auto-tag /mnt/c/Users/bo/Music/Samples -o tags.json -v
```

## Schema Integration

Auto-tag results integrate with schema v1 `model_outputs`:

```json
{
  "model_outputs": {
    "auto_tags": ["is_percussive", "wide_spectrum"],
    "auto_tags_confidence": {
      "is_percussive": 0.89,
      "wide_spectrum": 0.72
    },
    "classifier_version": "v0.1-b5-objective",
    "classifier_type": "deterministic_rules",
    "instrument_family": null,
    "texture": null,
    "timbre_type": null,
    "subjective_tags": [],
    "subjective_tags_confidence": {},
    "ml_model_version": null
  }
}
```

## Roadmap Beyond v0.1-b5

### v0.1-b6: ML-Based Subjective Tags
- Collect user-labeled training data (via review workflow)
- Train simple classifier (Random Forest / Logistic Regression)
- Add subjective tags: `dark`, `bright`, `energetic`, `calm`
- Keep objective tags as fallback/explanation
- Populate `model_outputs.subjective_tags` and `ml_model_version`

### v0.1-b7: Hybrid Scoring
- Combine objective features + ML predictions
- Confidence-weighted tag application
- User feedback loop improves ML over time

## Success Metrics (v0.1-b5)

| Metric | Target | Actual |
|--------|--------|--------|
| Objective tag accuracy (vs manual review) | > 80% agreement | TBD (needs user validation) |
| Processing speed | > 10 files/second | ~1-2 files/sec (depends on audio length) |
| User override rate | < 30% (tags users reject) | TBD (needs user validation) |
| Code coverage | > 80% for auto_tag.py | ~90% (50 tests covering core logic) |
| Test suite | All tests pass | ✅ 68 passed, 9 subtests passed |

## Git History (v0.1-b5)

| Commit | Description |
|--------|-------------|
| `3c22275` | feat(v0.1-b5): add auto-tag CLI command with batch processing |
| `cd93a02` | feat(v0.1-b5): add objective auto-tagging with HPSS/spectral/tempo features |
| `67885c8` | docs: update v0.1-b5 goal — objective feature tags + ML interface stub |

---

**v0.1-b5 is COMPLETE.** Ready for v0.1-b6 (ML-Based Subjective Tags) planning.
