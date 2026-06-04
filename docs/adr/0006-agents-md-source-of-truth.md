# 0006 — Adopt AGENTS.md as the source of truth; slim CLAUDE.md; add a control-doc layer

- **Evidence level:** IMPLEMENTED_UNVERIFIED (docs-only change; to be confirmed
  by `make check` green + the SessionStart hook still exiting 0 + a grep showing
  no rule duplication and no content lost from the old CLAUDE.md).
- **Date:** 2026-06-03

## Context
The repo had `CLAUDE.md` as its primary control doc but no `AGENTS.md`, no
consolidated security/tool policy, no startup-audit format, and no repo file map;
the `Makefile` had no single `check` gate (since added on `main` via PR #8; this PR relies on it and does not re-add it). A 2026 freshness check found that
**`AGENTS.md` is now the cross-tool open standard** (Linux Foundation / Agentic AI
Foundation; read natively by Codex, Cursor, Copilot, Zed, VS Code, Warp, etc.),
while **Claude Code still reads only `CLAUDE.md`**. So having a thin `AGENTS.md`
point at a rich `CLAUDE.md` (the obvious first instinct) is backwards: every
non-Claude tool reads `AGENTS.md` and would get only an indirection.

Security doctrine already existed in Scott's Drive (prompt-injection harness,
09_CHATGPT workflow rules, 00_CORE permission boundaries, source-of-truth
hierarchy) and `docs/DOC_DISCIPLINE.md` already owned the evidence levels — but
none of it was consolidated into the repo where agents act.

## Decision
- **`AGENTS.md` becomes the engine-agnostic source of truth** (operator rules,
  working limits, engine firewall, commands, where-to-find, load order, scope).
- **`CLAUDE.md` is slimmed to a pointer** to `AGENTS.md` plus only the
  genuinely Claude-Code-specific notes (`git push` allowlist → GitHub API write
  fallback; the `.claude/` skill/hook/commands). **No symlink** — two real files,
  cross-platform safe (Windows/OneDrive). No content was dropped, only relocated.
- **Add `SECURITY_AND_TOOL_POLICY.md`** — ported/consolidated from the Drive
  doctrine above + 2026 OWASP-LLM / least-privilege guidance; it *references*
  `DOC_DISCIPLINE.md` for evidence levels rather than restating them.
- **Add `LOAD_TRACE_TEMPLATE.md`** (startup audit) and wire two `echo` lines into
  `.claude/hooks/session_start.sh`; **add `PROJECT_MAP.md`** (file map from the
  live tree).
- **Update `LOAD.md`** +
  the `repo-onboard` skill to the AGENTS.md-first load order.

Rejected: (a) thin `AGENTS.md` → rich `CLAUDE.md` (against the standard;
weakens cross-tool portability); (b) symlink `CLAUDE.md` → `AGENTS.md` (symlinks
break on some Windows/OneDrive checkouts; mixes Claude-specific quirks into the
shared file); (c) writing fresh security doctrine (would diverge from the Drive
source — consolidate instead).

## Consequences
- One source of truth for rules, read by every agent; Claude Code still works via
  the slim `CLAUDE.md`.
- The control docs only *point* — rules are single-sourced (firewall in
  `AGENTS.md`, evidence levels in `DOC_DISCIPLINE.md`, engine facts in
  `architecture.md`), so they cannot drift apart.
- `make check` gives local/agent sessions one verification target (CI is
  unchanged — it does not call `make`).
- Docs-only: the engine (`recurrence.py`, `tests/`, `data/`) is untouched.

## Confirmation
- `make check` (test + `--self-test` + lint) green after the change.
- `bash .claude/hooks/session_start.sh` prints the new orientation lines and exits 0.
- `grep` of the new/edited control docs shows pointers only (no duplicated rules);
  the six evidence levels appear only in `docs/DOC_DISCIPLINE.md`.
- A diff of the old `CLAUDE.md` confirms every rule now lives in either `AGENTS.md`
  (shared) or the slim `CLAUDE.md` (Claude-specific) — nothing lost.
