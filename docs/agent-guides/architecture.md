# Architecture guide (Tier 3 — load when coding the engine)

_Detail moved out of CLAUDE.md to keep Tier 1 lean (2026 progressive-disclosure
pattern). Read this when actually working on `recurrence.py` or the tests._

## Commands
- Tests:     `python -m unittest discover -s tests -t .`  (or `make test`)
- Self-test: `python recurrence.py --self-test`  (the six spec cases)
- Demos:     `python recurrence.py --demo | --demo-v1 | --demo-gap | --demo-frequency`
- Report:    `python recurrence.py --report`  (all rules, one per-record view)
- Lint:      `make lint`   ·   Clean: `make clean`

## Engine map
- `recurrence.py` — shared core `_record_groups` feeds 3 rules:
  `detect_recurrence` (same item >=N), `detect_gap` (returns after absence),
  `detect_frequency` (clusters in a window). Hits: `RecurrenceHit` / `GapHit` /
  `FrequencyHit`, each carrying `variants` (audit trail of merged spellings).
- Matching is layered and OPT-IN (defaults = exact v0): `normalize` (case/space),
  `synonyms` (human-declared map), `fuzzy_cutoff` (difflib typos). Every merge
  cites originals in `variants`; `format_*` appends `[merged: ...]`.
- Router: an `EXPERTS` registry (one `Expert` per rule) + `run_report` route the
  3 rules into a per-record `RecordReport`; `format_report` renders it. Adding a
  4th rule = appending one `Expert`. The report lists only — it never ranks.
- `data/sample_records.py` — invented records + FIVE hand-written answer keys
  (`ANSWER_KEY`, `ANSWER_KEY_V1`, `GAP_ANSWER_KEY`, `FREQUENCY_ANSWER_KEY`,
  `REPORT_ANSWER_KEY`) + `SYNONYMS`.
- `data/RECORDS.md` — data dictionary (field rationale, per-record reasons).
- `tests/` — 6 files, 53 tests. CI: `.github/workflows/ci.yml` (Py 3.10-3.13).

## Engine hard rules
- Pure Python STDLIB ONLY at runtime. No network egress. Zero real PHI, ever.
- Defaults stay EXACT-MATCH (v0). New matching is opt-in, never a default.
- Validate args — raise `ValueError` on bad input (library code fails loudly).
- Determinism: stable ordering; ANSWER KEYS ARE WRITTEN BY HAND FIRST, the code
  is made to match — never patch the key toward the code.

## Engine firewall (also in CLAUDE.md — the one rule that governs the engine)
Librarian, not interpreter. Surface, count, cite provenance. NEVER score, rank,
diagnose, or say what a pattern means. No "caution/concern/worsening/risk/severe"
in output. Human or human-declared policy supplies all judgment. Tests enforce it.

## Workflow detail
- Log decisions as you go -> `docs/adr/` (each ADR: Context, Decision, Consequences,
  Confirmation = how it's checked, evidence level). Includes the assistant's own
  process/behavior changes, not just code.
- Tool-call discipline (ADR 0001): verify with ONE decisive call — capture to a
  file, trust exit code + a printed sentinel (`rc=0 :: OK`) over rendered prose,
  prefer ASCII summaries, batch checks, don't re-run a strong signal.
- Spec-driven: Drive `BUILD_SPEC` is the contract. Small, verified increments.
- Oracle method: expected answer first; cross-check tests catch errors.
- CodeRabbit triage: apply the good, skip noise, ask if ambiguous. Per 2026
  guidance, every reviewer comment is a signal the agent lacked context — when one
  lands, consider adding a line to CLAUDE.md.
- Branch protection active on `main` (4 `test` checks + conversation resolution).

## Scope
This repo only. Don't rebuild the old `pharmacy_tool_v13` (reference lumber).
