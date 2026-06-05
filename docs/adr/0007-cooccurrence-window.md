# 0007 — Co-occurrence within a window (opt-in `window_days`)

**Date:** 2026-06-05
**Evidence level:** CONFIRMED_ASSISTANT_SIDE (76 tests green, `ruff` clean,
`--demo-cooccurrence-window` surfaces the expected within-window pair; the
existing `CO_OCCURRENCE_ANSWER_KEY` / `REPORT_ANSWER_KEY` tests still pass
unedited, proving the default reduces to v0)
**Type:** Architecture / build

## Context
ADR 0003 shipped co-occurrence as **same-date** and named a within-window variant
(`window_days`) as "the obvious v1 extension … deliberately deferred — defaults
stay exact." STATUS.md's engine-code order put it first ("DO FIRST"). This ADR
implements it: extend rule #4 so "together" can mean "within N days," strictly
opt-in, without disturbing the same-date default or any existing oracle.

## Decision
Add `window_days: int = 0` to `detect_cooccurrence` (after `field`, before
`min_count`, mirroring `detect_frequency`). Three forks, each decided:

- **Default `window_days=0` == same date == v0.** At window 0 an `item_a` date
  qualifies iff `item_b` shares it — set intersection — so count and cited dates
  are byte-identical to today. The unedited `CO_OCCURRENCE_ANSWER_KEY` test is the
  guardrail. Validation mirrors frequency: `window_days < 0` raises `ValueError`.
- **Counting = anchor-date, anchored on `item_a` (Scott's choice).** `count` =
  the number of `item_a`'s distinct dated days that have **any** `item_b` day
  within `window_days`; cited `dates` are those `item_a` days. Anchoring on
  `item_a` (the pair's canonically-first item) keeps it deterministic. It is
  **asymmetric by design** — anchoring on `item_b` could give a different count
  when one item clusters denser than the other. Rejected: one-to-one greedy
  matching (more symmetric but needed a paired-date citation and a hit-shape
  change) and a combinatorial all-pairs count (inflates, not a clean "how many
  times").
- **No hit-shape or formatter change.** Because the citation stays the anchor
  item's single ISO dates, `CooccurrenceHit` and `format_cooccurrence_hit` are
  untouched; the line stays `"a" + "b" co-occurred N times — <dates>`. The window
  is **not** printed on the per-line output (it would need a new field and risks
  reading as a claim); the cited dates already show the proximity.

`window_days` is a rule-specific threshold, so — consistent with ADR 0002 — it
falls through to its default in `run_report`; the combined `--report` stays
same-date and `REPORT_ANSWER_KEY` is untouched. Windowing is reached via a direct
`detect_cooccurrence(..., window_days=N)` call and the new
`--demo-cooccurrence-window` (window 7).

## Consequences
- A genuinely new lens (near-in-time co-occurrence) with zero change to the hit,
  the formatter, the registry, or the router — the ADR 0002 abstraction holds.
- The count is asymmetric (anchored on `item_a`); this is documented here and
  asserted by a test, so it is a known property, not a surprise.
- No global oracle churn: windowing is tested with inline fixtures (the pattern
  the undated-exclusion test already uses), so `ANSWER_KEY` / `ANSWER_KEY_V1` /
  `CO_OCCURRENCE_ANSWER_KEY` / `REPORT_ANSWER_KEY` / gap / frequency keys are all
  unchanged. Test count 68 → 76.
- The combined report still treats co-occurrence as same-date; threading the
  window into `--report` (or a general CLI threshold flag) is a future option.

## Confirmation
- `python recurrence.py --demo-cooccurrence` → unchanged (R017, R018). `--demo-cooccurrence-window`
  → R017/R018 plus **R020** (edema/back-pain, 4 days apart) surfaces; R019 (15
  days apart) stays silent.
- `tests/test_cooccurrence.py::TestCooccurrenceWindow` — default reduces to
  same-date, within-window surfaces, just-outside stays silent, `min_count`
  respected, anchor-on-`item_a` asymmetry, undated excluded, `window_days < 0`
  raises, and the firewall holds on a windowed (cross-day) line.
- `tests/test_cooccurrence.py::TestCooccurrenceMatchesAnswerKey` and
  `tests/test_report.py` pass unedited (default == v0; report stays exact).
- `make check` → 76 tests OK, 6 self-test scenarios, `ruff` clean.
