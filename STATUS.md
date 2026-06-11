# STATUS — health-prototype

_The front door. Read this first, update it last. One source of "where am I."_
Last updated: 2026-06-11

## Current state
- **Session 2026-06-11 (cont.) — ADR 0029 STAGE 1 MERGED: governance audit trail + deterministic monitor (`audit.py`, ADR 0030) → `main` `9e61c2e` (squash PR #47, 2026-06-11); clinical modules untouched.**
  Scott approved the plan ("next phase"); ran the new-phase discipline in order: (1) standards research
  (`docs/RESEARCH_2026-06-11_audit-trail-standards.md` — RFC 6962 chain construction, SHA-256 still the default,
  RFC 8785 canonical JSON via stdlib with floats rejected, 45 CFR 164.312(b) / ASTM E2147-18 / FHIR AuditEvent as
  concept references only, OWASP digests+counts-only logging, single-writer JSONL); (2) hand-written oracle FIRST in
  its own commit (`AUDIT_ANSWER_KEY` tallied by hand from `REPORT_ANSWER_KEY` + the FREETEXT multi oracles); (3) the
  build: `audit.py` 0.1.0 — append-only SHA-256 hash-chained event log via pass-through wrappers (`audited_extract`
  / `audited_extract_multi` / `audited_report`; results byte-identical to un-audited calls), digests + per-lens
  counts ONLY (the suite's own no-identifier test caught raw record ids in the event entity mid-build — extracted
  ids ARE patient keys — fixed to per-id digests before landing), optional JSONL persistence (fsync, resume-and-
  continue), `summarize`/`compare` monitor (counts + signed differences, banned-words-clean), honest limits pinned
  AS TESTS (tail truncation passes `verify`, is caught only by the external `head()` anchor; HMAC rejected — zero-
  secret repo). Wired: `make compile`/`selftest`/`proptest` + the CI proptest step. Verified: `make check` green —
  **317 tests** (+50; 7 expected skips), self-tests 6+10+**8**, ruff; `CI=1 make proptest` **12/12** (4 new chain
  properties); `make scan-sensitive` OK; **five clinical modules byte-identical to `origin/main`** (diff empty).
  ADR 0030 CONFIRMED_ASSISTANT_SIDE → CONFIRMED_USER_SIDE when Scott runs `python audit.py --demo` on his device.
  Docs reconciled: ADR index → 0030, ADR 0029 stage pointer, PROJECT_MAP (module + research rows), architecture.md
  (23 files / 317 tests / audit.py map), COLD_START counts. **MERGED via PR #47** (Scott, squash `9e61c2e`,
  2026-06-11); the plan had merged separately as PR #46 (squash `66569fb`). **NEXT:** Stage 2 — deterministic
  temporal-relation surfacing (before/after/same-day/within-window) in `recurrence.py` per ADR 0029.
- **Session 2026-06-11 (cont.) — MoE "six experts" doc fact-checked + staged-rollout PLAN (ADR 0029, RESEARCH_ONLY); docs-only, no engine code.**
  Ran the full pass on the pasted Mixture-of-Experts → three-engines document (the item PARKED since 2026-06-07). Three parallel
  subagents web-verified every named system + metric: **real** — SparseDoctor (arXiv 2509.14269), CLINES (medRxiv 2025.12.01),
  the drift-monitor paper (Future Internet 18(3):156, 21 users / 40.6% MAE check out); **corrected** — MedLingo (project page, no
  paper → cite Med-MoE), "sparse MoE outperforms dense on clinical tasks" (conflates active-compute with param count, unsourced),
  "AMA *requires* audits" (guidance, not a mandate → *recommends*); **fabricated** — the "TRIAGE" framework and the follow-up
  extractor's 0.997/0.986 Pair F1 + 0.00-day MAE. Recorded in `docs/RESEARCH_2026-06-11_moe-clinical-rollout.md` (RESEARCH_ONLY +
  fabrication ledger). **Operator decisions:** hold librarian + local-only + zero-PHI; relax no-deps to optional/graceful-skip only;
  Stage 3 stays deterministic (no ML model); risk-scoring expert (1B/TRIAGE) **cut**. **ADR 0029** records the three-stage
  deterministic, librarian-safe rollout: **(1)** governance audit trail (hash-chained) + deterministic rule-firing/input-stats
  monitor — extends ADR 0028; **(2)** temporal-relation surfacing in `recurrence.py`; **(3)** deterministic (action,date) follow-up
  + NegEx-style assertion context in `extract.py` (UMLS normalization deferred). Indexes reconciled (ADR README, PROJECT_MAP
  0001–0029 + the research doc). DONE: plan **MERGED via PR #46** (Scott, squash `66569fb`, 2026-06-11); Stage 1 built
  behind ADR 0030 (entry above). testing-kits untouched (read-only).
- **Session 2026-06-11 — MERGED PR #44, clinical framework baseline (ADR 0028) → `main` `0f2c895` (squash, 2026-06-11); no clinical-module changes.**
  Branch `codex/clinical-framework-baseline` adds the cross-repo governance layer adapted for this public health
  prototype: public `SECURITY.md`, append-only `docs/LEARNINGS.md`, expanded PR evidence template, exact
  Ruff/Hypothesis manifest, immutable Action SHAs, read-only workflow permissions, weekly Dependabot, dependency
  review, and a stdlib staged/PR sensitive-change scanner with redacted findings. Exact synthetic sentinels are
  limited to `tests/` and `data/`; the gate explicitly does not claim HIPAA de-identification. Verification on the
  branch: **267 tests / 6 expected skips without site packages**, both self-tests (6+10), Ruff, all 8 Hypothesis
  properties, scanner self-test + staged scan, and four generated HTML demos; PR checks green (test 3.10–3.13,
  lint, HTML, sensitive scan, dependency review). The first dependency-review run correctly exposed that the repo
  dependency graph was disabled; vulnerability alerts/dependency graph were enabled and the rerun passed. Repository
  settings now verified: secret scanning **enabled**, push protection **enabled**, CodeQL default setup **configured**
  for `actions` + `python`, default query suite; initial CodeQL setup run passed. SHA comparison confirms
  `recurrence.py`, `extract.py`, `view_html.py`, `report_html.py`, and `digest_html.py` are unchanged from `main`.
  PR #44 has since MERGED to `main` (`0f2c895`, squash, 2026-06-11). (Superseded as the live next step by the
  2026-06-11 (cont.) entry above.)
- **Session 2026-06-10 — GitHub audit + STATUS reconcile (this PR); PR #42 (AI-assisted PR template) merged.**
  Since 2026-06-07: Scott merged **PR #41** (squash `721f216`); a separate pass via an external AI tool (working from
  an uploaded "AI coding assistant error report") added **`.github/pull_request_template.md`** — an AI-assistance /
  risk / verification checklist — on `governance/ai-pr-checklist`, **merged as PR #42** (2026-06-10, `main` `e0a4d4f`).
  CI green on both merges. Audit findings: **zero open PRs**; STATUS/PROJECT_MAP + the engine-facts docs
  (`architecture.md`, `COLD_START_HANDOFF.md`) stale (252→**253** tests / 18→19 test files / 5→6 skips; the latter two
  also drifted from main as the known squash-carries-draft-wording pattern, same as #38/#40) → this reconcile; a
  sync-merge `05411a1` pushed to `claude/serene-brahmagupta-S4Tjp`
  post-#41 had resurrected pre-merge doc content on the branch tip (no unique work; de-regressed here by restoring
  `main`'s versions of the 5 affected files). Branch cleanup per Scott's 2026-06-10 call: `governance/ai-pr-checklist`
  (#42), `claude/fervent-brown-JEwJA` (ADR 0021–0023 content verified on `main`), `coderabbitai/utg/379a87a` (PR #2
  closed unmerged 2026-05-30; generated tests discarded — Scott's call) deleted; `claude/serene-brahmagupta-S4Tjp`
  retires after this PR merges. (Deletion attempted from the session: blocked 403 — the push allowlist covers only the
  session branch — so the deletes are Scott's, in the UI.) STILL OPEN (Scott, UI): add the CI `html` job to
  branch-protection required checks (#39).
- **Session 2026-06-07 (cont.) — Rule-layer metamorphic property tests (ADR 0027) + AI-verification research fold-in — MERGED to `main` via PR #41 (Scott, squash `721f216`, 2026-06-07).**
  Audited three Gemini "deep research" docs via `AGENT_AUDIT_METHOD` (5-then-4 parallel subagents). Honest finding: this engine is deterministic/pure-stdlib/no-LLM, so most of the
  corpus is **inapplicable** (LLM-judge bias, agentic eval, quantization diff-testing, contamination, OTel) or merely **corroborates** existing practice; the one transferable technique is
  **metamorphic/property testing**, on a real gap (only the multi-patient EXTRACTOR had Hypothesis props; the 5 rules were oracle-pinned only). Added **4 properties at the RULE layer** — P1
  record-isolation (no-bleed), P2 reordering-invariance, P3 shift-invariance, P4 span-integrity — in new `tests/test_rule_properties.py` + extended `test_extract_multi_properties.py`, wired
  into `make proptest` + the CI proptest step (derandomized under `CI`). **`make proptest` 8/8 green (`CI=1`); `make check` green — 253 tests** (6 dev-only skips), self-test 6+10, ruff;
  **engine UNCHANGED** (`git diff` = tests + Makefile + ci.yml only). **CONFIRMED_ASSISTANT_SIDE** → CONFIRMED_USER_SIDE when Scott runs `make proptest`. Decision recorded in **ADR 0027**
  (real Confirmation = the new tests; graduates the research per the research gate). Recorded RESEARCH_ONLY: `docs/RESEARCH_2026-06-07_ai-verification.md` (corroborated findings + **bear case** +
  **fabrication ledger**), the **fabrication-terrain lesson** in `AGENT_AUDIT_METHOD.md`, and a 2026-06-07 corroboration block in `COUNSEL_VERIFICATION_CHECKLIST.md` (counsel gate unchanged).
  Docs reconciled: ADR 0027 + README index (→0027), PROJECT_MAP (ADR range 0001–0027 + research note + property module). **A pasted MoE "six experts" doc is PARKED (Scott's call — full run later);**
  as described it would break pure-stdlib/determinism/non-interpretation — the one portable idea is the property tests above.
- **Session 2026-06-07 (cont.) — CI HTML-validity gate + accessible view refactor — MERGED to `main` via PR #39 (squash; ADR 0026); `main` now `63748e6`.**
  A prior session added `anishathalye/proof-html` to CI but it ran on **0 files** (the views are generated on demand + gitignored) — a vacuous
  green. Confirmed it was in NO live location (not on `main`/#38, no open PR, no branch); this is a fresh wiring. A dedicated CI **`html` job**
  generates the four views into `_site/` via a new **`make html-demos`** target, then runs **proof-html@v2** offline (`disable_external`,
  favicon/opengraph off, `check_html` on) — real coverage = markup well-formedness + internal `#anchor`/id integrity (external/image/alt are moot;
  views are self-contained). CI↔Makefile parity preserved (the four-file list lives once in the Makefile, PR #29). **The gate immediately did its
  job:** the first CI run caught **4 real HTML5-conformance errors** from ADR 0022's `role=button` design (`<li role=button>` in a list; the digest
  card's `role=button` nesting an interactive `<details>`). Fixed with researched accessible patterns — findings are now real **`<button>`s** (native
  focus/keyboard, no tabindex/role/keydown shim); the digest card uses the **block-link/pseudo-content** pattern (card not a button; inner-button
  `::after` overlay; `<details>` raised via `z-index`). `uvx html5validator` (Nu) now reports the views **HTML-clean**; `make check` green; view modules
  bumped (view_html 0.4.0, report_html/digest_html 0.5.0); **ADR 0022 revised by ADR 0026**. Docs reconciled: ADR 0026 + README index (0024–0026),
  PROJECT_MAP (ADR range + ci.yml purpose + Makefile target), architecture.md CI line. **Not auto-required** — Scott adds `html` to branch protection
  to make it block. CI all green incl. the `html` gate (CONFIRMED_ASSISTANT_SIDE); **interaction CONFIRMED_USER_SIDE** — Scott ran the live JS/DOM test
  (`tests.test_view_js`, real headless Chromium, Windows, 2026-06-07) — 4/4 ok (also closes the ADR 0025 live-JS follow-up). **MERGED via PR #39** (Scott, squash, 2026-06-07); branch retire-able post-merge.
- **Session 2026-06-07 (cont.) — AUDIT FIX-LIST — MERGED to `main` via PR #37 (squash; ADR 0024–0025); `main` now 252 tests.**
  Worked all 15 items in `docs/AUDIT_2026-06-07.md` (Scott approved the plan + four decision-forks). **Tier 1 (governance):**
  JOURNAL.md **retired (chat-only)** — frozen with an ARCHIVED banner, the 5 docs that cited it as canonical reworded to
  "historical archive"; **LICENSE = Apache-2.0** added (patent grant, health-adjacent) + README license note; **ADR 0024**.
  **Tier 2 (verification ceiling):** new **dev-only live JS/DOM test** `tests/test_view_js.py` (Playwright headless Chromium —
  click-highlight, keyboard Enter/Space, beforeprint/afterprint, runtime multi-patient no-bleed) + `make jstest`, NOT in CI,
  skips cleanly without a browser; **Hypothesis properties now GATE CI** (installed in the workflow, run **derandomized** under
  `CI=true` so failures reproduce) — the prior 1-skip is gone; oracle-independence convention documented; **ADR 0025**.
  **Tier 3 (doc drift):** architecture.md (18 files / 252 tests, all 3 view modules), PROJECT_MAP (ADRs 0001–0025, +4 modules),
  ADR 0014/0015 "revised by 0017" pointers, ADR 0016/0019 promoted to CONFIRMED_USER_SIDE (0013 left — STATUS doesn't confirm it),
  COLD_START counts, STATUS "5 modules". **Tier 4 (nits):** cadence-floor docstring, recurrence.py header → 0.5.0, **`BANNED` hoisted
  to one `tests/banned_words.py`** (39-word union; all 9 copies now import it), `.gitignore` += `.coverage`/`htmlcov/`/`.hypothesis/`.
  `make check` green — **252 tests** (5 dev-only skips: Hypothesis + live-JS), self-test 6+10, `ruff` clean; `make proptest` 3/3 green
  (incl. `CI=true`). **JS test could not be run here** (sandbox blocks the Chromium binary download) — structurally sound + skips clean,
  CONFIRMED only when Scott runs `make jstest` locally. **Per-module versions unchanged.** MERGED via PR #37 (Scott, squash, 2026-06-07);
  branch `claude/repo-settings-load-Mpe4x` deleted post-merge. Open follow-up: Scott runs `make jstest` with a real browser for the live-JS CONFIRMED_USER_SIDE.
- **Session 2026-06-07 — MERGED PR #35 to `main` — UI build-out (ADR 0021–0023); `main` now 248 tests. CONFIRMED_USER_SIDE.**
  Three sequenced increments on `claude/fervent-brown-JEwJA`, each its own ADR + commit, web-research-led (Scott picked all three):
  (a) **`view_html.py` shared floor + `report_html` multi-patient parity (ADR 0021)** — promoted the theme / span helpers /
  click-to-highlight / multi-patient chrome out of the two views into a new dependency floor (resolves the circular-import wall
  ADR 0015/0017 pre-flagged; `THEME` re-exported from `report_html` for back-compat); `report_html` gains `render_html_multi` +
  `--demo-multi` in the findings-list idiom (no cross-patient bleed). (b) **Keyboard nav + print (ADR 0022)** — one
  `bindFindings`/`activate` path for mouse + keyboard (Enter/Space, `role=button` / `aria-pressed` / `:focus-visible`); custom
  role=button because the digest card nests `<details>` (WHATWG §4.10.6); `_PRINT_CSS` (single column, chrome hidden, grayscale-
  legible marks, `break-inside`, `@page A4`) + a `beforeprint` handler that opens `<details>` for printing (CSS can't — W3C #2084).
  (c) **At-a-glance cited-date timeline (ADR 0023)** — one neutral lane per surfaced finding, ticks = cited dates on the record's
  OWN axis; ticks only (no trend line / per-lens colour / density), document order; `.timeline` aria-hidden decorative (the cards
  are the text alternative); per-patient axis in the multi views (no bleed). `make check` green — **248 tests** (+27), self-test
  6+10, `ruff`; PR #35 CI green (lint + test 3.10–3.13). Per-module versions: `view_html` 0.3.0 (new), `report_html` 0.4.0,
  `digest_html` 0.4.0. **CONFIRMED_USER_SIDE** (Scott verified the four views on his device, 2026-06-07). Deferred: un-nest the
  digest disclosure from the toggle; optional timeline lane de-dup; note-left report-multi layout.
- **Session 2026-06-06 (cont.) — MERGED PR #32 to `main` — multi-patient digest RENDERING (ADR 0020); `main` now 221 tests.**
  Realizes STATUS step 11c, rendering the batch output of `extract_records_multi` (ADR 0016) in the clinician digest. Layout was research-led: a 2024–2026 web sweep (RESEARCH_ONLY) on clinician chart-review needs — documentation burden is the #1 pain (worst in behavioral health), clinicians want **scannable/less-is-more**, **citation/provenance is the trust lever** (our thesis, externally confirmed), and cognitive-load research says **minimize navigation, single-screen at-a-glance + drill-down**. So: **stacked per-patient blocks** (segment order, never reordered) + a compact **patient jump-index** (anchor links, no JS state) + a neutral **quarantine section** for refused segments (engine reason codes, never merged/guessed). **No cross-patient highlight bleed** — each block renders its OWN segment (spans rebased segment-local) AND `_MULTI_JS` scopes findings↔marks per `.patient` block. New `python digest_html.py --demo-multi`; `digest_html` VERSION 0.2.0; engine + shared helpers untouched; banned-words-clean. `report_html` (inspection) stays single-note (later follow-up). `make check` green — **221 tests** (+7), self-test 6+10, `ruff` (local + CI-pinned 0.15.16); PR #32 CI green. **CONFIRMED_USER_SIDE** (Scott confirmed on his phone, 2026-06-06).
- **Session 2026-06-06 (cont.) — MERGED PR #31 to `main` — view review refinements (ADR 0019) + CI ruff pin 0.15.16 + 2026 standards re-verify; `main` 214 tests.** ADR 0019 **CONFIRMED_USER_SIDE** (Scott confirmed the toggle placement, citation collapse, wording, and view names on his phone, 2026-06-06). Same PR bumped the CI `ruff` pin 0.15.8 → 0.15.16 (CI-verified green) and recorded a dated standards re-verify (WCAG 2.2 AA kept / APCA not adopted, ADR 0017; OWASP Top 10 for Agentic Applications 2026 cross-ref, SECURITY §B).
- **Session 2026-06-06 (cont.) — MERGED PR #30 to `main` — calm theme (ADR 0017) + Android responsive (ADR 0018); `main` now 213 tests.**
  Scott's direction: calm, easy on the eyes, **NOT "poppin".** Web-researched (eye comfort, healthcare/BH palettes, WCAG 2.2; Android devices).
  Both views (`report_html.py` + `digest_html.py`) share ONE theme via CSS design tokens (`THEME` in `report_html`):
  **aubergine + orchid** (deep purple, matched to a reference image Scott supplied), **light-first + optional dark toggle**, a **single NON-semantic accent**
  (same for every lens — no severity/type colour; librarian rule holds). **WCAG-AA contrast enforced by test** (`tests/test_view_theme.py`, computes luminance from `THEME`, light + dark).
  **Android responsive (ADR 0018):** shared `_THEME_MEDIA_CSS` (appended last) stacks the two columns below **640 px** (primary width **360 px** — Samsung A/S, Galaxy S25 = 360×780 CSS); foldable-unfolded/desktop keep two columns; CSS-only, no deps.
  `make check` green — **213 tests** (+5 theme, +1 responsive), self-test 6+10, `ruff`. Engine untouched. **CONFIRMED_USER_SIDE** — Scott confirmed the theme + responsive on his Samsung (light + dark).
  Revises the "grayscale-only" half of ADR 0014/0015; their "no colour by type/severity" rule stands. **NEXT in-phase: multi-patient digest RENDERING** (deferred pick).
- **Session 2026-06-06 — MERGED #28 (multi-patient fail-closed extractor, ADR 0016) to `main`; `main` now 207 tests, VERSION 0.4.0.**
  - **#28 — multi-patient fail-closed extractor (ADR 0016):** `extract.extract_records_multi` splits a
    multi-patient batch on an EXPLICIT delimiter and accepts a segment only when identity is unambiguous;
    missing/ambiguous/duplicate keys are QUARANTINED (never merged or guessed), per-patient date-shift with a
    fail-closed `require_shift`, whole-note `provenance` on every record. "No-bleed" tested by hand oracle +
    **Hypothesis** (dev-only, `make proptest`). Synthetic data only; real-PHI counsel/Expert-Determination gate
    unchanged. **CONFIRMED_USER_SIDE** (Scott ran `python extract.py --demo-multi` on his laptop, 2026-06-06).
    `make check` green — **207 tests** (+3 Hypothesis properties), self-test 6+10, `ruff`.
  - **Already on `main` this session:** #27 clinician Pre-visit Pattern Digest (ADR 0015, `digest_html.py`)
    + #29 review hardening (CI↔Makefile parity via `make compile`; README pipeline diagram + non-goals; honest
    compliance wording; `docs/DEMO_OUTPUT.md`) + #26 relative-date anchoring (ADR 0013) + counsel checklist +
    `report_html.py` inspection view (ADR 0014). `main` carries both HTML views.
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
  **RESOLVED (Scott, 2026-06-06):** `lint` + the `test (3.x)` checks are now *required*
  checks in branch protection (Settings → Branches) — the prior follow-up is closed.

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
- **Relative-date anchoring — MERGED (PR #26; ADR 0013) to `main`.**
  Opt-in (`resolve_relative`, default off → strict slices byte-for-byte), conservative: resolves only
  explicitly-anchored relatives ("3 weeks ago", "since <date>") against the line/`reference_date`; partial
  ("March 2026") and frequency ("q2wk") are surfaced **cited but undated**; an anchorless relative is left
  **unresolved**, never guessed. Additive provenance fields only — `recurrence.py` + its 90 tests untouched.
  (159 tests at merge; 221 on `main` now.) On `main`.
- **Counsel-verification checklist — NEW doc on the same branch (resolves ADR 0011's "counsel-verify" loop; RESEARCH_ONLY).**
  `docs/COUNSEL_VERIFICATION_CHECKLIST.md`: the ordered counsel path (two tracks; Expert Determination; FDA
  non-device memo; Q-Sub/513(g); pilot gate), the verified **FDA Jan-2026** findings (twice-refreshed; March =
  Town Hall; criterion 3→4), the HIPAA **date-shift = Expert Determination, NOT Safe Harbor** distinction, the
  BH-roadmap read, and a **deferred** list of ADR 0009 fixes (not applied until counsel — Scott's call).
- **UI slice 1 — self-contained HTML report (ADR 0014) — MERGED (PR #26) to `main`.**
  `report_html.py` (pure stdlib, no deps, no network): the source note with cited spans highlighted
  (item `source_span` + relative-date `date_span`) beside the `run_report` findings; click a finding →
  highlight its cited source. Grayscale-only, document order, banned-words-clean — the librarian rule
  holds in the view. `python report_html.py --demo`. The clinician-facing **pre-visit digest** is
  mocked in **Figma** (design-first; grayscale, 5 lenses + cited-source panel):
  https://www.figma.com/design/BcT7yhsMHAZl2AeJD9fAAK

## Open loops
- [x] **CI HTML-validity gate + accessible view refactor (ADR 0026) — MERGED via PR #39 (squash, 2026-06-07).**
      Dedicated CI `html` job: `make html-demos` → 4 self-contained views into `_site/` → `proof-html@v2` offline (`disable_external`,
      favicon/opengraph off, `check_html` on); replaces the prior vacuous "Ran on 0 files" run. The gate (full W3C/Nu `check_html`) caught
      4 real HTML5-conformance errors from ADR 0022's `role=button` design; fixed with real `<button>` findings + the block-link/pseudo-content
      card (ADR 0022 revised by 0026). CONFIRMED_USER_SIDE (Scott ran the live JS test, real Chromium, 4/4 ok). **Residual (optional):** Scott
      adds the `html` check to branch-protection required checks if he wants it to *block* merges (it reports but doesn't gate yet).
- [x] **Repo-wide audit (2026-06-07) — fix-list `docs/AUDIT_2026-06-07.md` — ALL 15 ITEMS DONE, MERGED via PR #37
      (squash; ADR 0024–0025). Open after merge: Scott runs `make jstest` with a real browser for live-JS CONFIRMED_USER_SIDE.**
      Tier 1: JOURNAL retired chat-only (frozen) + 5 docs reworded; LICENSE Apache-2.0 [Scott picked]. Tier 2:
      dev-only live JS test (`make jstest`, not CI) + Hypothesis gates CI (derandomized) [Scott picked] + oracle
      convention documented. Tier 3: architecture/PROJECT_MAP/COLD_START counts + module lists reconciled
      (18/252, ADRs 0001–0025), ADR 0014/0015 revised-by-0017 pointers, ADR 0016/0019 → CONFIRMED_USER_SIDE
      (0013 left — STATUS doesn't confirm it). Tier 4: cadence-floor docstring, recurrence.py header → 0.5.0,
      `BANNED` hoisted to `tests/banned_words.py`, `.gitignore` += coverage/hypothesis. The ENGINE CODE +
      COMPLIANCE HEDGING audited CLEAN — not re-litigated. **Open after merge:** Scott runs `make jstest` with a
      real browser for the live-JS CONFIRMED_USER_SIDE (sandbox blocked the Chromium download this session).
- [x] All 4 rules + v1 matching + combined report merged to `main`.
- [x] `docs/adr/` running log (0001 tool-call, 0002 report arch, 0003 co-occurrence,
      0004 `--report-v1`, 0005 doc/harness reconciliation, 0006 AGENTS.md source-of-truth,
      **0007 cadence-change rule**, 0008 free-text kickoff, 0009 legal grounding, 0010 rename,
      0011 compliance/market audit, 0012 matching modes, 0013 relative-date anchoring, 0014 HTML report view,
      0015 pre-visit digest, 0016 multi-patient extractor, 0017 calm theme, 0018 responsive,
      0019 view refinements, **0020 multi-patient digest rendering**).
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
      `make check` green at that milestone (117 tests; 221 on `main` now).
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
      **(2026-06-07, branch `claude/serene-brahmagupta-S4Tjp`):** a fresh audit of three AI deep-research docs
      (`docs/RESEARCH_2026-06-07_ai-verification.md`) re-confirmed the FDA Jan-2026 CDS + HIPAA Expert-Determination
      findings (corroboration added to the counsel checklist) and recorded the **bear case** — verification absorbed as a
      feature (Snowflake/TruEra; Abridge built citing in-house), FDA leniency weakening the forcing function,
      pay-for-friction resistance — as the steelman against this thesis, plus a **fabrication ledger**. Counsel-verify
      gate unchanged; BH-roadmap decision still Scott's.
- [x] **Relative-date anchoring (ADR 0013) — MERGED (PR #26).** Opt-in, conservative; default off ==
      strict byte-for-byte; resolves explicitly-anchored relatives, surfaces partial/frequency/unresolved
      cited-but-undated; engine + 90 tests untouched. On `main`.
- [x] **UI slice 1 — HTML report view (ADR 0014) — MERGED (PR #26).** `report_html.py`: dependency-free
      single-file HTML (cited spans ↔ surfaced patterns, click-to-highlight); grayscale / document-order /
      banned-words-clean (librarian rule in the view). On `main`.
- [x] **UI slice 2 — clinician Pre-visit Pattern Digest (ADR 0015) — MERGED (PR #27).**
      `digest_html.py`: the product view from the (approved) Figma mock — five lenses as cited cards beside the
      source note, click-to-highlight, all from real `run_report` output; dependency-free, grayscale, banned-words-clean.
      One synthetic patient surfaces all five lenses. On `main` (177 tests).
- [x] **Review hardening — MERGED (PR #29) (docs/CI/wording only).** CI↔Makefile parity (`make compile` =
      the one canonical file list; CI delegates to make → byte-compiles all 5 modules + runs BOTH self-tests,
      so it can't drift again); README pipeline diagram + non-goals ("what this deliberately does not do");
      honest/softened compliance wording (README, docstrings, SECURITY §C.1); new `docs/DEMO_OUTPUT.md`
      (captured stdout). The `--demo-multi` snapshot in DEMO_OUTPUT stays deferred until #28 lands. On `main`.
- [x] **Multi-patient extractor — slice (ADR 0016) — MERGED (PR #28) to `main`, CONFIRMED_USER_SIDE** (Scott ran
      `extract.py --demo-multi` on his laptop, 2026-06-06).
      `extract.extract_records_multi`: fail-closed identity — explicit operator delimiter; quarantine (never
      merge/guess) on missing/ambiguous/duplicate key or missing per-patient shift; spans rebased to whole-note
      offsets; engine + single-note `extract_records` untouched. +Hypothesis property tests (skip if absent;
      `make proptest`). Brought `main` to 207 tests at merge (221 now). **Now rendered in the digest — ADR 0020 (PR #32).**
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
6. ~~**Relative-date anchoring**~~ — DONE (ADR 0013; **MERGED PR #26** to `main`): opt-in, conservative,
   default-off byte-for-byte; explicitly-anchored relatives resolve, partial/frequency/unresolved surfaced
   cited-but-undated.
7. ~~**UI slice 1 — HTML report view**~~ — DONE (ADR 0014; **MERGED PR #26**): dependency-free self-contained
   HTML making provenance visible (cited spans ↔ findings); librarian rule holds in the view.
8. ~~**UI slice 2 — clinician Pre-visit Pattern Digest**~~ — DONE (ADR 0015; **MERGED PR #27**): the product
   view from the approved Figma mock — five lenses as cited cards from real `run_report` output;
   dependency-free, grayscale, banned-words-clean. `python digest_html.py --demo`.
9. ~~**Review hardening**~~ — DONE (**MERGED PR #29**; docs/CI/wording only): CI↔Makefile parity (anti-drift
   `make compile`), README pipeline diagram + non-goals, honest compliance wording, `docs/DEMO_OUTPUT.md`.
10. ~~**Multi-patient extractor (ADR 0016, PR #28)**~~ — DONE, **MERGED (squash)**, **CONFIRMED_USER_SIDE**
    (Scott ran `python extract.py --demo-multi` on his laptop, 2026-06-06). Brought `main` to **207 tests** +
    VERSION 0.4.0; the deferred `--demo-multi` snapshot is folded into `docs/DEMO_OUTPUT.md` in the same PR.
11. **UI phase (Scott, 2026-06-06): calm / eye-comfort, NOT "poppin".** ~~PR #30~~ **MERGED to `main`** — **CONFIRMED_USER_SIDE** (Scott confirmed on his Samsung, both modes).
    a. ~~Calm visual pass~~ — DONE (ADR 0017): both views share one **aubergine + orchid** theme (CSS tokens in `report_html.THEME`),
       light-first + optional dark toggle, ONE non-semantic accent, WCAG-AA contrast enforced by `tests/test_view_theme.py`. Color locked.
    b. ~~Android responsive pass~~ — DONE (ADR 0018): shared `_THEME_MEDIA_CSS` stacks the columns below **640 px** (primary **360 px**;
       Samsung A/S); foldable/desktop keep two columns; tap targets + note overflow handled. CSS-only. `make check` 213 green.
    c. ~~**multi-patient digest RENDERING**~~ — DONE (ADR 0020; **MERGED PR #32** to `main`):
       stacked per-patient blocks in segment order + patient jump-index + neutral quarantine
       section; no cross-patient highlight bleed (own-segment render + per-block-scoped JS). Layout research-led
       (clinician chart-review needs 2024–2026: scannable/less-is-more, citation-as-trust, minimize navigation).
       `python digest_html.py --demo-multi`. **CONFIRMED_USER_SIDE** (Scott, phone, 2026-06-06). `report_html` multi is a later follow-up.
    Framed by the behavioral-health pre-visit digest direction; the free-text extractor stays the regulated boundary.

## Key facts
- Branch: `main` has 5 rules + free-text slices 1–2 + relative-date anchoring (ADR 0013) + the
  `report_html.py` inspection view (ADR 0014) + the `digest_html.py` clinician digest (ADR 0015) +
  the counsel checklist + review hardening + the multi-patient fail-closed extractor (ADR 0016) +
  the calm aubergine view theme (ADR 0017) + Android responsive (ADR 0018) + view refinements (ADR 0019)
  + multi-patient digest rendering (ADR 0020) + the shared `view_html.py` floor + `report_html` multi-patient
  + keyboard/print + the at-a-glance cited-date timeline (**ADR 0021–0023**) + the audit fix-list (governance + verification
  ceiling + doc reconcile, **ADR 0024–0025**) + the CI HTML-validity gate (proof-html) + accessible view refactor (real `<button>` findings
  + block-link card, **ADR 0026**) + rule-layer metamorphic property tests + the AI-verification research
  fold-in (**ADR 0027**) + the AI-assisted PR checklist template (**#42**) + the clinical framework baseline
  (public SECURITY.md / LEARNINGS / sensitive-change scanner / hardened Actions, **ADR 0028**, #44) + the MoE
  fact-check + three-stage rollout plan (**ADR 0029**, #46) + the governance audit trail + deterministic monitor
  (`audit.py`, **ADR 0029 Stage 1 / ADR 0030**, #47) — **317 tests on `main`** (post #1–#47; 7 dev-only skips).
  Per-module versions (no single repo-wide version): `recurrence.py` 0.5.0, `extract.py` 0.4.0,
  `view_html.py` 0.4.0, `report_html.py` 0.5.0, `digest_html.py` 0.5.0, `audit.py` 0.1.0.
  Old work branches retired (#25/#28/#29/#30). Branch cleanup approved 2026-06-10 (Scott's call; he deletes in the
  UI — session push can't): `governance/ai-pr-checklist`, `claude/fervent-brown-JEwJA`, `coderabbitai/utg/379a87a`
  (PR #2, closed unmerged); `claude/serene-brahmagupta-S4Tjp` (merged via #41) once the 2026-06-10 reconcile merges.
  Per-session history + the free-text/legal-grounding design + the 2026 compliance/market audit live
  in Drive `health-prototype/` (`archive` + `freetext-design` + `audit-2026-06-05`).
- Spec (contract): Drive `BUILD_SPEC_RecurrenceDetection_v0_2026-05-30.md`
- Quick check: `make check` · `make test` · `python recurrence.py --self-test` · `python extract.py --self-test` · `python audit.py --self-test`
- Source of truth: **`AGENTS.md`** (rules + the librarian rule); `CLAUDE.md` = Claude-specific pointer.
  Engine detail (commands / architecture / counts): **`docs/agent-guides/architecture.md`**.
