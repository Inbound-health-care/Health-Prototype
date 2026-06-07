# 0019 — View review refinements (toggle / citation pills / wording / view names)

**Date:** 2026-06-06
**Evidence level:** CONFIRMED_USER_SIDE — Scott confirmed the toggle placement, citation collapse,
wording, and view names on his phone (2026-06-06). (`make check` green at merge: 214 tests /
self-test 6+10 / `ruff` clean.)
**Type:** UI / front-end
**Refines:** ADR 0014 (report view), 0015 (digest view), 0017 (theme), 0018 (responsive).

## Context
An external review (ChatGPT, on screenshots of the post-ADR-0018 build) surfaced four concrete UI
observations. Each was checked against ground truth in the code before acting; all four were real at the
code level (not taste-only). Scott picked items 1, 2, 3, 5 from that review to act on (item 4, monospace
note density, was an acknowledged tradeoff and left alone; item 6, branch protection, Scott resolved
himself by adding the `lint` + `test (3.x)` required checks).

## Decision
Four small, contained view changes. No engine change; the librarian rule holds in the view (no severity,
no ordering, no judgment; the wording change stays neutral-descriptive).

1. **Theme toggle stops floating over the card scroll area.** It was `position: fixed` (viewport-anchored),
   so on a long scroll it overlapped the cards. Moved the `<button class="theme-toggle">` inside `<header>`
   and switched it to `position: absolute` within a `position: relative` header (shared `_THEME_CSS`, so
   both views change together); `header { padding-inline-end }` reserves its space so it never overlaps the
   title. It now lives in the header band and scrolls with it instead of hovering over content.

2. **Long citation lists collapse in the clinician digest only.** A recurrence/co-occurrence chip with
   **more than three** cited dates now renders as a `<details class="chip cites">` summarizing
   `cited: N dates`, expanding on tap to the full list; short lists (≤ 3) and the already-short
   gap/frequency/cadence chips stay inline. The audit view (`report_html.py`) keeps full dates inline — it
   is the inspection surface. **Every cited date is still in the document**, one tap away — nothing is
   dropped or summarized away (provenance completeness is non-negotiable).

3. **"co-noted" → "appeared together"** on the co-occurrence card line — plainer language, same neutral
   meaning (counting co-occurrence, not asserting a relationship). The pinning test was updated in step.

4. **(item 5) The two view titles no longer collide on "digest."** The audit/inspection view's default title
   went from `"Pattern digest"` to **`"Pattern Inspection Report"`**; the clinician view stays
   **`"Pre-visit Pattern Digest"`**. The two views now read as distinct surfaces by name.

**Implementation note (banned-words rail):** the collapse disclosure must not re-toggle the card's
source-highlight. The first attempt used `stopPropagation` — rejected because it contains the substring
`top`, which the banned-words test forbids (logical-properties rule). The shipped guard lives in the shared
`_JS` card handler instead: `if (e.target.closest('details')) { return; }` — a click inside any disclosure
is ignored by the card handler, no banned token introduced, and `report_html.py` (which has no disclosures)
is unaffected.

**Rejected:** collapsing dates in the audit view too (it is the inspection surface — full provenance inline
is the point); collapsing *all* date lists including 2–3-date chips (over-hiding short lists); a JS tooltip
for the full dates (no hover on touch; `<details>` is the dependency-free, tap-friendly disclosure).

## Consequences
- The toggle change is shared, so any future view inherits the in-header placement for free.
- The digest stays scannable when a single item recurs many times, without ever hiding a cited date.
- Audit vs. clinician views are now distinguishable by title alone.

## Confirmation
- `make check` green — **214 tests** (+1 collapse test), self-test 6+10, `ruff` clean.
- `tests/test_digest_html.py::TestProvenanceIsVisible::test_long_date_list_collapses_but_keeps_every_date`
  asserts the 6-date recurrence chip collapses to `cited: 6 dates`, the full date list is still present, and
  short lists are not collapsed; the co-occurrence wording test asserts "appeared together"; every prior
  rail still passes (theme contrast, single accent, self-contained, no banned words, responsive).
- Manual: `python digest_html.py --demo` / `python report_html.py --demo` — the toggle sits in the header
  (no card overlap), the 6-date "poor sleep" chip expands on click, the audit view keeps full dates inline.
  CONFIRMED_USER_SIDE pending Scott's check.
