---
name: repo-onboard
description: Load Scott's operating rules and current project state for the health-prototype repo. Use at the START of any session working in this repo, when Scott says "load repo settings"/"load", or whenever you are unsure of the operator rules, tone, or where the project stands.
---

# repo-onboard skill

When this skill activates, do this and nothing else first:

## 1. Read, in order (Tier 1 — every session)
1. `AGENTS.md` — source of truth: operator rules, working limits, the librarian rule.
2. `CLAUDE.md` — Claude-Code-specific notes (points back to AGENTS.md).
3. `STATUS.md` — current state / next step. CANONICAL if anything conflicts.
4. `docs/COLD_START_HANDOFF.md` — orientation.

## 2. Report back (then STOP and wait)
One sentence each:
- (a) the operator rules you will hold (tone: dry, no emojis, Scott sets tone),
- (b) current project state,
- (c) the next step.
Then ask Scott where to start. Do NOT begin work until he answers.

## 3. Load deeper layers ONLY when the task needs them (Tier 3 — on demand)
- Architecture / commands / how the engine works -> `docs/agent-guides/architecture.md`
- Decisions / why X -> `docs/adr/`
- Narrative / lessons / limitations -> `JOURNAL.md`
- Full prior-session detail (handoffs + session log) -> Drive: `health-prototype/archive` (off-repo)
- Subagent-audit + code-review method -> `docs/AGENT_AUDIT_METHOD.md`
- Token-frugal tool patterns -> `docs/TOOLS_CHEAT_SHEET.md`
- Other project (clinical scribe) -> `SOVEREIGN_SCRIBE_SALVAGE.md`
- Data field meanings -> `data/RECORDS.md`
Pull on demand. Do not front-load everything — it wastes context.

## 4. Long-context self-check (run periodically; you degrade as the window grows)
- Re-read AGENTS.md "Operator rules" before any big step. If you catch yourself
  using emojis/hype, you have already drifted — re-read and correct.
- When the session gets long or a task gets complex, SAY: "Context is getting long
  — want me to re-load repo-onboard / start fresh?" Offer it; let Scott decide.
- Verify "done/pushed" against the real remote, not memory.
- If state looks off, assume Scott worked elsewhere; READ state; do not call it
  "drift."

Contract: activate -> read 3 -> report 3 -> ask. Branch out only as needed.
