# STATUS — health-prototype

_The front door. Read this first, update it last. One source of "where am I."_
Last updated: 2026-06-05

## Current state
- **Engine: 4 surfacing rules on `main`, 68 tests green, `ruff` clean.**
  `detect_recurrence` / `detect_gap` / `detect_frequency` / `detect_cooccurrence`
  + v1 opt-in matching (normalize / synonyms / fuzzy) + router/registry combined
  report (`--report` v0 and `--report-v1`). All merged — PRs #1, #3, #4, #7, #8.
- **Back-end / workflow hardening — MERGED (PR #8).** Toolchain audit, handoff-loss
  guard (live), a drift sweep correcting STATUS + the cold-start handoff, a new
  **CI lint gate** (ruff, pinned 0.15.8) + `make check`, and the back-end hygiene
  extracted from PR #6 (CONTRIBUTING / PUBLISH_CHECKLIST / `.gitignore`).
- **Control-doc hardening — MERGED (PR #9).** `AGENTS.md` as the engine-agnostic
  **source of truth** (2026 AGENTS.md standard); `CLAUDE.md` slimmed to a pointer +
  Claude-specific notes; `SECURITY_AND_TOOL_POLICY.md`, `LOAD_TRACE_TEMPLATE.md`,
  `PROJECT_MAP.md`; AGENTS.md-first load order (`LOAD.md` + `repo-onboard`).
  Docs-only — engine untouched. See ADR 0006.
- **Co-occurrence window (`claude/hopeful-einstein-C78CE`) — implemented, `make check`
  green, needs review/CI.** Opt-in `window_days` extends rule #4: default 0 ==
  same-date (v0 oracle untouched), anchor-date count on `item_a`, gated out of
  `--report`. New `--demo-cooccurrence-window`. 76 tests green, `ruff` clean.
  README/architecture brought current; see ADR 0007.
- Repo on **`Inbound-health-care/health-prototype`** (org on Team).
  **Branch protection ACTIVE** on `main` (4 `test` checks + up-to-date +
  conversation resolution + linear history + no-bypass; required approvals 0).
  **FOLLOW-UP for Scott:** the `lint` CI check is not yet a *required* check —
  add it to branch protection (GitHub Settings → Branches) to gate merges on it.

## Open loops
- [x] All 4 rules + v1 matching + combined report merged to `main`.
- [x] `docs/adr/` running log (0001 tool-call, 0002 report arch, 0003 co-occurrence,
      0004 `--report-v1`, 0005 doc/harness reconciliation, 0006 AGENTS.md source-of-truth,
      **0007 co-occurrence window**).
- [x] Doc/harness stack salvaged off `spec-jm3Ck` and merged to `main` via PR #7.
- [x] Stale branches retired: only `main` + active working branches remain on origin.
- [x] **PR #6 resolved**: back-end bits (`CONTRIBUTING.md`, `docs/PUBLISH_CHECKLIST.md`,
      `make check`, `.gitignore` hygiene) brought into PR #8; **PR #6 closed**, **PR #5 closed**.
- [x] **Control-doc hardening (PR #9) — MERGED**: AGENTS.md source of truth + slim
      CLAUDE.md + SECURITY_AND_TOOL_POLICY + LOAD_TRACE + PROJECT_MAP + ADR 0006.
- [ ] **Co-occurrence window (`claude/hopeful-einstein-C78CE`)** — opt-in `window_days`
      on rule #4 (ADR 0007); default 0 == v0, anchor-date count on `item_a`.
      Implemented, `make check` green; needs review/CI.
- [ ] **DEFERRED to the code phase** (the engine bit of PR #6): `VERSION = "0.4.0"`
      + a `--version` flag printing `Health-Prototype recurrence engine 0.4.0`
      + `tests/test_cli.py`. Re-add when engine code unfreezes.
- [x] **Toolchain audit** (`docs/TOOLCHAIN_AUDIT_2026-05-31.md`): managed web env
      pre-installs the 2026 stack (pytest 9 / ruff 0.15.8 / mypy 1.19 / uv 0.8);
      coverage/bandit/ty `uvx`-on-demand. Optional Makefile targets added; engine
      stays pure-stdlib (all dev-only, additive).
- [x] **Capability flags — leave-as-is (Scott, 2026-05-31):** mypy unguarded-Optional
      at `recurrence.py:501` noted (no runtime bug; tests green); `ruff format` NOT
      applied — keep hand-formatting. Preview via `make typecheck` / `make fmt-check`.
- [x] **pygame — dropped** (Scott, 2026-05-31): out-of-scope for this stdlib repo.
- [x] **Handoff-loss guard — LIVE**: `/handoff` commits+pushes by default; the `Stop`
      hook `.claude/hooks/stop_handoff_guard.py` refuses to end a session while a
      `*handoff*.md` is uncommitted. Narrow scope, fail-open, loop-safe.

## Next step — decided order (engine code phase)
A 5th rule is a **drop-in**: append one `Expert(name, detect_x, format_x)` to
`EXPERTS` and it joins `--report` automatically. Scott's order:
1. ~~**Co-occurrence within a window**~~ — DONE (ADR 0007, on
   `claude/hopeful-einstein-C78CE`): opt-in `window_days` extends rule #4,
   default 0 == same-date, anchor-date count on `item_a`.
2. **Cadence change** — interval shifts (e.g. monthly -> weekly); new rule #5,
   ISI-ratio method (no FFT/ML). **DO NEXT.**
3. ~~Free-text extraction~~ — deferred for now (Scott).

## Key facts
- Branch: `claude/hopeful-einstein-C78CE` (co-occurrence window; base `main`, post #1/#3/#4/#7/#8/#9)
- Spec (contract): Drive `BUILD_SPEC_RecurrenceDetection_v0_2026-05-30.md`
- Quick check: `make check` · `make test` · `python recurrence.py --self-test`
- Source of truth: **`AGENTS.md`** (rules + firewall); `CLAUDE.md` = Claude-specific pointer.
  Engine detail (commands / architecture / counts): **`docs/agent-guides/architecture.md`**.
