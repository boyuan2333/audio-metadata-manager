# AGENTS.md

## Mission
- Keep this repo as a local, single-user audio sample manager core.
- Extend retrieval carefully toward natural-language recommendation by building on the existing JSON + CLI workflow.
- Prefer improvements that make indexing, review, and retrieval more reliable before making them broader.

## Current Stage
- Current repo version is `v0.1-b3`.
- The repo already supports indexing, explicit metadata search, lightweight similarity search, manual review overrides, batch review presets, review candidate discovery, and review stats.
- It does not yet provide natural-language search, vector retrieval, UI, cloud features, team workflows, or automatic semantic classification.

## Architecture Invariants
- Storage is local JSON only. Do not introduce a database or service layer casually.
- `audio_metadata.schema` owns schema v1 normalization and effective-value shaping.
- `app.py` is the preferred unified CLI entry point. Older direct scripts remain compatibility paths.
- JSON-backed `search` and `similar` must continue to honor legal `review.overrides`.
- Similarity remains lightweight and numeric-metadata-based unless a task explicitly changes that contract.
- `retrieval`, `model_outputs`, and `segments` exist in schema v1, but they are mostly reserved fields today.
- Review write-back stays narrow: only the current override fields plus `review.notes` unless a task explicitly expands it.

## Scope Boundaries
- Prefer small, local improvements to CLI behavior, parsing, validation, tests, and docs.
- Reuse the current search pipeline before adding new retrieval layers.
- Treat natural-language work as query-to-intent translation first, not full semantic search.
- Keep local-first and single-user assumptions unless the task explicitly says otherwise.

## Coding And Change Rules
- Default to the smallest realistic change that solves the task.
- Keep module boundaries clear: parsing, schema, CLI wiring, and search execution should stay separable.
- Preserve existing CLI behavior unless the task explicitly changes it.
- Do not rename commands, files, or schema fields casually.
- Do not silently repurpose reserved fields to fake new capabilities.
- Schema changes, extractor rewrites, and broad refactors require explicit justification in the task and matching tests.
- Broad dependency additions need a clear reason tied to a current milestone.

## Task Decomposition
- Break work into one narrow behavior at a time.
- Prefer adding tests for a small slice, then implementing that slice.
- For NL-query work, keep intent parsing separate from the existing record-matching logic.
- Avoid mixing unrelated cleanup with feature work.
- If a task touches schema, CLI, and docs at once, keep the diff easy to review and justify each part.

## Testing And Validation
- Run relevant automated tests after changes. Start with targeted `unittest` modules, then broaden if needed.
- For CLI behavior changes, run at least one representative command path or parser-level test.
- Do not claim support for a behavior that is not covered by code and fresh verification output.

## Documentation Expectations
- `README.md` and `CURRENT_GOAL.md` must stay aligned with actual code behavior.
- Update docs when commands, constraints, or milestone scope change.
- Keep docs operational and factual. Do not add aspirational features as if they exist.

## Anti-Goals
- Do not casually add UI, cloud sync, multi-user workflows, vector databases, or background services.
- Do not casually rewrite the extractor pipeline.
- Do not casually bump schema versions or expand override semantics.
- Do not turn the next milestone into full semantic retrieval.
- Do not perform broad repo cleanup or file reorganization unless the task explicitly calls for it.
