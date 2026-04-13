# CURRENT_GOAL.md

## Version
- Current repo version: `v0.1-b6` 🚧 **IN PROGRESS**
- Previous version: `v0.1-b5` (Objective Auto-Tagging Layer) ✅
- Current milestone: `v0.1-b6` (CLAP Semantic Search — Optional)

**v0.1-b6 Progress:** Phase 1 ⏳ | Phase 2 ⏳ | Phase 3 ⏳

---

## Goal (v0.1-b6) — CLAP Semantic Search 🚧 IN PROGRESS

**Core idea:** Use pre-trained CLAP model to enable true natural language audio search without training data.

**Why CLAP:**
- Maps audio and text to same embedding space
- No training data required
- Understands musical terms like "dark", "bright", "energetic" out of the box
- Optional feature — doesn't break existing workflow

---

## v0.1-b6 Deliverables

### Phase 1: CLAP Embedding Computation ⏳
- [ ] `audio_metadata/clap_embed.py` — CLAP embedding module
  - Load pre-trained CLAP model (laion-audioclip-full-2022)
  - Batch compute embeddings for audio files
  - Export to independent JSON (doesn't pollute main library.json)
- [ ] `clap_embed_cli.py` — CLI command for batch embedding
  - `--input` audio directory or file list
  - `--output` embeddings JSON file
  - `--batch-size` for memory control
  - `--verbose` progress output
- [ ] `tests/test_clap_embed.py` — embedding tests (mock model for CI)
- [ ] `app.py compute-embeddings` — integrated CLI command

### Phase 2: Semantic Search ⏳
- [ ] `semantic_search.py` — semantic search module
  - Load embeddings from JSON
  - Convert text query to CLAP embedding
  - Cosine similarity search → Top-K results
- [ ] `semantic_search_cli.py` — CLI command
  - `--query` natural language query
  - `--embeddings` path to embeddings JSON
  - `--top-k` result count
  - `--threshold` minimum similarity score
- [ ] `tests/test_semantic_search.py` — search tests
- [ ] `app.py semantic-search` — integrated CLI command

### Phase 3: Hybrid Search ⏳
- [ ] Integrate semantic search with existing `nl-query`
  - Rule-based filtering (bpm/duration/keyword) → coarse filter
  - CLAP similarity → re-ranking
- [ ] `hybrid_search.py` — hybrid search module
- [ ] `app.py hybrid-search` — unified CLI command
- [ ] Documentation: when to use semantic vs rule-based search

---

## Design Decisions

### Optional Feature
- CLAP is **opt-in** — users without the model can still use all existing features
- Embeddings stored in separate file (`embeddings.json`) — doesn't modify schema v1
- Graceful degradation: if CLAP not installed, show helpful error message

### Embedding Storage
```json
{
  "model": "laion-audioclip-full-2022",
  "embedding_dim": 512,
  "computed_at": "2026-04-13T21:00:00Z",
  "files": [
    {
      "path": "/audio/pad_dark_120.wav",
      "embedding": [0.12, -0.45, 0.78, ...]
    }
  ]
}
```

### Search Flow
```
User query: "dark pad around 120 bpm"
         ↓
Rule-based filter: keyword="pad", tempo 110-130
         ↓
CLAP similarity: rank by text-audio embedding distance
         ↓
Top-K results with similarity scores
```

---

## Installation (Optional)

Users who want CLAP features install extra dependencies:

```bash
# Core features (no CLAP)
pip install -r requirements.txt

# With CLAP semantic search
pip install -r requirements.txt
pip install laion-clap
```

---

## Usage Examples

### Compute Embeddings

```bash
# One-time embedding computation
python app.py compute-embeddings --input ./audio --output embeddings.json -v

# Update embeddings for new files
python app.py compute-embeddings --input ./audio/new --output embeddings.json --append
```

### Semantic Search

```bash
# Simple semantic search
python app.py semantic-search --query "dark pad" --embeddings embeddings.json --top-k 10

# With similarity threshold
python app.py semantic-search --query "energetic drum loop" --embeddings embeddings.json --threshold 0.7

# Verbose output (show scores)
python app.py semantic-search --query "calm ambient" --embeddings embeddings.json -v
```

### Hybrid Search (Phase 3)

```bash
# Combine rule-based + semantic
python app.py hybrid-search --query "dark pad around 120 bpm" --input library.json --embeddings embeddings.json --top-k 10
```

---

## Performance Expectations

| Operation | Speed | Notes |
|-----------|-------|-------|
| Embedding computation | ~1-2 sec/file | One-time cost, batch processing |
| Text embedding | ~100-200 ms | Per query |
| Similarity search | ~10-50 ms | For 1000 embeddings |
| Total search latency | ~200-300 ms | Text embed + search |

**Memory:**
- CLAP model: ~300MB on disk, ~600MB RAM during inference
- Embeddings: ~2KB per file (512 floats)

---

## Alternatives Considered

| Approach | Why Not Chosen |
|----------|----------------|
| Train own classifier (original v0.1-b6) | Needs training data, chicken-egg problem |
| Rule-based only (existing nl-query) | Limited semantic understanding |
| Vector database (FAISS/Chroma) | Overkill for <10K files, adds complexity |
| PANNs/VGGish | No text embedding, need separate text model |

**CLAP chosen because:**
- Pre-trained on audio-text pairs
- No training data needed
- Single model for both audio and text
- Good enough for music production use cases

---

## Out of Scope (v0.1-b6)

- ❌ Vector database integration (keep it simple)
- ❌ Real-time embedding computation (pre-compute only)
- ❌ Multi-modal search (image→audio, etc.)
- ❌ Fine-tuning CLAP on user data (optional future work)
- ❌ UI for semantic search (CLI only for now)

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Search relevance (user-rated) | > 70% satisfied | Manual testing |
| Search latency | < 500 ms | Benchmark |
| Embedding coverage | 100% of library | Completeness check |
| Installation success rate | > 90% | User reports |

---

## Git History (v0.1-b6)

| Commit | Description |
|--------|-------------|
| *(pending)* | feat(v0.1-b6): add CLAP embedding computation |
| *(pending)* | feat(v0.1-b6): add semantic search CLI |
| *(pending)* | docs: update README with CLAP usage |

---

**Previous approach (ML classifier) archived:** See `docs/v0.1-b6-ml-classifier-approach.md` for reference.
