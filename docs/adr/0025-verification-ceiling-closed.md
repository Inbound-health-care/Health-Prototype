# 0025 — Verification ceiling: live JS test + Hypothesis gates CI + oracle convention

**Date:** 2026-06-07
**Evidence level:** IMPLEMENTED_UNVERIFIED — CONFIRMED_ASSISTANT_SIDE for the CI-gated
property tests (`make check` + CI green); the live JS test is dev-only and SKIPS where
Playwright/Chromium is absent, so it is CONFIRMED only when run locally with a browser.
Promotes to CONFIRMED_USER_SIDE when Scott runs `make jstest`.
**Type:** Testing / CI / verification
**Resolves:** `docs/AUDIT_2026-06-07.md` Tier 2 #3 (zero live JS testing), #4 (Hypothesis
properties don't gate CI), #5 (oracle independence unprovable).

## Context
The audit found that "248 green" did NOT prove three things:
- **#3 — the interactive JS is untested.** The views ship real behavior (click-to-highlight,
  keyboard Enter/Space, `beforeprint`/`afterprint` opening `<details>`, per-patient scope
  isolation), but the suite asserts it only as **static strings** (`assertIn("'Enter'", html)`).
  A runtime JS bug — a broken keyboard path, real cross-patient highlight bleed — passes green.
- **#4 — the best protection for the fail-closed extractor doesn't run in CI.** The Hypothesis
  no-bleed / consistent-shift / additivity properties (~600 generated cases) collapse to **1
  skip** under `make test`/CI because hypothesis isn't installed; they run only via `make proptest`.
- **#5 — oracle independence is git-unprovable.** `recurrence.py` and `data/sample_records.py`
  co-landed in the first commit (`21a150d`), so there is no git evidence the "oracle-first,
  never patch toward code" rule held.

## Decision
**(#3) Add a dev-only live JS/DOM test, NOT in CI.** New `tests/test_view_js.py` renders the
views' `build_demo_html` / `build_demo_multi_html` output, loads it in **headless Chromium via
Playwright**, and executes the real interactions: click toggles `.sel`/`aria-pressed` and lights
the matching `mark.cite`/`.tick`; Enter and Space activate from the keyboard; `beforeprint` opens
every `<details>` and `afterprint` restores; and — the key one — a click in one `.patient` block
lights **nothing** in any other block (runtime no-bleed). Guarded to **skip cleanly** when
Playwright or the browser binary is absent, so `make test`/CI stay pure-stdlib green. New
`make jstest` (uvx, mirrors `make proptest`). Kept OUT of CI by Scott's choice — browser binaries
are heavy; the protection is local/on-demand. (Web-confirmed 2026-06-07, RESEARCH_ONLY: Playwright
is the 2026 default for executing event paths like keyboard/`beforeprint` that lighter
HTML-parsers can't.)

**(#4) Gate the Hypothesis properties on CI.** A CI step installs hypothesis and runs
`tests.test_extract_multi_properties` on every PR — the ~600-case invariants now protect the
fail-closed extractor instead of skipping. **Determinism (web-confirmed best practice):** under
CI the module registers and loads a **derandomized** Hypothesis profile (keyed on the
`CI` env var) so a CI failure reproduces locally byte-for-byte; `make proptest` stays randomized
locally for broader exploration. Runtime stays pure-stdlib — hypothesis is a CI/dev tool only.

**(#5) Document the oracle convention as the guarantee.** `data/sample_records.py` now states
that, because engine and oracle co-landed, the independence rests on the stated convention
(oracle-first, never patched toward code) and author discipline, not commit ordering — and that
new oracle entries should land in their own commit, before the code that makes them pass.

## Consequences
- A runtime JS regression in the views is now catchable locally (`make jstest`); the static-string
  asserts remain as the always-on, dependency-free floor.
- The fail-closed extractor's safety invariants gate every PR; CI failures are reproducible.
- The oracle-independence claim is honestly scoped and made forward-visible.
- No runtime dependency added: the engine and `make test` stay pure-stdlib; Playwright and
  hypothesis are dev/CI-only.

## Confirmation
- `make check` green (the new JS module skips without Playwright; counts unchanged by the skip).
- `make proptest` runs the properties locally; CI runs them derandomized (the prior `1 skip` is gone).
- `make jstest` (after `playwright install chromium`) executes all four behaviors — pending
  CONFIRMED_USER_SIDE when Scott runs it.
