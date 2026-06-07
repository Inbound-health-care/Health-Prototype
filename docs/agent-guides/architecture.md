# Architecture guide (Tier 3 — load when coding the engine)

_Detail moved out of CLAUDE.md to keep Tier 1 lean (progressive-disclosure
pattern). Read this when actually working on `recurrence.py` or the tests.
This file is the source of truth for engine facts — keep the counts here in
sync with the code (see ADR 0005)._

## Commands
- Tests:     `python -m unittest discover -s tests -t .`  (or `make test`)
- Self-test: `python recurrence.py --self-test`  (the six spec cases)
- Demos:     `python recurrence.py --demo | --demo-v1 | --demo-gap | --demo-frequency | --demo-cooccurrence | --demo-cooccurrence-window | --demo-cadence-change`
- Report:    `python recurrence.py --report | --report-v1`  (all rules, one per-record view; v0 / v1 matching)
- Lint:      `make lint`   ·   Clean: `make clean`

## Engine map
- `recurrence.py` — the engine. Shared core `_record_groups` feeds 5 rules:
  `detect_recurrence` (same item >=N), `detect_gap` (returns after absence),
  `detect_frequency` (clusters in a window), `detect_cooccurrence` (two items on
  the same dates >=N, or within an opt-in `window_days`), `detect_cadence_change`
  (inter-event spacing shifted by `ratio` across a Pettitt-located pivot). Hits:
  `RecurrenceHit` / `GapHit` / `FrequencyHit` / `CooccurrenceHit` /
  `CadenceChangeHit`, each carrying `variants` (the audit trail of merged
  spellings; co-occurrence carries one per item: `variants_a` / `variants_b`).
- Matching is layered and OPT-IN (defaults = exact v0): `normalize` (case/space),
  `synonyms` (human-declared map), `fuzzy_cutoff` (difflib typos). Every merge
  cites originals in `variants`; `format_*` appends `[merged: ...]`.
- Router: an `EXPERTS` registry (one `Expert` per rule) + `run_report` route the
  5 rules into a per-record `RecordReport`; `format_report` renders it. Adding a
  6th rule = appending one `Expert`. The report lists only — it never ranks.
- `data/sample_records.py` — invented records + NINE hand-written answer keys
  (`ANSWER_KEY`, `ANSWER_KEY_V1`, `GAP_ANSWER_KEY`, `FREQUENCY_ANSWER_KEY`,
  `CO_OCCURRENCE_ANSWER_KEY`, `REPORT_ANSWER_KEY`, `REPORT_ANSWER_KEY_V1`,
  `CADENCE_CHANGE_ANSWER_KEY`, `FREETEXT_EXPECTED_RECORDS`) + `SYNONYMS`. Cadence has a dedicated
  `CADENCE_CHANGE_RECORDS` set (kept out of `SAMPLE_RECORDS` to avoid key ripple).
- `data/RECORDS.md` — data dictionary (field rationale, per-record reasons).
- `extract.py` — free-text extraction FRONT-END (slices 1–2 + relative-date anchoring +
  multi-patient): turns dated prose into the canonical record shape the 5 rules consume
  unchanged (allowlist gazetteer + explicit-date regex + char-offset `source_span`;
  de-identified date shift; opt-in matching modes; fail-closed `extract_records_multi`).
  A front door to the librarian, not part of it — imports `recurrence.py`, never the reverse.
  See ADR 0008/0012/0013/0016.
- `view_html.py` — shared VIEW FLOOR (ADR 0021): theme tokens, cited-span highlight helpers,
  one click+keyboard activation path (ADR 0022), print CSS + `beforeprint` handler, the
  at-a-glance cited-date timeline (ADR 0023), and the multi-patient chrome. Imported by both
  views; imports `recurrence.py` only (never the reverse).
- `report_html.py` — inspection view (ADR 0014): the source note with cited spans beside the
  `run_report` findings, click-to-highlight; single + multi-patient (ADR 0021).
- `digest_html.py` — clinician Pre-visit Pattern Digest (ADR 0015): the five lenses as cited
  cards beside the note; single + multi-patient (ADR 0020). Both views are pure stdlib, no network.
- `tests/` — 18 test files, 252 tests (5 skipped: the dev-only Hypothesis properties + the
  dev-only live-JS view test, both gated on optional tools — see ADR 0025). Engine 90 + free-text
  slices + multi-patient + all three HTML views + theme. CI: `.github/workflows/ci.yml`
  (Py 3.10-3.13); CI also runs the Hypothesis properties (ADR 0025).

## Engine hard rules
- Pure Python STDLIB ONLY at runtime. No network egress. Zero real PHI, ever.
- Defaults stay EXACT-MATCH (v0). New matching is opt-in, never a default.
- Validate args — raise `ValueError` on bad input (library code fails loudly).
- Determinism: stable ordering; ANSWER KEYS ARE WRITTEN BY HAND FIRST, the code
  is made to match — never patch the key toward the code. (Engine + oracle co-landed in
  the first commit, so this independence rests on the stated convention + author discipline,
  not git ordering — see `data/sample_records.py` and ADR 0025; land new oracle entries in
  their own commit, before the code that makes them pass.)

## The librarian rule (also in CLAUDE.md — the one rule that governs the engine)
Librarian, not interpreter. Surface, count, cite provenance. NEVER score, rank,
diagnose, or say what a pattern means. No "caution/concern/worsening/risk/severe"
in output. Human or human-declared policy supplies all judgment. Tests enforce it.

## Workflow detail
- Log decisions as you go -> `docs/adr/` (each ADR: Context, Decision,
  Consequences, Confirmation = how it's checked, evidence level). Includes the
  assistant's own process/behavior changes, not just code. An improvement left
  only in chat dies at the session reset.
- Tool-call discipline (ADR 0001): verify with ONE decisive call — capture to a
  file, trust exit code + a printed sentinel (`rc=0 :: OK`) over rendered prose,
  prefer ASCII summaries, batch checks, don't re-run a strong signal.
- Spec-driven: the Drive `BUILD_SPEC` is the contract. Small, verified increments.
- Oracle method: write the expected answer first; cross-check tests catch drift.
- Web-search current best practices when hitting a real issue; cite sources.
- Commit + push to the feature branch; keep PRs draft until asked. Branch
  protection active on `main` (4 `test` checks + conversation resolution). Be
  frugal with GitHub comments.
- Triage CodeRabbit: apply the good, skip noise, ask if ambiguous.

## Scope
This repo only. Don't rebuild the old `pharmacy_tool_v13` (reference lumber).
