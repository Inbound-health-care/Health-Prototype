# 0018 — Responsive / mobile pass (Android-targeted)

**Date:** 2026-06-06
**Evidence level:** IMPLEMENTED_UNVERIFIED — CONFIRMED_ASSISTANT_SIDE (`make check` green: 213 tests /
self-test 6+10 / `ruff` clean); promotes to CONFIRMED_USER_SIDE when Scott opens the views on his Android
phone. The device/version figures below are **RESEARCH_ONLY** (web-sourced this session).
**Type:** UI / front-end

## Context
Scott works ~67% on a phone (Samsung). Both views (`report_html.py` + `digest_html.py`) were a fixed
two-column flex (`main`) with **no media queries**, so on a narrow screen the columns shrank
side-by-side into unreadable slivers and the monospace `.note` could overflow horizontally. The product
target is **Android** (Scott + the clinician users); iOS is explicitly out of scope.

## Decision
An **Android-targeted responsive layer**, CSS-only (no JS change, no deps), reusing the ADR 0017 theme.

**Researched device landscape (RESEARCH_ONLY):** Samsung dominates Android (~31% of manufacturers);
best-sellers are Galaxy **A-series** (A12/A17/A36/A56) + **S-series** flagships. The CSS viewport widths
that matter: **360 px is the most common Android width** (incl. Galaxy S25 = 360×780 CSS, DPR 3) → the
**primary design target**; **~390–412 px** larger flagships; **foldables unfolded ≈ 768 px** (tablet-like).
Android is fragmented (16 ≈ 21%, 15 ≈ 19%, 14 ≈ 17%, 11/13 ≈ 13% each) but every live version runs current
**Chrome / Samsung Internet**, so flexbox, custom properties, logical properties, and `prefers-color-scheme`
are fully supported — no legacy-CSS concessions.

**Implementation:** a single shared `_THEME_MEDIA_CSS` (in `report_html.py`, imported by `digest_html.py`)
appended **last** in each view's `<style>` so it overrides both the shared base and the view's own layout:
- `@media (max-width: 640px)` → `main { flex-direction: column }` stacks the two columns. Below 640 covers
  every Android phone portrait (≤ ~430); foldable-unfolded ~768 + tablets/desktop keep two columns.
- `main > section` becomes content-height (`flex: 0 0 auto`) and full-width; the inter-section divider is
  generic — `main > section:not(:last-child) { border-block-end }` — so one block serves **both** views
  (no per-view duplication). The desktop inline divider (`border-inline-end`) is cleared.
- Trimmed `section` / `header` padding; `header { padding-inline-end }` keeps the fixed toggle off the title;
  `.note { overflow-x: auto }`; tap targets bumped (`.card` / `li.finding` padding, `.theme-toggle`
  `min-block-size: 44px`).

**Rails preserved:** pure stdlib, single self-contained HTML, no network/deps, document order, single
NON-semantic accent, WCAG-AA contrast, banned-words (logical properties — `inset-block-start`,
`border-block-*` — keep `top` out of the document). iOS-specific handling intentionally omitted.

**Rejected:** a CSS framework / grid library; JS-driven layout or device sniffing; a separate mobile page;
hard-coding one device width (foldables and rotation vary — the breakpoint is range-based).

## Consequences
- Both views are usable on the actual target hardware (Samsung A/S, 360–412 px) and on foldables; desktop
  is unchanged above 640 px.
- All responsive logic is one shared block with generic `main > section` selectors — adding a future view
  inherits it for free.
- The breakpoint is a deliberate range (640), not a per-device value, so new Android sizes need no change.

## Confirmation
- `make check` green — **213 tests** (+1 responsive), self-test 6+10, `ruff` clean.
- `tests/test_view_theme.py::TestResponsiveAndroid` asserts both views carry the viewport meta, a
  `@media (max-width: 640px)` block, and `flex-direction: column`; every prior rail still passes
  (contrast light+dark, no colour outside the token set, self-contained, no banned words).
- Manual: open `python digest_html.py --demo` / `report_html.py --demo` on Android (and narrow the desktop
  window to **360 and 412 px**) — columns stack, the note reads with no horizontal blow-out, the toggle
  clears the title, tap targets are comfortable. CONFIRMED_USER_SIDE pending Scott's phone check.
