# STATUS — health-prototype

_The front door. Read this first, update it last. One source of "where am I."_
Last updated: 2026-05-31

## Current state
- v0 recurrence engine + v1 opt-in matching (normalize / synonyms / fuzzy) +
  rules gap & frequency + **router/registry combined `--report`** — all built.
  **53 tests green**, CI green on Py 3.10–3.13.
- **PR #1** open with the full build + the Claude harness (`.claude/`, hooks,
  slash commands, `docs/`, `JOURNAL.md`). CodeRabbit review addressed; stale
  auto-generated test PR #2 closed.
- Repo on **`Inbound-health-care/health-prototype`** (org on Team).
  **Branch protection ACTIVE** on `main` (4 `test` checks + up-to-date +
  conversation resolution + linear history + no-bypass; required approvals 0).

## Open loops
- [x] Claude tool access restored on the new org (sessions run against the repo).
- [x] `JOURNAL.md` + `.claude/` harness + `docs/` landed on the branch.
- [ ] (optional) Add `docs/adr/` to complete the doc system.
- [ ] (optional) Add `CODEOWNERS` if you later move to required-approvals = 1.
- [ ] (deferred) `--report-v1` — v1-matched combined report (run_report already
      accepts the matching knobs; only `--demo-v1` is wired today).
- [ ] Pick the next build increment (below).

## Next step — pick one
Rule #4 is now a **drop-in**: append one `Expert(name, detect_x, format_x)` to
`EXPERTS` and it joins `--report` automatically.
1. **Another rule** — co-occurrence (two items recur together) or cadence change.
2. **Free-text extraction** (big) — narrative note → structured item + date.
   Reminder: it may surface "3× over 4 weeks + dates" but must NEVER label it
   "caution" — the firewall holds; the clinician judges.
3. **`--report-v1`** — small: wire a v1-matched combined report (deferred above).

## Key facts
- Branch: `claude/recurrence-detection-spec-jm3Ck`
- Spec (contract): Drive `BUILD_SPEC_RecurrenceDetection_v0_2026-05-30.md`
- Quick check: `make test` · `python recurrence.py --self-test`
- Design firewall, commands, and hard rules: see **`CLAUDE.md`**.
