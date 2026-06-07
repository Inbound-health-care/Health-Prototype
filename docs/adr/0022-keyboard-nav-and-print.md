# 0022 — Keyboard navigation + print pass (shared interaction layer)

**Date:** 2026-06-07
**Evidence level:** CONFIRMED_USER_SIDE — Scott verified the views on his device (2026-06-07)
and gave the OK to merge. `make check` green: 241 tests / self-test 6+10 / `ruff` clean; merged
to `main` via PR #35. The a11y/print method notes below are **RESEARCH_ONLY** (web-sourced 2026-06-07).
**Type:** UI / front-end / accessibility
**Builds on:** ADR 0021 (the shared `view_html.py` floor — both views inherit this in one place).

## Context
Both views were mouse-only: click a finding to highlight its cited source. A clinical tool
read for long stretches needs keyboard operation (WCAG 2.1.1 keyboard, 2.4.7 focus-visible),
and a pre-visit page is often handed off on paper, so it needs a real print layout. Putting
both in the shared floor means the inspection view, the digest, and both multi-patient views
get them at once.

Web research this session (RESEARCH_ONLY) shaped two method choices:
- **A native `<button>` gives Enter/Space for free, but the WHATWG HTML content model (§4.10.6)
  forbids an interactive-content descendant in a button** — and the digest card nests the
  cited-date `<details>` disclosure. So the focusable toggle is a custom `role="button"`, which
  per the W3C ARIA APG must handle **both Enter and Space** and keep its label **stable** across
  the pressed state.
- **CSS cannot set a `<details>` open state** (W3C csswg-drafts #2084), so a collapsed cited-date
  list will not print just by CSS. A `beforeprint` handler opens every `<details>` for printing
  (the `_PRINT_CSS` display rule is the no-JS fallback).

## Decision
One shared interaction layer in `view_html.py`; both views and both JS scopes reuse it.

- **One activation path for mouse + keyboard.** `_INTERACT_JS` defines `bindFindings(findings,
  marks)` with an inner `activate(el)` (the existing toggle/highlight body) wired to BOTH a
  `click` and a `keydown` (Enter / Space → `preventDefault` + activate) listener. `_JS` binds
  over the whole document; `_MULTI_JS` binds per `.patient` block (so the no-bleed guarantee
  holds for keyboard too). `bindFindings`/`activate` are defined once per page — the duplicated
  handler body the two scopes used to carry is gone.
- **Static ARIA.** Each finding carries `tabindex="0" role="button" aria-pressed="false"` in the
  rendered markup (present before JS, and test-visible); `activate` reflects `aria-pressed`
  true/false as the highlight toggles. The label never changes with state (APG).
- **Visible focus.** `.finding:focus-visible` draws a 2px outline in the `accent-line` token
  (already WCAG-3:1-checked in `tests/test_view_theme.py`).
- **Print (`_PRINT_CSS`, appended last in every view's `<style>`):** `@media print` → single
  column, on-screen chrome (theme toggle + footer) hidden, each cited `mark` given a
  `1px currentColor` border so it stays legible in grayscale (`print-color-adjust: exact` is a
  best-effort extra, never relied on), `break-inside: avoid` on patient/card/finding so a block
  is not split across a page, collapsed cited-date lists forced visible, and an `@page { size: A4
  }`. The `beforeprint`/`afterprint` handlers open/restore the `<details>` so the FULL provenance
  prints.
- **All rails hold:** pure stdlib, self-contained, **banned-words-clean** (logical properties +
  `break-inside`, never `page-break-*`; `block:'center'` not `top`). VERSIONs: `report_html`
  0.2.0 → **0.3.0**, `digest_html` 0.2.0 → **0.3.0**, `view_html` 0.2.0 → **0.3.0** (kept aligned).

**Rejected:** wrapping the card in a native `<button>` (HTML forbids the nested `<details>`);
relying on CSS alone to expand `<details>` for print (impossible — #2084); depending on
`print-color-adjust` to carry meaning (kept the grayscale border instead). **Known tradeoff /
deferred:** the digest card is a `role="button"` that still nests the `<details>` disclosure; the
click+keydown `closest('details')` guard keeps the two from interfering and the `<summary>` stays
in the tab order (reachable), but fully un-nesting the disclosure from the toggle is a cleaner
structure left as a cosmetic/a11y follow-up (it would change the card markup the prior view ADRs
visually confirmed).

## Consequences
- Both views are keyboard-operable with a visible focus ring and reflected pressed state, and
  print as a clean single-column paper handout with full provenance — in one shared place.
- The two click scopes now share one tested activation body; a future view gets keyboard + print
  for free by reusing the floor.
- The nested-disclosure-in-a-button tradeoff is documented; un-nesting is the next a11y refinement.

## Confirmation
- `make check` green — **241 tests** (+6 `tests/test_view_html.py`: `TestKeyboardAndAria`,
  `TestPrint`), self-test 6+10, `ruff` clean.
- `tests/test_view_html.py` asserts across all four demo surfaces: findings carry
  `tabindex`/`role=button`/`aria-pressed` and a `keydown` Enter/Space path; `bindFindings`/
  `activate` defined exactly once per page; `aria-pressed` count tracks the rendered findings;
  `.finding:focus-visible` uses `var(--accent-line)`; the print stylesheet hides chrome, borders
  the marks, forces `.cites-full` visible, uses `break-inside: avoid` + `@page`; `<details>` are
  opened via `beforeprint`/`afterprint`; print/interaction strings are banned-words-clean.
- Manual: tab to a card/finding (focus ring), press Enter or Space (highlights its cited source);
  browser print-preview of each `--demo` / `--demo-multi` (single column, chrome gone, dates
  expanded). CONFIRMED_USER_SIDE — Scott verified on his device (2026-06-07).
