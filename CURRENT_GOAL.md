# CURRENT_GOAL.md

## Version
- Current repo version: `v0.1-b3`
- Planned next milestone: `v0.1-b4`

## Goal
- Build the first minimal natural-language query layer that converts user text into structured search intent on top of the existing search system.

## Already True In The Repo
- Audio directories can be indexed into schema v1 JSON.
- Manual review overrides can correct a small set of derived and tempo fields.
- `review-batch`, `review-candidates`, and `review-stats` support a lightweight manual cleanup workflow.
- `search` already supports explicit filters such as keyword, loop state, brightness, tempo applicability, tempo quality, BPM range, duration range, and status.
- `similar` already performs lightweight numeric-metadata ranking after candidate filtering.
- Schema normalization preserves reserved `retrieval`, `model_outputs`, and `segments` fields, but no automatic semantic pipeline populates them.
- Tests already cover schema normalization, override behavior, batch review tools, and basic search/similar smoke paths.

## Missing Right Now
- No user-facing free-text query path.
- No query-to-intent parser that maps plain language onto existing structured filters.
- No eval set for natural-language search behavior.
- No vector retrieval, embedding index, or semantic ranker.
- No UI.
- No automatic classifier that fills `model_outputs` or semantic `retrieval` fields.

## This Version Should Deliver
- A minimal NL query input path that accepts short plain-English sample queries.
- Deterministic conversion from query text into a small structured intent object built from a safe subset of current `search` fields only.
- Execution that reuses the current explicit search path instead of creating a parallel retrieval system.
- The first version must not depend on, parse, or infer intent from `retrieval.*` or `model_outputs.*`.
- Clear fallback behavior for unsupported language: ignore it safely or keep it as keyword text, but do not invent meaning.
- Tests that lock the intended parsing behavior for a small eval set.

## Explicitly Out Of Scope
- UI, web app, or desktop app work.
- Cloud sync, shared state, or multi-user features.
- Vector DBs, embeddings, ANN search, rerankers, or full semantic retrieval.
- Automatic tagging or classifier pipelines for `model_outputs` or `retrieval`.
- Schema v2, large review-system changes, or extractor rewrites.

## Acceptance Criteria
- A plain-text query can be converted into structured intent using current filter concepts only.
- The first version supports only a narrow, documented safe subset of filters already present in `search`.
- The first version does not depend on or parse `retrieval.*` or `model_outputs.*`.
- The parser output is explainable enough to inspect in tests or CLI output.
- Search execution still flows through the existing search system.
- Unknown wording does not crash the command.
- No schema change is required for the feature.
- Automated tests cover representative success and fallback cases.

## Example Eval Queries
- `dark drum loops around 128 bpm`
- `bright percussion one shots`
- `show non-loop fills`
- `slow loops under 90 bpm`
- `dark sounds with no tempo`
- `show shaker loops between 120 and 130 bpm`
- `show failed files`
- `find crash one shots`

## Suggested Task Sequence
1. Define the smallest intent shape that maps only to existing `search` filters.
2. Write parser tests for the example queries above plus a few unsupported-wording cases.
3. Implement a minimal deterministic parser with a narrow vocabulary and safe fallback behavior.
4. Wire the parser into one small entry path that reuses existing search execution.
5. Verify the new path with tests and one or two representative CLI examples.
6. Update `README.md` and this file only after the code behavior exists.
