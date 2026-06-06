# CLAUDE.md — health-prototype (Claude Code notes)

**Read `AGENTS.md` first — it is the source of truth for this repo** (operator
rules, working limits, the librarian rule, commands, load order). It applies to
you. This file holds ONLY Claude-Code-specific notes that don't belong in the
engine-agnostic `AGENTS.md`.

Why two files: `AGENTS.md` is the open cross-tool standard (every agent reads it);
Claude Code still reads `CLAUDE.md`. So the rules live once in `AGENTS.md` and this
file just points there and adds the Claude-specific bits below.

## Claude-Code-specific notes
- **`git push` may be blocked** by the session repo allowlist even with the GitHub
  app authorized — the GitHub **API write tool** (`create_or_update_file`) may
  still work. Use it to persist when push fails.
- **`.claude/` tooling in this repo:**
  - Skill `repo-onboard` (`.claude/skills/repo-onboard/`) — onboarding; or say
    "load repo settings". Front door: `LOAD.md`.
  - Hook `.claude/hooks/session_start.sh` — orientation + toolchain check at start.
  - Commands `.claude/commands/` — `handoff`, `drift-check`, `new-phase`,
    `audit-prompt`.
- **End-session protocol (set 2026-06-06) — sessions close READ-ONLY, diary in chat.**
  Ending a session runs `/handoff`'s 5 steps: (1) check state + run a drift check; (2) close
  everything blocking AND non-blocking (PRs merged/closed, CI green, docs reconciled); (3) list
  it all for Scott to audit; (4) do whatever he says; (5) **only AFTER the final push/merge,
  switch to read-only** — no more commits/pushes, and write the diary in **chat only** (never a
  committed JOURNAL.md/handoff file; Scott logs his own thoughts). This REPLACES the old
  commit-and-push JOURNAL handoff. Session WORK still gets committed during step 2; read-only is
  only for after closure.
- **Merging PRs (set 2026-06-05):** Scott controls merges. Claude MAY merge a PR
  (GitHub MCP, squash — respecting branch protection: linear history + required
  checks), but ONLY after asking Scott and getting his explicit OK for that
  specific PR. Never auto-merge; never merge without the per-PR ask. (Refines the
  older "Scott merges, nothing auto-merges" convention; relates to
  `SECURITY_AND_TOOL_POLICY.md` §B.)
- **Operator knows the harness gates — stop narrating them (set 2026-06-05).** Scott
  is aware of: the per-PR merge ask-gate; the PR webhook subscription (it delivers CI
  *failures* + review comments, NOT CI-success or push/rebase/merge-conflict
  transitions); and that `send_later`/auto-scheduling may be absent in a session.
  These are intentional gates, not news. Verify state at session start if you must,
  then act within them quietly — repeating "no send_later / webhooks won't report
  success" every turn is the noise he asked to stop. The gate doesn't fully constrain
  you, so stay careful; just lose the play-by-play.

Everything else — operator rules, tone, the librarian rule,
working limits, commands, where-to-find-things, scope — is in `AGENTS.md`.
