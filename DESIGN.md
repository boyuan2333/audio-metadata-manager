---
version: alpha
name: AMM
description: >
  Dark, focused, instrument-like UI for audio sample management.
  Inspired by DAW aesthetics — Ableton's restraint, Spotify's playback clarity,
  and the data density of professional audio tools.
colors:
  # --- Base surfaces ---
  primary: "#0A0A0F"
  bg-base: "#0A0A0F"
  bg-surface: "#12121A"
  bg-elevated: "#1A1A24"
  bg-overlay: "#22222E"

  # --- Text ---
  text-primary: "#E8E8ED"
  text-secondary: "#8B8B9A"
  text-tertiary: "#5A5A6A"
  text-inverse: "#0A0A0F"

  # --- Accent (teal-cyan — audio tool standard) ---
  accent: "#00D4AA"
  accent-hover: "#00F0C0"
  accent-muted: "#1A3D35"
  accent-dim: "#112A25"

  # --- Semantic: Tag dimensions ---
  tag-tech: "#4A9EFF"
  tag-tech-bg: "#152233"
  tag-emotion: "#FF8A50"
  tag-emotion-bg: "#332218"
  tag-category: "#50E3C2"
  tag-category-bg: "#1A332E"
  tag-format: "#A78BFA"
  tag-format-bg: "#221A33"

  # --- Waveform gradient ---
  waveform-low: "#FF6B35"
  waveform-mid: "#00D4AA"
  waveform-high: "#4A9EFF"

  # --- Feedback ---
  success: "#00D4AA"
  warning: "#FFB84D"
  error: "#FF5A5A"
  info: "#4A9EFF"

  # --- Borders ---
  border-subtle: "#16161F"
  border-default: "#1F1F2C"
  border-strong: "#2E2E3F"

  # --- Glow (search box AI effect) ---
  glow-accent: "#00D4AA"
  glow-pulse: "#1A3D35"

typography:
  h1:
    fontFamily: Inter
    fontSize: 2rem
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  h2:
    fontFamily: Inter
    fontSize: 1.5rem
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  h3:
    fontFamily: Inter
    fontSize: 1.125rem
    fontWeight: 600
    lineHeight: 1.4
  body-md:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: 400
    lineHeight: 1.5
  body-sm:
    fontFamily: Inter
    fontSize: 0.75rem
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: Inter
    fontSize: 0.6875rem
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.06em"
  mono:
    fontFamily: JetBrains Mono
    fontSize: 0.8125rem
    fontWeight: 400
    lineHeight: 1.5
  mono-sm:
    fontFamily: JetBrains Mono
    fontSize: 0.6875rem
    fontWeight: 400
    lineHeight: 1.5
  mono-data:
    fontFamily: JetBrains Mono
    fontSize: 1.5rem
    fontWeight: 700
    lineHeight: 1.2

rounded:
  xs: 2px
  sm: 4px
  md: 8px
  lg: 12px
  xl: 16px
  full: 9999px

spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px

components:
  # --- Search Input (with AI glow) ---
  search-input:
    backgroundColor: "{colors.bg-surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: 14px
    height: 52px
  search-input-focus:
    backgroundColor: "{colors.bg-elevated}"
    rounded: "{rounded.lg}"

  # --- Filter Chip ---
  filter-chip:
    backgroundColor: "{colors.bg-overlay}"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.full}"
    padding: 6px
  filter-chip-active:
    backgroundColor: "{colors.accent-muted}"
    textColor: "{colors.accent}"
    rounded: "{rounded.full}"
    padding: 6px

  # --- Tag Pill (dimension-colored) ---
  tag-tech:
    backgroundColor: "{colors.tag-tech-bg}"
    textColor: "{colors.tag-tech}"
    rounded: "{rounded.full}"
    padding: 3px
  tag-emotion:
    backgroundColor: "{colors.tag-emotion-bg}"
    textColor: "{colors.tag-emotion}"
    rounded: "{rounded.full}"
    padding: 3px
  tag-category:
    backgroundColor: "{colors.tag-category-bg}"
    textColor: "{colors.tag-category}"
    rounded: "{rounded.full}"
    padding: 3px
  tag-format:
    backgroundColor: "{colors.tag-format-bg}"
    textColor: "{colors.tag-format}"
    rounded: "{rounded.full}"
    padding: 3px

  # --- Result Card ---
  result-card:
    backgroundColor: "{colors.bg-surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: 12px
  result-card-hover:
    backgroundColor: "{colors.bg-elevated}"
    rounded: "{rounded.md}"
  result-card-playing:
    backgroundColor: "{colors.accent-dim}"
    rounded: "{rounded.md}"

  # --- Play Button ---
  play-button:
    backgroundColor: "{colors.bg-overlay}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.full}"
    size: 36px
  play-button-hover:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.text-inverse}"
  play-button-active:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.text-inverse}"

  # --- Global Mini Player ---
  mini-player:
    backgroundColor: "{colors.bg-surface}"
    textColor: "{colors.text-primary}"
    height: 64px
  mini-player-expanded:
    backgroundColor: "{colors.bg-surface}"
    textColor: "{colors.text-primary}"
    height: 120px

  # --- Waveform Container ---
  waveform:
    backgroundColor: "{colors.bg-base}"
    rounded: "{rounded.sm}"
    height: 48px
  waveform-played:
    backgroundColor: "{colors.accent}"
  waveform-unplayed:
    backgroundColor: "{colors.bg-overlay}"

  # --- Spectrogram Thumbnail ---
  spectrogram:
    backgroundColor: "{colors.bg-base}"
    rounded: "{rounded.sm}"
    height: 64px

  # --- Stat Card (Report) ---
  stat-card:
    backgroundColor: "{colors.bg-surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: 24px
  stat-number:
    typography: "{typography.mono-data}"
    textColor: "{colors.accent}"

  # --- Button ---
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.md}"
    padding: 10px
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
    textColor: "{colors.text-inverse}"
  button-secondary:
    backgroundColor: "{colors.bg-overlay}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: 10px
  button-ghost:
    backgroundColor: "{colors.bg-base}"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.md}"
    padding: 10px

  # --- Progress Bar ---
  progress-bar:
    backgroundColor: "{colors.bg-overlay}"
    rounded: "{rounded.full}"
    height: 4px
  progress-bar-fill:
    backgroundColor: "{colors.accent}"
    rounded: "{rounded.full}"
    height: 4px

  # --- Tab ---
  tab:
    backgroundColor: "{colors.bg-base}"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.sm}"
    padding: 8px
  tab-active:
    backgroundColor: "{colors.bg-overlay}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.sm}"
    padding: 8px

  # --- Tooltip / Hover Preview ---
  tooltip:
    backgroundColor: "{colors.bg-elevated}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: 12px

  # --- Keyboard Shortcut Badge ---
  kbd:
    backgroundColor: "{colors.bg-overlay}"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.xs}"
    padding: 2px

  # --- Feedback Toasts ---
  toast-success:
    backgroundColor: "{colors.accent-dim}"
    textColor: "{colors.success}"
    rounded: "{rounded.md}"
    padding: 12px
  toast-warning:
    backgroundColor: "#2A2218"
    textColor: "{colors.warning}"
    rounded: "{rounded.md}"
    padding: 12px
  toast-error:
    backgroundColor: "#2A1515"
    textColor: "{colors.error}"
    rounded: "{rounded.md}"
    padding: 12px
  toast-info:
    backgroundColor: "#151A2A"
    textColor: "{colors.info}"
    rounded: "{rounded.md}"
    padding: 12px
---

## Overview

AMM (Audio Metadata Manager) is a local tool for music producers to manage their sample libraries. The visual language borrows from DAW culture — dark backgrounds that let content breathe, monospace data that feels like readouts, and accent colors that signal interactivity without shouting.

The UI should feel like an instrument: focused, responsive, and quiet until it has something to say. Every pixel serves either information density or playback control. Decorative elements are limited to the waveform visualizations, which are both functional and aesthetic.

## Colors

The palette is built around a near-black base with a teal-cyan accent — a nod to the color language of Ableton, Serum, and modern audio tooling.

- **Base surfaces** progress from `bg-base` (#0A0A0F) through `bg-surface`, `bg-elevated`, to `bg-overlay` — each step lifts content off the background by ~8% luminance.
- **Accent (#00D4AA)** is reserved for: active states, the currently-playing indicator, progress bars, and the search glow. Never use it for static labels or decorative fills.
- **Tag dimension colors** are fixed: blue for technical metadata (BPM, LUFS), warm orange for emotion/texture tags, teal for classification tags, purple for format/codec info. These are not user-configurable — they create a consistent visual language across the app.
- **Waveform gradient** maps frequency: low (warm orange) → mid (teal) → high (cool blue). This gives producers an instant visual read on frequency content without a spectrogram.

## Typography

Two families, split by purpose:

- **Inter** for all UI text — labels, descriptions, navigation. Weight carries hierarchy: 700 for headings, 600 for labels, 400 for body.
- **JetBrains Mono** for all data — numbers, dB values, BPM, file paths, timecodes. Monospace ensures column alignment in data tables and feels like a technical readout.

Display sizes use tight letter-spacing (`-0.02em`). Labels use open spacing (`0.06em`) for legibility at small sizes.

## Layout

The app uses a single-page shell with a fixed top bar, collapsible filter sidebar, scrollable results area, and a fixed bottom mini-player bar.

- **4px baseline grid.** All spacing derives from the `spacing` scale.
- **Top bar:** 52px height, contains the search input (visual focal point).
- **Sidebar:** 240px width, collapsible to 0 on mobile.
- **Mini player:** 64px default, expandable to 120px to show waveform.
- **Content padding:** 16px intra-component, 24px inter-component, 48px section breaks.

## Elevation & Depth

Minimal layering. The dark background already provides depth — use surface color steps instead of shadows. Reserve box-shadows for the search input glow effect only.

## Shapes

- **xs (2px):** keyboard shortcut badges, fine borders.
- **sm (4px):** waveform containers, progress bars, small indicators.
- **md (8px):** cards, buttons, inputs — the default radius.
- **lg (12px):** search input, main containers.
- **xl (16px):** large cards, modals.
- **full (9999px):** play buttons, filter chips, tag pills — anything that should feel like a pill or circle.

## Components

### Search Input

The visual anchor of the entire app. Large (52px), centered in the top bar. On focus, a subtle teal glow signals AI-powered natural language input. Placeholder text hints at query examples. A CSS shimmer animation on the border reinforces the AI affordance.

### Filter Chips

Pill-shaped toggles in the sidebar. Inactive: `bg-overlay` with `text-secondary`. Active: `accent-muted` background with `accent` text. Multi-select within groups (e.g., multiple brightness levels). Single-select across groups (e.g., only one duration bucket).

### Tag Pills

Small, dimension-colored labels. The color is determined by tag category, not user choice:
- Blue (`tag-tech`): BPM, LUFS, sample rate, tempo confidence.
- Orange (`tag-emotion`): dark, bright, calm, energetic, texture labels.
- Teal (`tag-category`): loop, one-shot, percussive, sustained, instrument family.
- Purple (`tag-format`): WAV, MP3, FLAC, AIFF, channel count.

Tags use progressive disclosure: result cards show 2-3 core tags, with a "+N" overflow. The detail page shows all tags grouped by dimension, collapsible.

### Result Card

A horizontal row in the search results list. Contains: waveform thumbnail (48px height, gradient-colored), file name, 2-3 metadata pills, tag pills, and a play button. On hover, lifts to `bg-elevated`. When playing, gets an `accent-dim` left border and the waveform animates.

### Play Button

36px circle. Default: `bg-overlay` with a play triangle. On hover: fills with `accent`. When active (playing): stays `accent`-filled, icon changes to pause bars.

### Global Mini Player

Fixed at the viewport bottom. Shows: waveform mini-visualization, file name, elapsed/total time, play/pause, volume slider. Expandable to 120px to show a full interactive waveform with seek. Persists across page navigation — clicking a result on any page updates the player without interrupting playback.

### Waveform

Container: 48px height in result cards, expandable in the mini-player and detail page. The waveform is rendered as a bar-style visualization with gradient coloring (low→mid→high frequency). Played portion uses accent color; unplayed portion uses `bg-overlay`. On hover, shows a time cursor. Click to seek.

### Spectrogram Thumbnail

A 64px-tall heatmap shown on hover (tooltip style) over result cards. Frequency on Y-axis, time on X-axis, intensity mapped to color brightness. Uses the same dark palette — brighter = more energy. This is an advanced feature for audio engineers who prefer spectral analysis over waveform shape.

### Stat Card

Used on the report page. Dark surface with large monospace numbers in accent color. Chart bars use `accent` fills on `bg-overlay` tracks. Progress bars for metadata coverage use semantic colors: `success` for high coverage, `warning` for medium, `error` for low.

### Keyboard Shortcut Badge

Small inline badges showing shortcut keys (e.g., `Space`, `Ctrl+K`, arrow keys). Rendered with `kbd` component style — `bg-overlay` background, `text-secondary`, `xs` rounded corners, mono font at `mono-sm` size.

### Feedback Toasts

Non-blocking notifications. Success uses accent-dim background. Warning, error, and info each have their own dark-tinted background that harmonizes with their semantic text color.

## Do's and Don'ts

- **Do** use `{colors.accent}` only for interactive/active states — never for static decoration.
- **Do** use `mono` typography for all numeric data (BPM, LUFS, duration, sample rate).
- **Do** use tag dimension colors consistently — blue=tech, orange=emotion, teal=category, purple=format.
- **Do** keep the search input visually prominent — it's the primary interaction point.
- **Don't** add shadows to cards on dark backgrounds — use surface color steps instead.
- **Don't** use the accent color for tag pills — tags have their own dimension colors.
- **Don't** nest component variants — `play-button-hover` is a sibling of `play-button`, not a child.
- **Do** use animation purposefully: waveform playback, search glow pulse, loading skeletons, tag expand/collapse, mini-player transitions.
- **Don't** use bright backgrounds for any full-width surface — the app lives in the dark.
