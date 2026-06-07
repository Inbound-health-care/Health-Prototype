# 0014 — HTML report view (UI slice 1): provenance made visible

**Date:** 2026-06-05
**Evidence level:** IMPLEMENTED_UNVERIFIED — CONFIRMED_ASSISTANT_SIDE (`make check` green:
167 tests / self-test 6+10 / `ruff` clean); promotes to CONFIRMED_USER_SIDE when Scott opens the file.
**Type:** Architecture / UI / front-end
**Revised by:** ADR 0017 (2026-06-06) — the **"grayscale-only"** highlight mechanism described
below is superseded by the calm aubergine theme (one non-semantic accent). The librarian-rule
intent it served — **no colour-coding by type or severity** — still holds. The view itself stands.

## Context
The engine + extractor already produce structured, **cited** output, but `source_span` was exercised
only by the test suite — provenance was invisible. Scott asked whether a UI is useful now that "the
code works." Decided yes, for a specific reason: a view is the first real consumer of provenance, and
it makes the librarian rule's core value (every line traces to source) tangible — which is also FDA
Non-Device CDS **criterion 4** (the basis is reviewable) rendered on screen. It is also a first step
toward the strategic product shape (the behavioral-health "pre-visit pattern digest" is a *read*
surface).

Two hard constraints shaped it: (1) the repo is **pure-stdlib, local-only, no network egress by
rule**, and **pygame was already dropped as out-of-scope** — so the UI must be dependency-free; (2)
the **librarian rule must hold in the view layer too** (a UI is exactly where ranking / severity
colors / alerts sneak interpretation back in).

## Decision
A new `report_html.py` renders a **single self-contained HTML file** (inline CSS + vanilla JS, no
CDN, no `src=`, no server, no network) via pure `html.escape` + string templating:
- **Provenance made visible:** the source note with each cited span highlighted — `source_span`
  concept hits *and* the ADR 0013 `date_span` temporal phrases — beside the `run_report` findings.
  Clicking a finding highlights its cited concept spans in the note (linked by item).
- **Librarian rule in the view:** **grayscale-only** highlights (no severity colors), **document
  order only** (no ranking/sorting by importance), neutral chrome, a stance line ("surfaced and cited
  — never judged, ordered, or recommended"), and an empty report that **never asserts a record is
  clean**. A **whole-document banned-words test** enforces it (this is why the footer uses
  `border-block-start`, not `border-top` — "top" is a banned ranking token).
- One-way dependency (`report_html` imports `extract` + `recurrence`, never the reverse). `VERSION`
  0.1.0. CLI: `python report_html.py --demo [outfile]` (the generated `.html` is git-ignored —
  regenerate, never commit).
- This is the **working / inspection** view. The clinician-facing **pre-visit pattern digest** is
  mocked separately in **Figma** (design-first), so the product surface and the engineering aren't
  entangled. **Figma mock:** https://www.figma.com/design/BcT7yhsMHAZl2AeJD9fAAK (Scott's Drafts —
  grayscale, all five lenses + a cited-source panel; design-only, off-repo).

**Rejected:** any JS framework / bundler / server (contradicts pure-stdlib + local; the pygame
precedent); color-coding by type or severity (interpretation); committing the generated HTML.

## Consequences
- `source_span` / `date_span` finally have a human consumer; the citation story is visceral.
- New module + test file; `recurrence.py` / `extract.py` and their tests are untouched.
- Multi-record / multi-note rendering is a straightforward later extension (loop records); the demo is
  single-note (multi-patient is still deferred, ADR 0013).

## Confirmation
- `make check` green — **167 tests** (engine 90 + extract slice-1 27 + modes 27 + relative 15 +
  report_html 8), self-test 6+10, `ruff` clean. `tests/test_report_html.py` asserts: the document is
  self-contained (no `http(s)` / `<link` / `src=` / `cdn` / `@import`); every cited span is marked and
  recovers its exact source text; the relative-date phrases are cited too; findings link to real
  concept marks; note content is HTML-escaped (no `<script>` injection); **no banned words anywhere**;
  and an empty report does not assert "clean".
- The clinician-facing digest design (Figma) is a separate, design-only artifact — not covered by
  these tests.
