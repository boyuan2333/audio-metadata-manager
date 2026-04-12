# CURRENT_GOAL.md

## Version
- Current repo version: `v0.1-b4` ✅ **RELEASED**
- Planned next milestone: `v0.1-b5` (Objective Feature Tags + ML Interface)

## Goal (v0.1-b5) — Objective Feature Tags + ML Interface

Build a minimal auto-tagging layer that:
1. Populates `model_outputs.auto_tags` with **objective, physically-measurable features**
2. Provides a clean interface for future ML-based subjective classifiers (v0.1-b6+)

## Philosophy

**What we CAN do with deterministic rules:**
- Detect percussive vs sustained content (Percussive/Harmonic separation)
- Measure frequency range (spectral span)
- Detect tempo confidence
- Measure dynamic range

**What we CANNOT do reliably without ML:**
- Subjective labels like `dark` / `bright` / `energetic` / `calm`
- Mood, emotion, genre classification
- Context-dependent perceptions

**Design decision:**
- v0.1-b5: Objective feature tags only (deterministic, explainable)
- v0.1-b6+: ML-based subjective classifiers (trained on user-labeled data)

## Already True In The Repo (v0.1-b4 delivered)
- Audio directories can be indexed into schema v1 JSON.
- Manual review overrides can correct a small set of derived and tempo fields.
- `review-batch`, `review-candidates`, and `review-stats` support a lightweight manual cleanup workflow.
- `search` already supports explicit filters such as keyword, loop state, brightness, tempo applicability, tempo quality, BPM range, duration range, and status.
- `nl-query` accepts natural language queries and converts them to structured search intent.
- `similar` already performs lightweight numeric-metadata ranking after candidate filtering.
- Schema v1 reserves `model_outputs` and `retrieval` fields.
- Tests cover schema normalization, override behavior, batch review tools, NL query parser, and basic search/similar smoke paths.

## What's Missing (v0.1-b5 target)
- No automatic feature detection for percussive/s sustained content.
- No frequency range analysis.
- No tempo confidence scoring.
- No `auto-tag` CLI command.
- No ML interface stub for future subjective classifiers.

## Explicitly Out Of Scope (v0.1-b5)
- Subjective labels (`dark`, `bright`, `energetic`, `calm`, etc.)
- ML model training or inference
- Vector DBs, embeddings, ANN search
- UI, web app, or desktop app work
- Cloud sync, shared state, or multi-user features
- Schema v2 changes

## Acceptance Criteria (v0.1-b5)

### Objective Feature Tags (deterministic)
- [ ] `is_percussive`: Percussive/Harmonic ratio > 0.7
- [ ] `is_sustained`: Harmonic/Percussive ratio > 0.7
- [ ] `wide_spectrum`: Frequency span > 4000Hz
- [ ] `narrow_spectrum`: Frequency span < 1000Hz
- [ ] `high_tempo_confidence`: Tempo detection confidence > 0.8
- [ ] `low_tempo_confidence`: Tempo detection confidence < 0.3

### ML Interface (stub for v0.1-b6+)
- [ ] `model_outputs.auto_tags` — stores auto-generated tags
- [ ] `model_outputs.auto_tags_confidence` — confidence scores per tag
- [ ] `model_outputs.classifier_version` — which classifier generated the tags
- [ ] Clean separation: objective tags (v0.1-b5) vs subjective tags (future)

### CLI & Tests
- [ ] `auto-tag` command applies feature detection to indexed audio
- [ ] Tests cover representative audio samples
- [ ] No schema change required (uses existing v1 structure)

## Example Auto-Tag Output

```json
{
  "model_outputs": {
    "auto_tags": ["is_percussive", "wide_spectrum", "high_tempo_confidence"],
    "auto_tags_confidence": {
      "is_percussive": 0.89,
      "wide_spectrum": 0.72,
      "high_tempo_confidence": 0.95
    },
    "classifier_version": "v0.1-b5-objective"
  }
}
```

## Feature Detection Algorithms

### is_percussive / is_sustained
```python
# Using librosa's percussive/harmonic separation
D = librosa.stft(audio)
D_harmonic, D_percussive = librosa.decompose.hpss(D)

percussive_energy = np.mean(np.abs(D_percussive))
harmonic_energy = np.mean(np.abs(D_harmonic))
total = percussive_energy + harmonic_energy

if percussive_energy / total > 0.7:
    tags.append("is_percussive")
if harmonic_energy / total > 0.7:
    tags.append("is_sustained")
```

### wide_spectrum / narrow_spectrum
```python
# Spectral bandwidth (span of frequencies)
spectral_centroid = librosa.feature.spectral_centroid(y=audio)
spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio)

# Frequency span approximation
freq_span = spectral_bandwidth.mean() * 2  # Rough estimate

if freq_span > 4000:
    tags.append("wide_spectrum")
if freq_span < 1000:
    tags.append("narrow_spectrum")
```

### high_tempo_confidence / low_tempo_confidence
```python
# Using existing tempo detection
tempo, confidence = librosa.beat.beat_track(y=audio, sr=sr)

if confidence > 0.8:
    tags.append("high_tempo_confidence")
if confidence < 0.3:
    tags.append("low_tempo_confidence")
```

## Suggested Task Sequence (v0.1-b5)

### Phase 1: Feature Detection Core
1. Create `audio_metadata/auto_tag.py` with feature detection functions
2. Write unit tests for each feature detector (synthetic test audio)
3. Verify thresholds with a small sample of real audio

### Phase 2: CLI Integration
4. Add `auto-tag` command to `app.py`
5. Support dry-run mode (preview without writing)
6. Support batch processing

### Phase 3: ML Interface Stub
7. Define `model_outputs` schema structure in `schema.py`
8. Add classifier version tracking
9. Document the interface for v0.1-b6+ ML integration

### Phase 4: Verification
10. Run on example audio directory
11. Manual review of auto-tag quality
12. Update README and this file

## Roadmap Beyond v0.1-b5

### v0.1-b6: ML-Based Subjective Tags
- Collect user-labeled training data (via review workflow)
- Train simple classifier (Random Forest / Logistic Regression)
- Add subjective tags: `dark`, `bright`, `energetic`, `calm`
- Keep objective tags as fallback/explanation

### v0.1-b7: Hybrid Scoring
- Combine objective features + ML predictions
- Confidence-weighted tag application
- User feedback loop improves ML over time

## Success Metrics (v0.1-b5)

| Metric | Target |
|--------|--------|
| Objective tag accuracy (vs manual review) | > 80% agreement |
| Processing speed | > 10 files/second |
| User override rate | < 30% (tags users reject) |
| Code coverage | > 80% for auto_tag.py |
