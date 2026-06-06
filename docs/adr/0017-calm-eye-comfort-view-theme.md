# 0017 — Calm, eye-comfort view theme (one non-semantic accent, light + dark)

**Date:** 2026-06-06
**Evidence level:** IMPLEMENTED_UNVERIFIED — CONFIRMED_ASSISTANT_SIDE (`make check` green:
212 tests / self-test 6+10 / `ruff` clean); promotes to CONFIRMED_USER_SIDE when Scott opens the
themed files. External design/eye-comfort claims below are **RESEARCH_ONLY** (web-sourced this session).
**Type:** Architecture / UI / front-end

## Context
Scott opened a UI phase and was explicit: the views should be **calm and easy on the eyes — NOT
loud / "popping."** It is a clinical, behavioral-health tool meant to *help*, read for long stretches.
The prior view rule (ADR 0014 / 0015) was **grayscale-only**, which is calm but flat and leaves a real
accessibility gap (faint hairline borders, cold pure-white).

The tension to resolve: any colour at all risks re-importing interpretation (red = bad), which the
**librarian rule forbids**. Web research this session (eye-comfort, healthcare/BH palettes, WCAG 2.2,
2026 trends) pointed one way: warmth, low stimulation, high readability, light-first.

## Decision
A single **shared, calm, low-stimulation theme** for both views, expressed as **CSS design tokens**
(`THEME` dict in `report_html.py` — one source of truth), built into `_THEME_CSS` / `_THEME_JS` that
`digest_html.py` imports; each view keeps only **layout** in its own `_CSS`.

- **Palette: aubergine + orchid** — a deep purple matched to a reference image Scott supplied. He first
  picked sage from three live calm previews, then chose this purple by eye to match the reference; it
  departs from the research-suggested *warm* neutrals (the operator's aesthetic call) but keeps every
  structural constraint. Light is a pale lavender, dark is the deep aubergine, with one de-saturated
  **orchid accent**.
- **Light-first, optional dark.** Default light (`<html data-theme="light">`); a no-dep toggle sets
  `data-theme` from `prefers-color-scheme` (no flash) and on click. Dark is an aubergine near-black,
  **never pure-white-on-pure-black**.
- **Colour is NON-semantic.** One accent, the **same for every lens**, used only to mark
  *interactivity / selection* (lens label, hover/selected border, the active-mark outline) — it never
  encodes severity, type, count, or judgment. This **revises** the "grayscale-only" half of ADR 0014/0015
  while keeping their "no colour-coding by type or severity" rule fully intact.
- **WCAG 2.2 contrast, enforced by test.** Text/affordance pairs ≥ 4.5:1; UI indicators (outlines,
  borders) ≥ 3:1 — in **both** light and dark. `tests/test_view_theme.py` imports `THEME` and computes
  relative luminance, so changing any token re-checks automatically.
- **All prior rails hold:** pure stdlib, single self-contained HTML, no network/deps, document order,
  HTML-escaped, **banned-words** (still dodging `top` via logical properties — `inset-block-start`,
  `border-block-*`).

**Research basis (RESEARCH_ONLY):** light-first beats dark for reading (positive contrast polarity;
dark-mode *halation* hurts the ~1/3 of adults with astigmatism); a warm off-white gives a low-blue
*feel* (a page can't set OS colour temperature); healthcare/BH UIs lean soft blue/teal/green/sage
(calming, lower HR/cortisol); 2026 "soft saturation + elevated neutrals." Re-confirm independently
before any clinical claim.

**Rejected:** "poppin" / high-saturation accents (Scott clarified: calm, not loud); any per-lens or
severity colour (interpretation — librarian rule); pure-white-on-pure-black; divergent per-view
palettes; any framework / bundler / server; committing the generated HTML.

## Consequences
- Both views are calmer, more readable, and accessibility-checked; one token source means the two
  views can't drift apart, and the colour palette is now machine-verified, not vibes.
- The **grayscale-only** stance of ADR 0014/0015 is superseded by this theme; the **no-semantic-colour**
  rule from those ADRs stands unchanged (this only adds a non-semantic accent + a calm palette).
- The next increment (multi-patient digest, STATUS step 11) inherits this theme for free.
- If a genuinely separate third view appears, promote `_THEME_CSS/_THEME_JS` + the shared helpers into a
  small `view_html` module (deferred per ADR 0015 — YAGNI until then).

## Confirmation
- `make check` green — **212 tests** (engine 90 + extract/modes/relative/multi + report_html 8 +
  digest_html 10 + **view_theme 5**), self-test 6+10, `ruff` clean.
- `tests/test_view_theme.py` asserts: every theme token pair meets its WCAG threshold (4.5 text / 3.0
  UI) in light **and** dark; **no colour outside the declared token set** appears in the stylesheet
  (no rogue / per-lens / severity colour); the accent is one uniform token (no `lens-*` colour class);
  the dark toggle is wired light-first (`data-theme="light"`, `prefers-color-scheme`, `theme-toggle`).
- The existing view tests still pass unchanged (self-contained, provenance visible, no injection,
  **no banned words**, all five lenses surface).
- Visual comfort/fidelity is verified by eye on Scott's laptop (CONFIRMED_USER_SIDE pending).
