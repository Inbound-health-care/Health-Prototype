# 0020 — Multi-patient digest rendering (stacked, per-patient scoped, quarantine surfaced)

**Date:** 2026-06-06
**Evidence level:** IMPLEMENTED_UNVERIFIED — CONFIRMED_ASSISTANT_SIDE (`make check` green: 221 tests /
self-test 6+10 / `ruff` clean, incl. CI-pinned ruff 0.15.16); promotes to CONFIRMED_USER_SIDE when
Scott opens the multi demo on his phone. The 2024–2026 clinician-needs research below is **RESEARCH_ONLY**
(web-sourced this session).
**Type:** UI / front-end
**Realizes:** STATUS step 11c (the deferred "multi-patient digest RENDERING" pick); renders the batch
output of **ADR 0016** (`extract.extract_records_multi`). Builds on ADR 0015 (digest), 0017 (theme),
0018 (responsive), 0019 (refinements).

## Context
The engine side of multi-patient already landed (ADR 0016): `extract_records_multi` splits a batch note
on an explicit delimiter and returns a `MultiExtractResult` — accepted records (each with a
`provenance.segment_span`) plus fail-closed `quarantined` segments. But both views were single-note.
This slice gives the **clinician digest** a multi-patient rendering (digest only this round; the
`report_html` inspection view stays single-note — a later follow-up).

Scott asked, before picking a layout, what clinicians actually want from chart-review / pre-visit tools
(2024–2026). The web research (RESEARCH_ONLY) was consistent and shaped this decision:
- **Documentation / chart-review burden is the #1 pain, worst in behavioral health** (admin ≈35–50% of
  hours; BH 93% burnout). "Note bloat" is the named complaint; clinicians want a **less-is-more**,
  **scannable** surface that makes the important findable.
- **Trust hinges on citation / provenance** — the tools gaining traction ground every answer in
  verifiable, checkable sources; generic LLM summaries are distrusted for lacking an auditable evidence
  chain. (This is the project's thesis, externally confirmed — the librarian rule is the differentiator.)
- **Cognitive-load research:** minimize navigation (it is extraneous load), prefer **single-screen,
  at-a-glance with drill-down that keeps context.**

## Decision
Render a multi-patient batch as **stacked, anchored per-patient blocks**, in **segment order** (never
reordered — the librarian rule), with a **compact patient jump-index** and a **neutral quarantine
section**. New code is contained in `digest_html.py`; the engine and the shared view helpers are untouched.

- **Per-patient block = lens cards + that patient's OWN cited source segment.** Each block slices its
  segment from the whole note via `provenance.segment_span` and rebases the entries' whole-note spans to
  segment-local (`_localized_note`), so every patient's note **stands alone**.
- **No cross-patient highlight bleed — structurally + in JS.** Two patients can share an item
  ("poor sleep"); a click must never light up the other patient. Guaranteed two ways: (1) each block
  renders only its own segment text, and (2) `_MULTI_JS` scopes findings↔marks **per `.patient` block**
  (`block.querySelectorAll(...)`), so a click is confined to its block. (Mirrors `report_html._JS` but
  scoped; avoids the banned `top` token — no `stopPropagation`, logical properties only.)
- **Patient jump-index** (`_render_patient_index`): plain in-page anchor links (`#patient-<id>`), no JS
  state, shown only when >1 patient — low navigation, single-page context preserved (the cognitive-load
  read). Stacked layout (not tabs) so context is never hidden behind a click.
- **Quarantine section** (`_render_quarantine`): the refused segments surfaced in segment order with the
  engine's own reason code (`missing_key` / `ambiguous_key` / `duplicate_key` / `missing_shift`) plus its
  neutral detail — **never merged, guessed, or interpreted**. Empty → nothing (no "all clean" claim).
- **All prior rails hold:** pure stdlib, single self-contained HTML (no network/deps), HTML-escaped,
  **banned-words-clean**, shared calm theme + dark toggle, and the cited-date `<details>` collapse; the
  `_MULTI_CSS` stacks the per-patient body below 640 px (Android).
- **New entry point:** `python digest_html.py --demo-multi [outfile]` over the synthetic
  `FREETEXT_MULTI_NOTE` batch (no per-patient shift, so cited dates stay hand-readable); `VERSION` 0.2.0.

**Rejected:** patient tabs / a switcher (the research flags navigation cost + hidden context, and it
needs JS state + scoped highlighting = more banned-words/JS risk); one shared whole-note panel with
`data-patient`-tagged marks (would touch the shared single-note helpers and risk bleed); reordering or
ranking patients (the librarian rule — segment order only); multi-patient in `report_html` too (deferred
— digest is the product view this round).

## Consequences
- The clinician digest now renders a whole batch in one scannable page; each patient is isolated, so
  click-to-highlight can never cross patients.
- `report_html` (inspection) stays single-note; a later slice can extend it the same way if needed.
- Per-patient shift is exercised by the extractor's own tests (ADR 0016); the view demo uses shift 0 for
  readability — the de-identification path is unchanged, just not re-demoed here.

## Confirmation
- `make check` green — **221 tests** (+7 multi-patient), self-test 6+10, `ruff` clean (local + CI-pinned
  0.15.16).
- `tests/test_digest_html.py::TestMultiPatientDigest` asserts: one block per accepted patient in segment
  order; the jump-index links each patient; the quarantine section surfaces all five refused segments
  with their reason codes; **no cross-patient bleed** (each block carries only its own dates, both blocks
  keep the shared concept mark scoped to their own note); self-contained; deterministic; banned-words-clean.
- Manual: `python digest_html.py --demo-multi` — two stacked patients, jump-index, quarantine section;
  clicking a card highlights only within that patient. CONFIRMED_USER_SIDE pending Scott's phone check.
