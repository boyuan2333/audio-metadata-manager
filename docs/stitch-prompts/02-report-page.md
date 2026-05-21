# Page 2 — Report Page (report.html)

库统计概览页面，帮助用户了解采样库的健康度和覆盖情况。

---

## Prompt

```
Design a library statistics dashboard page for a local audio sample manager used by music producers.

## Page Purpose
This is a read-only overview page. Producers come here to understand their sample library at a glance: how many files they have, what formats and types dominate, whether their metadata coverage is healthy, and what needs attention. No editing happens on this page.

## Layout Structure

### Top Bar (fixed, full width)
- Left: Back arrow icon + "AMM" wordmark (clicking navigates back to search page)
- Center: Page title "Library Report"
- Right: "Refresh" button (re-fetches report data from API)

### Main Content (scrollable, centered container, max-width ~960px)

The content is organized as a vertical stack of stat cards. Each card has a card title and content area.

---

#### Card 1: Overview Numbers (top, full width)
A horizontal row of 4 large number displays, evenly spaced:
1. **Total Files** — Large number (e.g. "1,562") with label "samples"
2. **Total Loops** — Number with label "loops" (e.g. "847")
3. **Total One-shots** — Number with label "one-shots" (e.g. "715")
4. **Avg Duration** — Number with label "avg duration" (e.g. "3.2s")

Each number is large and bold. The label is smaller and lighter below it.

---

#### Card 2: Format Distribution
Title: "Format Distribution"

A horizontal bar chart (simple, no external chart library needed — just CSS bars):
- Each row: format label (e.g. "wav") | horizontal bar (proportional width) | count number
- Sort by count descending
- Example:
  ```
  wav   ████████████████████  892
  mp3   ████████████          423
  flac  ██████                198
  ogg   ██                     49
  ```

---

#### Card 3: Duration Distribution
Title: "Duration Distribution"

Same horizontal bar chart format as Card 2, but with duration buckets:
- "<1s" | "1-5s" | "5-30s" | ">30s"
- Each row shows the bucket label, proportional bar, and count

---

#### Card 4: Type Distribution
Title: "Type Distribution"

A donut/ring chart (can be done with CSS conic-gradient) showing:
- Loop vs One-shot proportion
- Inside the ring: the dominant type and its percentage (e.g. "Loop 54%")
- Legend below: colored dot + "Loop (847)" | colored dot + "One-shot (715)"

If CSS charts are too complex, fall back to two large side-by-side number cards (one for loop, one for one-shot) with a visual proportion indicator.

---

#### Card 5: Tag Coverage
Title: "Metadata Coverage"

Three horizontal progress bars stacked vertically, each with:
- Label on the left: "Auto-tag" | "Semantic" | "Manual Review"
- Progress bar in the middle (filled proportionally)
- Percentage and count on the right: "78% (1,219 / 1,562)"

Purpose: shows how much of the library has been tagged. Color semantics: high coverage = good, low coverage = needs attention. (Use visual weight — thicker/thinner, filled/empty — not specific colors, to let the user control the palette.)

---

#### Card 6: Embedding Coverage
Title: "Embedding Coverage"

Two side-by-side stat boxes:
1. "Ready" — large number (e.g. "1,100") with a checkmark icon
2. "Missing" — large number (e.g. "462") with a warning/alert icon

Below the boxes: a thin horizontal stacked bar showing the proportion of ready vs missing.

---

#### Card 7: Top Categories (Category Heatmap)
Title: "Top Tags"

A grid of tag chips (3-4 columns), sorted by frequency:
- Each chip shows: tag name + count in parentheses
- Chip size or visual weight can indicate relative frequency (larger = more frequent)
- Example: "drum (234)" | "loop (198)" | "percussion (156)" | "bass (134)" | "synth (98)" | ...

---

#### Card 8: Warnings
Title: "Warnings" with a count badge (e.g. "12")

A compact list of warning items, each showing:
- A warning icon (triangle with exclamation mark)
- Warning text (e.g. "kick_128bpm.wav: missing duration")
- The list is collapsible — show first 5 items, then "Show 7 more…" expander

If no warnings: show a success state — checkmark icon + "All samples have complete metadata"

---

### Bottom of Page
- App version text: "AMM v0.1-b9 · Schema v1"
- "Back to Search" text link

## Navigation
- Back arrow in top bar → search page
- No other navigation targets (this is a read-only overview page)

## Affordances (What users should understand at a glance)
- The overview numbers (Card 1) should be the first thing the eye sees — large, confident, scannable
- Progress bars in Card 5 immediately communicate "how much work is left" through fill ratio
- The warnings section should feel like an actionable to-do list, not an error log
- The entire page should be scannable in under 10 seconds — a producer opens it, gets the picture, closes it
```
