# 0007 — Cadence change: the fifth surfacing rule (interval shifted)

**Date:** 2026-06-05
**Evidence level:** CONFIRMED_USER_SIDE (2026-06-05 — Scott ran the branch on
Windows / Python 3.12.10: `--self-test` 6 scenarios pass, full suite 87 tests
pass, and a hand-made record surfaced the expected lenses). Also
CONFIRMED_ASSISTANT_SIDE in the sandbox (87 tests, `ruff` clean,
`--demo-cadence-change` / `--report` surface R016's 10d→79d shift; the dedicated
`CADENCE_CHANGE_ANSWER_KEY` matches by hand).
**Type:** Architecture / build

## Context
With four rules merged (recurrence / gap / frequency / co-occurrence), STATUS.md
and the 2026-06-04 handoff named **cadence change** as the next increment: surface
an item whose *spacing between events* shifted (e.g. monthly → weekly), as a
drop-in 5th `Expert`. The hard constraint is the librarian rule: state that the interval
changed and where, never whether faster or slower means anything, and never why.
The handoff specified the ISI-ratio framing (median interval before vs after a
pivot) and explicitly ruled out FFT / ML / heavy change-point machinery
(determinism + stdlib-only).

## Decision
Add `detect_cadence_change` as a drop-in 5th `Expert`, reusing `_record_groups`,
`_dated_sorted`, `_pick_label`, and `_merge_clause`. Signature:
`detect_cadence_change(records, field="item", min_occurrences=4, ratio=2.0, normalize=False, synonyms=None, fuzzy_cutoff=None)`.

- **Method = Pettitt change-point + median-ratio flag.** Per item with
  `>= min_occurrences` **distinct dated days**, take the consecutive inter-event
  intervals; locate the single most likely change point with **Pettitt's rank
  statistic** (argmax `|U_k|`), then flag when `max(median_before/median_after,
  median_after/median_before) >= ratio`. The hit cites both medians, the pivot
  date (where the new spacing begins), and every dated day.
- **Why Pettitt (web-checked, Scott asked).** The open question was *how to pick
  the pivot*. Research showed this is the classic "single change point in central
  tendency" problem; the standard simple, deterministic, non-ML, stdlib-friendly
  method is **Pettitt's test (1979)** (rank/Mann-Whitney based), with CUSUM the
  mean-based cousin. A naive "max median-ratio over all splits" mislocates the
  pivot (it rewards isolating one extreme interval — e.g. it would place a clean
  monthly→weekly pivot a visit early); Pettitt locates it correctly. Ties (rare,
  small N) break by larger median-ratio, then earliest split — fully deterministic.
  Sources: CRAN `trend` vignette (Pettitt); Lancaster MATH337 (CUSUM).
- **The librarian rule.** `format_cadence_change_hit` emits only
  `"<item>" interval changed from ~Xd to ~Yd at <pivot> — <dates>`. No direction
  or judgment word; the test BANNED list gains
  accelerat/decelerat/increasing/decreasing/escalat/declining/deteriorat/improving/trend.
- **Validation:** `min_occurrences >= 2`, `ratio > 1.0`, else `ValueError`.
- **Drop-in only.** Append one `Expert("cadence_change", …)`; `run_report` passes
  only the shared knobs, so `min_occurrences`/`ratio` fall through to defaults
  (consistent with ADR 0002). New `--demo-cadence-change` + `_run_demo_cadence_change`.

Rejected: FFT / ML / PELT / e-divisive (break determinism + stdlib-only);
naive max-ratio split (mislocates the pivot); fixed midpoint (misses off-centre
shifts).

## Consequences
- A fifth lens with zero router/formatter change — the ADR 0002 registry holds.
- **Oracle kept off `SAMPLE_RECORDS`.** A dedicated `CADENCE_CHANGE_RECORDS` +
  `CADENCE_CHANGE_ANSWER_KEY` (RC1 clean tightening flag; RC2 steady control; RC3
  too-few/undated control) drives the MatchesAnswerKey test, so the other per-rule
  keys do not ripple. The rule still runs in `--report`, where one **existing**
  record, **R016** (chest pain, 10d→79d), naturally surfaces a cadence line — so
  `REPORT_ANSWER_KEY` and `REPORT_ANSWER_KEY_V1` each gain that single R016 row.
- Eighth answer key; test count 74 → 87 (new `tests/test_cadence_change.py`, 4
  classes incl. the librarian-rule test, + a report composition test).

## Confirmation
- `python recurrence.py --demo-cadence-change` → R016 "chest pain" interval
  changed from ~10d to ~79d at 2026-02-20. `--report` shows the same under R016.
- `tests/test_cadence_change.py` — oracle agreement, tightening + loosening,
  steady / too-few / undated controls, ratio-threshold respect, input validation,
  and the librarian rule (neutral, cited line). `tests/test_report.py` gains a cadence
  composition test + updated registry order; `REPORT_ANSWER_KEY(_V1)` updated.
- `make check` → 87 tests OK, 6 self-test scenarios, `ruff` clean.
- **User-side (2026-06-05):** Scott ran the branch on Windows (Python 3.12.10) —
  `python recurrence.py --self-test` → 6 scenarios; `python -m unittest discover -s
  tests -t .` → 87 tests OK; and a hand-written `mytest.py` record surfaced the
  expected recurrence / gap / frequency / cadence lines. CONFIRMED_USER_SIDE.
