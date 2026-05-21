# Page 3 — Sample Detail Page (sample.html)

单个采样的详情查看和元数据编辑页面。

---

## Prompt

```
Design a sample detail page for a local audio sample manager used by music producers.

## Page Purpose
This page shows all metadata for a single audio sample and allows the producer to edit review overrides (correct wrong metadata) and add notes. It's the "deep dive" view after clicking a result from the search page.

## Layout Structure

### Top Bar (fixed, full width)
- Left: Back arrow icon + "AMM" wordmark (clicking navigates back to search page with previous filters preserved)
- Center: File name as page title (e.g. "dark_loop_128bpm_v2.wav"), truncated with ellipsis if very long
- Right: "Save Changes" button (primary action, disabled/grayed when no changes made)

---

### Main Content (scrollable, two-column layout on desktop, single column on mobile)

#### Left Column — Audio Player & Quick Info (~40% width)

**Audio Player Section:**
A prominent audio player area containing:
- A large waveform-style visual element (decorative/pattern-based for now, functional waveform is Phase 2)
- Centered: A large circular play/pause button (▶ / ❚❚)
- Below the waveform: a linear progress/scrub bar (clickable to seek)
- Time display: "0:00 / 2.4s" (elapsed / total)
- Below the player: a volume icon + horizontal volume slider

**Quick Info Card:**
A compact summary card showing the most important fields at a glance:
- Duration: "2.4 sec"
- Sample Rate: "44100 Hz"
- Channels: "Stereo" / "Mono"
- Format: "WAV"
- Loop: "Yes" / "No" (toggle switch — clicking toggles the review override)
- Brightness: "Dark" (clickable chip — cycles through: dark → balanced → bright → very bright)
- BPM: "128" (editable number display — click to edit)
- Tempo Quality: "High" / "Medium" / "Low" / "N/A"

Each field in this card should show a small indicator if it has been manually overridden (e.g. a small colored dot or underline) vs auto-detected.

---

#### Right Column — Detailed Metadata & Edit (~60% width)

This column uses a tabbed interface with 3 tabs:

##### Tab 1: "Features" (default active)
A table/list of extracted audio features, each row showing:
- Feature name (left)
- Detected value (center)
- Review override value (right, if exists)
- An edit/override button per row

Feature rows:
| Feature | Detected | Override |
|---|---|---|
| Loudness (LUFS) | -14.2 | — |
| Tempo (BPM) | 128.0 | — |
| Tempo Confidence | 0.92 | — |
| Tempo Quality | high | — |
| Spectral Centroid (Hz) | 2340 | — |
| RMS | 0.15 | — |

When the override column has a value, highlight that row to show "this has been manually corrected."

An "Add Override" button at the bottom of the table opens a dropdown to select which field to override, then shows an inline edit form.

##### Tab 2: "Tags & Classification"
Shows all tag-related metadata:

**Auto Tags Section:**
- Header: "Auto Tags (objective)" with a count badge
- A list of tag chips: "is_percussive" | "is_bright" | "wide_spectrum" | "high_tempo_confidence" | ...
- Each chip is read-only (auto-generated, not editable)

**Semantic Tags Section:**
- Header: "Semantic Tags" with a count badge
- Tag chips (read-only): "dark_ambient" | "cinematic" | ...

**Retrieval Tags Section:**
- Header: "Retrieval Tags" with a count badge
- Tag chips (read-only): "drum" | "loop" | "bass" | ...
- These come from the folder path / filename analysis

**Subjective Tags Section:**
- Header: "Subjective Tags (ML)"
- If available: tag chips with confidence values (e.g. "dark 0.87" | "calm 0.45")
- If not available: "No ML model applied yet" with an info message

**Classification Info:**
- Instrument Family: e.g. "percussion" or "—"
- Texture: e.g. "rough" or "—"
- Timbre Type: e.g. "synthetic" or "—"

##### Tab 3: "Notes & Review"
A review workspace for the producer:

**Notes Section:**
- A text area (expandable) for adding free-text notes about this sample
- Below the text area: an "Add Note" button
- Existing notes shown as a chronological list above the text area, each with:
  - Note text
  - Timestamp (when the note was added)
  - A delete icon button (small X)

**Review History Section:**
- A compact list of all override actions taken on this sample
- Each entry: which field was changed | old value → new value | timestamp
- Read-only, just for audit trail

**Danger Zone (bottom, visually separated):**
- "Clear All Overrides" button — resets all review overrides to auto-detected values
- Shows a confirmation dialog/warning before executing

---

### Fixed Bottom Bar (when edits are pending)
When the user makes any change (toggle loop, add override, add note), a bottom action bar slides up:
- Left: "Discard Changes" text button
- Right: "Save Changes" primary button
- Center: "2 unsaved changes" counter text

This bar is only visible when there are unsaved edits.

---

## Data Fields Reference (for accurate content)

The page receives a sample object with these sections. Show all non-null values:

**source:** path, file_name, file_format
**technical:** duration_sec, sample_rate_hz, channels
**features:** loudness_lufs, tempo_bpm, tempo_confidence, tempo_quality, spectral_centroid_hz, rms
**derived:** tempo_applicable, is_loop, duration_bucket, brightness
**retrieval:** tags[], mood, texture, density, role, domain, semantic_tags[], embedding_ref, embedding_status
**model_outputs:** instrument_family, texture, timbre_type, auto_tags[], auto_tags_confidence{}, subjective_tags[], semantic_tags[]
**review:** overrides{}, notes[]

## Navigation
- Back arrow → search page (preserves previous search state via URL params)
- "Save" → saves via API, shows a toast notification "Changes saved" on success
- Failed save → shows a toast "Save failed: [error message]" with a retry option

## Affordances (What users should be able to do at a glance)
- The play button must be the most prominent element on the left — producers want to hear the sample first
- Overridden fields must be visually distinct from auto-detected fields (so the user knows what they've changed)
- The "Save Changes" button must be clearly disabled when there's nothing to save, and clearly active when there is
- The tab interface should show a badge/counter on tabs with content (e.g. "Tags (8)" | "Notes (3)")
- The loop toggle and brightness chip should feel like quick actions — one-click, no modal, no confirmation
- The "Clear All Overrides" button must feel appropriately dangerous (visual separation, confirmation step)
```
