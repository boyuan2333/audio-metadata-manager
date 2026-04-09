# CURRENT_GOAL.md

## Version
- Current repo version: `v0.1-b4` ✅
- Planned next milestone: `v0.1-b5` (TBD)

## Goal (v0.1-b4) — COMPLETED
- Build the first minimal natural-language query layer that converts user text into structured search intent on top of the existing search system.

## Already True In The Repo (v0.1-b4)
- Audio directories can be indexed into schema v1 JSON.
- Manual review overrides can correct a small set of derived and tempo fields.
- `review-batch`, `review-candidates`, and `review-stats` support a lightweight manual cleanup workflow.
- `search` already supports explicit filters such as keyword, loop state, brightness, tempo applicability, tempo quality, BPM range, duration range, and status.
- **`nl-query` accepts natural language queries and converts them to structured search intent.**
- `similar` already performs lightweight numeric-metadata ranking after candidate filtering.
- Schema normalization preserves reserved `retrieval`, `model_outputs`, and `segments` fields, but no automatic semantic pipeline populates them.
- Tests cover schema normalization, override behavior, batch review tools, NL query parser, and basic search/similar smoke paths.

## What's No Longer Missing (v0.1-b4 delivered)
- ~~No user-facing free-text query path.~~ → **Delivered: `nl-query` command**
- ~~No query-to-intent parser that maps plain language onto existing structured filters.~~ → **Delivered: `parse_nl_query()` with narrow vocabulary**
- ~~No eval set for natural-language search behavior.~~ → **Delivered: `tests/test_nl_query.py` with 5 test cases**

## Still Missing (future milestones)
- No vector retrieval, embedding index, or semantic ranker.
- No UI.
- No automatic classifier that fills `model_outputs` or semantic `retrieval` fields.

## Explicitly Out Of Scope (unchanged)
- UI, web app, or desktop app work.
- Cloud sync, shared state, or multi-user features.
- Vector DBs, embeddings, ANN search, rerankers, or full semantic retrieval.
- Automatic tagging or classifier pipelines for `model_outputs` or `retrieval`.
- Schema v2, large review-system changes, or extractor rewrites.

## Acceptance Criteria (v0.1-b4) — ALL MET ✅
- A plain-text query can be converted into structured intent using current filter concepts only. ✅
- The first version supports only a narrow, documented safe subset of filters already present in `search`. ✅
- The first version does not depend on or parse `retrieval.*` or `model_outputs.*`. ✅
- The parser output is explainable enough to inspect in tests or CLI output. ✅
- Search execution still flows through the existing search system. ✅
- Unknown wording does not crash the command. ✅
- No schema change is required for the feature. ✅
- Automated tests cover representative success and fallback cases. ✅

## Example Eval Queries (all tested)
- `dark drum loops around 128 bpm` ✅
- `bright percussion one shots` ✅
- `show non-loop fills` ✅
- `slow loops under 90 bpm` ✅
- `dark sounds with no tempo` ✅
- `show shaker loops between 120 and 130 bpm` ✅
- `show failed files` ✅
- `find crash one shots` ✅

## Suggested Task Sequence — COMPLETED ✅
1. Define the smallest intent shape that maps only to existing `search` filters. ✅
2. Write parser tests for the example queries above plus a few unsupported-wording cases. ✅
3. Implement a minimal deterministic parser with a narrow vocabulary and safe fallback behavior. ✅
4. Wire the parser into one small entry path that reuses existing search execution. ✅
5. Verify the new path with tests and one or two representative CLI examples. ✅
6. Update `README.md` and this file only after the code behavior exists. ✅
