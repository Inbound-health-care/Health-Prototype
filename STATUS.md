# STATUS — health-prototype

_The front door. Read this first, update it last. One source of "where am I."_
Last updated: 2026-05-31

## Current state
- v0 recurrence engine + v1 opt-in matching (normalize / synonyms / fuzzy) +
  rules gap, frequency & **co-occurrence** + router/registry combined report
  (`--report` v0 and `--report-v1`) — all built. **4 surfacing rules, 68 tests
  green**, `ruff` clean.
- **PR #1 merged** to `main` (the full v0 build + Claude harness `.claude/`,
  hooks, slash commands, `docs/`, `JOURNAL.md`); stale auto-generated test PR #2
  closed. Current work is on branch **`claude/amazing-fermi-PKUNM`** (rule #4
  co-occurrence + `--report-v1`) → new draft PR.
- Repo on **`Inbound-health-care/health-prototype`** (org on Team).
  **Branch protection ACTIVE** on `main` (4 `test` checks + up-to-date +
  conversation resolution + linear history + no-bypass; required approvals 0).

## Open loops
- [x] Claude tool access restored; `JOURNAL.md` + `.claude/` harness + `docs/`
      landed; PR #1 merged to `main`.
- [x] `docs/adr/` running decision log (0001 tool-call discipline, 0002 report
      architecture, **0003 co-occurrence**, **0004 --report-v1**).
- [x] **Rule #4 co-occurrence** — `detect_cooccurrence` + `--demo-cooccurrence`,
      `CO_OCCURRENCE_ANSWER_KEY`, records R017–R020, joins `--report`.
- [x] **`--report-v1`** — v1-matched combined report wired (`REPORT_ANSWER_KEY_V1`).
- [~] CODEOWNERS — not needed (solo developer; required-approvals stays 0).
- [x] Low-risk branch cleanup helper added: `make branch-audit` is read-only by default.
- [ ] Pick the next build increment (below).

## Next step — pick one
A 5th rule is still a **drop-in**: append one `Expert(name, detect_x, format_x)`
to `EXPERTS` and it joins `--report` automatically.
1. **Co-occurrence within a window** — opt-in `window_days` so "together" means
   "within N days," not just the same date (the deferred v1 extension of rule #4).
2. **Another rule** — cadence change (interval shifts, e.g. monthly → weekly).
3. **Free-text extraction** (big) — narrative note → structured item + date.
   Reminder: it may surface "3× over 4 weeks + dates" but must NEVER label it
   "caution" — the firewall holds; the clinician judges.

## Key facts
- Branch: `claude/amazing-fermi-PKUNM`  (base `main`, post-merge)
- Spec (contract): Drive `BUILD_SPEC_RecurrenceDetection_v0_2026-05-30.md`
- Quick check: `make test` · `python recurrence.py --self-test`
- Design firewall, commands, and hard rules: see **`CLAUDE.md`**.
