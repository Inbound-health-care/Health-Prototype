# 0015 — Pre-visit Pattern Digest view (UI slice 2): the clinician product surface

**Date:** 2026-06-06
**Evidence level:** IMPLEMENTED_UNVERIFIED — CONFIRMED_ASSISTANT_SIDE (`make check` green:
177 tests / self-test 6+10 / `ruff` clean); promotes to CONFIRMED_USER_SIDE when Scott opens the file.
**Type:** Architecture / UI / front-end

## Context
ADR 0014 shipped `report_html.py` as the working/**inspection** view and drew a deliberate split: the
clinician-facing **Pre-visit Pattern Digest** is a separate *product* surface, mocked design-first in
Figma (https://www.figma.com/design/BcT7yhsMHAZl2AeJD9fAAK — Scott approved the mock, 2026-06-06). With
the mock settled, the next slice is turning it into real, dependency-free code **driven by the engine**,
not hand-built HTML. Scott chose to ship it as a **new module**, keeping the two views distinct (his
call on the fork).

Same two hard constraints as ADR 0014: (1) pure-stdlib, local-only, **no network egress by rule** →
dependency-free; (2) the **librarian rule must hold in the view** — a product digest is exactly where
ranking / severity color / "priority" sneak interpretation back in.

## Decision
A new `digest_html.py` renders the digest as a **single self-contained HTML file** (inline CSS +
vanilla JS, no CDN / `src=` / server / network), distinct from `report_html.py`:
- **Five lenses as neutral cards** in the engine's **registry order** (recurrence, gap, frequency,
  co-occurrence, cadence change) — provenance order, never importance. Each card states only what was
  surfaced + a `cited:` chip of its provenance dates, derived **straight from the typed hit**, so the
  view can only show what `run_report` actually surfaced. Clicking a card highlights its cited spans in
  the source note (linked by item; co-occurrence carries both).
- **Driven by real engine output:** a synthetic free-text note (`DIGEST_SAMPLE_*` in
  `data/sample_records.py`, EXAMPLE-009, zero PHI) authored so **one patient trips all five lenses
  once each**, spacings tuned to avoid accidental extras (poor sleep's tight run never reaches
  3-in-30, leaving frequency to anxiety). Pipeline: `extract_records -> run_report -> render_digest`.
- **Librarian rule in the view:** grayscale only, document order, a stance line ("surfaced and cited —
  never judged, ordered, or recommended; the clinician decides"), an empty report that **never asserts
  clean**, and the same **whole-document banned-words test** (still dodging `top` via `border-block-*`
  and `block:'center'`).
- **DRY across views:** `digest_html` reuses the shared, pure view helpers (`_collect_spans`,
  `_render_note`, `_esc`, `_JS`) from `report_html`, so the two views can never highlight provenance
  differently. One-way deps only (`digest_html` -> `report_html` / `extract` / `recurrence`, never the
  reverse). `VERSION` 0.1.0. CLI: `python digest_html.py --demo [outfile]` (generated `.html`
  git-ignored — regenerate, never commit).

**Rejected:** evolving `report_html.py` into the digest (Scott chose the two-module split — inspection
vs product stay distinct); any JS framework / bundler / server; color or severity coding; ranking or a
"priority" ordering of the cards; committing the generated HTML.

## Consequences
- The strategic product shape (the behavioral-health pre-visit digest) now has a runnable, cited
  reference implementation — not just a mock.
- New module + sample constants + test file; `recurrence.py` / `extract.py` / `report_html.py` and
  their tests are untouched (additive).
- Multi-patient navigation and any served/hosted app remain deferred (separate roadmap items); the
  demo is single-patient.
- Coupling: the digest reuses `report_html`'s underscore-prefixed view helpers. Acceptable for a
  prototype; if a third view appears, promote them into a small shared `view_html` module.

## Confirmation
- `make check` green — **177 tests** (engine 90 + extract slice-1 27 + modes 27 + relative 15 +
  report_html 8 + digest_html 10), self-test 6+10, `ruff` clean. `tests/test_digest_html.py` asserts:
  self-contained (no `http(s)` / `<link` / `src=` / `cdn` / `@import`); **all five lens cards surface**
  from the sample; card count agrees with `run_report` (7 findings); co-occurrence is presented as a
  pair, not a relationship; cards cite real provenance (gap brackets / frequency window / cadence
  pivot) and link to real note marks; note content HTML-escaped (no `<script>` injection); **no banned
  words anywhere**; an empty report does not assert "clean".
- Visual fidelity to the Figma mock is verified by eye on Scott's laptop (CONFIRMED_USER_SIDE pending).
