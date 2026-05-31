# 0004 — `--report-v1`: the combined report with v1 opt-in matching

**Date:** 2026-05-31
**Evidence level:** CONFIRMED_ASSISTANT_SIDE (68 tests green, `ruff` clean,
`--report-v1` matches the hand-written oracle)
**Type:** Build (resolves a deferred loop)

## Context
ADR 0002 deferred `--report-v1` because the combined `run_report` already
accepted the matching knobs (`normalize`/`synonyms`/`fuzzy_cutoff`) and only
`--demo-v1` exercised them. STATUS.md carried it as a small open loop. With
co-occurrence (ADR 0003) adding a 4th lens, wiring the v1 report closes the loop
and makes the v0→v1 difference visible across *all* rules in one view.

## Decision
Add `_run_report_v1()` (mirroring `_run_demo_v1`: `normalize=True`,
`synonyms=SYNONYMS`, `fuzzy_cutoff=0.85`) and a `--report-v1` flag — **no engine
logic changes**, `run_report` already takes the knobs. The oracle is a new
hand-written `REPORT_ANSWER_KEY_V1`: identical to `REPORT_ANSWER_KEY` except the
three records that merge *only* under v1 — **R006** (synonyms), **R007**
(normalize), **R014** (fuzzy) — now surface a recurrence line. Gap/frequency and
the co-occurrence records (R017–R020, which carry no variants) are unchanged;
R003 still surfaces nothing. Written by hand first, from the per-rule keys.

## Consequences
- The deferred loop is closed; every rule's v0→v1 behaviour is now visible in a
  single command, pinned by an oracle.
- A sixth report-level oracle to maintain (`REPORT_ANSWER_KEY_V1`), kept honest
  by `TestReportV1`.

## Confirmation
- `python recurrence.py --report-v1` → R006/R007/R014 now present.
- `tests/test_report.py::TestReportV1` — oracle agreement with
  `REPORT_ANSWER_KEY_V1`, the three newly-surfacing records, and the firewall
  word-ban applied to the v1 report text.
- `python -m unittest discover -s tests -t .` → 68 tests OK. `ruff` clean.
