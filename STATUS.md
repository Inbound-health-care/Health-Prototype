# STATUS — health-prototype

_The front door. Read this first, update it last. One source of "where am I."_
Last updated: 2026-06-05

## Current state
- **Engine: 5 surfacing rules on `main`, 144 tests green (engine 90 + free-text slice-1 27 + matching-modes 27), `ruff` clean.**
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
- **Session 2026-06-05 — MERGED #15/#16/#17/#18 (engine logic unchanged):**
  polish (`--version` / `VERSION = "0.5.0"` / `tests/test_cli.py`); repo lean-out (deep-history
  docs → Drive `health-prototype/archive`); free-text extraction **design kickoff** (ADR 0008,
  RESEARCH_ONLY); **legal grounding** (ADR 0009 — HIPAA Safe Harbor + FDA Non-Device CDS).
- **Free-text extraction — slice 1 MERGED (PR #20).** new `extract.py` front-end turns dated
  prose → the canonical record shape the 5 rules consume unchanged. **Stance A** (strict literal:
  emit every literal gazetteer hit + char-offset `source_span`, no cue logic) + **de-identified/
  shifted dates** (default 0). `recurrence.py` + its 90 engine tests untouched; suite now 117.
  ADR 0008 → IMPLEMENTED_UNVERIFIED (awaiting CONFIRMED_USER_SIDE); ADR 0009 slice-1 tests pass.
- **Terminology — "firewall" renamed (ADR 0010, PR #21 — MERGED).** The overloaded metaphor is retired
  repo-wide: the surface/don't-interpret rule is **the librarian rule**, the HIPAA PHI layer is
  **the allowlist**, and the evidence-level rule is **the research gate**. Term-only + a staleness
  sweep reconciling docs to `main` = 117; no behavior change.
- **Free-text extraction — slice 2 (matching modes) MERGED (PR #25, squash; `claude/hopeful-albattani-sYkkR`).**
  `extract.py` gains an explicit `MatchConfig`: **strict** (default == slice-1, byte-for-byte) / **synonyms** /
  **fuzzy** / **both**, with always-on merge-safety guards (affix-antonym detector + LASA denylist + drug-name
  exemption + gazetteer-anchored fuzzy). Engine + its 90 tests untouched; suite now **144** (self-test 6+7).
  **CONFIRMED_USER_SIDE** — Scott ran it on his own laptop (2026-06-05); all results came back as expected.
  ADR 0012; liability framing RESEARCH_ONLY.
- **Relative-date anchoring — IMPLEMENTED on `claude/dazzling-shannon-jPWz2` (ADR 0013; draft PR #26; NOT yet on `main`).**
  Opt-in (`resolve_relative`, default off → strict slices byte-for-byte), conservative: resolves only
  explicitly-anchored relatives ("3 weeks ago", "since <date>") against the line/`reference_date`; partial
  ("March 2026") and frequency ("q2wk") are surfaced **cited but undated**; an anchorless relative is left
  **unresolved**, never guessed. Additive provenance fields only — `recurrence.py` + its 90 tests untouched.
  `make check` green (**159 tests**, self-test 6+10, ruff). Awaiting CONFIRMED_USER_SIDE.
- **Counsel-verification checklist — NEW doc on the same branch (resolves ADR 0011's "counsel-verify" loop; RESEARCH_ONLY).**
  `docs/COUNSEL_VERIFICATION_CHECKLIST.md`: the ordered counsel path (two tracks; Expert Determination; FDA
  non-device memo; Q-Sub/513(g); pilot gate), the verified **FDA Jan-2026** findings (twice-refreshed; March =
  Town Hall; criterion 3→4), the HIPAA **date-shift = Expert Determination, NOT Safe Harbor** distinction, the
  BH-roadmap read, and a **deferred** list of ADR 0009 fixes (not applied until counsel — Scott's call).

## Open loops
- [x] All 4 rules + v1 matching + combined report merged to `main`.
- [x] `docs/adr/` running log (0001 tool-call, 0002 report arch, 0003 co-occurrence,
      0004 `--report-v1`, 0005 doc/harness reconciliation, 0006 AGENTS.md source-of-truth,
      **0007 cadence-change rule**, 0008 free-text kickoff, 0009 legal grounding, 0010 rename,
      0011 compliance/market audit, 0012 matching modes, **0013 relative-date anchoring**).
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
- [x] **Free-text extraction — design kickoff (PR #17) + slice 1 MERGED (PR #20):** `extract.py`
      + `tests/test_extract.py` (27 tests). Scott chose **Stance A (strict literal)** +
      **de-identified/shifted dates** (default 0). Front-end; `recurrence.py` + its 90 engine
      tests untouched. ADR 0008 → IMPLEMENTED_UNVERIFIED; ADR 0009 slice-1 tests pass.
      `make check` green (117 tests / self-test 6+3 / ruff clean). Awaiting CONFIRMED_USER_SIDE.
- [x] **Legal grounding — MERGED (PR #18) (RESEARCH_ONLY legal cites):** ADR 0009 +
      `SECURITY_AND_TOOL_POLICY.md` §C.1 + Drive
      `health-prototype/freetext-design/FIREWALL_legal_grounding.md`. Maps the librarian rule +
      allowlist to HIPAA Safe Harbor (45 CFR §164.514 — allowlist gazetteer; dates via consistent
      shift) + FDA Non-Device CDS (§520(o)(1)(E) — surface/cite, no recommendations). Not legal
      advice; re-confirm vs primary HHS/FDA + counsel before any real-PHI use. Docs-only;
      `make check` green.
- [x] **Terminology rename — "firewall" → librarian rule / allowlist / research gate (ADR 0010).**
      Repo-wide term sweep + staleness audit (reconciled to `main` = 117 post-#20). Term-only;
      no behavior change; `make check` green.
- [ ] **Compliance + market audit — RESEARCH_ONLY (2026-06-05).** Cited research in Drive
      `health-prototype/audit-2026-06-05/` (HIPAA/FDA mitigations, 2026 customer problems, strategy).
      Repo got **ADR 0011**: FDA refreshed the 2022 CDS guidance twice in Jan 2026 → supersedes ADR
      0009's FDA cite (the four Non-Device criteria still hold). Strategic read: the white-space is a
      verifiable, non-interpreting "librarian layer" *under* the generative incumbents; the wedge is
      **behavioral health**; the product shape is a pull-based, EHR-embedded "pre-visit pattern
      digest," every line cited. **Open for Scott:** counsel-verify the legal claims before any
      real-PHI use; decide whether the BH-digest direction reshapes the roadmap.
      **(2026-06-05, branch `claude/dazzling-shannon-jPWz2`):** the counsel-verify sub-part now has a
      written path — `docs/COUNSEL_VERIFICATION_CHECKLIST.md` (draft PR #26) — incl. deferred ADR 0009
      fixes (date-shift = Expert Determination, not Safe Harbor). BH-roadmap decision still Scott's.
- [ ] **Relative-date anchoring (ADR 0013) — IMPLEMENTED on `claude/dazzling-shannon-jPWz2` (draft PR #26).**
      Opt-in, conservative; default off == strict byte-for-byte; resolves explicitly-anchored relatives,
      surfaces partial/frequency/unresolved cited-but-undated; engine + 90 tests untouched. `make check`
      green (**159 tests**, self-test 6+10, ruff). Awaiting CONFIRMED_USER_SIDE; not yet on `main`.
- [x] **Free-text slice 2 — matching modes + merge-safety guards (ADR 0012) — MERGED (PR #25).** `extract.py`
      gained an explicit, must-be-chosen `MatchConfig`: **strict** (default = slice-1 behavior) / **synonyms** /
      **fuzzy** / **both**. Fuzzy is guarded (domain-agnostic affix-antonym detector + look-alike
      denylist + drug-name exemption) and anchored to the gazetteer; affix-antonym synonyms are refused;
      vocabulary stays domain-agnostic/minimal (callers supply their own). Merged off
      `claude/hopeful-albattani-sYkkR`; `make check` green (**144 tests**, self-test 6+7, ruff). Liability
      framing RESEARCH_ONLY. **CONFIRMED_USER_SIDE** (Scott ran it on his own laptop, 2026-06-05 — all results as expected).

## Next step — decided order (engine code phase)
Both planned engine increments are MERGED to `main`:
1. ~~**Co-occurrence within a window**~~ — DONE, MERGED (PR #10).
2. ~~**Cadence change** (rule #5)~~ — DONE, MERGED (PR #13, Pettitt pivot + median-ratio).
3. **Polish / lean-out / free-text kickoff / legal grounding** — all MERGED (#15–#18).
4. ~~**Free-text extraction, slice 1**~~ — DONE, MERGED (PR #20): Stance A (strict literal) +
   de-identified/shifted dates (default 0); `extract.py` front-end (allowlist gazetteer +
   explicit-date regex + char-offset `source_span`) → canonical records → the existing 5 rules,
   untouched. ADR 0008 → IMPLEMENTED_UNVERIFIED.
5. ~~**Free-text slice 2 — matching modes**~~ — DONE, **MERGED (PR #25; ADR 0012)**; **CONFIRMED_USER_SIDE**
   (Scott ran it on his own laptop, 2026-06-05 — all results came back as expected). Synonym/fuzzy matching
   shipped as explicit, **must-be-chosen, guarded** modes (strict/synonyms/fuzzy/both) — affix-antonym detector
   + look-alike denylist + drug-name exemption + gazetteer-anchored fuzzy; strict default == slice 1, byte-for-byte.
6. ~~**Relative-date anchoring**~~ — DONE this session (ADR 0013; branch `claude/dazzling-shannon-jPWz2`,
   draft PR #26): opt-in, conservative, default-off byte-for-byte; explicitly-anchored relatives resolve,
   partial/frequency/unresolved surfaced cited-but-undated. Awaiting CONFIRMED_USER_SIDE; not yet on `main`.
7. **NEXT pick (open — Scott's call):** multi-patient notes (specced fail-closed in ADR 0013 /
   `COUNSEL_VERIFICATION_CHECKLIST.md`), or mid-line temporal expressions / partial-date normalization —
   framed by the **behavioral-health "pre-visit pattern digest"** direction. Treat the free-text extractor
   as the regulated boundary.

## Key facts
- Branch: `main` has 5 rules + free-text slices 1–2, **144 tests** (post #1–#25). Active dev branch
  **`claude/dazzling-shannon-jPWz2`** (draft PR #26) carries: the STATUS/ADR-0012 reconcile, **relative-date
  anchoring** (ADR 0013, opt-in) and `docs/COUNSEL_VERIFICATION_CHECKLIST.md` — **159 tests**, not yet on `main`.
  `claude/hopeful-albattani-sYkkR` is merged via #25 (retire-able).
  Per-session history + the free-text/legal-grounding design + the 2026 compliance/market audit live
  in Drive `health-prototype/` (`archive` + `freetext-design` + `audit-2026-06-05`).
- Spec (contract): Drive `BUILD_SPEC_RecurrenceDetection_v0_2026-05-30.md`
- Quick check: `make check` · `make test` · `python recurrence.py --self-test` · `python extract.py --self-test`
- Source of truth: **`AGENTS.md`** (rules + the librarian rule); `CLAUDE.md` = Claude-specific pointer.
  Engine detail (commands / architecture / counts): **`docs/agent-guides/architecture.md`**.
