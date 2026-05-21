# Page 1 — Search Page (index.html)

这是应用的主页和核心页面。用户打开 localhost:8000 默认进入此页。

---

## Prompt

```
Design a single-page audio sample search interface for a local desktop tool used by music producers.

## Page Purpose
This is the main workspace. Producers search their local sample library, filter results, preview audio, and navigate to detail views. The tool runs locally in a browser — no login, no cloud, no account system.

## Layout Structure

### Top Bar (fixed, full width)
- Left: App name "AMM" as a small logo/wordmark
- Center: A large search input field with placeholder text "Search samples… (e.g. dark drum loops 128 bpm)"
  - The search input supports both keyword and natural language queries
  - A search button (magnifying glass icon) at the right edge of the input
  - Below the input, show the detected search strategy as a small pill/badge: "keyword" / "semantic" / "hybrid"
- Right: Two icon buttons — "Report" (chart icon, links to report page) and a gear/settings icon

### Main Content Area (below top bar, full remaining height)
Split into two columns:

#### Left Column — Filter Sidebar (collapsible, ~240px width)
A vertical stack of filter groups, each with a group label and controls:

1. **Type** — Two toggle chips: "Loop" | "One-shot" (multi-select, neutral when neither selected)
2. **Brightness** — Four toggle chips in a row: "Dark" | "Balanced" | "Bright" | "Very Bright"
3. **Tempo** — A range slider with two handles: min BPM (left) / max BPM (right). Range: 0–300. Display current values as "120 — 148" text above the slider. Below the slider, a checkbox: "No tempo (non-rhythmic)"
4. **Duration** — Four toggle chips: "<1s" | "1-5s" | "5-30s" | ">30s"
5. **Format** — Checkbox list: wav, mp3, flac, ogg, aiff
6. **Tags** — Show top 10 most used tags as clickable chips. Clicking a tag adds it to the search. Show a small count number next to each tag.

At the bottom of the sidebar: a "Reset Filters" text button.

#### Right Column — Results Area (fills remaining width)

**Results Header Bar:**
- Left: "Found 47 results" text
- Right: Sort dropdown: "Relevance" / "Name A-Z" / "Duration" / "BPM"
- Right: View toggle: List view icon | Grid view icon

**Results — List View (default):**
Each result is a horizontal card/row with these elements from left to right:
1. A small colored indicator dot (shows brightness: maps to a semantic color — but the dot itself is just a shape indicator)
2. File name (bold, truncated with ellipsis if too long)
3. Three small inline metadata pills: duration (e.g. "2.4s") | BPM (e.g. "128") | format (e.g. "wav")
4. A "Loop" or "One-shot" tag pill
5. A brightness label pill (e.g. "dark")
6. Tags list (up to 3 shown, "+N" overflow indicator)
7. A circular play/stop button (▶ / ■ icon) at the far right

When hovering a result row, show a subtle elevation or border change to indicate clickability. Clicking the row (not the play button) navigates to the detail page.

**Results — Grid View:**
Each result is a square card showing:
- File name (top, bold)
- Waveform-style decorative element or a subtle pattern (visual placeholder, not functional waveform yet)
- Key metadata: duration, BPM, format stacked vertically
- Play button (centered overlay)

**Audio Playback:**
When a play button is clicked:
- The button changes to a stop icon (■)
- A thin progress bar appears at the bottom of the result row (or card)
- A mini audio player bar appears fixed at the very bottom of the viewport, showing: currently playing file name | elapsed time / total time | play/pause button | a close/dismiss button

**Empty States:**
- No search yet: Show a centered prompt — illustration of a magnifying glass over a waveform, text "Search your sample library", subtitle "Try: 'dark drum loops' or 'bright percussion one-shots'"
- No results found: Show "No samples match your filters" with a "Reset Filters" button

**Loading State:**
- Show a skeleton/placeholder list (3-5 gray animated rows) while the API responds

## Navigation
- Clicking "Report" icon in the top bar → navigates to report.html
- Clicking a result row → navigates to sample detail page (pass sample ID in URL)
- The search query and filter state persist in the URL query parameters so the back button works

## Responsive Behavior
- At narrow widths (<768px), the filter sidebar collapses into a horizontal "Filters" button that opens a slide-out drawer
- Results switch to a single-column card layout

## Affordances (What users should be able to do at a glance)
- The search input is the primary focal point — it must be visually prominent and clearly editable
- Play buttons must look tappable (circular, icon-based, with hover state)
- Filter chips must clearly communicate active vs inactive state through visual distinction
- The result count must update immediately when filters change (show a loading indicator if the API call takes time)
- The currently playing item must be visually distinct from other results
```
