# STATUS — health-prototype

_The front door. Read this first, update it last. One source of "where am I."_
Last updated: 2026-05-30

## Current state
- v0 recurrence engine + v1 opt-in matching (normalize / synonyms / fuzzy) + two
  more rules (gap, frequency) — all built. **37 tests green**, CI green on Py 3.10–3.13.
- **PR #1** open with the full build. CodeRabbit review addressed; the stale
  auto-generated test PR #2 was closed.
- Repo transferred to **`Inbound-health-care/health-prototype`** (org on Team).
  **Branch protection ACTIVE** on `main` (4 `test` checks + up-to-date +
  conversation resolution + linear history + no-bypass; required approvals 0).

## Open loops
- [ ] **Restore Claude tool access on the new org** — grant the Claude GitHub app
      access to `Inbound-health-care`, and run sessions provisioned for the new
      repo path (old env was wired to `lostsoulfs/*`).
- [ ] (optional) Add `docs/adr/` + `JOURNAL.md` to complete the doc system.
- [ ] (optional) Add `CODEOWNERS` if you later move to required-approvals = 1.
- [ ] Pick the next build increment (below).

## Next step — pick one
1. **Router + expert registry** — one dispatch over the 3 rules → a combined
   per-record report (`--report`); makes rule #4 a drop-in. (The flagged
   architecture payoff.)
2. **Combined human-readable report** — lighter, output-only version of #1.
3. **Another rule** — co-occurrence (two items recur together) or cadence change.
4. **Free-text extraction** (big) — narrative note → structured item + date.
   Reminder: it may surface "3× over 4 weeks + dates" but must NEVER label it
   "caution" — the firewall holds; the clinician judges.

## Key facts
- Branch: `claude/recurrence-detection-spec-jm3Ck`
- Spec (contract): Drive `BUILD_SPEC_RecurrenceDetection_v0_2026-05-30.md`
- Quick check: `make test` · `python recurrence.py --self-test`
- Design firewall, commands, and hard rules: see **`CLAUDE.md`**.
