# SESSION HANDOFF — 2026-06-04

_Engine-agnostic. For any future AI session (or Scott) resuming this work. Read
`AGENTS.md` (source of truth) + `STATUS.md` first, then this. One long session;
this logs everything so the chat does not need re-reading._

## ORIENT IN 60 SECONDS
- **Repo:** `Inbound-health-care/Health-Prototype`. Clone: `C:\Users\losts\Health-Prototype`.
- **`main` HEAD:** `3d7c15b` — PR #9 merged. 4 rules / 68 tests on main.
- **Open PR:** **#10** (`claude/cooccurrence-window`) — co-occurrence opt-in `window_days`. Draft, green locally (74 tests), ready for review/merge.
- **Next coding task:** **Phase C — cadence-change rule #5** (full spec below).
- **Plan file:** `C:\Users\losts\.claude\plans\i-want-you-to-humming-kay.md` (Phases A/B/C).
- **First action next session:** `git fetch`; check whether #10 merged (`gh pr view 10`); read `AGENTS.md` + `STATUS.md`; verify state with `python -m unittest discover -s tests -t .` + `python recurrence.py --self-test` (NOT `make` — see gotchas).

## WHAT THIS SESSION DID (chronological)
1. **RAG research kit** (separate deliverable, NOT part of this repo) — `C:\Users\losts\OneDrive\Desktop\Rag research\`. 13 files: `00_RAG_INDEX.md`, `RAG_PROFILE.md`, `RAG_BUILD_HANDOFF_TEMPLATE.md`, `RAG_LEDGER.md`, `RAG_CLAIM_MAP_TEMPLATE.md` + `knowledge/01..08`. Engine-agnostic RAG reference (~106 vectors across 8 dimensions + 2026 additions: contextual retrieval, ColPali/visual RAG, CRAG, OWASP RAG security, RAG-vs-long-context). **DONE.** Local files only (not a git repo).
2. **Evaluated an external (ChatGPT) "agent-ops" plan**; verified premises via `gh` (Health-Prototype real; PR #6 + #5 CLOSED; PR #8 merged adding `make check` + toolchain). Found it grounded but over-scoped; scoped down to a tight first cut.
3. **PR #9 — control-doc hardening — MERGED.** Adopted **`AGENTS.md` as the engine-agnostic source of truth** (2026 Linux-Foundation standard); slimmed `CLAUDE.md` to a pointer + Claude-specific notes (no content lost); added `SECURITY_AND_TOOL_POLICY.md` (ported from Scott's Drive doctrine + 2026 OWASP/least-privilege), `LOAD_TRACE_TEMPLATE.md` (+ session_start hook wiring), `PROJECT_MAP.md`, `docs/adr/0006`; set AGENTS.md-first load order in `LOAD.md` + the `repo-onboard` skill. Rebased onto main (#8), conflicts (Makefile/STATUS) resolved, force-pushed, Scott merged.
4. **PR #10 — co-occurrence within a window — OPEN (draft).** See below.

## VERIFIED STATE
- **PR #10** (`claude/cooccurrence-window`, head `d6d1993`): 74 tests OK (68 + 6 new), self-test 6 OK, `compileall` 0. `window_days=0` byte-identical to v0 (regression guard). Firewall test passes. 4 files changed: `recurrence.py`, `tests/test_cooccurrence.py`, `docs/agent-guides/architecture.md`, `STATUS.md`. **`data/sample_records.py` deliberately untouched** (window tests use real `R020` + inline records → no answer-key ripple).
- **main:** 4 rules, 68 tests, ruff clean. PRs #1/#3/#4/#7/#8/#9 merged.

## PR #10 — what it added (co-occurrence window)
- `detect_cooccurrence(..., window_days=0)`. `0` = exact same-date (v0, unchanged). `>0` = pair two items' dates within N days via **greedy one-to-one matching** (`_match_within_window`, smallest gap first) so no occurrence is double-counted; `count` = matched pairs.
- `CooccurrenceHit` gained `window_days: int = 0` + `pairs: list[(date_a, date_b, gap_days)]` (appended after `variants_b`, defaults keep positional construction valid).
- `format_cooccurrence_hit`: window branch shows `… co-occurred N times within W days — (d_a ~ d_b: Gd), …`; v0 branch unchanged.
- New `--demo-cooccurrence-window` (7-day window) + `_run_demo_cooccurrence_window`.
- Validation: `window_days >= 0` else `ValueError`.

## NEXT — PHASE C: cadence change (new rule #5, drop-in Expert)
Web-checked method = **ISI-ratio / moving-average** (NOT FFT/ML/change-point — those break determinism + stdlib-only). Full spec:
- **`detect_cadence_change(records, field="item", min_occurrences=4, ratio=2.0, normalize=False, synonyms=None, fuzzy_cutoff=None) -> list[CadenceChangeHit]`.**
- Per item with `>= min_occurrences` dated occurrences: compute consecutive inter-event intervals (days); find a **pivot** splitting early vs late; flag a shift when `median(before)/median(after) >= ratio` (tightening) **or** `median(after)/median(before) >= ratio` (loosening); require `>=1` interval each side. Deterministic pivot tie-break.
- **`CadenceChangeHit`**: `record_id, item, before_interval, after_interval, pivot_date, dates, variants`. **`format_cadence_change_hit`**: facts only — e.g. `"insulin" interval changed from ~30d to ~7d at 2026-04-01 — <dates>`. **FIREWALL: ban "worsening/accelerating/increasing/escalating/concern/risk"** etc. (state the interval change, never its meaning). Add to the test BANNED list.
- Validate: `min_occurrences >= 2`, `ratio > 1.0` else `ValueError`.
- **Drop-in:** append `Expert("cadence_change", detect_cadence_change, format_cadence_change_hit)` to `EXPERTS`; add `_run_demo_cadence_change` + `--demo-cadence-change` in `build_parser`/`main`.
- **Data/tests (answer-key-first):** records showing a clean monthly→weekly shift, a steady-cadence negative control, and an undated/too-few-occurrences edge; hand-written `CADENCE_CHANGE_ANSWER_KEY` + a `REPORT_ANSWER_KEY` row. **NOTE:** adding records to `SAMPLE_RECORDS` ripples `ANSWER_KEY`/`ANSWER_KEY_V1`/`REPORT_ANSWER_KEY(_V1)` — either update all of them, OR (cleaner, as done in Phase B) drive the new rule's tests from **inline records** + keep one or two SAMPLE records minimal. Decide at build time. `tests/test_cadence_change.py`: 4 classes — MatchesAnswerKey, InputValidation, Behavior, **Firewall**.
- **Docs:** `docs/agent-guides/architecture.md` (→ **5 rules**, new test count, `--demo-cadence-change`, EIGHT answer keys if a new key is added), `STATUS.md`.
- **Sequencing:** branch `claude/cadence-change` off `main` **after #10 merges** (keeps a clean base; avoids `STATUS.md`/`architecture.md` collisions). Draft PR; Scott merges.

## KNOWN GOTCHAS (read before "fixing")
- **Windows `autocrlf=true`:** working-copy files show CRLF, but git **commits LF** (verified via `git ls-files --eol` → `i/lf`). `.claude/hooks/session_start.sh` is LF in the index and runs clean on Linux/CI. **Do NOT "fix" CRLF locally** — it's only the local checkout.
- **No `make`/`ruff`/`mypy`/`uv` on Scott's Windows box** (the hook prints `dev tools present: (none)`). `make check` can't run locally here — run its components directly: `python -m unittest discover -s tests -t .` · `python recurrence.py --self-test` · `python -m compileall -q recurrence.py tests data scripts`. **CI runs ruff/lint.**
- **Broken PostToolUse hook in the editing harness** (`check-sql-files.py`, missing script) fires on every Write/Edit — harmless noise, NOT in this repo. (A spawn-task was flagged earlier to fix/disable it.)
- **Branch protection on `main`:** 4 `test` checks + conversation-resolution + linear history. **Rebase** feature branches (not merge). Scott merges; nothing auto-merges. Keep PRs **draft until asked**.
- The **`lint` CI check is not yet a *required* check** (FOLLOW-UP in `STATUS.md`): Scott to add it in GitHub branch-protection settings.
- `git push` worked this session (not allowlist-blocked); per `CLAUDE.md` the fallback is the GitHub API write tool (`create_or_update_file`) if it ever is.

## CONVENTIONS IN EFFECT (from `AGENTS.md` / `architecture.md`)
- **Librarian, not interpreter** — surface/count/cite; never score/rank/diagnose. Banned-word firewall enforced by tests.
- Pure stdlib; zero real PHI; no network egress.
- Defaults stay exact-v0; new behavior is opt-in.
- **Answer key written by hand FIRST**; code matched to it — never patch the key toward the code.
- Validate args (`ValueError`). Determinism (stable ordering).
- Log decisions as ADRs (`docs/adr/`, with a Confirmation field).

## POINTERS
- Plan: `C:\Users\losts\.claude\plans\i-want-you-to-humming-kay.md`
- Repo: `Inbound-health-care/Health-Prototype` · clone `C:\Users\losts\Health-Prototype`
- PRs: **#9** merged (control docs) · **#10** open (co-occurrence window) · this handoff is its own branch `claude/session-handoff-2026-06-04`
- RAG kit: `C:\Users\losts\OneDrive\Desktop\Rag research\` (done; local files)
- Source of truth: `AGENTS.md` (rules) · `STATUS.md` (state) · `docs/agent-guides/architecture.md` (engine facts) · `docs/adr/` (decisions)

## ACCEPTANCE — next session is bootstrapped when
1. `AGENTS.md` + `STATUS.md` read; #10 status confirmed via `gh`/`git`.
2. State verified by running the suite (not assumed).
3. If #10 merged → branch `claude/cadence-change` off `main` and build Phase C per the spec above (answer-key-first, 4 test classes incl. firewall, draft PR).
4. Scott asked ≤1 clarifying question.

NOT complete if: the engine architecture is re-explained to Scott · the firewall is weakened · `make` is assumed to exist locally · the answer key is patched toward the code.
