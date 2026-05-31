# 0003 — Co-occurrence: the fourth surfacing rule (two items, same dates)

**Date:** 2026-05-31
**Evidence level:** CONFIRMED_ASSISTANT_SIDE (68 tests green, `ruff` clean,
`--demo-cooccurrence` / `--report` match the hand-written oracles)
**Type:** Architecture / build

## Context
After the router/registry landed (ADR 0002), STATUS.md named a 4th rule as the
next increment and co-occurrence — "two items that recur *together*" — as the
first candidate. The registry was built so a 4th rule is a drop-in
(`detect_x` + `XHit` + `format_x` + one `Expert`; router/formatter unchanged).
The hard constraint: co-occurrence must stay a **librarian** — a count of shared
dates, never a claim that the two items are associated, linked, or correlated.

## Decision
Add `detect_cooccurrence` as a drop-in 4th `Expert`, reusing `_record_groups`,
`_pick_label`, and `_merge_clause`. Three design choices, each a real fork:

- **Definition = same-date, exact (v0).** Two distinct items in one record that
  both appear on the *same date*, on `min_count` (default **2**) or more distinct
  shared dates — so the *pairing itself* recurs. Pure string-set intersection of
  each item's dated days; **undated entries are excluded** (a date that does not
  exist cannot be shared). A within-window variant (`window_days`) is the obvious
  v1 extension and is **deliberately deferred** — defaults stay exact (the hard
  rule). `min_count` falls through to its default in `run_report`, consistent
  with how recurrence/frequency defaults already behave there.
- **`min_count=2` means the *pairing* recurs**, distinct from "two items each
  recur independently." Two controls pin the difference: **R019** (both items
  recur but never share a date → nothing) and **R020** (share exactly one date,
  below threshold → nothing).
- **Two-item provenance.** A pair has two audit trails, so `CooccurrenceHit`
  carries `variants_a` + `variants_b`; `_pair_merge_clause` appends an
  item-labelled `[merged: …]` clause per side that merged (reusing the existing
  token, so it stays grep-compatible), empty under v0. The hit also exposes a
  read-only `item` property (`"item_a + item_b"`) so the combined report — which
  shapes findings by `hit.item` — needs no special-casing. Pair and hit ordering
  are deterministic (sorted canonical key; `itertools.combinations`).

Rejected: cryptic `a`/`b` merge labels (chose item-labelled); special-casing the
report shaper for the pair (chose the `item` property — keeps the router generic).

## Consequences
- A genuinely new surfacing lens with zero router/formatter change — the
  registry abstraction paid off exactly as ADR 0002 predicted.
- Co-occurrence records entangle with recurrence (a shared-date item appears ≥2×,
  so it also recurs), which cascaded into `ANSWER_KEY` / `ANSWER_KEY_V1` /
  `REPORT_ANSWER_KEY`; all re-derived **by hand** (oracle-first), keeping
  GAP/FREQUENCY untouched by choosing tight dates (max 69-day gap, no 3-in-30).
- A fifth per-rule oracle (`CO_OCCURRENCE_ANSWER_KEY`) and the records R017–R020.

## Confirmation
- `python recurrence.py --demo-cooccurrence` → R017 (one pair), R018 (three
  pairs); `--report` shows R017/R018 co-occurrence lines.
- `tests/test_cooccurrence.py` — oracle agreement, the two controls (never-share,
  single-share), 3-pair combinatorics + ordering, undated exclusion, input
  validation, and a firewall test banning relationship words
  (associated/correlated/linked/cause/…). `tests/test_report.py` gained a
  co-occurrence composition test and updated registry order.
- `python -m unittest discover -s tests -t .` → 68 tests OK. `ruff` clean.
