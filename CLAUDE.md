# CLAUDE.md — health-prototype

Recurrence Detection Engine: a domain-agnostic surfacing engine for health
records. Repo: `Inbound-health-care/health-prototype`. Pure stdlib, local-only,
**zero real PHI**.

## The one rule that governs everything
**Librarian, not interpreter.** Surface, count, and cite provenance — NEVER
score, rank, diagnose, or say what a pattern *means*. No "caution / concern /
worsening / risk / severe" in output. The human (or a human-declared policy)
supplies all judgment. Tests enforce this — keep it that way.

## Commands
- Tests:     `python -m unittest discover -s tests -t .`  (or `make test`)
- Self-test: `python recurrence.py --self-test`  (the six spec cases)
- Demos:     `python recurrence.py --demo | --demo-v1 | --demo-gap | --demo-frequency`
- Report:    `python recurrence.py --report`  (all rules, one per-record view)
- Lint:      `make lint`   ·   Clean: `make clean`

## Architecture map
- `recurrence.py` — the engine. Shared core `_record_groups` feeds 3 rules:
  `detect_recurrence` (same item ≥N), `detect_gap` (returns after absence),
  `detect_frequency` (clusters in a window). Hits: `RecurrenceHit` / `GapHit` /
  `FrequencyHit`, each carrying `variants` (the audit trail of merged spellings).
- Matching is layered and **opt-in** (defaults = exact v0): `normalize`
  (case/space), `synonyms` (human-declared map), `fuzzy_cutoff` (difflib typos).
  Every merge cites originals in `variants`; `format_*` appends `[merged: ...]`.
- Router: an `EXPERTS` registry (one `Expert` per rule) + `run_report` route the
  3 rules into a per-record `RecordReport`; `format_report` renders it. Adding a
  4th rule = appending one `Expert`. The report lists only — it never ranks.
- `data/sample_records.py` — invented records + FIVE hand-written answer keys
  (`ANSWER_KEY`, `ANSWER_KEY_V1`, `GAP_ANSWER_KEY`, `FREQUENCY_ANSWER_KEY`,
  `REPORT_ANSWER_KEY`) + `SYNONYMS`.
- `data/RECORDS.md` — data dictionary (field rationale, per-record reasons).
- `tests/` — 6 files, 53 tests. CI: `.github/workflows/ci.yml` (Py 3.10–3.13).

## Hard rules
- Pure Python **stdlib only** at runtime. No network egress. Zero real PHI, ever.
- Defaults stay **exact-match** (v0). New matching is opt-in, never a default.
- Validate args — raise `ValueError` on bad input (library code fails loudly).
- Determinism: stable ordering; **answer keys are written by hand first**, the
  code is made to match — never patch the key toward the code.

## Workflow preferences
- **Log decisions as you go** → `docs/adr/` (see its README for format). Write an
  ADR *when the decision is made*, not at session end — and this includes your
  OWN process/behavior changes (what you started doing differently, and why), not
  just code. Each ADR carries a Confirmation (how it's checked) + evidence level.
  An improvement left only in chat dies at the session reset.
- **Tool calls (ADR 0001):** verify with ONE decisive call — capture to a file,
  trust the exit code + a printed sentinel (`rc=0 :: OK`) over rendered prose,
  prefer ASCII summaries, batch checks, and don't re-run a strong signal. Re-run
  only on genuine self-contradiction.
- Spec-driven: the Drive `BUILD_SPEC` is the contract. Small, verified increments.
- Oracle method: write the expected answer first; cross-check tests catch drift.
- Web-search current best practices when hitting a real issue; cite sources.
- Commit + push to the feature branch; keep PRs draft until asked. Branch
  protection on `main` is active (require the 4 `test` checks + conversation
  resolution). Be frugal with GitHub comments.
- Triage CodeRabbit: apply the good, skip noise, ask if ambiguous.

## Scope boundaries
- This repo only. Don't rebuild the old `pharmacy_tool_v13` (reference lumber).
- **Read `STATUS.md` first** for "where am I / what's next."
