# 0021 — Promote shared view primitives to `view_html.py`; report_html multi-patient parity

**Date:** 2026-06-07
**Evidence level:** CONFIRMED_USER_SIDE — Scott verified the four views on his device
(2026-06-07) and gave the OK to merge. `make check` green: 235 tests / self-test 6+10 /
`ruff` clean; merged to `main` via PR #35.
**Type:** Architecture / UI / front-end
**Realizes:** ADR 0020 §Consequences ("`report_html` stays single-note; a later slice can
extend it the same way"). Executes the deferred promotion pre-declared in ADR 0015
(§Consequences) and ADR 0017 (§Consequences): "if a third view appears, promote the shared
helpers into a small shared `view_html` module."

## Context
Both HTML views shared code by `digest_html.py` importing FROM `report_html.py` (the theme,
span helpers, the click-to-highlight script). That one-way coupling held for two views, but
bringing the **inspection** view to multi-patient parity (the ADR 0020 follow-up) needs the
multi-patient primitives that live in `digest_html.py` — and `report_html` cannot import from
`digest_html` without a circular import. The YAGNI fuse ADR 0015/0017 set is now lit: a third
view surface (inspection-multi) arrived, so the shared primitives must move to a floor both
views sit on.

## Decision
Create `view_html.py` as the **dependency floor**. Both views import FROM it; neither imports
from the other. New direction: `view_html` ← `report_html`, `view_html` ← `digest_html`.
`view_html` imports nothing from the views or the engine (only stdlib `html`), so it can never
close a cycle.

- **Moved into `view_html`:** the theme (`THEME`, `_root_block`, `_THEME_CSS`, `_THEME_JS`,
  `_THEME_MEDIA_CSS`), the neutral-span helpers (`_esc`, `_collect_spans`, `_render_note`), the
  single-scope click script (`_JS`), and the multi-patient chrome that was not digest-specific
  (`_anchor_id`, `_localized_note`, `_render_patient_index`, `_render_quarantine`,
  `_QUARANTINE_LABELS`, the per-`.patient`-scoped `_MULTI_JS`, and the multi layout chrome —
  `digest_html._MULTI_CSS` promoted as `_MULTI_CHROME_CSS`, used by both views).
- **Back-compat:** `report_html` re-exports `THEME` (so `tests/test_view_theme.py`'s
  `from report_html import THEME` is untouched). `digest_html` repoints its imports to
  `view_html` directly. No behavior change — the existing 221 tests pass unchanged.
- **report_html multi-patient (the new surface):** `render_html_multi` + `--demo-multi` mirror
  `digest_html.render_digest_multi`, but with the **inspection idiom** — a findings LIST per
  patient (`_render_findings_list`), not the digest's cards. It reuses the shared
  `_localized_note` / `_anchor_id` / `_render_patient_index` / `_render_quarantine` and the
  scoped `_MULTI_JS`, so **no cross-patient highlight bleed** comes for free (each block renders
  only its own segment; the JS scopes findings↔marks per `.patient`). Patients stay in segment
  order; the quarantine section surfaces refused segments with the engine's reason code.
- **All prior rails hold:** pure stdlib, single self-contained HTML (no network/deps),
  HTML-escaped, **banned-words-clean**, shared calm theme + dark toggle, Android-responsive.
  Per-module VERSIONs: `report_html` 0.1.0 → **0.2.0** (gains multi parity); `view_html` new at
  **0.1.0**; `digest_html` unchanged at 0.2.0 (imports moved only). `view_html.py` is added to
  the Makefile `compile` list so CI byte-compiles it.

**Rejected:** moving the multi-patient primitives DOWN into `report_html` (inverts the layering
— `report_html` is the inspection view, not a primitives library; ADR 0015/0017 named the
`view_html` module specifically); duplicating the helpers across the two views (would let the
two views drift on provenance highlighting and double the banned-words surface). For the
report-multi body layout, reusing the digest's `.patient-patterns`/`.patient-source` chrome
(findings list left, cited segment right) — consistent multi-view layout, note-left inspection
ordering deferred as a cosmetic follow-up if Scott wants it.

## Consequences
- The inspection view now renders a whole batch (stacked, isolated per patient) exactly like the
  digest; both views share ONE provenance-highlighting path, so they can't drift.
- `view_html.py` is the place a future third view (or a served app) layers on; the "promote to a
  shared module" decision is now executed, not deferred.
- The report-multi per-patient layout is findings-left / cited-segment-right (the digest chrome);
  if the inspection view should read note-first, that is a small follow-up.

## Confirmation
- `make check` green — **235 tests** (+7 `tests/test_view_html.py`, +7
  `tests/test_report_html.py::TestMultiPatientReport`), self-test 6+10, `ruff` clean, all four
  modules byte-compile.
- `tests/test_view_html.py` asserts: `view_html` imports with neither view in `sys.modules` (no
  cycle); each view imports standalone; `report_html.THEME is view_html.THEME` and both views
  share `view_html._render_note`/`_JS` (one provenance path); the moved multi primitives live in
  the floor; **no banned words** in the shared static strings.
- `tests/test_report_html.py::TestMultiPatientReport` asserts (mirroring the digest's multi test):
  one block per accepted patient in segment order; the jump-index links each patient; the
  quarantine section surfaces all refused reason codes; **no cross-patient bleed** (each block
  carries only its own dates, both keep the shared concept mark scoped to their own note);
  self-contained; deterministic; banned-words-clean.
- `tests/test_view_theme.py` now also runs both `--demo-multi` outputs through the
  non-semantic-colour / responsive / dark-toggle checks.
- Manual: `python report_html.py --demo-multi` — two stacked patients (findings list + own cited
  segment), jump-index, quarantine section. CONFIRMED_USER_SIDE — Scott verified on his device (2026-06-07).
