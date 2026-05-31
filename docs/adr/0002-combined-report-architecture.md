# 0002 — Combined report: expert registry, omit clean records, additive formatter kwarg

**Date:** 2026-05-31
**Evidence level:** CONFIRMED_ASSISTANT_SIDE (53 tests green, `make lint` clean,
`--report` output matches the hand-written oracle)
**Type:** Architecture / build

## Context
The three surfacing rules (`detect_recurrence`, `detect_gap`,
`detect_frequency`) were each reachable only one at a time via separate
`--demo-*` flags. There was no single view of everything surfaced for a record.
STATUS.md flagged a router over an expert registry → a combined per-record
`--report` as "the architecture payoff," and as the thing that makes a 4th rule
a drop-in. The hard constraint: the report must stay a **librarian** — list
what each rule surfaced, never rank/score/total/prioritize across records.

## Decision
Add a thin, **additive** layer over the unchanged rules:

- `Expert` (frozen dataclass) + an ordered `EXPERTS` registry — one entry per
  rule. The router calls each `detect_*` with **only the four shared matching
  knobs** (`field`/`normalize`/`synonyms`/`fuzzy_cutoff`); rule-specific
  thresholds (`min_count`/`gap_days`/`window_days`) fall through to their own
  defaults, so defaults live in one place (the function signatures).
- `run_report` groups hits into `RecordReport`/`Finding`, ordered records-by-id
  then experts-in-registry-order. **Records with zero findings are omitted** —
  surfacing what is present, never asserting "clean."
- `format_report` renders it; the three `format_*` functions gained an opt-in
  `with_record=True` kwarg (default preserves prior output) so the report can
  drop the redundant `Record Rxxx:` prefix under each header.
- Oracle: hand-written `REPORT_ANSWER_KEY` (the 5th key), composed from the
  three existing keys. `--report-v1` deliberately deferred (v1 only changes
  recurrence groupings, already shown by `--demo-v1`).

Rejected: a per-expert config dict in the registry (would re-encode defaults
that already live in the signatures — drift risk); and stripping the record
prefix via string surgery on existing output (fragile — chose the additive
kwarg instead).

## Consequences
- A 4th rule is now a true drop-in: append one `Expert` and it joins `--report`.
- The new view is pinned two ways — oracle agreement *and* composition
  consistency against the `detect_*` functions — so it can't silently diverge.
- Mild cost: the report repeats the rule logic only via three extra detect
  calls (acceptable; reuses each rule's own stable ordering verbatim).
- The user chose the "clean nested" render (record header + de-prefixed lines).

## Confirmation
- `python recurrence.py --report` → matches `REPORT_ANSWER_KEY` (12 records;
  R015 = recurrence+gap, R016 = recurrence+frequency; R003/R006/R007/R014
  omitted).
- `tests/test_report.py` — oracle, composition (×3), determinism, omission,
  registry integrity, and a firewall test that also bans ranking/aggregation
  words (top/most/priority/rank/total/highest/worst/best).
- `python -m unittest discover -s tests -t .` → 53 tests OK.
- `make lint` → clean. Commits `3cc27bb` + `bd657c9`.
