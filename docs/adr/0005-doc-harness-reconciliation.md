# 0005 — Reconcile the stranded doc/harness stack; adopt Tier-1/Tier-3 split

- **Evidence level:** CONFIRMED_ASSISTANT_SIDE (docs-only change; `make test`,
  `--self-test`, and `make lint` green afterward — the engine is untouched).
- **Date:** 2026-05-31

## Context
A re-audit, after parallel work landed from places this session couldn't see
(Codex, CodeRabbit, earlier web sessions), found that
`claude/recurrence-detection-spec-jm3Ck` — the original PR #1 development branch —
kept growing AFTER PR #1 was squash-merged. It carried ~12 commits of doc/harness
work that never reached `main`: `LOAD.md`, the `repo-onboard` skill, a Tier-3
architecture guide, the agent-audit method, two handoffs, a full session log, the
Sovereign Scribe salvage, an Operator Rules + assistant-limitations section in
CLAUDE.md, and two JOURNAL entries.

The trap: that branch PRE-DATES co-occurrence (PR #3) and the branch-audit helper
(PR #4). Its `recurrence.py`, `CLAUDE.md`, and architecture guide all assert the
OLD engine shape — "3 rules / 53 tests / FIVE answer keys, no co-occurrence." A
naive `merge spec-jm3Ck -> main` would have REVERTED #3/#4 and reintroduced stale
facts.

## Decision
- **Cherry-pick, don't merge.** Bring only the additive doc/harness commits onto
  a fresh branch off `main` (`claude/nifty-fermat-g4cKA`). Eight commits were pure
  new files (zero conflict); CLAUDE.md and JOURNAL.md were reconciled by hand.
- **Adopt the Tier-1 / Tier-3 split** the stack was building: CLAUDE.md becomes
  lean (operator rules + limits + the librarian rule + pointers); engine detail
  (commands / architecture map / hard rules / workflow) moves to
  `docs/agent-guides/architecture.md`.
- **Correct the stale engine facts on the way in.** The imported CLAUDE.md trim
  and architecture guide were rewritten to current reality (4 rules incl.
  co-occurrence, 68 tests, SEVEN keys, `--demo-cooccurrence` / `--report-v1`,
  "5th rule = drop-in"). The lean CLAUDE.md states NO counts, so it cannot go
  stale; the architecture guide is the single place counts live.
- **Two JOURNAL entries** (self-improving-loop ~03:59, long-context-limitation
  ~04:08) were inserted in chronological slot below the co-occurrence entry,
  bodies verbatim; their original "(later)/(latest)" labels — which only made
  sense on the isolated branch timeline — were replaced with commit-time stamps
  to disambiguate the merged timeline.
- **Closed PR #5** as a duplicate of PR #6 (same Codex task, same changes).

Rejected: (a) branch-merge of `spec-jm3Ck` (would revert #3/#4); (b) drop the
architecture guide and keep all detail in CLAUDE.md (keeps CLAUDE.md heavy and
discards the deliberate progressive-disclosure design).

## Consequences
- The doc/harness work persists on `main`'s line without touching the engine.
- CLAUDE.md stays lean and count-free; the architecture guide is the single
  source for engine facts and must be kept in sync with the code (noted in it).
- `spec-jm3Ck` is now superseded for docs but must still NOT be merged (it lacks
  co-occurrence / branch-audit); it is slated for retirement.

## Confirmation
- `make test` (68), `python recurrence.py --self-test` (6), and `make lint` all
  green after the change — proving it is docs-only and the engine is untouched.
- `grep -RInE "3 rules|53 tests|FIVE (hand|answer)" CLAUDE.md docs/agent-guides/`
  returns nothing — no stale engine facts survived the import.
