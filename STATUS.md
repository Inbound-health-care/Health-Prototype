# STATUS — health-prototype

_The front door. Read this first, update it last. One source of "where am I."_
Last updated: 2026-05-31

## Current state
- **Engine: 4 surfacing rules on `main`, 68 tests green, `ruff` clean.**
  `detect_recurrence` / `detect_gap` / `detect_frequency` / `detect_cooccurrence`
  + v1 opt-in matching (normalize / synonyms / fuzzy) + router/registry combined
  report (`--report` v0 and `--report-v1`). All merged — PRs #1, #3, #4, and #7
  (doc/harness salvage + Tier-1/Tier-3 split).
- **This branch (`claude/quirky-brahmagupta-P0H4b`) — back-end / workflow hardening
  (draft PR #8). ENGINE CODE FROZEN this phase** (Scott: fix all back-end/workflow
  things before changing any code). Done so far: toolchain audit, handoff-loss
  guard (live), and a drift sweep correcting STATUS + the cold-start handoff.
  CI green on PR #8 (3.10–3.13).
- Repo on **`Inbound-health-care/health-prototype`** (org on Team).
  **Branch protection ACTIVE** on `main` (4 `test` checks + up-to-date +
  conversation resolution + linear history + no-bypass; required approvals 0).

## Open loops
- [x] All 4 rules + v1 matching + combined report merged to `main`.
- [x] `docs/adr/` running log (0001 tool-call, 0002 report arch, 0003
      co-occurrence, 0004 `--report-v1`, **0005 doc/harness reconciliation**).
- [x] Doc/harness stack salvaged off `spec-jm3Ck` and merged to `main` via PR #7.
- [x] Stale branches retired: only `main` + the active working branch remain on
      origin (`spec-jm3Ck` and `coderabbitai/utg/379a87a` are gone).
- [ ] **PR #6** (Codex, draft) — `--version` + `VERSION` + CLI test + `make check`
      + hygiene docs (`CONTRIBUTING.md` / `PUBLISH_CHECKLIST.md` / `.gitignore`).
      **2 commits behind `main`; BUNDLES engine code** (`--version` in
      `recurrence.py`) with back-end hygiene — so it can't merge as-is during the
      engine-frozen phase. Disposition pending Scott (extract back-end bits / defer
      code / leave). **PR #5 closed** as its duplicate.
- [ ] Pick the next build increment (below) — AFTER the back-end pass is signed off.
- [x] **Toolchain audit** (`docs/TOOLCHAIN_AUDIT_2026-05-31.md`): the managed web
      env pre-installs the 2026 stack (pytest 9 / ruff 0.15.8 / mypy 1.19 / uv 0.8);
      coverage/bandit/ty are `uvx`-on-demand. Added optional Makefile targets
      (`tools`/`typecheck`/`fmt-check`/`fmt`/`cov`/`security`) + a hook tool line.
      Engine stays pure-stdlib — all dev-only, additive.
- [x] **Two SURFACED capability flags — DECIDED leave-as-is (Scott, 2026-05-31):**
      mypy's unguarded-Optional at `recurrence.py:501` stays a noted flag (no runtime
      bug; tests green); `ruff format` (would rewrite 10/12 files) NOT applied — keep
      hand-formatting. `make typecheck` / `make fmt-check` preview either anytime.
- [x] **pygame — dropped** (Scott, 2026-05-31): out-of-scope for this stdlib repo;
      not added. Nothing in the repo references it.
- [x] **Handoff-loss guard — LIVE** (so a local-only handoff can't vanish again, as
      the AuditAndBuild one did): `/handoff` commits+pushes by default, and the `Stop`
      hook `.claude/hooks/stop_handoff_guard.py` (registered in `.claude/settings.json`,
      Scott OK'd 2026-05-31) refuses to end a session while a `*handoff*.md` is
      uncommitted. Narrow scope (excludes `.claude/`), fail-open, loop-safe.

## Next step — pick one
A 5th rule is still a **drop-in**: append one `Expert(name, detect_x, format_x)`
to `EXPERTS` and it joins `--report` automatically.
1. **Co-occurrence within a window** — opt-in `window_days` so "together" means
   "within N days," not just the same date (the deferred v1 extension of rule #4).
2. **Cadence change** — interval shifts (e.g. monthly -> weekly).
3. **Free-text extraction** (big) — narrative note -> structured item + date.
   It may surface "3x over 4 weeks + dates" but must NEVER label it "caution" —
   the firewall holds; the clinician judges.

## Key facts
- Branch: `claude/quirky-brahmagupta-P0H4b`  (base `main`, post-merge of #1/#3/#4/#7)
- Spec (contract): Drive `BUILD_SPEC_RecurrenceDetection_v0_2026-05-30.md`
- Quick check: `make test` · `python recurrence.py --self-test`
- Tier-1 rules + firewall: **`CLAUDE.md`**.
  Engine detail (commands / architecture / hard rules): **`docs/agent-guides/architecture.md`**.
