# 0026 — CI HTML-validation gate: proof-html on the generated views

**Date:** 2026-06-07
**Evidence level:** IMPLEMENTED_UNVERIFIED — the `html` job is wired and the four views
generate locally (pure stdlib, deterministic); proof-html itself runs CI-side (Docker).
Promotes to CONFIRMED_ASSISTANT_SIDE once the first PR CI run shows the `html` job green.
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

## Confirmation
- Local: `make html-demos` writes the four files under `_site/` (pure stdlib, deterministic
  reference date 2026-03-15). Pre-landing audit (this session) of the actual generated output:
  **0 duplicate ids, 0 unresolved `#` anchors, 0 bare `href="#"`, 0 external refs** in all four
  views — so the gate is expected to land green with no markup fixes.
- CI (authoritative): the `html` job runs `proof-html@v2` on `./_site` and must pass alongside
  `lint` and `test (3.10–3.13)`. Optional local equivalent:
  `docker run --rm -v "$PWD/_site:/site" ghcr.io/gjtorikian/html-proofer:latest /site
  --disable-external --no-enforce-https --no-check-favicon --no-check-opengraph`.
