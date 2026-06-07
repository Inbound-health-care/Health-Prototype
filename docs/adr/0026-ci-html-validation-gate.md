# 0026 — CI HTML-validation gate: proof-html on the generated views

**Date:** 2026-06-07
**Evidence level:** IMPLEMENTED_UNVERIFIED — the `html` job is wired; the first CI run **caught 4 real
HTML5-conformance errors** (see "What the gate caught" below), which were fixed; the regenerated views
now pass an equivalent local Nu check (`html5validator`, HTML-clean). Promotes to CONFIRMED_ASSISTANT_SIDE
once the PR CI `html` job is green; the view interaction is CONFIRMED_USER_SIDE when Scott runs `make jstest`.
**Type:** CI / build infrastructure

## Context
The two HTML views (`report_html.py`, `digest_html.py`, on the `view_html.py` floor) are
**generated on demand and gitignored** — they are never committed. A naive
`anishathalye/proof-html` step with the default `directory: ./` therefore scans a checkout
with no `*.html` in it and reports "Ran on 0 files! HTML-Proofer finished successfully" — a
**vacuous green** that validates nothing. CI had no markup-validity gate at all; the live-JS
view test (`make jstest`, ADR 0025) is dev-only and not in CI. We want CI to actually catch a
malformed tag, a duplicate element `id`, or a broken internal `#anchor` in the generated output.

## Decision
Add a **dedicated `html` job** to `.github/workflows/ci.yml` that (1) generates the four views
into `_site/` via a new `make html-demos` target, then (2) runs `anishathalye/proof-html@v2`
pointed at `./_site`. Because the views are fully self-contained (inline CSS/JS; **no** `<img>`,
external links, `<script src>`, `<link>`, or favicon), the action runs **offline**:
`disable_external: true`, `enforce_https: false`, `check_favicon: false`, `check_opengraph: false`,
`check_html: true`. The real coverage is **markup well-formedness** + **internal `#anchor` / `id`
integrity** (the multi-patient jump-index links resolve to the per-patient section ids).

Generation delegates to the Makefile (`make html-demos`) so the four-file list lives in **one**
place and CI cannot drift from local — the same CI↔Makefile parity rule as `make compile` (PR #29).

**Alternatives rejected.** (a) Append the step to the existing `test` job — that job is a 4-way
Python matrix, so it would pull and run the proof-html Docker container 4× for identical,
Python-version-independent output. (b) Switch to the W3C Nu Html Checker / `html5validator` —
stricter true HTML5 validity, but heavier (Java/Docker) and not what was asked. (c) Make it a
dev-only `make` target with no CI gate — wouldn't protect PRs.

**Pinning.** `@v2` (currently v2.2.3; no v3) matches the repo convention of major-tag pins
(`actions/checkout@v6`, `actions/setup-python@v6`). proof-html is the first **third-party**
action here (it pulls `gjtorikian/html-proofer`), a larger trust surface than the first-party
`actions/*`; pinning the release **SHA** is the available supply-chain hardening upgrade
(OWASP Top-10-for-Agentic-Apps, SECURITY §B) if Scott prefers reproducibility over auto-patch.

## Consequences
- Every PR now gates on HTML validity + internal-anchor/id integrity — a real, if narrow,
  check (the views have no external surface). A future regression (e.g. two accepted patients
  whose sanitized ids collide, or a broken jump-index link) fails the gate instead of shipping.
- CI gains one Docker-based job (image-pull cost) and its first third-party action.
- CI↔Makefile parity preserved: `make html-demos` is the single definition of the file list.
- The job is **not** automatically a required check. To make it block merges to `main`, Scott
  must add the `html` check to branch protection (Settings → Branches) — intentionally left to him.

## What the gate caught (and the fix) — revises ADR 0022
The first CI `html` run did its job: `proof-html`'s `check_html` (a full W3C/**Nu** HTML5 validator,
stricter than first assumed) flagged **4 real conformance errors**, all from ADR 0022's custom
`role="button"` interaction:
- `<li class="finding" role="button">` inside a `<ul>` — an `<li>` in a list may only be
  `role="listitem"` (report single + multi: 3 errors).
- the cited-date `<details>` nested inside the digest card's `role="button"` — a button must not
  contain interactive content (digest: 1 error).

Both were fixed with the **researched accessible patterns** (web-sourced 2026-06-07; Inclusive
Components, Adrian Roselli, scottohara.me, MDN, Nu validator):
- Findings are now real **`<button class="finding">`** elements inside the `<li>` / card — valid, and
  natively focusable + Enter/Space-activatable, so the keyboard shim (tabindex / role / keydown) is gone.
- The digest card uses the **block-link / pseudo-content** pattern: the card is no longer a button; the
  inner `<button>` gets an `::after { inset: 0 }` overlay so the whole card stays clickable, and the
  `<details>` is a **sibling raised with `z-index`** so it remains independently operable.

The single-activation-path goal of ADR 0022 is unchanged (pointer added there). Selected state stays on
the `.finding` button; the digest card reflects it via `.card:has(.finding.sel)`. View modules bumped:
`view_html` 0.3.0→0.4.0, `report_html`/`digest_html` 0.4.0→0.5.0.

## Confirmation
- Local: `make check` green (static view tests updated for the real-`<button>` markup). `make html-demos`
  writes the four files under `_site/`; **`uvx html5validator --root _site` reports zero HTML errors** (its
  only messages are CSS-logical-property false positives from a stale CSS DB — proof-html validates HTML,
  not CSS, which is why CI never flagged the logical properties that pre-existed). `grep` confirms
  **0 `role="button"`** and **0 `<details>` inside a finding button** across `_site/`.
- CI (authoritative): the `html` job runs `proof-html@v2` on `./_site` and must pass alongside `lint` and
  `test (3.10–3.13)`. Optional local equivalent (needs Docker, absent in this sandbox):
  `docker run --rm -v "$PWD/_site:/site" ghcr.io/gjtorikian/html-proofer:latest /site
  --disable-external --no-enforce-https --no-check-favicon --no-check-opengraph`.
- Interaction (CONFIRMED_USER_SIDE): Scott runs `make jstest` (headless Chromium) — click + keyboard
  activation, no cross-patient bleed, beforeprint opens `<details>`.
