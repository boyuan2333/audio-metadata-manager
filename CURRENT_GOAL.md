# CURRENT_GOAL.md

## Version
- Current repo version: `v0.1-b7` 🚧 IN PROGRESS
- Previous version: `v0.1-b6` (CLAP Semantic Search — Optional) ✅ COMPLETE
- Current milestone: `v0.1-b7` (Metadata Enrichment Layer)

**v0.1-b7 Progress:** Phase 1 ✅ | Phase 2 ✅ | Phase 3 🚧 | Phase 4 🚧

---

## Goal (v0.1-b7) — Metadata Enrichment Layer

**Core idea:** Add `app.py enrich` so an indexed `library.json` can be combined with optional pre-computed embeddings and a controlled semantic vocabulary, producing a stable `library.enriched.json`.

**Why this matters:**
- Keep schema v1 compatible while expanding retrieval metadata
- Reuse existing `embeddings.json` instead of recomputing CLAP features
- Add controlled semantic tags without storing raw vectors in the main library file
- Keep the workflow local, inspectable, and easy to review

---

## v0.1-b7 Deliverables

### Phase 1: Schema + Enrichment Core ✅
- [x] `audio_metadata/schema.py`
  - Extend `retrieval` with `semantic_tags`, `embedding_ref`, `embedding_model`, `embedding_status`
  - Extend `model_outputs` with `semantic_tags` and `semantic_tags_confidence`
- [x] `audio_metadata/enrichment.py`
  - Implement pure `enrich_payload()` logic
  - Match embeddings by path with filename fallback
  - Write `ready` / `missing` / `invalid` / `not_requested`
- [x] `tests/test_schema_model_outputs.py`
- [x] `tests/test_enrichment.py`

### Phase 2: Semantic Vocabulary ✅
- [x] `config/semantic_tags.json`
  - Add default controlled vocabulary
- [x] Semantic tag scoring against vocabulary embeddings
- [x] Write tags into both `retrieval.semantic_tags` and `model_outputs.semantic_tags`

### Phase 3: CLI Integration 🚧
- [x] `enrich_cli.py`
  - Parse CLI args
  - Read input JSON and optional embeddings/vocabulary JSON
  - Support `--dry-run`
  - Refuse overwrite unless `--force`
  - Write output via atomic `.tmp` + `replace()`
- [x] `app.py enrich`
  - Register `enrich` subcommand in unified CLI
- [x] `tests/test_enrich_cli.py`

### Phase 4: Documentation + Final Verification 🚧
- [x] `README.md`
  - Add `enrich` command description and examples
- [x] `CURRENT_GOAL.md`
  - Update milestone to `v0.1-b7`
- [ ] Run targeted tests
- [ ] Run full pytest suite
- [ ] Run CLI smoke test

---

## Command Examples

### Metadata-only enrich

```bash
python app.py enrich \
  --input ./out/library.json \
  --output ./out/library.enriched.json
```

### Enrich with embeddings and semantic tags

```bash
python app.py enrich \
  --input ./out/library.json \
  --embeddings ./out/embeddings.json \
  --vocabulary ./config/semantic_tags.json \
  --semantic-tags \
  --output ./out/library.enriched.json
```

---

## Design Constraints

- `enrich` must not load a CLAP model directly
- `enrich` must not write 512-dimensional embeddings into `library.enriched.json`
- Semantic tags must come from a controlled vocabulary, not free generation
- Output writes must be atomic
- Existing schema v1 consumers should remain compatible

---

## Success Criteria

- `python app.py enrich --input ... --output ...` runs successfully
- `--dry-run` prints summary and does not create the output file
- Existing output is rejected unless `--force` is provided
- Missing embeddings mark records as `embedding_status=not_requested`
- Matching embeddings write coverage status and embedding references
- Semantic tags only appear when embeddings are ready and scoring is enabled
- New tests pass and existing tests do not regress
