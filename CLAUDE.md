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
- **Merging PRs (set 2026-06-05):** Scott controls merges. Claude MAY merge a PR
  (GitHub MCP, squash — respecting branch protection: linear history + required
  checks), but ONLY after asking Scott and getting his explicit OK for that
  specific PR. Never auto-merge; never merge without the per-PR ask. (Refines the
  older "Scott merges, nothing auto-merges" convention; relates to
  `SECURITY_AND_TOOL_POLICY.md` §B.)

Everything else — operator rules, tone, the librarian rule,
working limits, commands, where-to-find-things, scope — is in `AGENTS.md`.
