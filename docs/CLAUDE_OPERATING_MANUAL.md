# Claude Operating Manual

_For Scott. How to get consistent, optimized behavior out of Claude even though
each session is a fresh, memory-less instance. Written 2026-05-31._

## The core truth
**Claude resets every session and silently changes over time.** A new session
remembers NOTHING from the last one, and the underlying model is updated
periodically without notice. So you cannot "train" Claude directly. What you CAN
do is engineer the **harness** — the files and config a fresh instance reads on
startup. *The harness is the part of Claude that persists.* Every rule you write
down becomes part of the next Claude.

(This is your own METHOD-001, "harness engineering", applied to Claude itself.)

## The persistence levers (your real control panel)

| Lever | File / location | What it does | Status |
|---|---|---|---|
| **Constitution** | `CLAUDE.md` | Auto-read every session: rules, firewall, commands, frugality | ✅ live |
| **Front door** | `STATUS.md` | "Where am I / next step" — carries state across the reset | ✅ live |
| **Auto-verify + orient** | `.claude/settings.json` + `.claude/hooks/session_start.sh` | Runs on session start: points Claude at the docs, runs tests so it can verify its own work | ✅ added |
| **Saved workflows** | `.claude/commands/*.md` | Slash commands that force a habit on demand | ✅ added |
| **Helpers** | subagents | Fan out bulk work; they read in their own context, return summaries | ✅ in use |
| **Tools** | connectors / MCP | Add/remove capabilities (Drive, GitHub, …) | manage in settings |

## Slash commands now available
Type these to force the disciplined path (they work because they're files, not
memory):
- **`/new-phase <topic>`** — web-search current best practice → document → plan →
  then build. Encodes your "search before every phase" rule.
- **`/drift-check`** — your METHOD-003 audit: stale claims, wrong numbers,
  source-of-truth conflicts, evidence-level mislabels.
- **`/handoff`** — update STATUS.md + log what changed, so the next session
  inherits it. Run this at the END of every work session.

## How to "optimize Claude" (the loop)
1. Notice a behavior you want (good to keep, or bad to stop).
2. Write it as a rule in `CLAUDE.md` (durable behavior) OR a slash command (a
   workflow you invoke). Don't leave it in chat — chat dies.
3. If it should happen automatically, make it a **hook** (the harness runs it,
   not Claude's memory).
4. Tell Claude to **surface and log** when it changes approach, so improvements
   get captured instead of lost. (This rule is in CLAUDE.md.)

## What you can watch for (catching drift / waste in real time)
- Claude reads a whole file right before making a near-identical copy → should
  `copy_file` (see `docs/TOOLS_CHEAT_SHEET.md`).
- Claude changes how it does something without saying so → ask it to log the change.
- A doc says something that's no longer true → run `/drift-check`.
- Claude claims "done"/"pushed" → confirm the evidence level (did YOU see it, or
  did Claude just assert it?).

## Maintenance
- Keep `CLAUDE.md` tight (~80 lines). Overlong = the fresh instance skims it.
- Re-run `/handoff` at session end and `/drift-check` every few cycles.
- When you move machines/repos, these files travel WITH the repo — that's how the
  optimization follows you.
