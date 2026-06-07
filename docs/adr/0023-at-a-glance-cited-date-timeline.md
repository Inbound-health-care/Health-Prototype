# 0023 — At-a-glance cited-date timeline (ticks-only, single-accent, document order)

**Date:** 2026-06-07
**Evidence level:** CONFIRMED_USER_SIDE — Scott verified the four views on his device
(2026-06-07) and gave the OK to merge. `make check` green: 248 tests / self-test 6+10 / `ruff`
clean; merged to `main` via PR #35. The clinical-timeline evidence below is **RESEARCH_ONLY**
(web-sourced 2026-06-07).
**Type:** UI / front-end
**Builds on:** ADR 0021 (the shared `view_html.py` floor), 0022 (the shared interaction layer the
timeline ticks reuse), 0020 (the cognitive-load "single-screen, at-a-glance" read it realizes).

## Context
The cards/findings already cite every date, but as text only — there was no at-a-glance temporal
view. The ADR 0020 clinician research called for **single-screen, scannable, at-a-glance**.

Web research this session (RESEARCH_ONLY): clinical event/medication timelines let clinicians
absorb a history "almost at a glance," and a medication-history timeline improved chart-review
task correctness (≈90% vs 76%) and speed versus plain controls (JAMIA 2019; Gordon & Bhan 2019;
HeaRT 2023 Gantt-like chronological alignment). The tension: those studies boost performance with
class/schedule **highlighting** — semantic encoding the **librarian rule forbids**. So we adopt
the chronological-alignment method but **not** the semantic encoding.

## Decision
A horizontal time axis added to both views: one **neutral lane per surfaced finding**, each cited
date a **tick** positioned by date along the record's own min→max axis. It is a visual
re-arrangement of provenance the cards already cite — no new inference. Helpers live in the shared
floor (`view_html`): `_axis_bounds` (min/max from the record's OWN dates; `None` if <2 distinct),
`_tick_offset` (clamped percent), `_timeline_rows` (one row per finding, registry/document order),
`_render_timeline`.

- **Librarian rule in the chart:** ticks only — NO connecting/trend line (a single hairline is an
  axis, not data), NO per-lens colour (the one `accent-line` token, same as everywhere — the
  `test_accent_is_one_uniform_token` rule guards it), NO density shading/heatmap (uniform ticks),
  NO ordering by importance (registry/document order, the same iteration as the cards). The axis
  bounds are the record's own cited dates — never an external "today"/`reference_date`.
- **Accessibility (RESEARCH_ONLY method):** the ticks visually duplicate dates already shown as
  text in the cited chips/findings, so the whole `.timeline` section is `aria-hidden="true"` and
  the ticks are non-focusable — screen-reader users read the dates from the cards (the text
  alternative), not a flood of ticks, and the tab order is not bloated. Nothing about the data is
  hover- or colour-only: position carries "a date occurred," the text chip carries the exact dates.
- **Interaction reuse (ADR 0022):** each tick carries the finding's `data-item`, and `bindFindings`
  was widened to `mark.cite, .tick`, so a click lights a finding's cited dates in BOTH the note and
  the timeline. In the multi views the timeline is rendered **inside each `.patient` block** with
  its OWN axis, so the per-block-scoped highlight keeps the no-bleed guarantee (verified: each
  patient's timeline carries only its own dates).
- **Placement:** a full-width band above `main` in the single views; inside each patient block
  (per-patient axis) in the multi views. Prints via the ADR 0022 `_PRINT_CSS` (ticks fall back to
  `currentColor` so they survive grayscale).
- **All rails hold:** pure stdlib, self-contained, **banned-words-clean** (`inset-inline-start`
  not `left`/`top`; heading "Timeline of cited dates"). VERSIONs: `report_html` 0.3.0 → **0.4.0**,
  `digest_html` 0.3.0 → **0.4.0**, `view_html` 0.2.0 → **0.3.0**.

**Rejected:** SVG line / area charts (a connecting line implies a trajectory — interpretation);
colour-by-lens or severity colour (the librarian rule); density/opacity stacking (reads as
"more = worse"); sorting lanes by recency or count (importance ordering); per-tick `aria-label`
on a focusable tick (screen-reader flooding + tab-order bloat — the cards are the text
alternative). **Deferred:** de-duplicating an item that surfaces in several lenses into one lane
(kept one lane per finding — parallels the cards, adds no merging/interpretation).

## Consequences
- Both views gain a scannable temporal overview that adds zero interpretation — the dates, their
  spacing, and their span are visible at a glance, and a card click ties a finding to its dots.
- The timeline is a decorative layer over an accessible text base; assistive tech is unaffected.
- One-lane-per-finding can repeat an item across lenses; de-duplication is a future option.

## Confirmation
- `make check` green — **248 tests** (+7 `tests/test_view_html.py`: `TestTimelineAxis`,
  `TestTimelineSurface`), self-test 6+10, `ruff` clean.
- `tests/test_view_html.py` asserts: `_axis_bounds` (min/max, `None` for <2 distinct, undated
  ignored); `_tick_offset` (0/50/100, clamp, single-day midpoint); `_timeline_rows` (one row per
  finding in order, co-occurrence pair joined, dateless finding dropped); `_render_timeline` is
  `aria-hidden`, ticks positioned by `inset-inline-start`, link via `data-item`, with NO
  `<line>`/`<path>`/gradient/`lens-` and empty/single-date drawing nothing. `TestTimelineSurface`
  asserts every view renders the neutral timeline and the tick dates also exist as cited text.
- `tests/test_view_theme.py` (already looping all four demos) confirms the timeline introduces no
  colour outside the token set and stays responsive.
- Manual: `python digest_html.py --demo` (one lane per lens, 24 ticks across 7 lanes) and
  `--demo-multi` (a per-patient axis, each carrying only its own dates). CONFIRMED_USER_SIDE —
  Scott verified on his device (2026-06-07).
