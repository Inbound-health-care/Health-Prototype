# STATUS — health-prototype

_The front door. Read this first, update it last. One source of "where am I."_
Last updated: 2026-06-05

## Current state
- **Engine: 5 surfacing rules on `main`, 90 tests green, `ruff` clean.**
  `detect_recurrence` / `detect_gap` / `detect_frequency` / `detect_cooccurrence`
  (opt-in `window_days`) / `detect_cadence_change` + v1 opt-in matching (normalize /
  synonyms / fuzzy) + router/registry combined report (`--report` v0 and `--report-v1`).
  All merged — PRs #1, #3, #4, #7, #8, #9, #10, #13.
- **Back-end / workflow hardening — MERGED (PR #8).** Toolchain audit, handoff-loss
  guard (live), a drift sweep correcting STATUS + the cold-start handoff, a new
  **CI lint gate** (ruff, pinned 0.15.8) + `make check`, and the back-end hygiene
  extracted from PR #6 (CONTRIBUTING / PUBLISH_CHECKLIST / `.gitignore`).
- **Control-doc hardening — MERGED (PR #9).**
  `AGENTS.md` as the engine-agnostic **source of truth** (2026 AGENTS.md standard);
  `CLAUDE.md` slimmed to a pointer + Claude-specific notes (no content lost);
  `SECURITY_AND_TOOL_POLICY.md` (Drive doctrine + OWASP / least-privilege),
  `LOAD_TRACE_TEMPLATE.md` (+ hook wiring), `PROJECT_MAP.md`; AGENTS.md-first load
  order (`LOAD.md` + `repo-onboard`). Relies on main's existing `make check`.
  Docs-only — engine untouched. See ADR 0006.
- Repo on **`Inbound-health-care/health-prototype`** (org on Team).
  **Branch protection ACTIVE** on `main` (4 `test` checks + up-to-date +
  conversation resolution + linear history + no-bypass; required approvals 0).
  **FOLLOW-UP for Scott:** the `lint` CI check is not yet a *required* check —
  add it to branch protection (GitHub Settings → Branches) to gate merges on it.

- **Co-occurrence window — MERGED (PR #10, `claude/cooccurrence-window`).**
  Opt-in `window_days` on `detect_cooccurrence` (default 0 = exact same-date, v0
  unchanged); greedy one-to-one date pairing (no double-count); cites matched
  pairs + gaps; adds `--demo-cooccurrence-window`. Engine extension — rule count
  stays 4. (A parallel anchor-date take, PR #12, was closed as a duplicate.)
- **Cadence change — rule #5 — MERGED (PR #13).** CI green; **CONFIRMED_USER_SIDE**
  (Scott ran it on Windows / Py 3.12.10 — 6 scenarios + 87 tests + a hand-made record).
  `detect_cadence_change`: an item whose inter-event spacing shifted by `ratio`
  across a single change point. Pivot located with **Pettitt's rank statistic**
  (web-checked; the standard non-ML, stdlib method), flagged on the median
  before/after ratio. Dedicated `CADENCE_CHANGE_RECORDS` oracle (no key ripple);
  R016 surfaces it naturally in `--report`. Adds `--demo-cadence-change`. See ADR 0007.
- **Session 2026-06-05 — MERGED #15/#16/#17/#18 (engine logic unchanged; `main` green, 90 tests):**
  polish (`--version` / `VERSION = "0.5.0"` / `tests/test_cli.py`); repo lean-out (deep-history
  docs → Drive `health-prototype/archive`); free-text extraction **design kickoff** (ADR 0008,
  RESEARCH_ONLY); firewall **legal grounding** (ADR 0009 — HIPAA Safe Harbor + FDA Non-Device CDS).

## Open loops
- [x] All 4 rules + v1 matching + combined report merged to `main`.
- [x] `docs/adr/` running log (0001 tool-call, 0002 report arch, 0003 co-occurrence,
      0004 `--report-v1`, 0005 doc/harness reconciliation, 0006 AGENTS.md source-of-truth,
      **0007 cadence-change rule**).
- [x] Doc/harness stack salvaged off `spec-jm3Ck` and merged to `main` via PR #7.
- [x] Stale branches retired: only `main` + active working branches remain on origin.
- [x] **PR #6 resolved**: back-end bits (`CONTRIBUTING.md`, `docs/PUBLISH_CHECKLIST.md`,
      `make check`, `.gitignore` hygiene) brought into PR #8; **PR #6 closed**, **PR #5 closed**.
- [x] **Control-doc hardening (PR #9) — MERGED**: AGENTS.md source of truth + slim
      CLAUDE.md + SECURITY_AND_TOOL_POLICY + LOAD_TRACE + PROJECT_MAP + ADR 0006.
- [x] **Co-occurrence window (PR #10) — MERGED**: opt-in `window_days` on rule #4
      (greedy one-to-one). Duplicate anchor-date take (PR #12) closed.
- [x] **Cadence change — rule #5 (PR #13) — MERGED**: Pettitt pivot + median-ratio
      (ADR 0007); dedicated oracle; 87 tests, CI green, **CONFIRMED_USER_SIDE**
      (Scott ran it on Windows).
- [x] **Polish — MERGED (PR #15).** The engine
      bit deferred from PR #6: `VERSION = "0.5.0"` (bumped from the spec's 0.4.0 — 5 rules
      now), a `--version` flag printing `Health-Prototype recurrence engine 0.5.0`, and
      `tests/test_cli.py` (3 in-process CLI tests). CONFIRMED_ASSISTANT_SIDE: `make check`
      green — 90 tests, self-test OK, ruff clean. Awaiting CONFIRMED_USER_SIDE.
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
- [x] **Repo lean-out — MERGED (PR #16)**: the 3 per-session handoffs + the full session log
      moved off-repo to Drive (`health-prototype/archive`); references repointed (LOAD /
      PROJECT_MAP / COLD_START / repo-onboard skill). Front door de-staled (COLD_START
      → 5 rules / 90 tests; PROJECT_MAP ADRs → 0001–0007; JOURNAL `(latest)` tag dropped).
      Docs-only; `make check` green.
- [ ] **Free-text extraction — design kickoff MERGED (PR #17), RESEARCH_ONLY**: ADR 0008 +
      Drive `health-prototype/freetext-design` (DESIGN / ORACLE / RESEARCH). No engine
      code. **OPEN for Scott:** negation/context stance (A strict-literal vs B cue-tagged)
      + approve the first-slice scope before any build.
- [x] **Firewall legal grounding — MERGED (PR #18) (RESEARCH_ONLY legal cites):** ADR 0009 +
      `SECURITY_AND_TOOL_POLICY.md` §C.1 + Drive
      `health-prototype/freetext-design/FIREWALL_legal_grounding.md`. Maps the firewall to
      HIPAA Safe Harbor (45 CFR §164.514 — allowlist gazetteer; dates via consistent shift)
      + FDA Non-Device CDS (§520(o)(1)(E) — surface/cite, no recommendations). Not legal
      advice; re-confirm vs primary HHS/FDA + counsel before any real-PHI use. Docs-only;
      `make check` green.

## Next step — decided order (engine code phase)
Both planned engine increments are MERGED to `main`:
1. ~~**Co-occurrence within a window**~~ — DONE, MERGED (PR #10).
2. ~~**Cadence change** (rule #5)~~ — DONE, MERGED (PR #13, Pettitt pivot + median-ratio).
3. **Polish / lean-out / free-text kickoff / firewall grounding** — all MERGED (#15–#18).
   **NEXT = free-text extraction, slice 1** (deterministic allowlist gazetteer + explicit-date
   regex + char-offset provenance → canonical records → existing 5 rules; design/oracle in Drive
   `health-prototype/freetext-design`, grounded by ADR 0009). **Gated on Scott (2 decisions):**
   (a) negation stance — A strict-literal vs B cue-tagged; (b) date posture — de-identified/shifted
   vs identified treatment-use. Both written up; pick to start the build.

## Key facts
- Branch: `main` is current (5 rules, 90 tests; post #1/#3/#4/#7/#8/#9/#10/#13/#15/#16/#17/#18).
  Per-session history + the free-text/firewall design live in Drive `health-prototype/`
  (`archive` + `freetext-design`).
- Spec (contract): Drive `BUILD_SPEC_RecurrenceDetection_v0_2026-05-30.md`
- Quick check: `make check` · `make test` · `python recurrence.py --self-test`
- Source of truth: **`AGENTS.md`** (rules + firewall); `CLAUDE.md` = Claude-specific pointer.
  Engine detail (commands / architecture / counts): **`docs/agent-guides/architecture.md`**.
